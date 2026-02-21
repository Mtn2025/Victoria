"""
SetActiveAgentUseCase.
Part of the Domain Layer (Hexagonal Architecture).
"""
from backend.domain.ports.persistence_port import AgentRepository, AgentNotFoundError
from backend.domain.entities.agent import Agent


class SetActiveAgentUseCase:
    """
    Activates the agent identified by agent_uuid.
    Guarantees that only one agent is active at a time.
    The actual atomicity is enforced at the repository layer
    (single DB transaction).
    """

    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    async def execute(self, agent_uuid: str) -> Agent:
        """
        Deactivate all agents, then activate the given one.

        Args:
            agent_uuid: The public UUID of the agent to activate.

        Returns:
            The newly activated Agent.

        Raises:
            AgentNotFoundError: If no agent with the given UUID exists.
            ValueError: If agent_uuid is empty.
        """
        if not agent_uuid or not agent_uuid.strip():
            raise ValueError("agent_uuid cannot be empty")

        return await self._repo.set_active_agent(agent_uuid)
