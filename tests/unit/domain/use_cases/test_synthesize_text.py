import pytest
from unittest.mock import AsyncMock, Mock

from backend.domain.use_cases.synthesize_text import SynthesizeTextUseCase
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat


class TestSynthesizeTextUseCase:
    """Test direct TTS synthesis use case."""

    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful text synthesis."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio_data")

        voice_config = VoiceConfig(
            name="en-US-JennyNeural",
            style="friendly",
            speed=1.0,
            pitch=0
        )

        use_case = SynthesizeTextUseCase(mock_tts)

        audio = await use_case.execute(
            text="Hello, how can I help you?",
            voice_config=voice_config,
            trace_id="test-123"
        )

        assert audio == b"audio_data"
        # execute() defaults to AudioFormat.for_browser() — verify it is forwarded
        mock_tts.synthesize.assert_called_once_with(
            "Hello, how can I help you?",
            voice_config,
            AudioFormat.for_browser(),
        )
    
    @pytest.mark.asyncio
    async def test_synthesize_with_trace_id(self):
        """Test synthesis includes trace_id in logs."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio")
        
        voice_config = Mock()
        use_case = SynthesizeTextUseCase(mock_tts)
        
        audio = await use_case.execute(
            text="Test message",
            voice_config=voice_config,
            trace_id="trace-456"
        )
        
        assert audio == b"audio"
    
    @pytest.mark.asyncio
    async def test_synthesize_failure_raises(self):
        """Test synthesis failure propagates exception."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(side_effect=Exception("TTS Error"))
        
        voice_config = Mock()
        use_case = SynthesizeTextUseCase(mock_tts)
        
        with pytest.raises(Exception, match="TTS Error"):
            await use_case.execute(
                text="Error test",
                voice_config=voice_config
            )
    
    @pytest.mark.asyncio
    async def test_long_text_synthesis(self):
        """Test synthesis of long text."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(return_value=b"long_audio_data")
        
        long_text = "This is a very long message. " * 50  # 1500+ chars
        voice_config = Mock()
        use_case = SynthesizeTextUseCase(mock_tts)
        
        audio = await use_case.execute(
            text=long_text,
            voice_config=voice_config
        )
        
        assert audio == b"long_audio_data"
        mock_tts.synthesize.assert_called_once()
