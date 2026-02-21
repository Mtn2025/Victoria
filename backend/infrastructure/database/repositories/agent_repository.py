
import logging
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Domain Imports
from backend.domain.ports.persistence_port import AgentRepository, AgentNotFoundError
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

# Infrastructure Imports
from backend.infrastructure.database.models import AgentModel, CallModel

logger = logging.getLogger(__name__)


def _model_to_agent(agent_model: AgentModel) -> Agent:
    """Convert an AgentModel ORM object to an Agent domain entity."""
    voice_config = VoiceConfig(
        name=agent_model.voice_name,
        provider=getattr(agent_model, "voice_provider", "azure"),
        style=agent_model.voice_style,
        speed=float(agent_model.voice_speed),
        pitch=float(agent_model.voice_pitch),
        volume=float(agent_model.voice_volume),
    )
    # Build metadata from DB JSON columns into the declared domain field.
    # These are the extended blobs not stored as individual columns.
    metadata: dict = {}
    if agent_model.voice_config_json:
        metadata["voice_config_json"] = agent_model.voice_config_json
    if agent_model.stt_config:
        metadata["stt_config"] = agent_model.stt_config

    agent = Agent(
        name=agent_model.name,
        system_prompt=agent_model.system_prompt,
        voice_config=voice_config,
        first_message=agent_model.first_message,
        silence_timeout_ms=agent_model.silence_timeout_ms,
        agent_uuid=agent_model.agent_uuid,
        is_active=agent_model.is_active,
        created_at=agent_model.created_at,
        metadata=metadata,
        # Map tools_config (DB JSON column) to domain list
        tools=([agent_model.tools_config] if isinstance(agent_model.tools_config, dict) else []
               if agent_model.tools_config else []),
        # Map llm_config JSON column directly
        llm_config=agent_model.llm_config or {},
    )
    return agent


class SqlAlchemyAgentRepository(AgentRepository):
    """
    SQLAlchemy implementation of AgentRepository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------ #
    # Legacy method — kept for backward compatibility with /config/ routes #
    # ------------------------------------------------------------------ #
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        stmt = select(AgentModel).where(AgentModel.name == agent_id)
        result = await self.session.execute(stmt)
        agent_model = result.scalar_one_or_none()
        if not agent_model:
            return None
        return _model_to_agent(agent_model)

    async def update_agent(self, agent: Agent) -> None:
        """
        Persist changes to an existing agent.
        Searches by agent_uuid (preferred) for agents managed by the new UUIDbased API.
        Falls back to name-based lookup for legacy /config/ routes.
        """
        if agent.agent_uuid:
            stmt = select(AgentModel).where(AgentModel.agent_uuid == agent.agent_uuid)
        else:
            # Legacy fallback: /config/ endpoint may not have UUID
            stmt = select(AgentModel).where(AgentModel.name == agent.name)

        result = await self.session.execute(stmt)
        agent_model = result.scalar_one_or_none()

        if not agent_model:
            agent_model = AgentModel(name=agent.name)
            self.session.add(agent_model)

        agent_model.system_prompt = agent.system_prompt
        agent_model.first_message = agent.first_message
        agent_model.silence_timeout_ms = agent.silence_timeout_ms

        if agent.voice_config:
            agent_model.voice_name = agent.voice_config.name
            agent_model.voice_style = agent.voice_config.style
            agent_model.voice_speed = agent.voice_config.speed
            agent_model.voice_pitch = agent.voice_config.pitch
            agent_model.voice_volume = agent.voice_config.volume

        if agent.tools:
            agent_model.tools_config = agent.tools[0] if agent.tools else {}

        if agent.llm_config:
            existing_llm = agent_model.llm_config or {}
            agent_model.llm_config = {**existing_llm, **agent.llm_config}

        # Persist extended JSON blobs from the domain metadata field
        if agent.metadata:
            if "voice_config_json" in agent.metadata:
                existing_voice = agent_model.voice_config_json or {}
                agent_model.voice_config_json = {**existing_voice, **agent.metadata["voice_config_json"]}
            if "stt_config" in agent.metadata:
                existing_stt = agent_model.stt_config or {}
                agent_model.stt_config = {**existing_stt, **agent.metadata["stt_config"]}

        await self.session.commit()

    # ------------------------------------------------------------------ #
    # New methods for the Agent Management System                          #
    # ------------------------------------------------------------------ #

    async def get_all_agents(self) -> List[Agent]:
        stmt = select(AgentModel).order_by(AgentModel.created_at)
        result = await self.session.execute(stmt)
        return [_model_to_agent(m) for m in result.scalars().all()]

    async def create_agent(self, agent: Agent) -> Agent:
        """Persist a new agent. The agent_uuid is pre-set at domain layer."""
        new_model = AgentModel(
            name=agent.name,
            agent_uuid=agent.agent_uuid,
            system_prompt=agent.system_prompt,
            first_message=agent.first_message,
            silence_timeout_ms=agent.silence_timeout_ms,
            is_active=False,
            voice_name=agent.voice_config.name,
            voice_provider=agent.voice_config.provider,
            voice_style=agent.voice_config.style,
            voice_speed=agent.voice_config.speed,
            voice_pitch=agent.voice_config.pitch,
            voice_volume=agent.voice_config.volume,
        )
        self.session.add(new_model)
        await self.session.commit()
        await self.session.refresh(new_model)
        return _model_to_agent(new_model)

    async def get_agent_by_uuid(self, agent_uuid: str) -> Optional[Agent]:
        stmt = select(AgentModel).where(AgentModel.agent_uuid == agent_uuid)
        result = await self.session.execute(stmt)
        agent_model = result.scalar_one_or_none()
        if not agent_model:
            return None
        return _model_to_agent(agent_model)

    async def set_active_agent(self, agent_uuid: str) -> Agent:
        """
        Atomically deactivate all agents then activate the target one.
        Raises AgentNotFoundError if the UUID doesn't exist.
        """
        # Verify existence first
        stmt = select(AgentModel).where(AgentModel.agent_uuid == agent_uuid)
        result = await self.session.execute(stmt)
        target = result.scalar_one_or_none()
        if not target:
            raise AgentNotFoundError(f"No agent found with uuid={agent_uuid}")

        # Deactivate all in one UPDATE
        await self.session.execute(
            update(AgentModel).values(is_active=False)
        )
        # Activate the target
        await self.session.execute(
            update(AgentModel)
            .where(AgentModel.agent_uuid == agent_uuid)
            .values(is_active=True)
        )
        await self.session.commit()
        await self.session.refresh(target)
        return _model_to_agent(target)

    async def delete_agent(self, agent_uuid: str) -> None:
        """Permanently delete an agent row by UUID."""
        from sqlalchemy import delete as sa_delete
        await self.session.execute(
            sa_delete(AgentModel).where(AgentModel.agent_uuid == agent_uuid)
        )
        await self.session.commit()

    async def get_active_agent(self) -> Optional[Agent]:
        """Return the agent with is_active=True, or None."""
        stmt = select(AgentModel).where(AgentModel.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        agent_model = result.scalar_one_or_none()
        if not agent_model:
            return None
        return _model_to_agent(agent_model)
