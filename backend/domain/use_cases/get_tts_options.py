from typing import List, Dict, Any
from backend.domain.ports.tts_port import TTSPort, VoiceMetadata

class GetTTSOptionsUseCase:
    def __init__(self, tts_port: TTSPort):
        self.tts_port = tts_port

    async def get_voices(self, language: str = None) -> List[VoiceMetadata]:
        return await self.tts_port.get_available_voices(language)

    async def get_languages(self) -> List[str]:
        return await self.tts_port.get_available_languages()
