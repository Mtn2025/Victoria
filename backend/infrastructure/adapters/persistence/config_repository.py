"""
SQLAlchemy Config Repository - Implementation of ConfigRepositoryPort.

Hexagonal Architecture: Infrastructure adapter for agent configuration.
Translates domain calls to SQLAlchemy ORM operations.
"""
import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.ports.config_repository_port import (
    ConfigDTO,
    ConfigNotFoundException,
    ConfigRepositoryPort,
)

logger = logging.getLogger(__name__)


class SQLAlchemyConfigRepository(ConfigRepositoryPort):
    """
    SQLAlchemy adapter for configuration persistence.
    
    Maps between domain ConfigDTO and database AgentConfig model.
    Handles CRUD operations for agent configuration profiles.
    
    Note: Requires AgentConfig model from Victoria's database schema.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initialize config repository.
        
        Args:
            session_factory: Callable that returns AsyncSession
        """
        self._session_factory = session_factory

    async def get_config(self, profile: str = "default") -> ConfigDTO:
        """
        Retrieve configuration by profile.
        
        Victoria uses AgentModel with simplified config fields.
        Profile maps to agent.name.
        """
        async with self._session_factory() as session:
            from sqlalchemy import select
            from backend.infrastructure.database.models import AgentModel
            
            # Query agent by name (profile)
            result = await session.execute(
                select(AgentModel).where(AgentModel.name == profile)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise ConfigNotFoundException(f"Profile '{profile}' not found")
            
            return self._model_to_dto(agent)

    async def update_config(self, profile: str, **updates) -> ConfigDTO:
        """
        Update configuration profile.
        
        Updates AgentModel fields based on provided kwargs.
        """
        async with self._session_factory() as session:
            from sqlalchemy import select
            from backend.infrastructure.database.models import AgentModel
            
            # Fetch agent
            result = await session.execute(
                select(AgentModel).where(AgentModel.name == profile)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise ConfigNotFoundException(f"Profile '{profile}' not found")
            
            # Apply updates to model fields
            for key, value in updates.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
                # Handle nested JSON configs
                elif key.startswith("llm_") and agent.llm_config is not None:
                    agent.llm_config[key] = value
                elif key.startswith("tool_") and agent.tools_config is not None:
                    agent.tools_config[key] = value
            
            await session.commit()
            await session.refresh(agent)
            
            return self._model_to_dto(agent)

    async def create_config(self, profile: str, config: ConfigDTO) -> ConfigDTO:
        """
        Create new configuration profile.
        
        Creates new AgentModel with provided configuration.
        """
        async with self._session_factory() as session:
            from backend.infrastructure.database.models import AgentModel
            
            # Create new agent
            agent = AgentModel(
                name=profile,
                system_prompt=config.system_prompt,
                voice_provider=config.tts_provider,
                voice_name=config.voice_name,
                voice_style=config.voice_style,
                voice_speed=config.voice_speed,
                first_message=config.first_message,
                silence_timeout_ms=config.silence_timeout_ms,
                llm_config={
                    "provider": config.llm_provider,
                    "model": config.llm_model,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                },
                tools_config={
                    "enabled": config.async_tools,
                    "timeout_ms": config.tool_timeout_ms,
                }
            )
            
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            
            return self._model_to_dto(agent)

    def _model_to_dto(self, agent) -> ConfigDTO:
        """
        Convert AgentModel to ConfigDTO.
        
        Maps Victoria's simplified agent model to full ConfigDTO.
        """
        # Extract from JSON configs with defaults
        llm_config = agent.llm_config or {}
        tools_config = agent.tools_config or {}
        
        return ConfigDTO(
            # LLM Config
            llm_provider=llm_config.get("provider", "groq"),
            llm_model=llm_config.get("model", "llama-3.3-70b-versatile"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 600),
            system_prompt=agent.system_prompt or "",
            first_message=agent.first_message or "",
            first_message_mode="text",  # Default
            # TTS Config  
            tts_provider=agent.voice_provider or "azure",
            voice_name=agent.voice_name or "es-MX-DaliaNeural",
            voice_style=agent.voice_style or "default",
            voice_speed=agent.voice_speed or 1.0,
            voice_language="es-MX",  # Default
            # STT Config
            stt_provider="azure",  # Default
            stt_language="es-MX",  # Default
            silence_timeout_ms=agent.silence_timeout_ms or 1000,
            # Advanced
            enable_denoising=True,  # Default
            enable_backchannel=False,  # Default
            max_duration=300,  # Default
            # Tools
            async_tools=tools_config.get("enabled", False),
            tool_timeout_ms=tools_config.get("timeout_ms", 5000),
        )
