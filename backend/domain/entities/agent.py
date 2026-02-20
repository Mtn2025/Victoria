"""
Agent Entity.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from backend.domain.value_objects.voice_config import VoiceConfig

@dataclass
class Agent:
    """
    Represents the Artificial Intelligence Agent configuration.
    Decoupled from Infrastructure details (ORM).
    
    Attributes:
        name: Internal identifier (e.g., "support_agent_v1")
        system_prompt: Base instructions for the LLM.
        first_message: Initial greeting text
        voice_config: Voice synthesis settings (VO)
        tools: List of available tool definitions
        llm_config: Configuration for the Language Model (provider agnostic)
    """
    name: str
    system_prompt: str
    voice_config: VoiceConfig
    first_message: str = ""
    silence_timeout_ms: int = 1000 # Default 1s
    tools: List[Dict[str, Any]] = field(default_factory=list)
    llm_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate agent configuration."""
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        if not self.system_prompt:
             raise ValueError("Agent system prompt cannot be empty")
        if self.silence_timeout_ms <= 0:
            raise ValueError("Silence timeout must be positive")
    
    def get_greeting(self) -> Optional[str]:
        """Get the initial greeting message if defined."""
        return self.first_message if self.first_message else None

    def update_system_prompt(self, new_prompt: str) -> None:
        """Update system prompt (e.g., based on dynamic context)."""
        if not new_prompt:
             raise ValueError("System prompt cannot be empty")
        self.system_prompt = new_prompt
