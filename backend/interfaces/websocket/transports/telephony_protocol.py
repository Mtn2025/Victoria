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
             # Assert "type" is present, or map "event"
             msg_type = msg.get("type") or msg.get("event")
             if msg_type == "start":
                 return {"type": "start", "stream_id": msg.get("stream_id")}
             elif msg_type == "stop":
                 return {"type": "stop"}
             elif msg_type == "media":
                 # Browser typically sends raw bytes via binary frame, but if they send JSON media:
                 payload = msg.get("data") or msg.get("payload")
                 if payload:
                      # Is it base64? Simulator uses base64 in JSON mode? 
                      # The simulator in frontend calls `ws.send(audioData)` which are bytes.
                      # But for text events it uses JSON.
                      # If browser sends JSON media, assume base64.
                      try:
                          chunk = base64.b64decode(payload)
                          return {"type": "media", "data": chunk}
                      except:
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
