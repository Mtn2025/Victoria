import asyncio
import logging
from unittest.mock import AsyncMock

from backend.application.processors.frames import TextFrame, UserStartedSpeakingFrame, FrameDirection
from backend.application.processors.stt_processor import STTProcessor
from backend.domain.ports.stt_port import STTPort, STTConfig, STTSession
from backend.domain.value_objects.audio_format import AudioFormat

logging.basicConfig(level=logging.DEBUG)

class MockSession(STTSession):
    def __init__(self):
        self.text_yields = [
            ("hola como estas", False),
            ("hola como estas", False),
            ("espera un momento", False)
        ]
    async def process_audio(self, audio_data: bytes):
        pass
    async def get_results(self):
        for t, final in self.text_yields:
            yield t, final
            await asyncio.sleep(0.1)
    async def close(self):
        pass
    def subscribe(self, event, callback):
        pass

class MockSTTPort(STTPort):
    async def start_stream(self, format: AudioFormat, config: STTConfig) -> STTSession:
        return MockSession()
    async def transcribe(self, audio_data: bytes, format: AudioFormat, config: STTConfig) -> str:
        return ""
    async def close(self):
        pass

class MockConfig:
    barge_in_phrases = ["espera", "para"]
    client_type = "browser"

async def test_semantic_barge():
    port = MockSTTPort()
    fmt = AudioFormat.for_client("browser")
    config = MockConfig()
    
    stt = STTProcessor(stt_provider=port, audio_format=fmt, config=config)
    
    frames_received = []
    
    class DummyDownstream:
        async def process_frame(self, frame, d):
            frames_received.append(frame)
    
    stt.link(DummyDownstream())
    
    await stt.start()
    
    # Let the background reader task run for a bit
    await asyncio.sleep(0.5)
    
    await stt.stop()
    
    barge_triggered = any(isinstance(f, UserStartedSpeakingFrame) for f in frames_received)
    assert barge_triggered, "Barge-in frame was not pushed downstream!"
    print("TEST PASSED: UserStartedSpeakingFrame requested successfully.")

if __name__ == "__main__":
    asyncio.run(test_semantic_barge())
