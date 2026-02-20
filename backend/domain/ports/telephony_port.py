"""
Telephony Port (Interface).
Part of the Domain Layer (Hexagonal Architecture).
"""
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber

class TelephonyPort(ABC):
    """
    Interface for telephony providers (Twilio, Telnyx, Browser).
    Handles call signaling and media control.
    """

    @abstractmethod
    async def end_call(self, call_id: CallId) -> None:
        """
        Hangup an active call.
        """
        pass

    @abstractmethod
    async def transfer_call(self, call_id: CallId, target: PhoneNumber) -> None:
        """
        Transfer call to another number (SIP REFER or Dial).
        """
        pass

    @abstractmethod
    async def send_dtmf(self, call_id: CallId, digits: str) -> None:
        """
        Send DTMF tones (e.g., for IVR navigation).
        """
        pass

    @abstractmethod
    async def answer_call(self, call_control_id: str) -> None:
        """
        Answer an incoming call.
        """
        pass

    @abstractmethod
    async def start_streaming(self, call_control_id: str, stream_url: str, client_state: Optional[str] = None) -> None:
        """
        Start media streaming.
        """
        pass
