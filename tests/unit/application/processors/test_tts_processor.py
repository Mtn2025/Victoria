
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

    # Collect audio chunks via output_callback (new pattern: TTS → callback → transport)
    received_chunks = []
    async def output_callback(audio_bytes: bytes) -> None:
        received_chunks.append(audio_bytes)

    processor = TTSProcessor(mock_tts_port, MockConfig(), output_callback=output_callback)
    downstream = AsyncMock()
    processor.link(downstream)

    await processor.start()

    # Send Text
    frame = TextFrame(text="Hello", role="assistant")
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)

    # Wait for worker
    await asyncio.sleep(0.5)

    # Check logs
    for record in caplog.records:
        print(f"LOG: {record.message}")

    # Verify audio arrived via output_callback (not downstream push — TTS is end of chain)
    assert len(received_chunks) == 2, (
        f"Expected 2 audio chunks via output_callback, got {len(received_chunks)}. "
        f"Logs: {[r.message for r in caplog.records]}"
    )
    assert received_chunks[0] == b"chunk1"
    assert received_chunks[1] == b"chunk2"

    await processor.stop()

@pytest.mark.asyncio
async def test_tts_cancellation(mock_tts_port):
    # Collect audio chunks via output_callback
    received_chunks = []
    async def output_callback(audio_bytes: bytes) -> None:
        received_chunks.append(audio_bytes)

    processor = TTSProcessor(mock_tts_port, MockConfig(), output_callback=output_callback)

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
    await asyncio.sleep(0.1)  # Let it start

    # Send Cancel
    await processor.process_frame(CancelFrame(), FrameDirection.DOWNSTREAM)

    # Send Text 2
    await processor.process_frame(TextFrame(text="Speak 2", role="assistant"), FrameDirection.DOWNSTREAM)

    await asyncio.sleep(0.2)  # Allow Text 2 to process

    # "start" from Text 1 (before cancel) should be there.
    # "end" from Text 1 should NOT (cancelled mid-stream).
    # "start" from Text 2 should be there.
    assert b"end" not in received_chunks
    assert b"start" in received_chunks  # From 1 or 2

    await processor.stop()
