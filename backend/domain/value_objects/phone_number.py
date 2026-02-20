"""
Phone Number Value Object.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class PhoneNumber:
    """
    E.164 validated phone number.
    Example: +14155552671
    """
    value: str

    def __post_init__(self) -> None:
        """Validates the phone number format (E.164 or SIP URI)."""
        if not self.value:
            # Allow empty for anonymous/unknown callers if domain permits, 
            # but usually a phone number VO implies a valid number.
            # Let's assume strict for now, or use a specific NullObject if needed.
            raise ValueError("Phone number cannot be empty")
        
        # Basic E.164 regex (very simplified)
        # Must start with + and have 7-15 digits
        if not re.match(r'^\+[1-9]\d{6,14}$', self.value):
             # check if it is a SIP URI (Telnyx/Twilio sometimes send SIP)
             if not self.value.startswith("sip:"):
                raise ValueError(f"Invalid E.164 phone number: {self.value}")

    def __str__(self) -> str:
        """Returns the string representation of the PhoneNumber."""
        return self.value
