
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from backend.application.processors.stt_processor import STTProcessor
from backend.application.processors.frames import AudioFrame, TextFrame
from backend.application.processors.frame_processor import FrameDirection
from backend.domain.ports.stt_port import STTPort, STTSession
from backend.domain.value_objects.audio_format import AudioFormat

class MockSTTSession(STTSession):
    def __init__(self):
        self.queue = asyncio.Queue()
        self.closed = False

    async def process_audio(self, audio_chunk: bytes) -> None:
        # Simulate processing - if "trigger" in bytes, yield text
        if b"trigger" in audio_chunk:
            await self.queue.put("Hello World")

    async def get_results(self) -> AsyncGenerator[str, None]:
        while not self.closed:
            try:
                # Timeout to allow test to cancel
                text = await asyncio.wait_for(self.queue.get(), 0.1)
                yield text
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def subscribe(self, callback):
        pass  # No-op for mock

    async def close(self) -> None:
        self.closed = True

@pytest.fixture
def mock_stt_port():
    port = MagicMock(spec=STTPort)
    session = MockSTTSession()
    port.start_stream = AsyncMock(return_value=session)
    return port, session

@pytest.mark.asyncio
async def test_stt_processor_lifecycle(mock_stt_port):
    port, session = mock_stt_port
    # audio_format obligatorio (contrato de capa — ver audio_format.py)
    processor = STTProcessor(port, audio_format=AudioFormat.for_telephony())
    
    # Start
    await processor.start()
    port.start_stream.assert_awaited_once()
    assert processor.session is session
    assert not processor._reader_task.done()
    
    # Stop
    await processor.stop()
    assert session.closed
    assert processor._reader_task.done()

@pytest.mark.asyncio
async def test_process_audio_frame(mock_stt_port):
    # Setup
    port, session = mock_stt_port
    # for_telephony() = 8kHz, coincide con sample_rate=8000 del AudioFrame
    processor = STTProcessor(port, audio_format=AudioFormat.for_telephony())
    
    # Mock downstream
    downstream = AsyncMock()
    processor.link(downstream)
    
    await processor.start()
    
    # Send Audio
    frame = AudioFrame(data=b"trigger audio", sample_rate=8000)
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    
    # Verify downstream received the audio frame (pass-through)
    downstream.process_frame.assert_awaited_with(frame, FrameDirection.DOWNSTREAM)
    
    # Verify Text Generated (async wait)
    # We expect the reader task to pick up "Hello World" from session queue
    # and push a new TextFrame downstream.
    
    # Wait a bit for background task
    await asyncio.sleep(0.2)
    
    # Check downstream calls
    # Should have called:
    # 1. process_frame(audio_frame) (Pass through)
    # 2. process_frame(text_frame) (Generated)
    
    assert downstream.process_frame.call_count >= 2
    
    # Find TextFrame in calls
    text_frame_found = False
    for call in downstream.process_frame.call_args_list:
        args, _ = call
        if isinstance(args[0], TextFrame) and args[0].text == "Hello World":
            text_frame_found = True
            break
            
    assert text_frame_found
    
    await processor.stop()
