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

    def __init__(self, session: AsyncSession):
        """
        Initialize config repository.
        
        Args:
            session: AsyncSession object from dependency injection
        """
        self._session = session

    async def get_config(self, profile: str = "default") -> ConfigDTO:
        """
        Retrieve configuration by profile.
        
        Victoria uses AgentModel with simplified config fields.
        Profile maps to agent.name.
        """
        from sqlalchemy import select
        from backend.infrastructure.database.models import AgentModel
        
        # Query agent by name (profile)
        result = await self._session.execute(
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
        from sqlalchemy import select
        from backend.infrastructure.database.models import AgentModel
        
        # Fetch agent
        result = await self._session.execute(
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
            elif (key.startswith("barge_") or key.startswith("amd_") or key.startswith("pacing_")) and agent.flow_config is not None:
                # SQLAlchemy JSON in-place mutations might need flag_modified or re-assignment
                updated_flow = dict(agent.flow_config)
                updated_flow[key] = value
                agent.flow_config = updated_flow
            elif key in ["analysis_prompt", "success_rubric", "extraction_schema", "sentiment_analysis", "webhook_url", "webhook_secret", "log_webhook_url", "pii_redaction_enabled", "cost_tracking_enabled", "retention_days"]:
                current_analysis = dict(agent.analysis_config) if agent.analysis_config else {}
                current_analysis[key] = value
                agent.analysis_config = current_analysis
        
        await self._session.commit()
        await self._session.refresh(agent)
        
        return self._model_to_dto(agent)

    async def create_config(self, profile: str, config: ConfigDTO) -> ConfigDTO:
        """
        Create new configuration profile.
        
        Creates new AgentModel with provided configuration.
        """
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
            },
            flow_config={
                "barge_in_enabled": config.barge_in_enabled,
                "barge_in_sensitivity": config.barge_in_sensitivity,
                "barge_in_phrases": config.barge_in_phrases,
                "amd_enabled": config.amd_enabled,
                "amd_sensitivity": config.amd_sensitivity,
                "amd_action": config.amd_action,
                "amd_message": config.amd_message,
                "pacing_response_delay_ms": config.pacing_response_delay_ms,
                "pacing_wait_for_greeting": config.pacing_wait_for_greeting,
                "pacing_hyphenation": config.pacing_hyphenation,
                "pacing_end_call_phrases": config.pacing_end_call_phrases,
            },
            analysis_config={
                "analysis_prompt": config.analysis_prompt,
                "success_rubric": config.success_rubric,
                "extraction_schema": config.extraction_schema,
                "sentiment_analysis": config.sentiment_analysis,
                "webhook_url": config.webhook_url,
                "webhook_secret": config.webhook_secret,
                "log_webhook_url": config.log_webhook_url,
                "pii_redaction_enabled": config.pii_redaction_enabled,
                "cost_tracking_enabled": config.cost_tracking_enabled,
                "retention_days": config.retention_days,
            }
        )
        
        self._session.add(agent)
        await self._session.commit()
        await self._session.refresh(agent)
        
        return self._model_to_dto(agent)

    def _model_to_dto(self, agent) -> ConfigDTO:
        """
        Convert AgentModel to ConfigDTO.
        
        Maps Victoria's simplified agent model to full ConfigDTO.
        """
        # Extract from JSON configs with defaults
        llm_config = agent.llm_config or {}
        tools_config = agent.tools_config or {}
        flow_config = agent.flow_config or {}
        analysis_config = agent.analysis_config or {}
        
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
            # Flow Config
            barge_in_enabled=flow_config.get("barge_in_enabled", True),
            barge_in_sensitivity=flow_config.get("barge_in_sensitivity", 0.5),
            barge_in_phrases=flow_config.get("barge_in_phrases", []),
            amd_enabled=flow_config.get("amd_enabled", False),
            amd_sensitivity=flow_config.get("amd_sensitivity", 0.5),
            amd_action=flow_config.get("amd_action", "hangup"),
            amd_message=flow_config.get("amd_message", "Hola, he detectado un buzón."),
            pacing_response_delay_ms=flow_config.get("pacing_response_delay_ms", 0),
            pacing_wait_for_greeting=flow_config.get("pacing_wait_for_greeting", False),
            pacing_hyphenation=flow_config.get("pacing_hyphenation", False),
            pacing_end_call_phrases=flow_config.get("pacing_end_call_phrases", []),
            # Analysis
            analysis_prompt=analysis_config.get("analysis_prompt", None),
            success_rubric=analysis_config.get("success_rubric", None),
            extraction_schema=analysis_config.get("extraction_schema", None),
            sentiment_analysis=analysis_config.get("sentiment_analysis", False),
            webhook_url=analysis_config.get("webhook_url", None),
            webhook_secret=analysis_config.get("webhook_secret", None),
            log_webhook_url=analysis_config.get("log_webhook_url", None),
            pii_redaction_enabled=analysis_config.get("pii_redaction_enabled", False),
            cost_tracking_enabled=analysis_config.get("cost_tracking_enabled", False),
            retention_days=analysis_config.get("retention_days", 30),
        )
