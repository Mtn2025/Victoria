"""
ListAgentsUseCase.
Part of the Domain Layer (Hexagonal Architecture).
"""
from typing import List

from backend.domain.ports.persistence_port import AgentRepository
from backend.domain.entities.agent import Agent


class ListAgentsUseCase:
    """
    Returns all registered agents.
    Pure domain logic — no infrastructure dependencies.
    """

    def __init__(self, repo: AgentRepository) -> None:
        self._repo = repo

    async def execute(self) -> List[Agent]:
        return await self._repo.get_all_agents()
