"""
End Call Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from backend.domain.entities.call import Call
from backend.domain.ports.persistence_port import CallRepository
from backend.domain.ports.telephony_port import TelephonyPort

# Razones donde el backend ES quien inicia el cuelgue (Telnyx no lo sabe aún)
_BACKEND_INITIATED_HANGUP = {"timeout", "idle_disconnect", "error", "transfer"}

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
            reason: Reason for termination.
                - 'completed'/'disconnected'/'voicemail': Telnyx ya colgó — no enviar hangup
                - 'timeout'/'idle_disconnect'/'error': backend inicia el cuelgue → sí enviar
        """
        # 1. Update Domain State
        call.end(reason)

        # 2. Persist Final State
        await self.call_repo.save(call)

        # 3. Trigger Telephony Hangup — SOLO si el backend inicia el cuelgue
        # Para 'completed'/'disconnected', Telnyx ya envió call.hangup → no duplicar (422)
        if reason in _BACKEND_INITIATED_HANGUP:
            await self.telephony_port.end_call(call.id)
