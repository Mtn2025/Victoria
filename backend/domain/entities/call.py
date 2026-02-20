"""
Call Entity (Aggregate Root).
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from datetime import datetime
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
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark call as in progress."""
        if self.status not in (CallStatus.INITIATED, CallStatus.RINGING):
            raise ValueError(f"Cannot start call from status: {self.status}")
        self.status = CallStatus.IN_PROGRESS

    def end(self, reason: str = "completed") -> None:
        """End the call and record duration."""
        if self.status in [CallStatus.COMPLETED, CallStatus.FAILED]:
            return # Already ended
        
        # Determine status based on reason (simple heuristic for now)
        is_failure = reason.lower() in ["failed", "error", "timeout", "system_error"]
        self.status = CallStatus.FAILED if is_failure else CallStatus.COMPLETED
        
        self.end_time = datetime.utcnow()
        self.metadata["termination_reason"] = reason

    @property
    def duration_seconds(self) -> float:
        """Calculate call duration in seconds."""
        if not self.end_time:
             return (datetime.utcnow() - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()

    def update_metadata(self, key: str, value: Any) -> None:
        """Update arbitrary metadata."""
        self.metadata[key] = value
