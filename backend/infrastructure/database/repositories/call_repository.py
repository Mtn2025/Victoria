import logging
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Domain Imports
from backend.domain.ports.persistence_port import CallRepository
from backend.domain.entities.call import Call, CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.conversation_turn import ConversationTurn
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.phone_number import PhoneNumber

# Infrastructure Imports
from backend.infrastructure.database.models import CallModel, AgentModel, TranscriptModel

logger = logging.getLogger(__name__)

class SqlAlchemyCallRepository(CallRepository):
    """
    Implementation of CallRepository using SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, call: Call) -> None:
        """
        Save or update a call.
        """
        # Check if call exists
        stmt = select(CallModel).where(CallModel.session_id == call.id.value).options(
            selectinload(CallModel.transcripts)
        )
        result = await self.session.execute(stmt)
        call_model = result.scalar_one_or_none()

        if not call_model:
            # Create new CallModel
            call_model = CallModel(
                session_id=call.id.value,
                status=call.status.value,
                start_time=call.start_time,
                end_time=call.end_time,
                metadata_=call.metadata,
                client_type=call.metadata.get("client_type", "unknown")
            )
            
            # Handle phone number
            if call.phone_number:
                call_model.phone_number = call.phone_number.value

            # Try to link existing Agent by name
            stmt_agent = select(AgentModel).where(AgentModel.name == call.agent.name)
            res_agent = await self.session.execute(stmt_agent)
            agent_model = res_agent.scalar_one_or_none()
            
            if agent_model:
                call_model.agent = agent_model
            
            self.session.add(call_model)
        else:
            # Update existing
            call_model.status = call.status.value
            call_model.end_time = call.end_time
            call_model.metadata_ = call.metadata
            # Re-link agent if needed? Usually agent doesn't change mid-call in DB structure
        
        # Sync Transcripts
        # Strategy: Delete all existing transcripts for this call and re-insert all from entity.
        # This ensures exact match with Domain state.
        
        # 1. Flush to ensure call_model.id is available if new
        await self.session.flush()
        
        # 2. Delete existing transcripts for this call ID
        # (Only if call existed, but safe to do always if we have ID)
        if call_model.id:
            await self.session.execute(
                delete(TranscriptModel).where(TranscriptModel.call_id == call_model.id)
            )
        
        # 3. Insert current turns
        for turn in call.conversation.turns:
            transcript = TranscriptModel(
                call_id=call_model.id,
                role=turn.role,
                content=turn.content,
                timestamp=turn.timestamp
            )
            self.session.add(transcript)

        # Commit handled by caller or here? 
        # Usually Repository methods should be atomic or part of Unit of Work.
        # For simplicity in this architecture, we commit here.
        await self.session.commit()

    async def get_by_id(self, call_id: CallId) -> Optional[Call]:
        """
        Retrieve call by ID.
        """
        stmt = select(CallModel).where(CallModel.session_id == call_id.value).options(
            selectinload(CallModel.transcripts),
            selectinload(CallModel.agent)
        )
        result = await self.session.execute(stmt)
        call_model = result.scalar_one_or_none()

        if not call_model:
            return None

        # Reconstruct Agent
        if call_model.agent:
            voice_config = VoiceConfig(
                name=call_model.agent.voice_name,
                provider=getattr(call_model.agent, "voice_provider", "azure"),
                style=call_model.agent.voice_style,
                speed=float(call_model.agent.voice_speed),
                pitch=float(call_model.agent.voice_pitch),
                volume=float(call_model.agent.voice_volume)
            )
            agent = Agent(
                name=call_model.agent.name,
                system_prompt=call_model.agent.system_prompt,
                voice_config=voice_config,
                first_message=call_model.agent.first_message,
                silence_timeout_ms=call_model.agent.silence_timeout_ms
            )
        else:
            # Fallback basic agent
            vc = VoiceConfig(name="default")
            agent = Agent(name="Unknown", system_prompt="", voice_config=vc)

        # Reconstruct Conversation
        conversation = Conversation()
        # Sort by timestamp/id if needed, assuming order is preserved or implicit
        # SQLAlchemy usually preserves insertion order for lists if mapped correctly
        for t in call_model.transcripts:
             conversation.add_turn(ConversationTurn(
                role=t.role,
                content=t.content,
                timestamp=t.timestamp
             ))

        # Reconstruct Call
        call = Call(
            id=CallId(call_model.session_id),
            agent=agent,
            conversation=conversation,
            status=CallStatus(call_model.status),
            start_time=call_model.start_time, # ensure timezone awareness?
            metadata=call_model.metadata_ or {}
        )
        
        call.end_time = call_model.end_time
        if call_model.phone_number:
            call.phone_number = PhoneNumber(call_model.phone_number)
            
        return call

    async def get_calls(self, limit: int = 20, offset: int = 0, client_type: Optional[str] = None) -> tuple[List[Call], int]:
        """
        Retrieve paginated calls and total count.
        """
        # Base Query
        stmt = select(CallModel).options(selectinload(CallModel.transcripts), selectinload(CallModel.agent)).order_by(CallModel.start_time.desc())
        
        if client_type and client_type.lower() != 'all':
             stmt = stmt.where(CallModel.client_type == client_type)
             
        # Count Query
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(CallModel)
        if client_type and client_type.lower() != 'all':
             count_stmt = count_stmt.where(CallModel.client_type == client_type)
             
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0
        
        # Paginate
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        call_models = result.scalars().all()
        
        calls = []
        for cm in call_models:
             # Agent Reconstruct
             if cm.agent:
                 vc = VoiceConfig(
                     name=cm.agent.voice_name,
                     style=cm.agent.voice_style,
                     speed=float(cm.agent.voice_speed),
                     pitch=float(cm.agent.voice_pitch),
                     volume=float(cm.agent.voice_volume)
                 )
                 agent = Agent(name=cm.agent.name, system_prompt=cm.agent.system_prompt, voice_config=vc)
             else:
                 agent = Agent(name="Unknown", system_prompt="", voice_config=VoiceConfig(name="default"))
                 
             # Transcript/Conversation Reconstruct
             conversation = Conversation()
             for t in cm.transcripts:
                  conversation.add_turn(ConversationTurn(role=t.role, content=t.content, timestamp=t.timestamp))
                  
             call = Call(
                 id=CallId(cm.session_id),
                 agent=agent,
                 conversation=conversation,
                 status=CallStatus(cm.status),
                 start_time=cm.start_time,
                 metadata=cm.metadata_ or {}
             )
             call.end_time = cm.end_time
             if cm.phone_number:
                 call.phone_number = PhoneNumber(cm.phone_number)
             
             calls.append(call)
             
        return calls, total

    async def delete(self, call_id: CallId) -> None:
        """Delete by ID."""
        stmt = select(CallModel.id).where(CallModel.session_id == call_id.value)
        res = await self.session.execute(stmt)
        db_id = res.scalar_one_or_none()
        
        if db_id:
             await self.session.execute(delete(CallModel).where(CallModel.id == db_id))
             await self.session.commit()

    async def clear(self) -> int:
        """Clear all calls."""
        res = await self.session.execute(delete(CallModel))
        await self.session.commit()
        return res.rowcount
