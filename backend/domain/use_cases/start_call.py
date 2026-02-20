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
        
        Args:
            agent_id: Identifier for the AI agent configuration.
            call_id_value: Unique identifier for the call (stream_id).
            from_number: Caller's number (E.164).
            to_number: Called number (E.164).
            
        Returns:
            Initialized Call entity.
            
        Raises:
            ValueError: If agent not found.
        """
        # 1. Load Agent Configuration
        agent = await self.agent_repo.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # 2. Create Value Objects
        call_id = CallId(call_id_value)
        phone = PhoneNumber(from_number) if from_number else None
        # Note: We might want to store to_number as well in the future

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
