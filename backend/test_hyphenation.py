import asyncio
import logging
from backend.application.processors.tts_processor import TTSProcessor
from backend.domain.ports.tts_port import TTSPort
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat

logging.basicConfig(level=logging.INFO)

class MockTTS(TTSPort):
    async def synthesize(self, text: str, voice: VoiceConfig, format:AudioFormat) -> bytes: 
        return b""
    async def synthesize_stream(self, text: str, voice: VoiceConfig, format: AudioFormat):
        print(f"--- MOCK TTS RECEIVED TEXT ---\n{text}\n------------------------------")
        yield b"audio"
    async def synthesize_ssml(self, ssml: str, voice: VoiceConfig, format: AudioFormat): pass
    async def synthesize_request(self, req): pass
    async def get_available_voices(self, lang): return []
    async def get_voice_styles(self, name): return []
    async def close(self): pass

class MockConfig:
    pacing_hyphenation = True
    client_type = "browser"

async def test_hyphenation():
    tts = TTSProcessor(MockTTS(), MockConfig())
    await tts._synthesize("Hola, cómo estás el día de hoy. Espero que muy bien", "trace-123")

if __name__ == "__main__":
    asyncio.run(test_hyphenation())
