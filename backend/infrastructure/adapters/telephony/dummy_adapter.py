"""
Dummy Telephony Adapter.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
import logging
from backend.domain.ports.telephony_port import TelephonyPort
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber

logger = logging.getLogger(__name__)

class DummyTelephonyAdapter(TelephonyPort):
    """
    Dummy adapter for Telephony actions.
    Logs actions to console/file.
    """

    async def end_call(self, call_id: CallId) -> None:
        logger.info(f"[Telephony] END CALL command received for {call_id.value}")

    async def transfer_call(self, call_id: CallId, target: PhoneNumber) -> None:
        logger.info(f"[Telephony] TRANSFER CALL {call_id.value} -> {target.value}")

    async def send_dtmf(self, call_id: CallId, digits: str) -> None:
        logger.info(f"[Telephony] SEND DTMF {call_id.value}: {digits}")

    async def answer_call(self, call_control_id: str) -> None:
        logger.info(f"[Telephony] ANSWER CALL {call_control_id}")

    async def start_streaming(self, call_control_id: str, stream_url: str, client_state: str = None) -> None:
        logger.info(f"[Telephony] START STREAMING {call_control_id} -> {stream_url}")
