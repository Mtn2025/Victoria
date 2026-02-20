"""
Configuration Endpoints.
Part of the Interfaces Layer (HTTP).
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.session import get_db_session
from backend.infrastructure.database.repositories import SqlAlchemyAgentRepository
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.ports.persistence_port import AgentRepository
from backend.domain.ports.tts_port import VoiceMetadata
from backend.interfaces.http.schemas.config_schemas import ConfigUpdate
from backend.domain.use_cases.get_llm_options import GetLLMOptionsUseCase
from backend.infrastructure.adapters.llm.static_registry import StaticLLMRegistryAdapter

router = APIRouter(prefix="/config", tags=["config"])
logger = logging.getLogger(__name__)

from backend.interfaces.deps import get_agent_repository
from backend.infrastructure.config.features import features

@router.get("/features")
async def get_system_features():
    """
    Get system-wide feature flags.
    """
    return features.get_all()


@router.get("/{agent_id}")
async def get_agent_config(
    agent_id: str,
    repo: AgentRepository = Depends(get_agent_repository)
):
    """
    Get configuration for a specific agent.
    """
    agent = await repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "name": agent.name,
        "system_prompt": agent.system_prompt,
        "first_message": agent.first_message,
        "voice": {
            "name": agent.voice_config.name,
            "style": agent.voice_config.style,
            "speed": agent.voice_config.speed,
            "pitch": agent.voice_config.pitch,
            "volume": agent.voice_config.volume
        },
        "silence_timeout_ms": agent.silence_timeout_ms,
        # TODO(INT-05): Verify if tools_config should be exposed here.
        "tools_config": agent.tools if hasattr(agent, "tools") else {},
        "llm_config": agent.llm_config if hasattr(agent, "llm_config") else {}
    }

@router.patch("/")
async def update_agent_config(
    update: ConfigUpdate,
    repo: AgentRepository = Depends(get_agent_repository)
):
    """
    Update agent configuration.
    """
    agent_id = update.agent_id
    
    # 1. Get existing
    current = await repo.get_agent(agent_id)
    if not current:
        # Create default if not exists
        current = Agent(
            name=agent_id,
            system_prompt="You are a helpful assistant.",
            voice_config=VoiceConfig(name="en-US-JennyNeural")
        )
    
    # 2. Apply updates
    if update.system_prompt is not None:
        current.system_prompt = update.system_prompt
    if update.first_message is not None:
        current.first_message = update.first_message
    if update.silence_timeout_ms is not None:
        current.silence_timeout_ms = update.silence_timeout_ms

    # TODO(INT-05): Update tools_config.
    # Contract: Frontend sends 'tools_config' JSON, Backend persists it.
    if update.tools_config is not None:
        current.tools = update.tools_config
        
    # JSON LLM Config dict mapping
    if not current.llm_config:
        current.llm_config = {}
        
    if update.llm_provider is not None:
        current.llm_config["provider"] = update.llm_provider
    if update.llm_model is not None:
        current.llm_config["model"] = update.llm_model
    if update.max_tokens is not None:
        current.llm_config["max_tokens"] = update.max_tokens
    if update.temperature is not None:
        current.llm_config["temperature"] = update.temperature
        
    # Voice Config Update
    # Since VoiceConfig is immutable (frozen), we must replace it
    vc = current.voice_config
    new_vc_args = {
        "name": update.voice_name if update.voice_name is not None else vc.name,
        "style": update.voice_style if update.voice_style is not None else vc.style,
        "speed": update.voice_speed if update.voice_speed is not None else vc.speed,
        "pitch": int(update.voice_pitch) if update.voice_pitch is not None else vc.pitch,
        "volume": int(update.voice_volume) if update.voice_volume is not None else vc.volume
    }
    
    current.voice_config = VoiceConfig(**new_vc_args)
    
    # 3. Save
    await repo.update_agent(current)
    
    return {"status": "updated", "agent_id": agent_id}

# --- Dynamic Options ---
from backend.domain.use_cases.get_tts_options import GetTTSOptionsUseCase

@router.get("/options/tts/voices")
async def get_tts_voices(language: str | None = None):
    """
    Get available TTS voices.
    """
    # Composition Root: Instantiate Adapter and Use Case
    adapter = AzureTTSAdapter()
    use_case = GetTTSOptionsUseCase(adapter)
    
    try:
        voices = await use_case.get_voices(language)
        return {"voices": [v.__dict__ for v in voices]}
    finally:
        # cleanup if needed
        pass

@router.get("/options/tts/languages")
async def get_tts_languages():
    """
    Get available TTS languages.
    """
    adapter = AzureTTSAdapter()
    use_case = GetTTSOptionsUseCase(adapter)
    
    langs = await use_case.get_languages()
    return {"languages": langs}

@router.get("/options/llm/providers")
async def get_llm_providers():
    """Get available LLM providers."""
    adapter = StaticLLMRegistryAdapter()
    use_case = GetLLMOptionsUseCase(adapter)
    providers = await use_case.get_providers()
    return {"providers": providers}

@router.get("/options/llm/models")
async def get_llm_models(provider: str):
    """Get available LLM models for a given provider."""
    adapter = StaticLLMRegistryAdapter()
    use_case = GetLLMOptionsUseCase(adapter)
    models = await use_case.get_models(provider)
    return {"models": models}
