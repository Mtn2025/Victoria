"""
CreateAgentUseCase.
Part of the Domain Layer (Hexagonal Architecture).
"""
import uuid

from backend.domain.ports.persistence_port import AgentRepository
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig


# System defaults for a newly created agent
_DEFAULT_SYSTEM_PROMPT = (
    "Eres un asistente de voz amable y profesional. "
    "Responde de forma clara y concisa."
)
_DEFAULT_VOICE_NAME = "es-MX-DaliaNeural"
_DEFAULT_FIRST_MESSAGE = "Hola, ¿en qué puedo ayudarte hoy?"


class CreateAgentUseCase:
    """
    Creates a new agent with system-default values.
    Does NOT clone an existing agent.
    Generates a public UUID at the domain layer.
    """

    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    async def execute(self, name: str) -> Agent:
        """
        Create and persist a new agent.

        Args:
            name: Display name for the new agent. Must be non-empty.

        Returns:
            The persisted Agent with agent_uuid and created_at populated.
        """
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")

        agent_uuid = str(uuid.uuid4())

        new_agent = Agent(
            name=name.strip(),
            system_prompt=_DEFAULT_SYSTEM_PROMPT,
            voice_config=VoiceConfig(name=_DEFAULT_VOICE_NAME),
            first_message=_DEFAULT_FIRST_MESSAGE,
            silence_timeout_ms=600,
            agent_uuid=agent_uuid,
            is_active=False,
        )

        return await self._repo.create_agent(new_agent)
