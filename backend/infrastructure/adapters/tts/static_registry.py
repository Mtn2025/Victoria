"""
Static TTS Provider Registry Adapter.
Part of the Infrastructure Layer.

Provides a hardcoded or configured mapping of providers to their TTS adapters.
"""
from typing import List, Dict, Type

from backend.domain.ports.tts_provider_registry import TTSProviderRegistry
from backend.domain.ports.tts_port import TTSPort
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
# Import other adapters when they are functional
# from backend.infrastructure.adapters.tts.elevenlabs_adapter import ElevenLabsTTSAdapter

class StaticTTSRegistryAdapter(TTSProviderRegistry):
    """
    Static registry implementation. Instantiates adapters lazily or returns pre-configured ones.
    """
    
    def __init__(self):
        # We can store singleton instances here if we want to share sessions
        self._adapters_cache: Dict[str, TTSPort] = {}
        
        # Define supported providers and their adapter classes
        self._provider_map: Dict[str, Type[TTSPort]] = {
            "azure": AzureTTSAdapter
            # "elevenlabs": ElevenLabsTTSAdapter
            # "openai": OpenAITTSAdapter
        }

    def get_provider_adapter(self, provider_id: str) -> TTSPort:
        """Get or instantiate the adapter for the given provider."""
        if not provider_id:
            provider_id = "azure" # Default fallback
            
        if provider_id not in self._provider_map:
            raise ValueError(f"TTS Provider '{provider_id}' is not supported.")
            
        if provider_id not in self._adapters_cache:
            adapter_class = self._provider_map[provider_id]
            self._adapters_cache[provider_id] = adapter_class()
            
        return self._adapters_cache[provider_id]

    def get_supported_providers(self) -> List[str]:
        """Return the list of configured providers."""
        return list(self._provider_map.keys())
