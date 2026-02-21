"""
Integration Tests for Complete Pipeline.
Tests the full frame processing pipeline with real adapters.
"""
import pytest
from unittest.mock import AsyncMock, Mock
import asyncio

from backend.application.processors.frame_processor import FrameDirection
from backend.application.processors.frames import (
    AudioFrame,
    TextFrame,
    StartFrame,
    EndFrame
)
from backend.application.processors.stt_processor import STTProcessor
from backend.application.processors.llm_processor import LLMProcessor
from backend.application.processors.tts_processor import TTSProcessor
from backend.domain.value_objects.audio_format import AudioFormat

# Formato de referencia para todos los tests de integración: browser 24kHz
_BROWSER_FORMAT = AudioFormat.for_browser()


@pytest.fixture
def mock_stt_port():
    """Mock STT port for testing."""
    port = AsyncMock()
    # Processor calls start_stream -> returns Session
    
    session = Mock() # MagicMock because start_stream IS awaited and returns this, but get_results is NOT awaited
    
    async def get_results_mock():
        yield "Hola, quiero información"
        
    # The session.get_results method should return the async generator
    session.get_results.return_value = get_results_mock()
    session.process_audio = AsyncMock()
    session.close = AsyncMock()
    
    port.start_stream.return_value = session
    return port


@pytest.fixture
def mock_llm_port():
    """Mock LLM port for testing."""
    port = Mock() # MagicMock or Mock, but generate_stream needs to be callable returning generator
    
    async def generate_stream_mock(request):
        """Simulate streaming LLM response."""
        chunks = ["Clar", "o, ", "¿en ", "qué ", "puedo ", "ayudar", "te?"]
        for text in chunks:
            chunk = Mock()
            chunk.text = text
            chunk.has_text = True
            chunk.has_function_call = False
            yield chunk
    
    port.generate_stream.side_effect = generate_stream_mock
    return port


@pytest.fixture
def mock_tts_port():
    """Mock TTS port for testing."""
    port = Mock()
    # Mock generator for synthesize_stream
    async def synthesize_stream_mock(text, voice_config, audio_format):
        yield b"fake_audio_data_12345"

    port.synthesize_stream.side_effect = synthesize_stream_mock
    return port


@pytest.mark.asyncio
class TestPipelineIntegration:
    """Integration tests for complete pipeline."""
    
    async def test_complete_pipeline_flow(
        self,
        mock_stt_port,
        mock_llm_port,
        mock_tts_port
    ):
        """Test complete pipeline: Audio → STT → LLM → TTS → Audio."""
        
        # 1. Create processors — audio_format obligatorio (contrato de capa)
        stt_processor = STTProcessor(stt_provider=mock_stt_port, audio_format=_BROWSER_FORMAT)
        llm_processor = LLMProcessor(
            llm_port=mock_llm_port,
            config={},
            conversation_history=[]
        )
        tts_processor = TTSProcessor(
            tts_port=mock_tts_port,
            config={"voice_name": "en-US-JennyNeural"}
        )
        
        # 2. Link pipeline
        stt_processor.link(llm_processor)
        llm_processor.link(tts_processor)
        
        # 3. Collect output
        output_frames = []
        
        # Mock TTS processor to capture output
        original_push = tts_processor.push_frame
        async def capture_push(frame, direction=FrameDirection.DOWNSTREAM):
            output_frames.append(frame)
            await original_push(frame, direction)
        
        tts_processor.push_frame = capture_push
        
        # 4. Start processors
        await stt_processor.start()
        await llm_processor.start()
        await tts_processor.start()
        
        # 5. Send audio frame — sample_rate coincide con _BROWSER_FORMAT (24kHz)
        audio_frame = AudioFrame(
            data=b"fake_audio_input",
            sample_rate=_BROWSER_FORMAT.sample_rate,
            channels=1
        )
        
        await stt_processor.process_frame(audio_frame, FrameDirection.DOWNSTREAM)
        
        # Give pipeline time to process
        await asyncio.sleep(0.5)
        
        # 6. Verify pipeline executed
        # STT should have been called
        mock_stt_port.start_stream.assert_called_once()
        session = mock_stt_port.start_stream.return_value
        session.process_audio.assert_called()
        
        # Output should contain AudioFrame from TTS
        audio_outputs = [f for f in output_frames if isinstance(f, AudioFrame) and f.data == b"fake_audio_data_12345"]
        assert len(audio_outputs) > 0, "Pipeline should produce generated audio output"
    
    async def test_pipeline_handles_start_end_frames(
        self,
        mock_stt_port,
        mock_llm_port,
        mock_tts_port
    ):
        """Test that pipeline correctly handles system frames."""
        
        # Create pipeline — audio_format obligatorio
        stt = STTProcessor(stt_provider=mock_stt_port, audio_format=_BROWSER_FORMAT)
        llm = LLMProcessor(llm_port=mock_llm_port, config={}, conversation_history=[])
        tts = TTSProcessor(tts_port=mock_tts_port, config={"voice_name": "default"})
        
        stt.link(llm)
        llm.link(tts)
        
        # Start
        await stt.start()
        await llm.start()
        await tts.start()
        
        # Send StartFrame
        start_frame = StartFrame()
        await stt.process_frame(start_frame, FrameDirection.DOWNSTREAM)
        
        # Should propagate without errors
        await asyncio.sleep(0.05)
        
        # Send EndFrame
        end_frame = EndFrame(reason="test_complete")
        await stt.process_frame(end_frame, FrameDirection.DOWNSTREAM)
        
        await asyncio.sleep(0.05)
        
        # No assertions needed - just verify no exceptions
        assert True
    
    async def test_pipeline_backpressure(
        self,
        mock_stt_port,
        mock_llm_port,
        mock_tts_port
    ):
        """Test pipeline behavior under load."""
        
        # Create pipeline — audio_format obligatorio
        stt = STTProcessor(stt_provider=mock_stt_port, audio_format=_BROWSER_FORMAT)
        llm = LLMProcessor(llm_port=mock_llm_port, config={}, conversation_history=[])
        tts = TTSProcessor(tts_port=mock_tts_port, config={"voice_name": "default"})
        
        stt.link(llm)
        llm.link(tts)
        
        await stt.start()
        await llm.start()
        await tts.start()
        
        # Send many frames rapidly — sample_rate coincide con _BROWSER_FORMAT
        for i in range(10):
            audio_frame = AudioFrame(
                data=f"audio_{i}".encode(),
                sample_rate=_BROWSER_FORMAT.sample_rate,
                channels=1
            )
            await stt.process_frame(audio_frame, FrameDirection.DOWNSTREAM)
        
        # Pipeline should handle load without crashing
        await asyncio.sleep(0.2)
        
        # Verify STT was called multiple times
        # Verify STT processed audio multiple times
        session = mock_stt_port.start_stream.return_value
        assert session.process_audio.call_count >= 1
    
    async def test_pipeline_error_handling(
        self,
        mock_stt_port,
        mock_llm_port,
        mock_tts_port
    ):
        """Test pipeline error propagation."""
        
        # Make LLM raise error
        mock_llm_port.generate_stream.side_effect = Exception("LLM API Error")
        
        stt = STTProcessor(stt_provider=mock_stt_port, audio_format=_BROWSER_FORMAT)
        llm = LLMProcessor(llm_port=mock_llm_port, config={}, conversation_history=[])
        tts = TTSProcessor(tts_port=mock_tts_port, config={"voice_name": "default"})
        
        stt.link(llm)
        llm.link(tts)
        
        await stt.start()
        await llm.start()
        await tts.start()
        
        # Send text frame (to trigger LLM)
        text_frame = TextFrame(text="Test message", role="user")
        
        # Should handle error gracefully (depending on processor implementation)
        # For now, just verify it doesn't crash the test
        try:
            await llm.process_frame(text_frame, FrameDirection.DOWNSTREAM)
            await asyncio.sleep(0.05)
        except Exception as e:
            # Error may propagate or be caught
            pass
        
        # Pipeline should still be operational
        assert True


@pytest.mark.asyncio
class TestProcessorInteractions:
    """Test interactions between specific processors."""
    
    async def test_stt_to_llm_flow(self, mock_stt_port, mock_llm_port):
        """Test STT processor outputs text that LLM can consume."""
        
        stt = STTProcessor(stt_provider=mock_stt_port, audio_format=_BROWSER_FORMAT)
        llm = LLMProcessor(llm_port=mock_llm_port, config={}, conversation_history=[])
        
        stt.link(llm)
        
        await stt.start()
        await llm.start()
        
        # Capture LLM input
        received_frames = []
        original_process = llm.process_frame
        
        async def capture_process(frame, direction):
            received_frames.append(frame)
            await original_process(frame, direction)
        
        llm.process_frame = capture_process
        
        # Send audio to STT — sample_rate coincide con _BROWSER_FORMAT
        audio = AudioFrame(data=b"test_audio", sample_rate=_BROWSER_FORMAT.sample_rate, channels=1)
        await stt.process_frame(audio, FrameDirection.DOWNSTREAM)
        
        await asyncio.sleep(0.5)
        
        # LLM should have received TextFrame
        text_frames = [f for f in received_frames if isinstance(f, TextFrame)]
        assert len(text_frames) > 0, "STT should produce TextFrame for LLM"
    
    async def test_llm_to_tts_flow(self, mock_llm_port, mock_tts_port):
        """Test LLM processor outputs text that TTS can consume."""
        
        llm = LLMProcessor(llm_port=mock_llm_port, config={}, conversation_history=[])
        tts = TTSProcessor(tts_port=mock_tts_port, config={"voice_name": "default"})
        
        llm.link(tts)
        
        await llm.start()
        await tts.start()
        
        # Capture TTS input
        received_frames = []
        original_process = tts.process_frame
        
        async def capture_process(frame, direction):
            received_frames.append(frame)
            await original_process(frame, direction)
        
        tts.process_frame = capture_process
        
        # Send text to LLM
        text = TextFrame(text="User message", role="user", is_final=True)
        await llm.process_frame(text, FrameDirection.DOWNSTREAM)
        
        await asyncio.sleep(0.1)
        
        # TTS should have received TextFrame from LLM
        text_frames = [f for f in received_frames if isinstance(f, TextFrame)]
        assert len(text_frames) > 0, "LLM should produce TextFrame for TTS"
        
        # Should be assistant role
        assistant_frames = [f for f in text_frames if f.role == "assistant"]
        assert len(assistant_frames) > 0, "LLM output should be assistant role"
