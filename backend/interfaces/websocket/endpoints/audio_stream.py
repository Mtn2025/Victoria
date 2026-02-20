"""
Audio Stream Websocket Endpoint.
Handles real-time audio streaming for Twilio, Telnyx, and Browser clients.
"""
import logging
import asyncio
import json
import base64
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

# Dependencies
from backend.interfaces.deps import get_agent_repository, get_call_repository
from backend.domain.ports.persistence_port import CallRepository, AgentRepository
from backend.application.services.call_orchestrator import CallOrchestrator
from backend.domain.use_cases.start_call import StartCallUseCase
from backend.domain.use_cases.process_audio import ProcessAudioUseCase
from backend.domain.use_cases.generate_response import GenerateResponseUseCase
from backend.domain.use_cases.end_call import EndCallUseCase
from backend.infrastructure.factories.telephony_factory import TelephonyAdapterFactory
# from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
# from backend.infrastructure.adapters.telephony.dummy_adapter import DummyTelephonyAdapter
from backend.interfaces.websocket.transports.telephony_protocol import TelephonyProtocol
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase

# Adapter Imports
from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter as GroqAdapter
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter
from backend.application.processors.vad_processor import VADProcessor
from backend.infrastructure.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

async def build_orchestrator(
    agent_repo: AgentRepository,
    call_repo: CallRepository,
    client_type: str = "twilio"
) -> CallOrchestrator:
    
    # Adapters (Ports)
    llm_port = GroqAdapter() 
    tts_port = AzureTTSAdapter()
    stt_port = AzureSTTAdapter() # Typically needs Azure Key in env
    
    # Telephony Port via Factory (Dynamic Selection) [D-A10-001 Fix]
    telephony_port = TelephonyAdapterFactory.get_adapter(client_type)
    
    # Processors
    detect_turn_end = DetectTurnEndUseCase()
    vad = VADProcessor(config=settings, detect_turn_end=detect_turn_end)
    
    # Use Cases
    start_call = StartCallUseCase(call_repo, agent_repo)
    process_audio = ProcessAudioUseCase(stt_port)
    generate_response = GenerateResponseUseCase(llm_port, tts_port)
    end_call = EndCallUseCase(call_repo, telephony_port)
    
    return CallOrchestrator(
        start_call_uc=start_call,
        process_audio_uc=process_audio,
        generate_response_uc=generate_response,
        end_call_uc=end_call
    )

@router.websocket("/ws/media-stream")
async def audio_stream(
    websocket: WebSocket,
    client: str = "twilio",
    agent_id: str = "default",
    call_control_id: Optional[str] = None,
    client_state: Optional[str] = None,
    # Browser Overrides
    initial_message: Optional[str] = None,
    initiator: Optional[str] = None,
    voice_style: Optional[str] = None,
    agent_repo: AgentRepository = Depends(get_agent_repository),
    call_repo: CallRepository = Depends(get_call_repository)
):
    """
    WebSocket Endpoint for Audio Streaming.
    Supports Twilio, Telnyx, and Browser (Simulator).
    """
    # 1. Handle Browser Context Overrides
    if client == "browser" and not client_state:
        context_data = {}
        if initial_message:
            context_data["first_message"] = initial_message
        if initiator:
            context_data["first_message_mode"] = initiator
        if voice_style:
            context_data["voice_style"] = voice_style
            
        if context_data:
            client_state = base64.b64encode(json.dumps(context_data).encode()).decode()

    await websocket.accept()
    logger.info(f"WS Connected: {client}")
    
    # Initialize Protocol Helper
    protocol = TelephonyProtocol(client_type=client)
    
    # Build Orchestrator
    orchestrator = await build_orchestrator(agent_repo, call_repo, client_type=client)
    
    # Identify Stream
    # For browser/telnyx immediate start, we might generate ID now or wait for 'start'
    stream_id = call_control_id # Might be None initially for Twilio
    
    try:
        # If browser, we might start session immediately if no "start" event needed?
        # Legacy: Simulator sends "start" event too?
        # Legacy `routes_simulator` sends "start" event.
        
        while True:
            # Hybrid Receive Loop
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                break
                
            if "text" in message:
                msg_text = message["text"]
                event = protocol.parse_message(msg_text)
                
                if event["type"] == "start":
                    stream_id = event.get("stream_id") or stream_id
                    protocol.set_stream_id(stream_id)
                    await orchestrator.start_session(agent_id=agent_id, stream_id=stream_id)
                    logger.info(f"Session started: {stream_id}")
                    
                elif event["type"] == "media":
                    if not stream_id:
                        continue
                    chunk = event["data"]
                    async for response_chunk in orchestrator.process_audio_input(chunk):
                        resp_msg = protocol.create_media_message(response_chunk)
                        await websocket.send_text(resp_msg)
                        
                elif event["type"] == "stop":
                    logger.info("Stop event received")
                    break

            elif "bytes" in message:
                # RAW AUDIO (Browser)
                if not stream_id:
                     # Auto-start if stream_id missing for browser?
                     # Better to enforce 'start' event or generate one.
                     pass
                     
                chunk = message["bytes"]
                # Convert to base64 for Orchestrator (Phase 9 compatibility)
                async for response_chunk in orchestrator.process_audio_input(chunk):
                     if client == "browser":
                         await websocket.send_bytes(response_chunk)
                     else:
                         resp_msg = protocol.create_media_message(response_chunk)
                         await websocket.send_text(resp_msg)

    except WebSocketDisconnect:
        logger.info("WS Disconnected")
    except Exception as e:
        logger.error(f"WS Error: {e}")
    finally:
        await orchestrator.end_session()
        try:
            await websocket.close()
        except:
            pass
