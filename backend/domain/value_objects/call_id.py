"""
Call Identifier Value Object.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class CallId:
    """
    Unique identifier for a Call.
    Wraps strict string validation logic.
    """
    value: str

    def __post_init__(self) -> None:
        """Validates the call ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("CallId must be a non-empty string")
        if len(self.value) > 255:
            raise ValueError("CallId too long")

    def __str__(self) -> str:
        """Returns the string representation of the CallId."""
        return self.value
