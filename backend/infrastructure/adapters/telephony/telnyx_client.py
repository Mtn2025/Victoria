"""
Telnyx Client (Infrastructure Adapter).
Handles explicit API calls to Telnyx (Answer, Streaming).
"""
import logging
import base64
import json
import httpx
from typing import Optional, Any
from urllib.parse import quote

from backend.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

from backend.domain.ports.telephony_port import TelephonyPort
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber

class TelnyxClient(TelephonyPort):
    """
    Client for Telnyx Call Control API.
    """
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.TELNYX_API_KEY
        self.base_url = settings.TELNYX_API_BASE
        
        if not self.api_key:
            logger.warning("Telnyx API Key not set. API calls will fail.")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def answer_call(self, call_control_id: str):
        """
        Send 'answer' command to Telnyx.
        Stores call_control_id in client_state for persistence.
        """
        if not self.api_key:
            return
            
        url = f"{self.base_url}/calls/{call_control_id}/actions/answer"
        
        client_state = base64.b64encode(
            json.dumps({"call_control_id": call_control_id}).encode()
        ).decode()
        
        payload = {"client_state": client_state}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.status_code >= 400:
                    logger.error(f"Failed to answer Telnyx call: {response.text}")
                else:
                    logger.info(f"Telnyx Call answered: {call_control_id}")
        except Exception as e:
            logger.error(f"Telnyx answer error: {e}")

    async def start_streaming(self, call_control_id: str, stream_url: str, client_state: Optional[str] = None):
        """
        Send 'streaming_start' command to Telnyx.
        """
        if not self.api_key:
            return

        # Construct WS URL if needed, but usually passed fully formed
        # Legacy logic constructed it here. We will assume caller constructs it or we do it here.
        # Caller (Endpoint) has access to Request scope (Host), so Endpoint should build URL.
        
        url = f"{self.base_url}/calls/{call_control_id}/actions/streaming_start"
        
        payload = {
            "stream_url": stream_url,
            "stream_track": "inbound_track", # we only need Start for inbound handling usually, or generic
            "stream_bidirectional_mode": "rtp",
            "stream_bidirectional_codec": "PCMA",
            "client_state": client_state
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.status_code >= 400:
                    logger.error(f"Failed to start streaming: {response.text}")
                else:
                    logger.info(f"Telnyx Streaming started: {call_control_id}")
                    
            # Also start noise suppression as per legacy
            await self.start_noise_suppression(call_control_id)
            
        except Exception as e:
            logger.error(f"Telnyx start_streaming error: {e}")

    async def start_noise_suppression(self, call_control_id: str):
        url = f"{self.base_url}/calls/{call_control_id}/actions/suppression_start"
        payload = {"direction": "both"}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, headers=self.headers, json=payload)
        except Exception:
            pass # Non-critical

    async def end_call(self, call_id: CallId) -> None:
        """
        End a call (Hangup).
        """
        if not self.api_key:
            return

        url = f"{self.base_url}/calls/{call_id.value}/actions/hangup"
        payload = {"client_state": "hanging_up"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.status_code >= 400:
                    logger.error(f"Failed to hangup Telnyx call {call_id.value}: {response.text}")
                else:
                    logger.info(f"Telnyx Call ended: {call_id.value}")
        except Exception as e:
            logger.error(f"Telnyx hangup error: {e}")

    async def transfer_call(self, call_id: CallId, target: PhoneNumber) -> None:
        """
        Transfer call to another number.
        """
        if not self.api_key:
            return

        url = f"{self.base_url}/calls/{call_id.value}/actions/transfer"
        payload = {
            "to": target.value,
            "webhook_url": f"{settings.BASE_URL}/telephony/telnyx/call-control" if hasattr(settings, 'BASE_URL') else None
        }
        # Filter None
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.status_code >= 400:
                    logger.error(f"Failed to transfer Telnyx call {call_id.value}: {response.text}")
                else:
                    logger.info(f"Telnyx Call transferred: {call_id.value} -> {target.value}")
        except Exception as e:
            logger.error(f"Telnyx transfer error: {e}")

    async def send_dtmf(self, call_id: CallId, digits: str) -> None:
        """
        Send DTMF tones.
        """
        if not self.api_key:
            return

        url = f"{self.base_url}/calls/{call_id.value}/actions/send_dtmf"
        payload = {"digits": digits}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                if response.status_code >= 400:
                    logger.error(f"Failed to send DTMF on Telnyx call {call_id.value}: {response.text}")
                else:
                    logger.info(f"Telnyx DTMF sent: {call_id.value} -> {digits}")
        except Exception as e:
            logger.error(f"Telnyx DTMF error: {e}")
