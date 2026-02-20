from typing import List, Dict, Any
from backend.domain.ports.tts_port import VoiceMetadata
from backend.domain.ports.tts_provider_registry import TTSProviderRegistry

class GetTTSOptionsUseCase:
    def __init__(self, registry: TTSProviderRegistry):
        self.registry = registry

    async def get_voices(self, provider_id: str, language: str = None) -> List[VoiceMetadata]:
        adapter = self.registry.get_provider_adapter(provider_id)
        return await adapter.get_available_voices(language=language)

    async def get_languages(self, provider_id: str) -> List[str]:
        # Most TTS ports might not have a generic get_available_languages yet in TTSPort
        # If it doesn't exist, we will try to call it, or fallback.
        adapter = self.registry.get_provider_adapter(provider_id)
        if hasattr(adapter, 'get_available_languages'):
            return await adapter.get_available_languages()
        return []
        
    async def get_styles(self, provider_id: str, voice_id: str) -> List[str]:
        adapter = self.registry.get_provider_adapter(provider_id)
        if hasattr(adapter, 'get_voice_styles'):
            return await adapter.get_voice_styles(voice_id)
        return []
