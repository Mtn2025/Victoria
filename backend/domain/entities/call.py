"""
Call Entity (Aggregate Root).
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation


class CallStatus(str, Enum):
    """Call Lifecycle States."""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    VOICEMAIL_DELAYED = "voicemail_delayed"


@dataclass
class Call:
    """
    Aggregate Root for a Voice Call session.
    Manages lifecycle, state transitions, and holds the conversation history.
    """
    id: CallId
    agent: Agent
    conversation: Conversation
    status: CallStatus = CallStatus.INITIATED
    phone_number: Optional[PhoneNumber] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark call as in progress."""
        if self.status not in (CallStatus.INITIATED, CallStatus.RINGING):
            raise ValueError(f"Cannot start call from status: {self.status}")
        self.status = CallStatus.IN_PROGRESS

    def end(self, reason: str = "completed") -> None:
        """End the call and record duration."""
        if self.status in [CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.BUSY, CallStatus.NO_ANSWER, CallStatus.VOICEMAIL]:
            return # Already ended
        
        # Determine status based on reason
        lower_reason = reason.lower()
        if lower_reason in ["busy", "no-answer", "no_answer"]:
            self.status = CallStatus.NO_ANSWER if "answer" in lower_reason else CallStatus.BUSY
        elif lower_reason in ["failed", "error", "timeout", "system_error", "canceled"]:
            self.status = CallStatus.FAILED
        elif lower_reason in ["voicemail", "machine_start", "machine_end_beep", "machine_end_other"]:
            # Voicemail Time Heuristic: >12s implies delayed voicemail (did not pick up)
            elapsed_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            if elapsed_seconds > 12.0:
                self.status = CallStatus.VOICEMAIL_DELAYED
            else:
                self.status = CallStatus.VOICEMAIL
        else:
            self.status = CallStatus.COMPLETED
        
        self.end_time = datetime.now(timezone.utc)
        self.metadata["termination_reason"] = reason

    @property
    def duration_seconds(self) -> float:
        """Calculate call duration in seconds."""
        if not self.end_time:
             return (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()

    def update_metadata(self, key: str, value: Any) -> None:
        """Update arbitrary metadata."""
        self.metadata[key] = value
