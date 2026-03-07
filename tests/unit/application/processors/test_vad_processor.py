import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from backend.application.processors.vad_processor import VADProcessor, SileroVadAdapter
from backend.application.processors.frames import AudioFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from backend.application.processors.frame_processor import FrameDirection
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase

class MockConfig:
    client_type = 'browser'
    silence_timeout_ms = 1000
    vad_confirmation_window_ms = 0
    vad_min_speech_frames = 3
    vad_threshold_start = 0.5
    vad_threshold_return = 0.35
    vad_enable_confirmation = False
    barge_in_enabled = True
    barge_in_sensitivity = 1.0

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
    
    chunk = b'\x00' * 512 
    frame = AudioFrame(data=chunk, sample_rate=8000)
    
    # Send 3 frames
    with patch("time.time", side_effect=[1000.0, 1000.0, 1000.0, 1001.0, 1001.0]):
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM) # Trigger confirm
    
    # Verify UserStartedSpeakingFrame emitted
    frames_emitted = [call.args[0] for call in downstream.process_frame.call_args_list]
    start_frames = [f for f in frames_emitted if isinstance(f, UserStartedSpeakingFrame)]
    
    assert len(start_frames) > 0

@pytest.mark.asyncio
async def test_vad_stop_speaking(mock_vad_adapter, detect_turn_end):
    processor = VADProcessor(MockConfig(), detect_turn_end, vad_adapter=mock_vad_adapter)
    downstream = AsyncMock()
    processor.link(downstream)
    
    # Force speaking state as if _trigger_start_speaking just ran
    processor.speaking = True
    processor.speech_frames = 10
    processor.silence_frames = 0
    processor._voice_detected_at = None
    
    # Silence adapter
    mock_vad_adapter.side_effect = lambda x, sr: 0.0 # Absolute silence
    
    chunk = b'\x00' * 512
    frame = AudioFrame(data=chunk, sample_rate=8000)
    
    # Threshold 1200ms (forced minimum in VADProcessor). Chunk 32ms.
    # We need at least 1200 / 32 = 37.5 frames. Let's send 50.
    for _ in range(50):
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
            
    frames_emitted = [call.args[0] for call in downstream.process_frame.call_args_list]
    stop_frames = [f for f in frames_emitted if isinstance(f, UserStoppedSpeakingFrame)]
    
    assert len(stop_frames) >= 1
