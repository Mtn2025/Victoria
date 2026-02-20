"""
Conversation Entity.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any

from backend.domain.value_objects.conversation_turn import ConversationTurn

@dataclass
class Conversation:
    """
    Represents a conversation history (Associate Entity).
    
    Attributes:
        turns: List of chronological conversation turns.
    """
    turns: List[ConversationTurn] = field(default_factory=list)

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a new turn to the conversation."""
        if not isinstance(turn, ConversationTurn):
            raise TypeError("Turn must be of type ConversationTurn")
        self.turns.append(turn)

    def get_context_window(self, limit: int = 10) -> List[ConversationTurn]:
        """
        Get the most recent turns for LLM context window.
        
        Args:
            limit: Maximum number of turns to return (default 10)
            
        Returns:
            List of the last N turns.
        """
        if limit < 0:
             raise ValueError("Limit must be non-negative")
        if limit == 0:
            return []
        return self.turns[-limit:]

    def get_history_as_dicts(self) -> List[Dict[str, Any]]:
        """Convert full history to list of dicts (for LLM context)."""
        return [turn.to_dict() for turn in self.turns]

    @property
    def turn_count(self) -> int:
        return len(self.turns)
