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
        import uuid
        
        # Query agent by uuid or name (profile)
        try:
            val_uuid = uuid.UUID(profile)
            stmt = select(AgentModel).where(AgentModel.agent_uuid == str(val_uuid))
        except ValueError:
            stmt = select(AgentModel).where(AgentModel.name == profile)
            
        result = await self._session.execute(stmt)
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
        import uuid
        
        # Fetch agent by uuid or name
        try:
            val_uuid = uuid.UUID(profile)
            stmt = select(AgentModel).where(AgentModel.agent_uuid == str(val_uuid))
        except ValueError:
            stmt = select(AgentModel).where(AgentModel.name == profile)
            
        result = await self._session.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise ConfigNotFoundException(f"Profile '{profile}' not found")
        
        # Apply updates to model fields
        for key, value in updates.items():
            if hasattr(agent, key) and key not in ["voice_config_json"]:
                setattr(agent, key, value)
            # Handle nested JSON configs
            elif key.startswith("llm_") and agent.llm_config is not None:
                agent.llm_config[key] = value
            elif key.startswith("tool_") and agent.tools_config is not None:
                agent.tools_config[key] = value
            elif key in ["voiceStyleDegree", "voiceBgSound", "voiceBgUrl", "voiceStability", "voiceSimilarityBoost", "voiceStyleExaggeration", "voiceSpeakerBoost", "voiceMultilingual"]:
                current_voice = dict(agent.voice_config_json) if agent.voice_config_json else {}
                current_voice[key] = value
                agent.voice_config_json = current_voice
            elif (key.startswith("barge_") or key.startswith("amd_") or key.startswith("pacing_")) and agent.flow_config is not None:
                # SQLAlchemy JSON in-place mutations might need flag_modified or re-assignment
                updated_flow = dict(agent.flow_config)
                updated_flow[key] = value
                agent.flow_config = updated_flow
            elif key in ["analysis_prompt", "success_rubric", "extraction_schema", "sentiment_analysis", "webhook_url", "webhook_secret", "log_webhook_url", "pii_redaction_enabled", "cost_tracking_enabled", "retention_days", "crm_enabled"]:
                current_analysis = dict(agent.analysis_config) if agent.analysis_config else {}
                current_analysis[key] = value
                agent.analysis_config = current_analysis
            elif key in ["concurrency_limit", "spend_limit_daily", "environment", "privacy_mode", "audit_log_enabled"]:
                current_system = dict(agent.system_config) if agent.system_config else {}
                current_system[key] = value
                agent.system_config = current_system
        
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
                "responseLength": config.responseLength,
                "conversationTone": config.conversationTone,
                "conversationFormality": config.conversationFormality,
                "conversationPacing": config.conversationPacing,
                "contextWindow": config.contextWindow,
                "frequencyPenalty": config.frequencyPenalty,
                "presencePenalty": config.presencePenalty,
                "toolChoice": config.toolChoice,
                "dynamicVarsEnabled": config.dynamicVarsEnabled,
                "dynamicVars": config.dynamicVars,
                "mode": config.mode,
                "hallucination_blacklist": config.hallucination_blacklist,
                "end_call_enabled": config.end_call_enabled,
                "end_call_phrases": config.end_call_phrases,
                "end_call_instructions": config.end_call_instructions,
            },
            tools_config={
                "enabled": config.async_tools,
                "timeout_ms": config.tool_timeout_ms,
                "retry_count": config.tool_retry_count,
                "error_message": config.tool_error_msg,
                "redact_params": config.redact_params,
                "transfer_whitelist": config.transfer_whitelist,
                "state_injection_enabled": config.state_injection_enabled,
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
                "enable_backchannel": config.enable_backchannel,
                "idle_message": config.idle_message,
            },
            stt_config={
                "noise_suppression_level": config.noise_suppression_level,
                "audio_codec": config.audio_codec,
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
                "crm_enabled": config.crm_enabled,
            },
            system_config={
                "concurrency_limit": config.concurrency_limit,
                "spend_limit_daily": config.spend_limit_daily,
                "environment": config.environment,
                "privacy_mode": config.privacy_mode,
                "audit_log_enabled": config.audit_log_enabled,
                "max_duration": config.max_duration,
                "max_retries": config.max_retries,
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
        system_config = agent.system_config or {}
        stt_config = agent.stt_config or {}
        voice_config_json = agent.voice_config_json or {}
        connectivity_config = agent.connectivity_config or {}

        # Safe extraction for nested Telnyx config
        telnyx_config = connectivity_config.get("telnyx", {})
        
        return ConfigDTO(
            # LLM Config
            llm_provider=llm_config.get("provider", "groq"),
            llm_model=llm_config.get("model", "llama-3.3-70b-versatile"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 600),
            system_prompt=agent.system_prompt or "",
            first_message=agent.first_message or "",
            first_message_mode=llm_config.get("mode", "text"),
            responseLength=llm_config.get("responseLength"),
            conversationTone=llm_config.get("conversationTone"),
            conversationFormality=llm_config.get("conversationFormality"),
            conversationPacing=llm_config.get("conversationPacing"),
            contextWindow=llm_config.get("contextWindow", 10),
            frequencyPenalty=llm_config.get("frequencyPenalty", 0.0),
            presencePenalty=llm_config.get("presencePenalty", 0.0),
            toolChoice=llm_config.get("toolChoice", "auto"),
            dynamicVarsEnabled=llm_config.get("dynamicVarsEnabled", False),
            dynamicVars=llm_config.get("dynamicVars"),
            hallucination_blacklist=llm_config.get("hallucination_blacklist"),
            end_call_enabled=llm_config.get("end_call_enabled", False),
            end_call_phrases=llm_config.get("end_call_phrases", []),
            end_call_instructions=llm_config.get("end_call_instructions"),
            # TTS Config  
            tts_provider=agent.voice_provider or "azure",
            voice_name=agent.voice_name or "es-MX-DaliaNeural",
            voice_style=agent.voice_style or "default",
            voice_speed=agent.voice_speed or 1.0,
            voice_pitch=agent.voice_pitch or 0.0,
            voice_volume=agent.voice_volume or 100.0,
            voice_language=getattr(agent, "language", "es-MX") or "es-MX",  # Default Root
            voice_style_degree=float(voice_config_json.get("voiceStyleDegree", 1.0) if voice_config_json.get("voiceStyleDegree") is not None else 1.0),
            voice_bg_sound=voice_config_json.get("voiceBgSound", "none"),
            voice_bg_url=voice_config_json.get("voiceBgUrl", None),
            voice_stability=voice_config_json.get("voiceStability", None),
            voice_similarity_boost=voice_config_json.get("voiceSimilarityBoost", None),
            voice_style_exaggeration=voice_config_json.get("voiceStyleExaggeration", None),
            voice_speaker_boost=voice_config_json.get("voiceSpeakerBoost", None),
            voice_multilingual=voice_config_json.get("voiceMultilingual", None),
            # STT Config
            stt_provider="azure",  # Default
            stt_language="es-MX",  # Default
            silence_timeout_ms=agent.silence_timeout_ms or 1000,
            # Telephony
            telnyx_phone_number=telnyx_config.get("outbound_phone_number", None),
            telnyx_connection_id=telnyx_config.get("connection_id", None),
            # Advanced
            enable_denoising=stt_config.get("noise_suppression_level", "balanced") != "off",
            noise_suppression_level=stt_config.get("noise_suppression_level", "balanced"),
            audio_codec=stt_config.get("audio_codec", "PCMU"),
            enable_backchannel=flow_config.get("enable_backchannel", False),
            max_duration=system_config.get("max_duration", 300),
            max_retries=system_config.get("max_retries", 1),
            idle_message=flow_config.get("idle_message", "¿Hola? ¿Sigues ahí?"),
            # Tools
            async_tools=tools_config.get("enabled", False),
            tool_timeout_ms=tools_config.get("timeout_ms", 5000),
            tool_retry_count=tools_config.get("retry_count", 0),
            tool_error_msg=tools_config.get("error_message", "Lo siento, hubo un error con la herramienta."),
            redact_params=tools_config.get("redact_params", None),
            transfer_whitelist=tools_config.get("transfer_whitelist", None),
            state_injection_enabled=tools_config.get("state_injection_enabled", False),
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
            crm_enabled=analysis_config.get("crm_enabled", False),
            # System
            concurrency_limit=system_config.get("concurrency_limit", 1),
            spend_limit_daily=system_config.get("spend_limit_daily", 10.0),
            environment=system_config.get("environment", "development"),
            privacy_mode=system_config.get("privacy_mode", False),
            audit_log_enabled=system_config.get("audit_log_enabled", False),
        )
