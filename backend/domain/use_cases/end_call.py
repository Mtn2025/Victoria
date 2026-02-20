"""
End Call Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from backend.domain.entities.call import Call
from backend.domain.ports.persistence_port import CallRepository
from backend.domain.ports.telephony_port import TelephonyPort

class EndCallUseCase:
    """
    Orchestrates the termination of a call session.
    Ensures state is updated and resources are released.
    """

    def __init__(
        self,
        call_repository: CallRepository,
        telephony_port: TelephonyPort
    ):
        self.call_repo = call_repository
        self.telephony_port = telephony_port

    async def execute(self, call: Call, reason: str = "completed") -> None:
        """
        End the call.
        
        Args:
            call: The active call entity.
            reason: Reason for termination (e.g., "completed", "timeout", "user_hangup").
        """
        # 1. Update Domain State
        call.end(reason)
        
        # 2. Persist Final State
        await self.call_repo.save(call)
        
        # 3. Trigger Telephony Hangup (Side Effect)
        # Note: In some scenarios, telephony might already be disconnected (e.g. user hangup).
        # The port implementation should handle idempotency or specific error codes.
        await self.telephony_port.end_call(call.id)
