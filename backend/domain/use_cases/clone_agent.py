"""
CloneAgentUseCase.
Part of the Domain Layer (Hexagonal Architecture).
"""
import uuid
import copy

from backend.domain.ports.persistence_port import AgentRepository, AgentNotFoundError
from backend.domain.entities.agent import Agent


class CloneAgentUseCase:
    """
    Clones an existing agent, assigns a new UUID, and sets a target provider.
    This effectively branches the agent configuration.
    """

    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    async def execute(self, source_agent_uuid: str, target_provider: str) -> Agent:
        """
        Deep clones an agent.

        Args:
            source_agent_uuid: Public UUID of the source agent (browser configuration).
            target_provider: Target native provider (e.g. telnyx, twilio).

        Returns:
            The physically independent cloned Agent entity.
        Raises:
            AgentNotFoundError: If source agent does not exist.
        """
        source_agent = await self._repo.get_agent_by_uuid(source_agent_uuid)
        if not source_agent:
            raise AgentNotFoundError(f"Source agent {source_agent_uuid} not found")

        # Create a deep copy of the original to avoid reference collision in ORM
        cloned_agent = copy.deepcopy(source_agent)

        # Re-assign core identity fields
        cloned_agent.agent_uuid = str(uuid.uuid4())
        cloned_agent.provider = target_provider.strip()
        cloned_agent.name = f"{source_agent.name} - {target_provider.capitalize()}"
        cloned_agent.created_at = None  # Force BD to generate the timestamp
        cloned_agent.is_active = False  # Avoid stealing activity status
        
        # Reset provider specific fields to prevent bleeding
        cloned_agent.connectivity_config = {}

        return await self._repo.create_agent(cloned_agent)
