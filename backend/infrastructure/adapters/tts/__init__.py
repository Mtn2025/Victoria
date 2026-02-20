"""TTS Adapters."""
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.infrastructure.adapters.tts.tts_fallback import TTSFallbackAdapter

__all__ = [
    "AzureTTSAdapter",
    "TTSFallbackAdapter",
]
