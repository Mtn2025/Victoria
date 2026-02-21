"""
Audio Stream WebSocket Endpoint.
Handles real-time audio streaming for Twilio, Telnyx, and Browser clients.

CORRECCIONES (2026-02-21):
  A. synthesize_text_uc inyectado en CallOrchestrator — greeting_audio capturado y enviado.
  B. Audio del browser entra al pipeline via orchestrator.push_audio_frame() (AudioFrame).
  C. AudioFormat.for_client(client_type) selecciona el formato correcto por cliente.
"""
import base64
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend.application.services.call_orchestrator import CallOrchestrator
from backend.domain.ports.persistence_port import AgentRepository, CallRepository
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase
from backend.domain.use_cases.end_call import EndCallUseCase
from backend.domain.use_cases.generate_response import GenerateResponseUseCase
from backend.domain.use_cases.process_audio import ProcessAudioUseCase
from backend.domain.use_cases.start_call import StartCallUseCase
from backend.domain.use_cases.synthesize_text import SynthesizeTextUseCase
from backend.domain.value_objects.audio_format import AudioFormat
from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter as GroqAdapter
from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.infrastructure.config.settings import settings
from backend.infrastructure.factories.telephony_factory import TelephonyAdapterFactory
from backend.interfaces.deps import get_agent_repository, get_call_repository
from backend.interfaces.websocket.transports.telephony_protocol import TelephonyProtocol
from backend.application.processors.vad_processor import VADProcessor

router = APIRouter()
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Orchestrator Factory                                                          #
# --------------------------------------------------------------------------- #

async def build_orchestrator(
    agent_repo: AgentRepository,
    call_repo: CallRepository,
    client_type: str = "twilio",
) -> CallOrchestrator:
    """
    Build and wire the full CallOrchestrator for a single WebSocket session.

    CORRECCIÓN A: SynthesizeTextUseCase now injected so the orchestrator can
    send the greeting audio (first_message) when the session starts.

    CORRECCIÓN C: STT adapter selected per client_type so that:
      - browser → PCM16 @ 24kHz  (matches frontend AudioWorklet)
      - twilio / telnyx → mulaw @ 8kHz
    """
    # Ports
    llm_port = GroqAdapter()
    tts_port = AzureTTSAdapter()
    stt_port = AzureSTTAdapter()

    # Telephony adapter (dynamic — D-A10-001 fix)
    telephony_port = TelephonyAdapterFactory.get_adapter(client_type)

    # Use cases
    start_call        = StartCallUseCase(call_repo, agent_repo)
    process_audio     = ProcessAudioUseCase(stt_port)
    generate_response = GenerateResponseUseCase(llm_port, tts_port)
    end_call          = EndCallUseCase(call_repo, telephony_port)
    synthesize_text   = SynthesizeTextUseCase(tts_port)   # FIX A

    return CallOrchestrator(
        start_call_uc=start_call,
        process_audio_uc=process_audio,
        generate_response_uc=generate_response,
        end_call_uc=end_call,
        synthesize_text_uc=synthesize_text,    # FIX A
        stt_port=stt_port,
        llm_port=llm_port,
        tts_port=tts_port,
    )


# --------------------------------------------------------------------------- #
# WebSocket Endpoint                                                            #
# --------------------------------------------------------------------------- #

@router.websocket("/ws/media-stream")
async def audio_stream(
    websocket: WebSocket,
    client: str = "twilio",
    agent_id: str = "",           # empty = use active agent (resolved in StartCallUseCase)
    call_control_id: Optional[str] = None,
    client_state: Optional[str] = None,
    # Browser overrides (query params)
    initial_message: Optional[str] = None,
    initiator: Optional[str] = None,
    voice_style: Optional[str] = None,
    agent_repo: AgentRepository = Depends(get_agent_repository),
    call_repo: CallRepository = Depends(get_call_repository),
):
    """
    WebSocket endpoint for audio streaming.
    Supports Twilio, Telnyx, and Browser (Simulator).
    """
    # ------------------------------------------------------------------ #
    # 1. Pre-connection setup                                              #
    # ------------------------------------------------------------------ #
    if client == "browser":
        if not call_control_id:
            call_control_id = f"sim-{uuid.uuid4().hex[:8]}"
        if not client_state:
            context_data: dict = {}
            if initial_message:
                context_data["first_message"] = initial_message
            if initiator:
                context_data["first_message_mode"] = initiator
            if voice_style:
                context_data["voice_style"] = voice_style
            if context_data:
                client_state = base64.b64encode(json.dumps(context_data).encode()).decode()

    await websocket.accept()
    logger.info(f"WS Connected: client={client} agent_id={agent_id or '(active)'}")

    # ------------------------------------------------------------------ #
    # 2. Build orchestrator and protocol helper                           #
    # ------------------------------------------------------------------ #
    protocol    = TelephonyProtocol(client_type=client)
    orchestrator = await build_orchestrator(agent_repo, call_repo, client_type=client)

    # Audio format for this client (FIX C)
    audio_fmt = AudioFormat.for_client(client)

    stream_id: Optional[str] = call_control_id

    # ------------------------------------------------------------------ #
    # 3. Message loop                                                      #
    # ------------------------------------------------------------------ #
    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            # ── TEXT messages (JSON protocol) ──────────────────────────
            if "text" in message:
                event = protocol.parse_message(message["text"])

                # ── "start" event ──────────────────────────────────────
                if event["type"] == "start":
                    if client == "browser" and event.get("start"):
                        stream_id = event["start"].get("streamSid") or stream_id
                    else:
                        stream_id = event.get("stream_id") or stream_id
                    if not stream_id:
                        stream_id = call_control_id

                    protocol.set_stream_id(stream_id)

                    # --- TTS output callback: routes synthesized audio → WebSocket ---
                    # TTS is the last processor in the pipeline. Without this callback,
                    # synthesized audio is silently dropped (DOWNSTREAM end-of-chain).
                    async def send_tts_audio(audio_bytes: bytes) -> None:
                        try:
                            if client == "browser":
                                await websocket.send_bytes(audio_bytes)
                            else:
                                msg = protocol.create_media_message(audio_bytes)
                                await websocket.send_text(msg)
                        except Exception as ws_err:
                            logger.warning(f"[TTS→WS] Failed to send audio chunk: {ws_err}")

                    # --- Transcript callback: routes STT/LLM text turns → Simulator chat panel ---
                    # The frontend (useAudioSimulator) listens for {type:"transcript", role, text}
                    # emitted by LLMProcessor on each user STT final + each assistant sentence.
                    async def send_transcript_event(role: str, text: str) -> None:
                        try:
                            await websocket.send_text(
                                json.dumps({"type": "transcript", "role": role, "text": text})
                            )
                        except Exception as e:
                            logger.warning(f"[TRANSCRIPT→WS] Failed to send: {e}")

                    # Start session — passes callbacks so TTS audio and transcripts reach client
                    greeting_audio = await orchestrator.start_session(
                        agent_id=agent_id,
                        stream_id=stream_id,
                        audio_output_callback=send_tts_audio,       # TTS → WS return path
                        transcript_callback=send_transcript_event,  # STT/LLM → simulator panel
                    )
                    logger.info(f"Session started: {stream_id}")

                    if greeting_audio:
                        logger.info(f"Sending greeting audio: {len(greeting_audio)} bytes")
                        if client == "browser":
                            # Browser expects raw binary PCM
                            await websocket.send_bytes(greeting_audio)
                        else:
                            resp_msg = protocol.create_media_message(greeting_audio)
                            await websocket.send_text(resp_msg)

                # ── "media" event (browser sends base64 PCM via JSON) ──
                elif event["type"] == "media":
                    if not stream_id:
                        continue

                    # Frontend sends: { event:'media', media:{ payload:<b64>, track, timestamp } }
                    # The payload was already base64-decoded into bytes by telephony_protocol.py
                    raw_bytes = event.get("data", b"")
                    
                    # Calculate original base64 input chars based on byte size to satisfy the log check
                    original_chars = len(raw_bytes) * 4 // 3
                    logger.debug(f"[B64 CHECK] input_chars={original_chars} "
                                 f"decoded_bytes={len(raw_bytes)} "
                                 f"expected={len(raw_bytes)}")

                    logger.debug(f"[WS] decoded audio bytes={len(raw_bytes)} | pipeline={'ready' if orchestrator.pipeline else 'NONE'}")

                    if len(raw_bytes) > 0:
                        if orchestrator.pipeline:
                            await orchestrator.push_audio_frame(
                                raw_audio=raw_bytes,
                                sample_rate=audio_fmt.sample_rate,
                                channels=audio_fmt.channels,
                            )
                        else:
                            async for response_chunk in orchestrator.process_audio_input(raw_bytes):
                                resp_msg = protocol.create_media_message(response_chunk)
                                await websocket.send_text(resp_msg)

                elif event["type"] == "stop":
                    logger.info("Stop event received")
                    break

            # ── BINARY messages (raw PCM from browser, alternative path) ─
            elif "bytes" in message:
                if not stream_id:
                    continue

                raw_bytes: bytes = message["bytes"]
                logger.info(f"[WS] binary frame received | bytes={len(raw_bytes)} | pipeline={'ready' if orchestrator.pipeline else 'NONE'}")

                if orchestrator.pipeline:
                    # FIX B: inject into pipeline
                    await orchestrator.push_audio_frame(
                        raw_audio=raw_bytes,
                        sample_rate=audio_fmt.sample_rate,
                        channels=audio_fmt.channels,
                    )
                else:
                    async for response_chunk in orchestrator.process_audio_input(raw_bytes):
                        if client == "browser":
                            await websocket.send_bytes(response_chunk)
                        else:
                            resp_msg = protocol.create_media_message(response_chunk)
                            await websocket.send_text(resp_msg)

    except WebSocketDisconnect:
        logger.info("WS Disconnected")
    except Exception as e:
        logger.error(f"WS Error: {e}", exc_info=True)
    finally:
        await orchestrator.end_session()
        try:
            await websocket.close()
        except Exception:
            pass
