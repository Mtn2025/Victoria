
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from backend.application.processors.vad_processor import VADProcessor, SileroVadAdapter
from backend.application.processors.frames import AudioFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from backend.application.processors.frame_processor import FrameDirection
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase

class MockConfig:
    client_type = 'twilio'
    silence_timeout_ms = 500
    vad_confirmation_window_ms = 0 # Immediate trigger for test simplification
    vad_enable_confirmation = False

@pytest.fixture
def mock_vad_adapter():
    adapter = MagicMock(spec=SileroVadAdapter)
    # Mock return confidence
    adapter.side_effect = lambda x, sr: 0.9 # Always confident for this test
    return adapter

@pytest.fixture
def detect_turn_end():
    return DetectTurnEndUseCase()

@pytest.mark.asyncio
async def test_vad_start_speaking(mock_vad_adapter, detect_turn_end):
    processor = VADProcessor(MockConfig(), detect_turn_end, vad_adapter=mock_vad_adapter)
    
    downstream = AsyncMock()
    processor.link(downstream)
    
    # 512 samples for 16k, 256 for 8k. Config uses twilio (8k).
    # 256 samples * 2 bytes = 512 bytes per chunk.
    # Need 3 frames (min_speech_frames=3) to trigger.
    
    chunk = b'\x00' * 512 
    frame = AudioFrame(data=chunk, sample_rate=8000)
    
    # Send 3 frames
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    
    # Verify UserStartedSpeakingFrame emitted
    frames_emitted = [call.args[0] for call in downstream.process_frame.call_args_list]
    start_frames = [f for f in frames_emitted if isinstance(f, UserStartedSpeakingFrame)]
    
    assert len(start_frames) > 0

@pytest.mark.asyncio
async def test_vad_stop_speaking(mock_vad_adapter, detect_turn_end):
    processor = VADProcessor(MockConfig(), detect_turn_end, vad_adapter=mock_vad_adapter)
    downstream = AsyncMock()
    processor.link(downstream)
    
    # Force speaking state
    processor.speaking = True
    processor.speech_frames = 10
    
    # Silence adapter
    mock_vad_adapter.side_effect = lambda x, sr: 0.1 # Low confidence
    
    # Send enough silence frames to trigger turn end
    # Threshold 500ms. Chunk 32ms.
    # Need ~16 frames.
    chunk = b'\x00' * 512
    frame = AudioFrame(data=chunk, sample_rate=8000)
    
    for _ in range(20):
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        
    frames_emitted = [call.args[0] for call in downstream.process_frame.call_args_list]
    stop_frames = [f for f in frames_emitted if isinstance(f, UserStoppedSpeakingFrame)]
    
    assert len(stop_frames) > 0
