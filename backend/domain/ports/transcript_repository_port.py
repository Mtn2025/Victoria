"""
Port (Interface) for transcript persistence.

Hexagonal Architecture: Domain defines contract for saving conversation transcripts.
"""
from abc import ABC, abstractmethod


class TranscriptRepositoryPort(ABC):
    """
    Port for transcript persistence operations.
    
    Implementations store conversation transcripts for:
    - Historical analysis
    - Compliance/auditing
    - Training data
    - User review
    """

    @abstractmethod
    async def save(self, call_id: str, role: str, content: str) -> None:
        """
        Save a single transcript line.
        
        Args:
            call_id: Database ID of the call
            role: "user" or "assistant"
            content: Text content of the message
        """
        pass
