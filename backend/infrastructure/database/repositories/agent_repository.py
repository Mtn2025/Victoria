
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Domain Imports
from backend.domain.ports.persistence_port import AgentRepository
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

# Infrastructure Imports
from backend.infrastructure.database.models import AgentModel, CallModel

logger = logging.getLogger(__name__)

class SqlAlchemyAgentRepository(AgentRepository):
    """
    Implementation of AgentRepository.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        stmt = select(AgentModel).where(AgentModel.name == agent_id)
        result = await self.session.execute(stmt)
        
        agent_model = result.scalar_one_or_none()
        
        if not agent_model:
            return None
            
        voice_config = VoiceConfig(
            name=agent_model.voice_name,
            provider=getattr(agent_model, "voice_provider", "azure"),
            style=agent_model.voice_style,
            speed=float(agent_model.voice_speed),
            pitch=float(agent_model.voice_pitch),
            volume=float(agent_model.voice_volume)
        )
        agent = Agent(
            name=agent_model.name,
            system_prompt=agent_model.system_prompt,
            voice_config=voice_config,
            first_message=agent_model.first_message,
            silence_timeout_ms=agent_model.silence_timeout_ms
        )
        
        # Tools and LLM config
        if agent_model.tools_config:
            # naive mapping
             agent.tools = [agent_model.tools_config] if isinstance(agent_model.tools_config, dict) else []
             
        if agent_model.llm_config:
             agent.llm_config = agent_model.llm_config
             
        return agent

    async def update_agent(self, agent: Agent) -> None:
        """
        Update agent configuration in DB.
        """
        # Find model by name (assuming name is ID)
        stmt = select(AgentModel).where(AgentModel.name == agent.name)
        result = await self.session.execute(stmt)
        agent_model = result.scalar_one_or_none()
        
        if not agent_model:
            # Create new or raise error? Use Case usually handles "if exists".
            # If "Configuration" is singleton-like, we might create.
            # Allowing creation for robustness.
            agent_model = AgentModel(name=agent.name)
            self.session.add(agent_model)
            
        # Update Fields
        agent_model.system_prompt = agent.system_prompt
        agent_model.first_message = agent.first_message
        agent_model.silence_timeout_ms = agent.silence_timeout_ms
        
        if agent.voice_config:
            agent_model.voice_name = agent.voice_config.name
            agent_model.voice_style = agent.voice_config.style
            agent_model.voice_speed = agent.voice_config.speed
            agent_model.voice_pitch = agent.voice_config.pitch
            agent_model.voice_volume = agent.voice_config.volume
            
        # Tools and LLM
        if agent.tools:
            # Assuming first tool config dictates "tools_config" column
            agent_model.tools_config = agent.tools[0] if agent.tools else {}
            
        if agent.llm_config:
            agent_model.llm_config = agent.llm_config
            
        await self.session.commit()
