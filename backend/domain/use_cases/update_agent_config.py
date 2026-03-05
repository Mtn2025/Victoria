import logging
from typing import Dict, Any

from backend.domain.ports.persistence_port import AgentRepository, AgentNotFoundError
from backend.interfaces.http.schemas.config_schemas import ConfigUpdate
from backend.domain.value_objects.voice_config import VoiceConfig

logger = logging.getLogger(__name__)

class UpdateAgentConfigUseCase:
    """
    Use Case: Update an Agent's Configuration.
    Handles the merging of partial configuration updates into the agent's JSON metadata fields,
    ensuring domain rules are respected and decoupling the HTTP interface from data mapping.
    """
    def __init__(self, repository: AgentRepository):
        self.repository = repository

    async def execute(self, agent_uuid: str, update: ConfigUpdate) -> None:
        agent = await self.repository.get_agent_by_uuid(agent_uuid)
        if not agent:
            raise AgentNotFoundError(f"Agent with UUID {agent_uuid} not found")

        # Apply basic updates
        if update.system_prompt is not None:
            agent.system_prompt = update.system_prompt
        if update.first_message is not None:
            agent.first_message = update.first_message
        if update.silence_timeout_ms is not None:
            agent.silence_timeout_ms = update.silence_timeout_ms
        if getattr(update, "agent_provider", None) is not None:
            agent.provider = update.agent_provider


        # Voice Config update
        if any([
            update.voice_name is not None, 
            update.voice_style is not None,
            update.voice_speed is not None, 
            update.voice_pitch is not None, 
            update.voice_volume is not None
        ]):
            agent.voice_config = VoiceConfig(
                name=update.voice_name or agent.voice_config.name,
                provider=update.voice_provider or agent.voice_config.provider,
                style=update.voice_style if update.voice_style is not None else agent.voice_config.style,
                speed=update.voice_speed or agent.voice_config.speed,
                pitch=update.voice_pitch if update.voice_pitch is not None else agent.voice_config.pitch,
                volume=update.voice_volume if update.voice_volume is not None else agent.voice_config.volume,
            )

        # Merge LLM config
        # Canonical keys: llm_provider / llm_model
        llm_updates: Dict[str, Any] = {}
        if update.llm_provider is not None:
            llm_updates["llm_provider"] = update.llm_provider
        if update.llm_model is not None:
            llm_updates["llm_model"] = update.llm_model
            
        llm_fields = [
            "max_tokens", "temperature", "responseLength", "conversationTone",
            "conversationFormality", "conversationPacing", "contextWindow",
            "frequencyPenalty", "presencePenalty", "toolChoice", "dynamicVarsEnabled",
            "dynamicVars", "mode", "hallucination_blacklist",
            "end_call_enabled", "end_call_phrases", "end_call_instructions"
        ]
        for field in llm_fields:
            val = getattr(update, field, None)
            if val is not None:
                llm_updates[field] = val
                
        if llm_updates:
            agent.llm_config = {**(agent.llm_config or {}), **llm_updates}

        # Merge extended Voice config into metadata (incl ElevenLabs and Advanced Settings)
        voice_ext_updates: Dict[str, Any] = {}
        voice_fields = [
            "voiceStyleDegree", "voiceBgSound", "voiceBgUrl",
            "voiceStability", "voiceSimilarityBoost", "voiceStyleExaggeration",
            "voiceSpeakerBoost", "voiceMultilingual",
            "voiceFillerInjection", "voiceBackchanneling", "textNormalizationRule",
            "ttsLatencyOptimization", "ttsOutputFormat"
        ]
        for field in voice_fields:
            val = getattr(update, field, None)
            if val is not None:
                voice_ext_updates[field] = val
                
        if voice_ext_updates:
            existing_voice = agent.metadata.get("voice_config_json") or {}
            agent.metadata["voice_config_json"] = {**existing_voice, **voice_ext_updates}

        # Merge STT config into metadata
        stt_updates: Dict[str, Any] = {}
        stt_fields = [
            "sttProvider", "sttModel", "sttLang", "sttKeywords",
            "interruption_threshold", "vadSensitivity", 
            "noise_suppression_level", "audio_codec"
        ]
        for field in stt_fields:
            val = getattr(update, field, None)
            if val is not None:
                stt_updates[field] = val
                
        if update.silence_timeout_ms is not None:
            stt_updates["silence_timeout_ms"] = update.silence_timeout_ms
            
        if stt_updates:
            existing_stt = agent.metadata.get("stt_config") or {}
            agent.metadata["stt_config"] = {**existing_stt, **stt_updates}

        # Merge Flow Config
        flow_updates: Dict[str, Any] = {}
        flow_fields = [
            "barge_in_enabled", "barge_in_sensitivity", "barge_in_phrases",
            "amd_enabled", "amd_sensitivity", "amd_action", "amd_message",
            "pacing_response_delay_ms", "pacing_wait_for_greeting",
            "pacing_hyphenation", "pacing_end_call_phrases",
            "enable_backchannel", "idle_message"
        ]
        for field in flow_fields:
            val = getattr(update, field, None)
            if val is not None:
                flow_updates[field] = val
                
        if flow_updates:
            existing_flow = agent.metadata.get("flow_config") or {}
            agent.metadata["flow_config"] = {**existing_flow, **flow_updates}

        # Merge Analysis Config
        analysis_updates: Dict[str, Any] = {}
        analysis_fields = [
            "analysis_prompt", "success_rubric", "extraction_schema",
            "sentiment_analysis", "webhook_url", "webhook_secret",
            "pii_redaction_enabled", "cost_tracking_enabled", "retention_days"
        ]
        for field in analysis_fields:
            val = getattr(update, field, None)
            if val is not None:
                analysis_updates[field] = val
                
        if analysis_updates:
            existing_analysis = agent.metadata.get("analysis_config") or {}
            agent.metadata["analysis_config"] = {**existing_analysis, **analysis_updates}

        # Merge System Config
        system_updates: Dict[str, Any] = {}
        system_fields = [
            "concurrency_limit", "spend_limit_daily", "environment",
            "privacy_mode", "audit_log_enabled",
            "max_duration", "max_retries"
        ]
        for field in system_fields:
            val = getattr(update, field, None)
            if val is not None:
                system_updates[field] = val
                
        if system_updates:
            existing_system = agent.metadata.get("system_config") or {}
            agent.metadata["system_config"] = {**existing_system, **system_updates}

        # Tools
        if update.tools_config is not None:
            agent.tools = [update.tools_config]

        # Connectivity / Provider Config (Twilio / Telnyx)
        if hasattr(update, 'connectivity_config') and update.connectivity_config is not None:
            existing_conn = getattr(agent, 'connectivity_config', None) or {}
            agent.connectivity_config = {**existing_conn, **update.connectivity_config}

        await self.repository.update_agent(agent)
