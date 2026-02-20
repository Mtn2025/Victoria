"""
Conversation Turn Value Object.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Dict, List, Any, Optional

Role = Literal["user", "assistant", "system", "tool"]

@dataclass(frozen=True)
class ConversationTurn:
    """
    Represents a single turn in the conversation.
    Immutable log of what was said/done.
    """
    role: Role
    content: str = ""  # Default empty string instead of using __setattr__ hack
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.role not in ["user", "assistant", "system", "tool"]:
# Note: Literal check usually happens at static type checking, but runtime check is fine too.
            raise ValueError(f"Invalid role: {self.role}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM context."""
        d: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_results:
            d["tool_results"] = self.tool_results
        return d
