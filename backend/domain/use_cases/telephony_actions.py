from typing import Optional
from backend.domain.ports.telephony_port import TelephonyPort

class AnswerCallUseCase:
    def __init__(self, telephony_port: TelephonyPort):
        self.telephony_port = telephony_port

    async def execute(self, call_control_id: str):
        await self.telephony_port.answer_call(call_control_id)

class StartStreamUseCase:
    def __init__(self, telephony_port: TelephonyPort):
        self.telephony_port = telephony_port

    async def execute(
        self,
        call_control_id: str,
        stream_url: str,
        client_state: str = None,
        codec: str = "PCMU",
    ):
        """Start a Telnyx media stream. codec: 'PCMU' (default, G.711 8kHz) or 'L16' (PCM 16kHz)."""
        await self.telephony_port.start_streaming(call_control_id, stream_url, client_state, codec)
