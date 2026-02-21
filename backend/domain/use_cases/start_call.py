"""
Start Call Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from typing import Optional

from backend.domain.entities.call import Call
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber
from backend.domain.ports.persistence_port import CallRepository, AgentRepository


class StartCallUseCase:
    """
    Orchestrates the initialization of a voice call.
    """

    def __init__(
        self,
        call_repository: CallRepository,
        agent_repository: AgentRepository
    ):
        self.call_repo = call_repository
        self.agent_repo = agent_repository

    async def execute(
        self,
        agent_id: str,
        call_id_value: str,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None
    ) -> Call:
        """
        Initialize a new call session.

        Agent resolution order:
          1. If agent_id is non-empty → look up by UUID first, then by name (legacy).
          2. If agent_id is empty or not found → fall back to the active agent
             (is_active=True). This makes the Simulator work without hardcoding
             any agent identifier: it always uses whichever agent is marked active.

        Args:
            agent_id: UUID or name of the agent. Pass "" to use the active agent.
            call_id_value: Unique identifier for the call (stream_id).
            from_number: Caller's number (E.164).
            to_number: Called number (E.164).

        Returns:
            Initialized Call entity.

        Raises:
            ValueError: If no suitable agent is found.
        """
        agent = None

        # --- Try explicit agent_id first ---
        if agent_id:
            # Try UUID lookup (preferred, unambiguous)
            agent = await self.agent_repo.get_agent_by_uuid(agent_id)
            if not agent:
                # Fallback: legacy name-based lookup
                agent = await self.agent_repo.get_agent(agent_id)

        # --- Fall back to active agent ---
        if not agent:
            agent = await self.agent_repo.get_active_agent()

        if not agent:
            raise ValueError(
                "No agent found. "
                "Either provide a valid agent_id or activate an agent from the /agents panel."
            )

        # 2. Create Value Objects
        call_id = CallId(call_id_value)
        phone = PhoneNumber(from_number) if from_number else None

        # 3. Create Entities
        conversation = Conversation()

        call = Call(
            id=call_id,
            agent=agent,
            conversation=conversation,
            phone_number=phone
        )
        call.update_metadata("to_number", to_number)

        # 4. Change State
        call.start()

        # 5. Persist
        await self.call_repo.save(call)

        return call
