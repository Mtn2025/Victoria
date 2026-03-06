"""
Telnyx E2E Audio Stream WebSocket Endpoint.
Endpoint dedicado pura y exclusivamente a procesar el tráfico WebRTC de Telnyx.
Separación rigurosa: Ni Twilio ni Simulator Web tienen acceso aquí.
"""
import base64
import json
import logging
import asyncio
import time
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
from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient

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
    
    # Cargar agente para revisar flags de Telemetría Corporativa Telnyx
    agent = await agent_repo.get_agent_by_uuid(agent_id) if agent_id else await agent_repo.get_active_agent()
    
    # flow_config se guarda como blob JSON en el diccionario metadata de la entidad Agent
    flow_config = agent.metadata.get("flow_config", {}) if agent and agent.metadata else {}
    
    telnyx_client = TelnyxClient()

    # Disparadores Asíncronos Inmediatos para limpiar tráfico (No bloqueantes)
    if flow_config.get("telnyx_noise_suppression", True):
        logger.info(f"🎧 [TELNYX E2E] Activating Dynamic Noise Suppression for {call_control_id}")
        asyncio.create_task(telnyx_client.start_noise_suppression(call_control_id))
        
    if flow_config.get("telnyx_record_s3", False):
        logger.info(f"📼 [TELNYX E2E] Activating Dual Cloud Recording for {call_control_id}")
        asyncio.create_task(telnyx_client.start_recording(call_control_id, channels="dual"))
        
    if flow_config.get("telnyx_fork_udp"):
        target_udp = flow_config.get("telnyx_fork_udp")
        logger.info(f"🔱 [TELNYX E2E] Activating Live Forking to {target_udp} for {call_control_id}")
        asyncio.create_task(telnyx_client.start_forking(call_control_id, target_udp))
        
    if flow_config.get("telnyx_siprec_dest"):
        siprec_dest = flow_config.get("telnyx_siprec_dest")
        logger.info(f"🏛️ [TELNYX E2E] Activating SIPREC Compliance Tunnel to {siprec_dest}")
        asyncio.create_task(telnyx_client.start_siprec(call_control_id, siprec_dest))

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

                    media_queue = asyncio.Queue()
                    clear_event = asyncio.Event()

                    async def pacing_worker():
                        """Background task that sends queued audio and chunk-paces it for Telnyx RTP"""
                        logger.info(f"☎️ [TELNYX E2E] Pacing Worker started for {stream_id}")
                        chunk_size = 160  # 20ms of 8000Hz 8-bit mulaw
                        sleep_time = 0.02 # 20ms sleep
                        
                        while True:
                            try:
                                audio_bytes = await media_queue.get()
                                
                                # Si hubo un barge-in (interrupción) mentras estábamos inactivos (esperando),
                                # la bandera se quedó 'seteada'. Debemos limpiarla para no descartar
                                # ESTE nuevo audio orgánico recién salido del horno.
                                if clear_event.is_set():
                                    clear_event.clear()
                                
                                logger.info(f"☎️ [TELNYX E2E] Dispensing {len(audio_bytes)} bytes of media to PSTN queue in {chunk_size}-byte chunks")
                                
                                next_tick = time.time()
                                for i in range(0, len(audio_bytes), chunk_size):
                                    if clear_event.is_set():
                                        logger.info("☎️ [TELNYX E2E] Pacing Worker cleanly interrupted (Barge-In) mid-stream")
                                        clear_event.clear()
                                        break
                                        
                                    chunk = audio_bytes[i:i + chunk_size]
                                    msg = protocol.create_media_message(chunk)
                                    await websocket.send_text(msg)
                                    
                                    next_tick += sleep_time
                                    delay = next_tick - time.time()
                                    if delay > 0:
                                        # await wait_for an event allows cancelling sleep instantly
                                        try:
                                            await asyncio.wait_for(clear_event.wait(), timeout=delay)
                                            # If wait_for returns instead of raising TimeoutError, event was set
                                            logger.info("☎️ [TELNYX E2E] Pacing Worker interrupted during sleep (Barge-In)")
                                            clear_event.clear()
                                            break
                                        except (asyncio.TimeoutError, TimeoutError):
                                            pass
                                    else:
                                        await asyncio.sleep(0)  # Yield loop, we are lagging slightly
                                        
                                media_queue.task_done()
                            except asyncio.CancelledError:
                                logger.info(f"☎️ [TELNYX E2E] Pacing Worker cancelled for {stream_id}")
                                break
                            except Exception as e:
                                logger.error(f"[TELNYX E2E] Pacing Worker error: {e}")

                    worker_task = asyncio.create_task(pacing_worker())

                    async def send_tts_audio(audio_bytes: bytes) -> None:
                        try:
                            if audio_bytes:
                                # Put in queue instead of sending directly to WS
                                media_queue.put_nowait(audio_bytes)
                        except Exception as ws_err:
                            logger.warning(f"[TELNYX E2E] Failed to queue audio chunk: {ws_err}")

                    async def send_transcript_event(role: str, text: str) -> None:
                        # Evento especial del Orchestrator para limpiar buffers remotos
                        if role == "clear":
                            logger.info(f"☎️ [TELNYX E2E/BARGE-IN] Dispatching CLEAR event to PSTN Jitter Buffer")
                            # 1. Empty the queue
                            while not media_queue.empty():
                                try:
                                    media_queue.get_nowait()
                                except asyncio.QueueEmpty:
                                    break
                            # 2. Wake up pacing worker to cancel sleep
                            clear_event.set()
                            logger.info(f"☎️ [TELNYX E2E/BARGE-IN] Local RTP queue cleared successfully")

                    async def disconnect_call() -> None:
                        logger.info(f"[TELNYX E2E] Closing stream {stream_id}")
                        if 'worker_task' in locals() and worker_task:
                            worker_task.cancel()
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
                        logger.info(f"[TELNYX E2E] Queueing initial greeting... ({len(greeting_audio)} bytes)")
                        media_queue.put_nowait(greeting_audio)

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
        # Guarantee worker task is cancelled on drop
        if 'worker_task' in locals() and worker_task:
            worker_task.cancel()
        if orchestrator.active:
            await orchestrator.end_session(reason="disconnected")
