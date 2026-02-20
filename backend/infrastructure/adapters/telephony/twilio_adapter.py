import logging
from typing import Optional
from backend.domain.ports.telephony_port import TelephonyPort
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber

logger = logging.getLogger(__name__)

class TwilioAdapter(TelephonyPort):
    """
    Adapter for Twilio Telephony.
    Currently a stub to satisfy the interface and factory.
    Actual implementation would use twilio-python package.
    """

    async def answer_call(self, call_control_id: str) -> None:
        # Twilio usually answers via TwiML, but API can also modify live calls.
        logger.info(f"[Twilio] Answer Call: {call_control_id}")

    async def start_streaming(self, call_control_id: str, stream_url: str, client_state: Optional[str] = None) -> None:
        # Twilio starts streaming via TwiML <Connect><Stream> usually.
        # But if mid-call, we might update the call.
        logger.info(f"[Twilio] Start Streaming: {call_control_id} -> {stream_url}")

    async def end_call(self, call_id: CallId) -> None:
        logger.info(f"[Twilio] End Call: {call_id.value}")

    async def transfer_call(self, call_id: CallId, target: PhoneNumber) -> None:
        logger.info(f"[Twilio] Transfer Call: {call_id.value} -> {target.value}")

    async def send_dtmf(self, call_id: CallId, digits: str) -> None:
        logger.info(f"[Twilio] Send DTMF: {call_id.value} -> {digits}")

    def generate_connect_twiml(self, ws_url: str) -> str:
        """
        Generates TwiML to connect a call to a WebSocket stream.
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>"""
