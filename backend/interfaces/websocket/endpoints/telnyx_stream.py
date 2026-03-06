"""
Telnyx E2E Audio Stream WebSocket Endpoint.
Part of the Interfaces Layer (WebSocket Transport).

Endpoint dedicado pura y exclusivamente a procesar el tráfico WebRTC de Telnyx.
Separación rigurosa: Ni Twilio ni Simulator Web tienen acceso aquí.

REFACTORED (Sprint 1 — Marzo 2026):
  - Reemplazado audioop.ulaw2lin() (eliminado en Python 3.13) con implementación pura Python
  - Eliminado dead code 'worker_task' en bloque finally
  - Corregido parsing del stream_id desde evento 'start' (usaba key 'raw' inexistente)
  - Logging mejorado con call_session_id para trazabilidad E2E

References:
  - telnyx_call_architecture.md §7 Pipeline de Audio
  - telnyx_native_orchestrator.md §3a Media Streaming
"""
import base64
import json
import logging
import asyncio
import struct
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend.application.services.call_orchestrator import CallOrchestrator
from backend.domain.ports.persistence_port import AgentRepository, CallRepository
from backend.domain.use_cases.end_call import EndCallUseCase
from backend.domain.use_cases.generate_response import GenerateResponseUseCase
from backend.domain.use_cases.process_audio import ProcessAudioUseCase
from backend.domain.use_cases.start_call import StartCallUseCase
from backend.domain.use_cases.synthesize_text import SynthesizeTextUseCase
from backend.domain.value_objects.audio_format import AudioFormat
from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter as GroqAdapter
from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
from backend.infrastructure.factories.telephony_factory import TelephonyAdapterFactory
from backend.interfaces.deps import get_agent_repository, get_call_repository
from backend.interfaces.websocket.transports.telephony_protocol import TelephonyProtocol

from backend.infrastructure.registries.dtmf_registry import DtmfRegistry

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Audio conversion ─────────────────────────────────────────────────────────

def _ulaw_to_pcm16(ulaw_bytes: bytes) -> bytes:
    """
    Convert G.711 µ-law encoded bytes to linear PCM 16-bit.

    Replaces audioop.ulaw2lin() which was deprecated in Python 3.11
    and removed in Python 3.13.

    Algorithm: ITU-T G.711 µ-law decompression
      - Invert all bits
      - Extract sign (bit 7), exponent (bits 6-4), mantissa (bits 3-0)
      - Reconstruct linear sample: ((mantissa << 1) + 33) << exponent
      - Apply sign

    Output: little-endian signed 16-bit PCM, 2 bytes per input byte.
    """
    output = bytearray(len(ulaw_bytes) * 2)
    write_pos = 0
    for byte_val in ulaw_bytes:
        b = (~byte_val) & 0xFF
        exponent = (b >> 4) & 0x07
        mantissa = b & 0x0F
        sample = ((mantissa << 1) + 33) << exponent
        if b & 0x80 == 0:          # negative sample
            sample = -sample
        # Clamp to int16 range and pack little-endian
        clamped = max(-32768, min(32767, sample))
        struct.pack_into('<h', output, write_pos, clamped)
        write_pos += 2
    return bytes(output)


def _decode_audio(raw_bytes: bytes, codec: str) -> bytes:
    """
    B-05: Decode incoming Telnyx audio based on the session codec.

    PCMU (G.711 µ-law) → _ulaw_to_pcm16() required
    L16 (PCM linear)   → pass-through (already PCM16 native)
    """
    if codec == "L16":
        return raw_bytes  # Native PCM16, no conversion needed
    return _ulaw_to_pcm16(raw_bytes)


# ── Orchestrator factory ─────────────────────────────────────────────────────

async def build_telnyx_orchestrator(
    agent_repo: AgentRepository,
    call_repo: CallRepository,
) -> CallOrchestrator:
    """Build an isolated, sealed orchestrator for Telnyx calls."""
    llm_port       = GroqAdapter()
    tts_port       = AzureTTSAdapter()
    stt_port       = AzureSTTAdapter()
    telephony_port = TelephonyAdapterFactory.get_adapter("telnyx")

    start_call        = StartCallUseCase(call_repo, agent_repo)
    process_audio     = ProcessAudioUseCase(stt_port)
    generate_response = GenerateResponseUseCase(llm_port, tts_port)
    end_call          = EndCallUseCase(call_repo, telephony_port)
    synthesize_text   = SynthesizeTextUseCase(tts_port)

    return CallOrchestrator(
        start_call_uc=start_call,
        process_audio_uc=process_audio,
        generate_response_uc=generate_response,
        end_call_uc=end_call,
        synthesize_text_uc=synthesize_text,
        stt_port=stt_port,
        llm_port=llm_port,
        tts_port=tts_port,
    )


# ── Main WebSocket handler ───────────────────────────────────────────────────

async def handle_telnyx_stream(
    websocket: WebSocket,
    call_control_id: str,
    client_state: Optional[str] = None,
    agent_id: str = "",   # Empty = loads active agent from DB (the Dashboard clone)
    agent_repo: AgentRepository = Depends(get_agent_repository),
    call_repo: CallRepository = Depends(get_call_repository),
) -> None:
    """
    Dedicated handler for Telnyx bidirectional audio streaming.

    Logically isolated from Twilio and Browser. Invoked within the unified
    /ws/media-stream endpoint to avoid proxy blocking rules (HTTP 422).

    Flow:
        1. Accept WebSocket
        2. Load agent + flow_config for telemetry flags
        3. Build isolated CallOrchestrator
        4. Configure optional recording / forking / SIPREC
        5. Process frames: start → media (audio) → stop
    """
    await websocket.accept()

    # Use call_control_id as the primary session identifier for this WebSocket.
    # call_session_id (the cross-leg correlator) is extracted from the 'start' event.
    stream_id = call_control_id
    session_codec = "PCMU"          # B-05: updated from 'start' event
    call_session_id = call_control_id  # B-09: for DtmfRegistry key
    logger.info(f"☎️ [TELNYX] WS connected: call_control_id={call_control_id}")

    protocol = TelephonyProtocol(client_type="telnyx")
    protocol.set_stream_id(call_control_id)

    orchestrator = await build_telnyx_orchestrator(agent_repo, call_repo)
    audio_fmt    = AudioFormat.for_client("telnyx")

    # Load agent for flow_config flags (telemetry, recording, etc.)
    agent = (
        await agent_repo.get_agent_by_uuid(agent_id)
        if agent_id
        else await agent_repo.get_active_agent()
    )
    flow_config: dict = (
        agent.metadata.get("flow_config", {})
        if agent and agent.metadata
        else {}
    )

    telnyx_client = TelnyxClient()

    # ── Optional async telemetry tasks (non-blocking) ────────────────────────
    # NOTE: Noise suppression disabled — Telnyx AGC caused volume
    # fluctuations and silenced the AI assistant (discovered FASE 8).
    # Re-enable only via explicit flow_config flag:
    #   flow_config.get("telnyx_noise_suppression", False)

    if flow_config.get("telnyx_record_s3", False):
        logger.info(f"☎️ [TELNYX] 📼 Activating dual cloud recording: {call_control_id}")
        asyncio.create_task(telnyx_client.start_recording(call_control_id, channels="dual"))

    if flow_config.get("telnyx_fork_udp"):
        udp_target = flow_config["telnyx_fork_udp"]
        logger.info(f"☎️ [TELNYX] 🔱 Activating live forking → {udp_target}")
        asyncio.create_task(telnyx_client.start_forking(call_control_id, udp_target))

    if flow_config.get("telnyx_siprec_dest"):
        siprec_dest = flow_config["telnyx_siprec_dest"]
        logger.info(f"☎️ [TELNYX] 🏛️ Activating SIPREC → {siprec_dest}")
        asyncio.create_task(telnyx_client.start_siprec(call_control_id, siprec_dest))

    # ── WebSocket message loop ───────────────────────────────────────────────
    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            if "text" not in message:
                continue

            event = protocol.parse_message(message["text"])

            # ── 'start' — stream initialized ─────────────────────────────────
            if event["type"] == "start":
                # Extract stream_id from the parsed event (protocol handles the
                # nested 'start.stream_id' path correctly — no 'raw' key needed)
                stream_id = event.get("stream_id") or call_control_id
                call_session_id = event.get("call_session_id") or stream_id
                session_codec = event.get("codec", "PCMU")  # B-05: detect L16 or PCMU
                protocol.set_stream_id(stream_id)
                logger.info(
                    f"☎️ [TELNYX] Stream started: stream_id={stream_id} "
                    f"session_id={call_session_id} codec={session_codec}"
                )

                # B-09: Register this orchestrator by call_session_id so
                # that _handle_dtmf() in telephony.py can route signals here
                await DtmfRegistry.register(call_session_id, orchestrator)
                logger.debug(f"☎️ [TELNYX] DtmfRegistry registered: {call_session_id}")

                # ── Callbacks for the orchestrator ────────────────────────────

                async def send_tts_audio(audio_bytes: bytes) -> None:
                    """Push TTS audio chunk back to caller via WebSocket."""
                    try:
                        if audio_bytes:
                            msg = protocol.create_media_message(audio_bytes)
                            await websocket.send_text(msg)
                    except Exception as ws_err:
                        logger.warning(f"☎️ [TELNYX] TTS send failed: {ws_err}")

                async def send_transcript_event(role: str, text: str) -> None:
                    """Handle orchestrator signals (barge-in clear, transcript)."""
                    if role == "clear":
                        logger.info(
                            f"☎️ [TELNYX] 🗑️ Barge-in: sending clear event to Telnyx"
                        )
                        clear_msg = protocol.create_clear_message()
                        if clear_msg:
                            try:
                                await websocket.send_text(clear_msg)
                            except Exception as clr_err:
                                logger.error(f"☎️ [TELNYX] Clear send failed: {clr_err}")

                async def disconnect_call() -> None:
                    """Close the WebSocket connection."""
                    logger.info(f"☎️ [TELNYX] Closing WS for stream_id={stream_id}")
                    try:
                        await websocket.close()
                    except Exception:
                        pass

                # ── Start the core orchestrator ───────────────────────────────
                # Injecting agent pulls ALL dashboard controls (system prompt,
                # voice, tools, etc.) from the DB.
                greeting_audio = await orchestrator.start_session(
                    agent_id=agent_id,
                    stream_id=call_control_id,
                    audio_output_callback=send_tts_audio,
                    transcript_callback=send_transcript_event,
                    disconnect_callback=disconnect_call,
                    client_type="telnyx",
                )

                if greeting_audio:
                    logger.info(
                        f"☎️ [TELNYX] Streaming greeting "
                        f"({len(greeting_audio)} bytes)"
                    )
                    try:
                        await websocket.send_text(
                            protocol.create_media_message(greeting_audio)
                        )
                    except Exception as greet_err:
                        logger.error(f"☎️ [TELNYX] Greeting send failed: {greet_err}")

            # ── 'media' — incoming audio frame ───────────────────────────────
            elif event["type"] == "media":
                raw_bytes = event.get("data", b"")
                if raw_bytes and orchestrator.active:
                    # B-05: Codec-aware decode — L16 passes through, PCMU decompressed
                    try:
                        pcm16_bytes = _decode_audio(raw_bytes, session_codec)
                    except Exception as dec_err:
                        logger.error(
                            f"☎️ [TELNYX] Audio decode error ({session_codec}): {dec_err}"
                        )
                        continue

                    await orchestrator.push_audio_frame(
                        raw_audio=pcm16_bytes,
                        sample_rate=16000 if session_codec == "L16" else audio_fmt.sample_rate,
                        channels=audio_fmt.channels,
                    )

            # ── 'stop' — stream ended cleanly ────────────────────────────────
            elif event["type"] == "stop":
                logger.info(f"☎️ [TELNYX] Stop event: stream_id={stream_id}")
                await orchestrator.end_session(reason="completed")
                break

    except WebSocketDisconnect:
        logger.info(f"☎️ [TELNYX] WS disconnected: stream_id={stream_id}")
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] Fatal WS error: {exc}", exc_info=True)
    finally:
        # B-09: Unregister from DtmfRegistry so stale sessions don't leak
        await DtmfRegistry.unregister(call_session_id)
        logger.debug(f"☎️ [TELNYX] DtmfRegistry unregistered: {call_session_id}")
        # Ensure orchestrator session is always cleaned up on exit
        if orchestrator.active:
            await orchestrator.end_session(reason="disconnected")
        # Close the TelnyxClient persistent HTTP connection
        try:
            await telnyx_client.close()
        except Exception:
            pass
