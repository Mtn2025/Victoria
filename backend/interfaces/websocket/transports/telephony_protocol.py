"""
Telephony Protocol Helper.
Handles framing of JSON messages for Twilio/Telnyx WebSockets.
"""
import json
import base64
from typing import Optional, Any

class TelephonyProtocol:
    def __init__(self, client_type: str = "twilio", stream_id: Optional[str] = None):
        self.client_type = client_type
        self.stream_id = stream_id

    def set_stream_id(self, stream_id: str):
        self.stream_id = stream_id

    def parse_message(self, text_data: str) -> dict[str, Any]:
        """
        Parse incoming JSON message.
        Returns generic event structure: {"type": "media", "data": bytes} or {"type": "control", ...}
        """
        msg = json.loads(text_data)
        event_type = msg.get("event")

        # Twilio
        if self.client_type == "twilio":
            if event_type == "media":
                payload = msg["media"]["payload"]
                chunk = base64.b64decode(payload)
                return {"type": "media", "data": chunk}
            elif event_type == "start":
                return {"type": "start", "stream_id": msg["start"]["streamSid"]}
            elif event_type == "stop":
                return {"type": "stop"}
            elif event_type == "connected":
                return {"type": "connected"}
        
        # Telnyx
        elif self.client_type == "telnyx":
            if event_type == "media":
                 payload = msg["media"]["payload"]
                 chunk = base64.b64decode(payload)
                 return {"type": "media", "data": chunk}
            elif event_type == "start":
                 # Telnyx V2: Extract stream_id and call_control_id
                 return {
                     "type": "start",
                     "stream_id": msg.get("stream_id"),
                     "call_control_id": msg.get("call_control_id")
                 }
            elif event_type == "call.hangup":
                 return {"type": "stop"}

        # Browser / Generic
        elif self.client_type == "browser":
            msg_type = msg.get("type") or msg.get("event")
            if msg_type == "start":
                return {"type": "start", "stream_id": msg.get("stream_id"), "start": msg.get("start")}
            elif msg_type == "stop":
                return {"type": "stop"}
            elif msg_type == "media":
                # Frontend sends: { event:'media', media:{ payload:<b64>, track, timestamp } }
                payload = (
                    msg.get("data")
                    or msg.get("payload")
                    or msg.get("media", {}).get("payload")  # ← correct path
                )
                if payload:
                    try:
                        chunk = base64.b64decode(payload)
                        return {"type": "media", "data": chunk}
                    except Exception:
                        return {"type": "unknown", "raw": msg}
                return {"type": "unknown", "raw": msg}

        return {"type": "unknown", "raw": msg}

    def create_media_message(self, audio_chunk: bytes) -> str:
        """
        Create JSON message for outbound audio.
        """
        b64_payload = base64.b64encode(audio_chunk).decode('utf-8')
        
        if self.client_type == "twilio":
            return json.dumps({
                "event": "media",
                "streamSid": self.stream_id,
                "media": {
                    "payload": b64_payload
                }
            })
        elif self.client_type == "telnyx":
            return json.dumps({
                "event": "media",
                "stream_id": self.stream_id,
                "media": {
                    "payload": b64_payload,
                    "track": "inbound_track"
                }
            })
            
        return ""
