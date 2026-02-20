"""
Configuration Endpoints.
Part of the Interfaces Layer (HTTP).
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.session import get_db_session
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.ports.persistence_port import AgentRepository
from backend.domain.ports.tts_port import VoiceMetadata
from backend.domain.ports.tts_provider_registry import TTSProviderRegistry
from backend.domain.ports.persistence_port import AgentRepository
from backend.domain.ports.tts_port import VoiceMetadata
from backend.interfaces.http.schemas.config_schemas import ConfigUpdate, VoicePreviewRequest
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
        
    # Helper to parse empty strings from frontend safely
    def _parse_val(val, fallback, cast_func=None):
        if val is None or val == "":
            return fallback
        return cast_func(val) if cast_func else val
        
    # JSON LLM Config dict mapping
    if not current.llm_config:
        current.llm_config = {}
        
    if update.llm_provider is not None:
        current.llm_config["provider"] = update.llm_provider
    if update.llm_model is not None:
        current.llm_config["model"] = update.llm_model
    if update.max_tokens is not None:
        current.llm_config["max_tokens"] = _parse_val(update.max_tokens, current.llm_config.get("max_tokens", 1024), int)
    if update.temperature is not None:
        current.llm_config["temperature"] = _parse_val(update.temperature, current.llm_config.get("temperature", 0.7), float)
        
    vc = current.voice_config
    
    new_vc_args = {
        "name": _parse_val(update.voice_name, vc.name),
        "style": _parse_val(update.voice_style, vc.style),
        "speed": _parse_val(update.voice_speed, vc.speed, float),
        "pitch": _parse_val(update.voice_pitch, vc.pitch, int),
        "volume": _parse_val(update.voice_volume, vc.volume, int)
    }
    
    # Drop None values so the Domain object can trigger its own defaults
    clean_vc_args = {k: v for k, v in new_vc_args.items() if v is not None}
    current.voice_config = VoiceConfig(**clean_vc_args)
    
    # 3. Save
    await repo.update_agent(current)
    
    return {"status": "updated", "agent_id": agent_id}

# --- Dynamic Options ---
# --- Dynamic Options ---
from backend.domain.use_cases.get_tts_options import GetTTSOptionsUseCase
from backend.infrastructure.adapters.tts.static_registry import StaticTTSRegistryAdapter

@router.get("/options/tts/voices")
async def get_tts_voices(provider: str = "azure", language: str | None = None):
    """
    Get available TTS voices for a specific provider.
    """
    registry = StaticTTSRegistryAdapter()
    use_case = GetTTSOptionsUseCase(registry)
    
    try:
        voices = await use_case.get_voices(provider, language)
        return {"voices": [v.__dict__ for v in voices]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/options/tts/languages")
async def get_tts_languages(provider: str = "azure"):
    """
    Get available TTS languages for a specific provider.
    """
    registry = StaticTTSRegistryAdapter()
    use_case = GetTTSOptionsUseCase(registry)
    
    try:
        langs = await use_case.get_languages(provider)
        return {"languages": langs}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/options/tts/styles")
async def get_tts_styles(voice_id: str, provider: str = "azure"):
    """
    Get available emotion styles for a specific voice.
    """
    registry = StaticTTSRegistryAdapter()
    use_case = GetTTSOptionsUseCase(registry)
    
    try:
        styles = await use_case.get_styles(provider, voice_id)
        return {"styles": styles}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi.responses import Response
from backend.domain.value_objects.audio_format import AudioFormat

@router.post("/options/tts/preview")
async def preview_tts_voice(request: VoicePreviewRequest):
    """
    Generate an audio preview for a specific voice configuration.
    """
    registry = StaticTTSRegistryAdapter()
    
    try:
        adapter = registry.get_provider_adapter(request.provider)
        
        # Build VoiceConfig domain object
        vc = VoiceConfig(
            name=request.voice_name,
            speed=request.voice_speed,
            pitch=request.voice_pitch,
            volume=request.voice_volume,
            style=request.voice_style or "default",
            style_degree=request.voice_style_degree or 1.0
        )
        
        # Request Web-compatible format for browser HTML5 Audio playback (WAV)
        format_obj = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
        
        # We need a generic sample text for the language
        sample_text = "Hola, esta es una prueba de voz para comprobar la configuración."
        if request.provider == "elevenlabs" and "multilingual" not in getattr(vc, 'locale', ''):
             # Elevenlabs default preview.
             sample_text = "Hello, this is a voice test to check the current configuration."
             
        audio_bytes = await adapter.synthesize(text=sample_text, voice=vc, format=format_obj)
        
        return Response(content=audio_bytes, media_type="audio/wav")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Text-to-Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Voice synthesis failed")

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
