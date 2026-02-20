"""
Telephony Endpoints.
Part of the Interfaces Layer (HTTP).
Handles webhooks for Twilio and Telnyx.
"""
import logging
import base64
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, Response, Depends, BackgroundTasks, Header

from backend.infrastructure.config.settings import settings
from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
# Security deps if needed (Legacy had signature checks)
# For Phase 9, we focus on functionality. We can import security if available or scaffold it.

router = APIRouter(prefix="/telephony", tags=["telephony"])
logger = logging.getLogger(__name__)

# Instantiate client (Singleton-ish) acting as Port Adapter
telnyx_adapter = TelnyxClient()

from backend.domain.use_cases.telephony_actions import AnswerCallUseCase, StartStreamUseCase

@router.api_route("/twilio/incoming-call", methods=["GET", "POST"])
async def twilio_incoming_call(request: Request):
    """
    Twilio Webhook. Returns TwiML to connect to WebSocket.
    """
    host = request.headers.get("host") or "localhost"
    ws_url = f"wss://{host}{settings.WS_MEDIA_STREAM_PATH}"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.post("/telnyx/call-control")
async def telnyx_call_control(
    request: Request, 
    background_tasks: BackgroundTasks
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
            # Answer the call via Use Case
            use_case = AnswerCallUseCase(telnyx_adapter)
            background_tasks.add_task(use_case.execute, call_control_id)

        elif event_type == "call.answered":
            # Start streaming via Use Case
            client_state = payload.get("client_state")
            
            proto = request.headers.get("x-forwarded-proto", "https")
            host = request.headers.get("host") or "localhost"
            ws_scheme = "wss" if proto == "https" else "ws"
            
            ws_url = f"{ws_scheme}://{host}{settings.WS_MEDIA_STREAM_PATH}?client=telnyx&call_control_id={call_control_id}"
            
            if client_state:
                ws_url += f"&client_state={client_state}"
                
            use_case = StartStreamUseCase(telnyx_adapter)
            background_tasks.add_task(use_case.execute, call_control_id, ws_url, client_state)

        return {"status": "received", "event_type": event_type}

    except Exception as e:
        logger.error(f"Telnyx handler error: {e}")
        return {"status": "error", "message": str(e)}
