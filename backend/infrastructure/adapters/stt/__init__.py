"""STT Adapters."""
from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter
from backend.infrastructure.adapters.stt.stt_fallback import STTFallbackAdapter

__all__ = [
    "AzureSTTAdapter",
    "STTFallbackAdapter",
]
