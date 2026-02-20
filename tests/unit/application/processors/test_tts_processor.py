
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from backend.application.processors.tts_processor import TTSProcessor
from backend.application.processors.frames import TextFrame, AudioFrame, CancelFrame
from backend.application.processors.frame_processor import FrameDirection
from backend.domain.ports.tts_port import TTSPort

class MockConfig:
    voice_name = "test-voice"
    client_type = "twilio"

@pytest.fixture
def mock_tts_port():
    port = MagicMock(spec=TTSPort)
    async def stream_gen(text, voice, format):
        yield b"chunk1"
        yield b"chunk2"
    port.synthesize_stream.side_effect = stream_gen
    return port

@pytest.mark.asyncio
async def test_tts_process_text(mock_tts_port, caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    
    processor = TTSProcessor(mock_tts_port, MockConfig())
    downstream = AsyncMock()
    processor.link(downstream)
    
    await processor.start()
    
    # Send Text
    frame = TextFrame(text="Hello", role="assistant")
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    
    # Wait for worker
    await asyncio.sleep(0.5) # Increase wait time
    
    # Check logs
    for record in caplog.records:
        print(f"LOG: {record.message}")
    
    # Check Downstream Audio
    frames = [call.args[0] for call in downstream.process_frame.call_args_list if isinstance(call.args[0], AudioFrame)]
    assert len(frames) == 2, f"Expected 2 frames, got {len(frames)}. Logs: {[r.message for r in caplog.records]}"
    assert frames[0].data == b"chunk1"
    assert frames[1].data == b"chunk2"
    
    await processor.stop()

@pytest.mark.asyncio
async def test_tts_cancellation(mock_tts_port):
    processor = TTSProcessor(mock_tts_port, MockConfig())
    
    # Mock synthesis to hang/sleep
    async def slow_gen(text, voice, fmt):
        yield b"start"
        await asyncio.sleep(1.0)
        yield b"end"
        
    mock_tts_port.synthesize_stream.side_effect = slow_gen
    
    downstream = AsyncMock()
    processor.link(downstream)
    await processor.start()
    
    # Send Text 1
    await processor.process_frame(TextFrame(text="Speak 1", role="assistant"), FrameDirection.DOWNSTREAM)
    await asyncio.sleep(0.1) # Let it start
    
    # Send Cancel
    await processor.process_frame(CancelFrame(), FrameDirection.DOWNSTREAM)
    
    # Send Text 2
    await processor.process_frame(TextFrame(text="Speak 2", role="assistant"), FrameDirection.DOWNSTREAM)
    
    await asyncio.sleep(0.2) # Allow Text 2 to process
    
    # Check audio frames
    # We expect "start" from Text 1 (before cancel)
    # Then maybe "start" from Text 2.
    # Text 1 should NOT complete "end".
    
    frames = [call.args[0] for call in downstream.process_frame.call_args_list if isinstance(call.args[0], AudioFrame)]
    
    data_chunks = [f.data for f in frames]
    # "start" from 1 might be there.
    # "end" from 1 should NOT be there (cancelled).
    # "start" from 2 should be there.
    
    assert b"end" not in data_chunks
    assert b"start" in data_chunks # From 1 or 2
    
    await processor.stop()
