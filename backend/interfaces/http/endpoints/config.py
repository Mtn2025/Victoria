"""
Configuration Endpoints.
Part of the Interfaces Layer (HTTP).

Provides:
- GET  /config/features        — Feature flags
- GET  /config/options/llm/*   — LLM providers / models catalog
- GET  /config/options/tts/*   — TTS languages / voices / styles catalog
- POST /config/options/tts/preview — Voice preview synthesis

NOTE: The legacy `GET /config/{agent_id}` and `PATCH /config/` endpoints have been
removed. Configuration updates now go exclusively through `PATCH /agents/{uuid}`,
which uses the UUID-based agent system and canonical llm_provider/llm_model keys.
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat
from backend.interfaces.http.schemas.config_schemas import VoicePreviewRequest
from backend.domain.use_cases.get_llm_options import GetLLMOptionsUseCase
from backend.domain.use_cases.get_tts_options import GetTTSOptionsUseCase
from backend.infrastructure.adapters.llm.static_registry import StaticLLMRegistryAdapter
from backend.infrastructure.adapters.tts.static_registry import StaticTTSRegistryAdapter
from backend.infrastructure.config.features import features

router = APIRouter(prefix="/config", tags=["config"])
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# GET /config/features                                                          #
# --------------------------------------------------------------------------- #
@router.get("/features")
async def get_system_features():
    """Get system-wide feature flags."""
    return features.get_all()


# --------------------------------------------------------------------------- #
# GET /config/options/llm/providers                                            #
# GET /config/options/llm/models                                               #
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# GET /config/options/tts/voices                                               #
# GET /config/options/tts/languages                                            #
# GET /config/options/tts/styles                                               #
# --------------------------------------------------------------------------- #
@router.get("/options/tts/voices")
async def get_tts_voices(provider: str = "azure", language: str | None = None):
    """Get available TTS voices for a specific provider."""
    registry = StaticTTSRegistryAdapter()
    use_case = GetTTSOptionsUseCase(registry)
    try:
        voices = await use_case.get_voices(provider, language)
        return {"voices": [v.__dict__ for v in voices]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/options/tts/languages")
async def get_tts_languages(provider: str = "azure"):
    """Get available TTS languages for a specific provider."""
    registry = StaticTTSRegistryAdapter()
    use_case = GetTTSOptionsUseCase(registry)
    try:
        langs = await use_case.get_languages(provider)
        return {"languages": langs}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/options/tts/styles")
async def get_tts_styles(voice_id: str, provider: str = "azure"):
    """Get available emotion styles for a specific voice."""
    registry = StaticTTSRegistryAdapter()
    use_case = GetTTSOptionsUseCase(registry)
    try:
        styles = await use_case.get_styles(provider, voice_id)
        return {"styles": styles}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------------------------------- #
# POST /config/options/tts/preview                                             #
# --------------------------------------------------------------------------- #
@router.post("/options/tts/preview")
async def preview_tts_voice(request: VoicePreviewRequest):
    """
    Generate a WAV audio preview for a specific voice configuration.

    Returns Riff16Khz16BitMonoPcm (WAV with RIFF header) — required by
    HTML5 Audio / new Audio(). Raw PCM causes NotSupportedError in browsers.
    """
    registry = StaticTTSRegistryAdapter()

    try:
        adapter = registry.get_provider_adapter(request.provider)

        vc = VoiceConfig(
            name=request.voice_name,
            speed=request.voice_speed,
            pitch=request.voice_pitch,
            volume=request.voice_volume,
            style=request.voice_style or "default",
            style_degree=request.voice_style_degree or 1.0,
        )

        sample_text = "Hola, esta es una prueba de voz para comprobar la configuración."
        if request.provider == "elevenlabs":
            sample_text = "Hello, this is a voice test to check the current configuration."

        # synthesize_for_preview() uses Riff (WAV header included).
        # Fallback: generic synthesize() — non-Azure adapters may not need the header.
        if hasattr(adapter, "synthesize_for_preview"):
            audio_bytes = await adapter.synthesize_for_preview(text=sample_text, voice=vc)
        else:
            format_obj = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
            audio_bytes = await adapter.synthesize(text=sample_text, voice=vc, format=format_obj)

        return Response(content=audio_bytes, media_type="audio/wav")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Text-to-Speech preview failed: {e}")
        raise HTTPException(status_code=500, detail="Voice synthesis failed")
