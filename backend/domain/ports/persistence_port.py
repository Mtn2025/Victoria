"""
Persistence Port (Interface).
Part of the Domain Layer (Hexagonal Architecture).
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from backend.domain.value_objects.call_id import CallId
from backend.domain.entities.call import Call
from backend.domain.entities.agent import Agent


class AgentNotFoundError(Exception):
    """Raised when an agent cannot be found by the given identifier."""
    pass


class CallRepository(ABC):
    """
    Interface for persisting Call Aggregate Root.
    """

    @abstractmethod
    async def save(self, call: Call) -> None:
        """Save or update a call record."""
        pass

    @abstractmethod
    async def get_by_id(self, call_id: CallId) -> Optional[Call]:
        """Retrieve a call by its ID."""
        pass

    @abstractmethod
    async def get_calls(self, limit: int = 20, offset: int = 0, client_type: Optional[str] = None) -> tuple[list[Call], int]:
        """Retrieve paginated calls and total count."""
        pass

    @abstractmethod
    async def delete(self, call_id: CallId) -> None:
        """Delete a call by ID."""
        pass

    @abstractmethod
    async def clear(self) -> int:
        """Clear all calls. Returns count deleted."""
        pass


class AgentRepository(ABC):
    """
    Interface for managing Agent entities.
    """

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent configuration by name (legacy, kept for backward compat)."""
        pass

    @abstractmethod
    async def update_agent(self, agent: Agent) -> None:
        """Update agent configuration."""
        pass

    @abstractmethod
    async def get_all_agents(self) -> List[Agent]:
        """Return all agents ordered by created_at."""
        pass

    @abstractmethod
    async def create_agent(self, agent: Agent) -> Agent:
        """
        Persist a new agent and return it with DB-generated fields
        (agent_uuid, created_at) populated.
        """
        pass

    @abstractmethod
    async def get_agent_by_uuid(self, agent_uuid: str) -> Optional[Agent]:
        """Get a single agent by its public UUID."""
        pass

    @abstractmethod
    async def set_active_agent(self, agent_uuid: str) -> Agent:
        """
        Atomically deactivate all agents and activate the one
        identified by agent_uuid.
        Raises AgentNotFoundError if the UUID does not exist.
        """
        pass
