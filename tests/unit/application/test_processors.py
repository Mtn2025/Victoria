import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.application.processors.stt_processor import STTProcessor
from backend.application.processors.vad_processor import VADProcessor
from backend.application.processors.llm_processor import LLMProcessor
from backend.application.processors.tts_processor import TTSProcessor
from backend.application.processors.frames import AudioFrame, TextFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from backend.application.processors.frame_processor import FrameDirection
from backend.domain.ports.stt_port import STTPort, STTSession
from backend.domain.ports.llm_port import LLMPort, LLMRequest, LLMResponseChunk
from backend.domain.ports.tts_port import TTSPort
from backend.domain.value_objects.audio_format import AudioFormat

# STT Processor Tests

class TestSTTProcessor:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=STTSession)
        async def result_gen():
            yield "Hello"
            yield "World"
        session.get_results.return_value = result_gen()
        return session

    @pytest.fixture
    def mock_provider(self, mock_session):
        provider = AsyncMock(spec=STTPort)
        provider.start_stream.return_value = mock_session
        return provider

    @pytest.fixture
    def processor(self, mock_provider):
        # audio_format obligatorio (contrato de capa — ver audio_format.py)
        return STTProcessor(stt_provider=mock_provider, audio_format=AudioFormat.for_browser())

    @pytest.mark.asyncio
    async def test_process_audio_pushes_to_session(self, processor, mock_provider, mock_session):
        await processor.start()
        processor.push_frame = AsyncMock()
        
        frame = AudioFrame(data=b"audio", sample_rate=16000, metadata={"duration_ms": 20})
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        
        mock_session.process_audio.assert_called_once_with(b"audio")
        processor.push_frame.assert_called_once_with(frame, FrameDirection.DOWNSTREAM)
        
        await processor.stop()

    @pytest.mark.asyncio
    async def test_read_results_pushes_text_frames(self, processor, mock_provider):
        processor.push_frame = AsyncMock()
        await processor.start()
        await asyncio.sleep(0.1)
        
        assert processor.push_frame.call_count >= 2
        args1, _ = processor.push_frame.call_args_list[0]
        assert isinstance(args1[0], TextFrame)
        assert args1[0].text == "Hello"
        
        await processor.stop()

# VAD Processor Tests

class TestVADProcessor:
    @pytest.fixture
    def mock_vad_adapter(self):
        mock = MagicMock()
        mock.return_value = 0.0
        return mock

    @pytest.fixture
    def mock_detect_use_case(self):
        uc = MagicMock()
        uc.execute.return_value = False
        return uc

    @pytest.fixture
    def processor(self, mock_vad_adapter, mock_detect_use_case):
        config = MagicMock()
        config.vad_confirmation_window_ms = 0
        config.client_type = 'browser'
        config.silence_timeout_ms = 1000
        
        proc = VADProcessor(config, mock_detect_use_case, vad_adapter=mock_vad_adapter)
        proc.push_frame = AsyncMock()
        return proc

    @pytest.mark.asyncio
    async def test_speech_detection_trigger(self, processor, mock_vad_adapter):
        chunk = b'\x00' * 1024
        mock_vad_adapter.return_value = 0.8 # Speaking
        
        frame = AudioFrame(data=chunk, sample_rate=16000, metadata={"duration_ms": 32})
        
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        
        calls = processor.push_frame.call_args_list
        started_frames = [c.args[0] for c in calls if isinstance(c.args[0], UserStartedSpeakingFrame)]
        assert len(started_frames) == 1
        assert processor.speaking is True

# LLM Processor Tests

class TestLLMProcessor:
    @pytest.fixture
    def mock_llm_port(self):
        port = AsyncMock(spec=LLMPort)
        async def mock_stream(request):
            yield LLMResponseChunk(text="Hello", is_final=False)
            yield LLMResponseChunk(text=" there.", is_final=True)
        port.generate_stream.side_effect = mock_stream
        return port

    @pytest.fixture
    def processor(self, mock_llm_port):
        config = MagicMock()
        # Mock attributes accessed by get_cfg helper
        config.llm_model = "test-model"
        config.dynamic_vars_enabled = False # Prevent iteration error in PromptBuilder
        
        # Or if config is accessed as dict
        # Config can be anything. Using MagicMock that responds to getattr.
        
        proc = LLMProcessor(
            llm_port=mock_llm_port,
            config=config,
            conversation_history=[]
        )
        proc.push_frame = AsyncMock()
        return proc

    @pytest.mark.asyncio
    async def test_handle_user_text_generates_response(self, processor, mock_llm_port):
        frame = TextFrame(text="Hi", role="user", is_final=True)
        
        # Trigger processing
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        
        # Wait for background task
        await asyncio.sleep(0.1)
        
        mock_llm_port.generate_stream.assert_called_once()
        
        # Verify Assistant TextFrames pushed
        # Logic buffers text. "Hello there." might be split if > 10 chars and punctuation.
        # "Hello there." -> 12 chars, ends with dot.
        # Should push one frame.
        
        assert processor.push_frame.call_count >= 2 # 1 for User frame pass-through, 1 for Assistant
        
        user_calls = [c for c in processor.push_frame.call_args_list if c.args[0].role == "user"]
        asst_calls = [c for c in processor.push_frame.call_args_list if c.args[0].role == "assistant"]
        
        assert len(user_calls) == 1
        assert len(asst_calls) >= 1
        assert "Hello there." in "".join([c.args[0].text for c in asst_calls])


# TTS Processor Tests

class TestTTSProcessor:
    @pytest.fixture
    def mock_tts_port(self):
        port = AsyncMock(spec=TTSPort)
        async def mock_synth(text, voice, format):
            yield b"audio_chunk"
        # Use MagicMock for async generator to avoid coroutine wrapping issues
        port.synthesize_stream = MagicMock(side_effect=mock_synth)
        return port

    @pytest.fixture
    def processor(self, mock_tts_port):
        config = MagicMock()
        config.voice_name = "v"
        config.voice_speed = 1.0
        config.voice_pitch = 0.0
        config.voice_volume = 100.0
        config.voice_style = "default"
        config.voice_style_degree = 1.0
        config.client_type = "browser"
        
        proc = TTSProcessor(tts_port=mock_tts_port, config=config)
        proc.push_frame = AsyncMock()
        return proc

    @pytest.mark.asyncio
    async def test_process_assistant_text_synthesizes(self, processor, mock_tts_port):
        await processor.start()
        
        frame = TextFrame(text="Hello", role="assistant")
        await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        
        # Wait for worker
        await asyncio.sleep(0.1)
        
        mock_tts_port.synthesize_stream.assert_called_once()
        
        # Verify AudioFrame pushed
        assert processor.push_frame.call_count >= 1
        args, _ = processor.push_frame.call_args
        assert isinstance(args[0], AudioFrame)
        assert args[0].data == b"audio_chunk"
        
        await processor.stop()
