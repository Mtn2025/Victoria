from typing import List, Dict, Any
from backend.domain.ports.tts_port import VoiceMetadata
from backend.domain.ports.tts_provider_registry import TTSProviderRegistry

class GetTTSOptionsUseCase:
    def __init__(self, registry: TTSProviderRegistry):
        self.registry = registry

    async def get_voices(self, provider_id: str, language: str = None) -> List[VoiceMetadata]:
        adapter = self.registry.get_provider_adapter(provider_id)
        voices = await adapter.get_available_voices(language=language)
        
        # Fallback if no voices returned (e.g. absent API keys)
        if not voices:
            return self._mock_voices(provider_id, language)
        return voices

    async def get_languages(self, provider_id: str) -> List[str]:
        adapter = self.registry.get_provider_adapter(provider_id)
        langs = []
        if hasattr(adapter, 'get_available_languages'):
            langs = await adapter.get_available_languages()
            
        # Fallback if no languages returned
        if not langs:
            return self._mock_languages(provider_id)
        return langs
        
    async def get_styles(self, provider_id: str, voice_id: str) -> List[str]:
        adapter = self.registry.get_provider_adapter(provider_id)
        styles = []
        if hasattr(adapter, 'get_voice_styles'):
            styles = await adapter.get_voice_styles(voice_id)
        return styles

    def _mock_languages(self, provider_id: str) -> List[dict]:
        """Provides mock formats so the UI doesn't break without API keys."""
        if provider_id == "azure":
            return [{"id": "es-MX", "name": "Español (México)"}, {"id": "en-US", "name": "English (US)"}]
        elif provider_id == "elevenlabs":
            return [{"id": "multilingual", "name": "Multilingual (All)"}]
        else:
            return [{"id": "none", "name": "Default"}]

    def _mock_voices(self, provider_id: str, language: str) -> List[VoiceMetadata]:
        """Provides mock voices so the UI doesn't break without API keys."""
        if provider_id == "azure":
            return [
                VoiceMetadata(id="es-MX-DaliaNeural", name="Dalia", gender="female", locale="es-MX"),
                VoiceMetadata(id="es-MX-JorgeNeural", name="Jorge", gender="male", locale="es-MX")
            ]
        elif provider_id == "elevenlabs":
            return [
                VoiceMetadata(id="pNInz6obbfDQGcgMyIGC", name="Adam", gender="male", locale="multilingual"),
                VoiceMetadata(id="EXAVITQu4vr4xnSDxMaL", name="Bella", gender="female", locale="multilingual")
            ]
        else:
            return [VoiceMetadata(id="default", name="Default Voice", gender="neutral", locale="en-US")]
