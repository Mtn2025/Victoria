"""
Telephony Endpoints.
Part of the Interfaces Layer (HTTP).
Handles webhooks for Twilio and Telnyx.
"""
import logging
import base64
import json
from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Response, Depends, BackgroundTasks, Header, HTTPException

from backend.infrastructure.config.settings import settings
from backend.interfaces.deps import get_config_repository, get_call_repository, get_agent_repository
from backend.domain.ports.config_repository_port import ConfigRepositoryPort
from backend.domain.ports.persistence_port import CallRepository, AgentRepository
from backend.application.services.outbound_service import OutboundDialerService
from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
# Security deps if needed (Legacy had signature checks)
# For Phase 9, we focus on functionality. We can import security if available or scaffold it.

router = APIRouter(prefix="/telephony", tags=["telephony"])
protected_router = APIRouter(prefix="/telephony", tags=["Telephony Actions"])
logger = logging.getLogger(__name__)

# Instantiate client (Singleton-ish) acting as Port Adapter
telnyx_adapter = TelnyxClient()

from backend.domain.use_cases.telephony_actions import AnswerCallUseCase, StartStreamUseCase

@router.api_route("/twilio/incoming-call", methods=["GET", "POST"])
async def twilio_incoming_call(request: Request):
    """
    Twilio Webhook. Returns TwiML to connect to WebSocket.
    """
    host = request.headers.get("host")
    if not host:
        raise ValueError("Host header is missing")
    ws_url = f"wss://{host}{settings.WS_MEDIA_STREAM_PATH}"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.api_route("/twilio/outbound-twiml", methods=["GET", "POST"])
async def twilio_outbound_twiml(request: Request, agent_id: str):
    """
    Twilio Webhook for outbound calls once connected. Returns TwiML WS Connect.
    Passes agent_id as a custom parameter for the WebSocket.
    """
    host = request.headers.get("host")
    if not host:
        raise ValueError("Host header is missing")
    ws_url = f"wss://{host}{settings.WS_MEDIA_STREAM_PATH}"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="agent_id" value="{agent_id}" />
        </Stream>
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.api_route("/twilio/amd-callback", methods=["POST"])
async def twilio_amd_callback(
    request: Request, 
    agent_id: str,
    config_repo: ConfigRepositoryPort = Depends(get_config_repository),
    call_repo: CallRepository = Depends(get_call_repository)
):
    """
    Async webhook from Twilio reporting Answering Machine Detection result.
    """
    form = await request.form()
    answered_by = form.get("AnsweredBy")
    call_sid = form.get("CallSid")
    
    logger.info(f"☎️ Twilio AMD Callback: Call {call_sid} answered by {answered_by}")
    
    if answered_by in ("machine_start", "machine_end_beep", "machine_end_other"):
        config_dto = await config_repo.get_config(agent_id)
        action = getattr(config_dto, "amd_action", "hangup")
        amd_message = getattr(config_dto, "amd_message", "Hola, le llamábamos para darle información.")
        
        logger.info(f"AMD action config for agent {agent_id}: {action}")
        
        if call_sid:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            if account_sid and auth_token:
                import httpx
                import urllib.parse
                url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
                
                async with httpx.AsyncClient(auth=(account_sid, auth_token)) as client:
                    if action == "leave_message" and amd_message:
                        # Twilio Allows TwiML via URL or inline Twiml parameter.
                        # We use <Play> pointing to our dynamic TTS generator endpoint.
                        host = request.headers.get('host', 'localhost')
                        scheme = request.headers.get('x-forwarded-proto', 'https')
                        base_url = f"{scheme}://{host}"
                        play_url = f"{base_url}/api/telephony/voicemail-audio?agent_id={agent_id}"
                        
                        twiml_str = f"<Response><Play>{play_url}</Play><Hangup/></Response>"
                        await client.post(url, data={"Twiml": twiml_str})
                        logger.info(f"Injected Leave Message TwiML (Play) into call {call_sid}")
                    else:
                        # Default is hangup
                        await client.post(url, data={"Status": "completed"})
                        logger.info(f"Hung up call {call_sid} due to machine detection")
            
            # Update DB History
            try:
                from backend.domain.value_objects.call_id import CallId
                call = await call_repo.get_by_id(CallId(call_sid))
                if call:
                    call.end("voicemail")
                    await call_repo.save(call)
            except Exception as e:
                logger.error(f"Error marking call {call_sid} as voicemail in DB: {e}")
                    
    return Response(content="OK", status_code=200)

@router.api_route("/twilio/status-callback", methods=["POST"])
async def twilio_status_callback(
    request: Request,
    call_repo: CallRepository = Depends(get_call_repository)
):
    """
    Twilio StatusCallback webhook.
    Receives call lifecycle events (ringing, answered, completed, busy, failed, no-answer, canceled).
    """
    form = await request.form()
    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")  # e.g., 'completed', 'busy', 'no-answer', 'failed', 'canceled'

    logger.info(f"☎️ Twilio Status Callback: Call {call_sid} changed to {call_status}")

    if call_sid and call_status in ("completed", "busy", "no-answer", "failed", "canceled"):
        from backend.domain.value_objects.call_id import CallId
        try:
            call = await call_repo.get_by_id(CallId(call_sid))
            if call:
                # If call was already VOICEMAIL or something else, it might already be ended.
                if call.status.value not in ("completed", "voicemail", "failed", "busy", "no_answer"):
                    call.end(reason=call_status)
                    await call_repo.save(call)
                    logger.info(f"✅ DB Update: Call {call_sid} terminal status recorded as {call_status}.")
        except Exception as e:
            logger.error(f"Failed to update call {call_sid} status in DB: {e}")

    return Response(content="OK", status_code=200)

@router.post("/telnyx/call-control")
async def telnyx_call_control(
    request: Request, 
    background_tasks: BackgroundTasks,
    call_repo: CallRepository = Depends(get_call_repository)
):
    """
    Telnyx Call Control Webhook.
    """
    try:
        event = await request.json()
        data = event.get("data", {})
        event_type = data.get("event_type")
        payload = data.get("payload", {})
        call_control_id = payload.get("call_control_id")

        logger.info(f"📞 Telnyx Event: {event_type} | Call: {call_control_id}")

        if event_type == "call.initiated":
            direction = payload.get("direction")
            if direction == "inbound":
                # Answer the call via Use Case
                use_case = AnswerCallUseCase(telnyx_adapter)
                background_tasks.add_task(use_case.execute, call_control_id)
            else:
                logger.info(f"Outbound call initiated (ringing): {call_control_id}, waiting for answered event.")

        elif event_type == "call.answered":
            # Start streaming via Use Case
            client_state = payload.get("client_state")
            
            proto = request.headers.get("x-forwarded-proto", "https")
            forwarded_host = request.headers.get("x-forwarded-host")
            host = forwarded_host if forwarded_host else request.headers.get("host")
            
            if not host:
                raise ValueError("Host header is missing")
                
            ws_scheme = "wss" if proto == "https" else "ws"
            
            # Restauración al Path probado y Whitelisteado por el Proxy
            ws_url = f"{ws_scheme}://{host}{settings.WS_MEDIA_STREAM_PATH}?client=telnyx&call_control_id={call_control_id}"
            
            if client_state:
                ws_url += f"&client_state={client_state}"
            
            logger.info(f"🚨 [TELNYX MEDIA HANDSHAKE] Attempting to connect Streaming to URL: {ws_url}")
            
            use_case = StartStreamUseCase(telnyx_adapter)
            background_tasks.add_task(use_case.execute, call_control_id, ws_url, client_state)
            
            # --- Move Call to IN_PROGRESS in DB ---
            async def _mark_call_in_progress(cid: str):
                from backend.domain.value_objects.call_id import CallId
                try:
                    call = await call_repo.get_by_id(CallId(cid))
                    if call:
                        call.start()
                        await call_repo.save(call)
                        logger.info(f"✅ DB Update: Call {cid} officially answered and marked IN_PROGRESS")
                except Exception as e:
                    logger.error(f"Failed to mark call {cid} as answered: {e}")
                    
            background_tasks.add_task(_mark_call_in_progress, call_control_id)

            # Phase 1: Call Recording (Telnyx)
            async def _start_recording_if_enabled(cid: str):
                from backend.domain.value_objects.call_id import CallId
                try:
                    call = await call_repo.get_by_id(CallId(cid))
                    if call and hasattr(call, 'agent'):
                        agent = call.agent
                        conn_config = getattr(agent, "connectivity_config", {}) or {}
                        # Check if Telnyx recording is enabled
                        if conn_config.get("enableRecordingTelnyx", False):
                            channels = conn_config.get("recordingChannelsTelnyx", "dual")
                            logger.info(f"🎙️ Triggering native Telnyx recording for call {cid} (channels: {channels})")
                            await telnyx_adapter.start_recording(cid, channels)
                except Exception as e:
                    logger.error(f"Failed to trigger Telnyx recording for {cid}: {e}")
                    
            background_tasks.add_task(_start_recording_if_enabled, call_control_id)

        # Telephony Network Status Events
        elif event_type == "call.hangup":
            raw_cause = payload.get("sip_hangup_cause") or payload.get("hangup_cause") or ""
            cause = str(raw_cause).lower()
            mapped_reason = "completed"
            
            if "busy" in cause or cause in ["486", "600", "603"]:
                mapped_reason = "busy"
            elif "no answer" in cause or "timeout" in cause or cause in ["408", "480"]:
                mapped_reason = "no_answer"
            elif cause in ["404", "410", "484", "503"]:
                mapped_reason = "failed"
            elif cause in ["normal_clearing", "200"]:
                mapped_reason = "completed"
                
            async def _mark_call_hungup(cid: str, mr: str):
                from backend.domain.value_objects.call_id import CallId
                try:
                    call = await call_repo.get_by_id(CallId(cid))
                    if call and call.status.value not in ("voicemail", "failed", "busy", "no_answer", "completed"):
                        call.end(reason=mr)
                        await call_repo.save(call)
                        logger.info(f"✅ DB Update: Telnyx Call {cid} ended with {mr}")
                except Exception as e:
                    logger.error(f"Failed to update Telnyx call {cid}: {e}")
                    
            background_tasks.add_task(_mark_call_hungup, call_control_id, mapped_reason)

        # DTMF Gathering (Keypad)
        elif event_type == "call.dtmf.received":
            digit = payload.get("digit")
            logger.info(f"🔢 Telnyx DTMF Received on call {call_control_id}: {digit}")

        # Answering Machine Detection (AMD)
        elif event_type in ("call.machine.greeting.ended", "call.machine.premium.greeting.ended", "call.machine.detect"):
            amd_result = payload.get("result", "")
            if amd_result != "machine":
                logger.info(f"🤖 Telnyx AMD triggered ({event_type}), but result is '{amd_result}'. NOT hanging up.")
            else:
                host = request.headers.get('host', 'localhost')
                scheme = request.headers.get('x-forwarded-proto', 'https')
                
                async def _handle_amd(cid: str, current_host: str, current_scheme: str):
                    from backend.domain.value_objects.call_id import CallId
                    try:
                        call = await call_repo.get_by_id(CallId(cid))
                        if call:
                            import httpx
                            from backend.infrastructure.database.session import AsyncSessionLocal
                            from backend.infrastructure.adapters.persistence.config_repository import ConfigRepository
                            
                            agent_id = getattr(call.agent, "agent_uuid", None)
                            if agent_id:
                                async with AsyncSessionLocal() as session:
                                    conf_repo = ConfigRepository(session)
                                    config_dto = await conf_repo.get_config(str(agent_id))
                                    action = getattr(config_dto, "amd_action", "hangup")
                                    amd_message = getattr(config_dto, "amd_message", "Hola, le llamábamos para darle información.")
                                    
                                    if action == "leave_message" and amd_message:
                                        base_url = f"{current_scheme}://{current_host}"
                                        audio_url = f"{base_url}/api/telephony/voicemail-audio?agent_id={agent_id}"

                                        url = f"{telnyx_adapter.base_url}/calls/{cid}/actions/playback.start"
                                        import base64, json
                                        client_state = base64.b64encode(json.dumps({
                                            "call_control_id": cid, 
                                            "action": "hangup_after_playback"
                                        }).encode()).decode()
                                        playback_payload = {
                                            "audio_url": audio_url,
                                            "client_state": client_state
                                        }
                                        async with httpx.AsyncClient() as client:
                                            await client.post(url, headers=telnyx_adapter.headers, json=playback_payload)
                                            logger.info(f"▶️ Sent Playback command to Telnyx call {cid} with custom TTS audio.")
                                    else:
                                        url = f"{telnyx_adapter.base_url}/calls/{cid}/actions/hangup"
                                        async with httpx.AsyncClient() as client:
                                            await client.post(url, headers=telnyx_adapter.headers)
                                            logger.info(f"Hung up Telnyx call {cid} due to machine detection")

                            call.end("voicemail")
                            await call_repo.save(call)
                            logger.info(f"✅ DB Update: Telnyx Call {cid} marked as Voicemail")
                    except Exception as e:
                        logger.error(f"Failed to save Telnyx AMD state for {cid}: {e}")
                
                background_tasks.add_task(_handle_amd, call_control_id, host, scheme)

        # Handle end of playback if client_state has hangup_after_playback
        elif event_type == "call.playback.ended":
            client_state_b64 = payload.get("client_state", "")
            if client_state_b64:
                async def _handle_playback_ended(cid: str, state_b64: str):
                    try:
                        import base64, json, httpx
                        state_data = json.loads(base64.b64decode(state_b64).decode())
                        if state_data.get("action") == "hangup_after_playback":
                            url = f"{telnyx_adapter.base_url}/calls/{cid}/actions/hangup"
                            async with httpx.AsyncClient() as client:
                                await client.post(url, headers=telnyx_adapter.headers)
                                logger.info(f"📞 Hung up Telnyx call {cid} after TTS playback")
                    except Exception as e:
                        logger.error(f"Error handling speak.ended for {cid}: {e}")
                
                background_tasks.add_task(_handle_playback_ended, call_control_id, client_state_b64)

        return {"status": "received", "event_type": event_type}

    except Exception as e:
        logger.error(f"Telnyx handler error: {e}")
        return {"status": "error", "message": str(e)}

class OutboundCallRequest(BaseModel):
    agent_id: str
    to_number: str
    provider: str = "twilio"

@protected_router.post("/outbound")
async def create_outbound_call(
    request: OutboundCallRequest,
    config_repo: ConfigRepositoryPort = Depends(get_config_repository),
    call_repo: CallRepository = Depends(get_call_repository),
    agent_repo: AgentRepository = Depends(get_agent_repository)
):
    """
    Initiates an outbound call via Twilio or Telnyx, reading AMD settings from the Agent's Flow Config.
    """
    dialer = OutboundDialerService(config_repo=config_repo, call_repo=call_repo, agent_repo=agent_repo)
    try:
        result = await dialer.create_call(
            agent_id=request.agent_id,
            to_number=request.to_number,
            provider=request.provider
        )
        
        call_id = None
        if request.provider == "telnyx":
            call_id = result.get("data", {}).get("call_control_id")
        elif request.provider == "twilio":
            call_id = result.get("sid")
            
        return {"status": "success", "call": result, "call_id": call_id or "undefined"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating outbound call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@protected_router.get("/status/{call_id}")
async def get_call_status(
    call_id: str,
    call_repo: CallRepository = Depends(get_call_repository)
):
    """
    Lightweight endpoint for frontend polling of live call statuses without loading WebSockets.
    """
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(call_id))
        if call:
            st = call.status.value
            ui_status = "ringing"
            if st == "in_progress":
                ui_status = "in_progress"
            elif st in ["completed", "voicemail", "failed", "busy", "no_answer"]:
                ui_status = "ended"
            return {"status": "success", "call_status": ui_status}
        return {"status": "not_found", "call_status": "idle"}
    except Exception as e:
        logger.error(f"Error fetching status for {call_id}: {e}")
        return {"status": "error", "message": str(e), "call_status": "idle"}

@router.get("/voicemail-audio")
async def get_voicemail_audio(agent_id: str):
    """
    Generates high-fidelity TTS audio for voicemail dropping, using the Agent's configured voice.
    Returns 16Khz WAV.
    """
    from backend.infrastructure.database.session import AsyncSessionLocal
    from backend.infrastructure.adapters.persistence.config_repository import ConfigRepository
    from backend.infrastructure.adapters.tts.static_registry import StaticTTSRegistryAdapter
    from backend.domain.value_objects.voice_config import VoiceConfig
    from backend.domain.value_objects.audio_format import AudioFormat
    
    async with AsyncSessionLocal() as session:
        conf_repo = ConfigRepository(session)
        try:
            config_dto = await conf_repo.get_config(agent_id)
        except Exception as e:
            logger.error(f"Failed to find config for voicemail audio: {e}")
            raise HTTPException(status_code=404, detail="Config not found")
        
        provider = getattr(config_dto, "tts_provider", "azure")
        voice_name = getattr(config_dto, "tts_voice", "es-MX-DaliaNeural")
        amd_message = getattr(config_dto, "amd_message", "Hola, le llamábamos para darle información.")
        speed = getattr(config_dto, "tts_speed", 1.0)
        pitch = getattr(config_dto, "tts_pitch", "default")
        
        registry = StaticTTSRegistryAdapter()
        try:
            adapter = registry.get_provider_adapter(provider)
            vc = VoiceConfig(name=voice_name, speed=speed, pitch=pitch)
            
            if hasattr(adapter, "synthesize_for_preview"):
                audio_bytes = await adapter.synthesize_for_preview(text=amd_message, voice=vc)
            else:
                format_obj = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
                audio_bytes = await adapter.synthesize(text=amd_message, voice=vc, format=format_obj)
                
            return Response(content=audio_bytes, media_type="audio/wav")
        except Exception as e:
            logger.error(f"Voicemail TTS generation failed: {e}")
            raise HTTPException(status_code=500, detail="TTS generation failed")
