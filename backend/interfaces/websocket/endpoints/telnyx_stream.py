"""
Telnyx E2E Audio Stream WebSocket Endpoint.
Endpoint dedicado pura y exclusivamente a procesar el tráfico WebRTC de Telnyx.
Separación rigurosa: Ni Twilio ni Simulator Web tienen acceso aquí.
"""
import base64
import json
import logging
import asyncio
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
from backend.infrastructure.factories.telephony_factory import TelephonyAdapterFactory
from backend.interfaces.deps import get_agent_repository, get_call_repository
from backend.interfaces.websocket.transports.telephony_protocol import TelephonyProtocol

router = APIRouter()
logger = logging.getLogger(__name__)


async def build_telnyx_orchestrator(
    agent_repo: AgentRepository,
    call_repo: CallRepository,
) -> CallOrchestrator:
    """Construye un orchestrator aislado y sellado para Telnyx."""
    llm_port = GroqAdapter()
    tts_port = AzureTTSAdapter()
    stt_port = AzureSTTAdapter()
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


async def handle_telnyx_stream(
    websocket: WebSocket,
    call_control_id: str,
    client_state: Optional[str] = None,
    agent_id: str = "", # Vacío = Carga el Agente Activo desde la BD (El Clon del Dashboard)
    agent_repo: AgentRepository = Depends(get_agent_repository),
    call_repo: CallRepository = Depends(get_call_repository),
):
    """
    Función exclusiva para Audio Streaming de Telnyx.
    Aislado lógicamente del navegador y Twilio, pero invocado en el endpoint unificado
    para evitar reglas de bloqueo proxy (Error 422).
    """
    await websocket.accept()
    logger.info(f"[TELNYX E2E] WS Connected: call_control_id={call_control_id}")

    protocol = TelephonyProtocol(client_type="telnyx")
    protocol.set_stream_id(call_control_id)
    
    orchestrator = await build_telnyx_orchestrator(agent_repo, call_repo)
    # Formato estrictamente telefónico dictaminado por infraestructura PSTN:
    audio_fmt = AudioFormat.for_client("telnyx") 
    
    stream_id = call_control_id

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break

            if "text" in message:
                event = protocol.parse_message(message["text"])
                
                if event["type"] == "start":
                    # Telnyx provee su propio stream_id interno en este evento
                    # event_payload["start"]["stream_id"]
                    start_data = event.get("raw", {}).get("start", {})
                    if start_data.get("stream_id"):
                        stream_id = start_data.get("stream_id")
                    
                    protocol.set_stream_id(stream_id)

                    async def send_tts_audio(audio_bytes: bytes) -> None:
                        try:
                            # PARTICIONAMIENTO ESTRICTO TELNYX:
                            # Fragmentos de 160 bytes equivalentes a 20ms de audio MuLaw
                            chunk_size = 160
                            sleep_time = 0.02
                            for i in range(0, len(audio_bytes), chunk_size):
                                chunk = audio_bytes[i:i + chunk_size]
                                msg = protocol.create_media_message(chunk)
                                await websocket.send_text(msg)
                                await asyncio.sleep(sleep_time)
                        except Exception as ws_err:
                            logger.warning(f"[TELNYX E2E] Failed to send audio chunk: {ws_err}")

                    async def send_transcript_event(role: str, text: str) -> None:
                        # Telnyx no tiene una interfaz gráfica para escupir JSON de transcripción
                        # Se ignora pacíficamente, todo queda respaldado en base de datos.
                        pass

                    async def disconnect_call() -> None:
                        logger.info(f"[TELNYX E2E] Closing stream {stream_id}")
                        try:
                            await websocket.close()
                        except Exception:
                            pass

                    # Iniciar el núcleo orquestador marcando "telnyx" puramente.
                    # Aquí la Inyección del Agente arrastra TODOS LOS CONTROLES DEL DASHBOARD 
                    # guardados en DB.
                    greeting_audio = await orchestrator.start_session(
                        agent_id=agent_id,
                        stream_id=call_control_id,
                        audio_output_callback=send_tts_audio,
                        transcript_callback=send_transcript_event,
                        disconnect_callback=disconnect_call,
                        client_type="telnyx",
                    )
                    
                    if greeting_audio:
                        logger.info(f"[TELNYX E2E] Sending initial greeting... ({len(greeting_audio)} bytes)")
                        chunk_size = 160
                        sleep_time = 0.02
                        for i in range(0, len(greeting_audio), chunk_size):
                            chunk = greeting_audio[i:i + chunk_size]
                            resp_msg = protocol.create_media_message(chunk)
                            await websocket.send_text(resp_msg)
                            await asyncio.sleep(sleep_time)

                elif event["type"] == "media":
                    raw_bytes = event.get("data", b"")
                    if raw_bytes and orchestrator.active:
                        await orchestrator.push_audio_frame(
                            raw_audio=raw_bytes,
                            sample_rate=audio_fmt.sample_rate,
                            channels=audio_fmt.channels
                        )

                elif event["type"] == "stop":
                    logger.info(f"[TELNYX E2E] Stop event received for stream_id: {stream_id}")
                    await orchestrator.end_session(reason="completed")
                    break

    except WebSocketDisconnect:
        logger.info(f"[TELNYX E2E] WS Disconnected naturally for {stream_id}")
    except Exception as e:
        logger.error(f"[TELNYX E2E] Fatal WS Error: {e}", exc_info=True)
    finally:
        if orchestrator.active:
            await orchestrator.end_session(reason="disconnected")
