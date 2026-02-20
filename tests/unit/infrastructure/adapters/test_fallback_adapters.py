"""
Unit tests for Fallback Adapters.

Tests failover logic for LLM, TTS, and STT.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from backend.infrastructure.adapters.llm.llm_fallback import LLMFallbackAdapter
from backend.infrastructure.adapters.tts.tts_fallback import TTSFallbackAdapter
from backend.infrastructure.adapters.stt.stt_fallback import STTFallbackAdapter

from backend.domain.ports.llm_port import LLMException
from backend.domain.ports.tts_port import TTSException
from backend.domain.ports.stt_port import STTException


class TestLLMFallbackAdapter:
    """Test LLM fallback adapter failover."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Test fallback to secondary when primary fails."""
        # Mock adapters
        primary = AsyncMock()
        
        # Define explicit async generator that raises exception
        async def fail_stream(*args, **kwargs):
            raise LLMException("Primary failed", retryable=True)
            yield "unreachable"
            
        primary.generate_stream = fail_stream
        
        secondary = AsyncMock()
        async def mock_stream(*args, **kwargs):
            yield Mock(has_text=True, text="fallback response")
        secondary.generate_stream = mock_stream
        
        # Create fallback adapter
        adapter = LLMFallbackAdapter(primary, [secondary])
        
        # Generate should use secondary
        chunks = []
        async for chunk in adapter.generate_stream(Mock(), Mock()):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert chunks[0].text == "fallback response"

    @pytest.mark.asyncio
    async def test_generated_response_fallback(self):
         # Validating generated_response I added
        primary = AsyncMock()
        primary.generate_response = AsyncMock(side_effect=LLMException("Fail", retryable=True))
        
        secondary = AsyncMock()
        secondary.generate_response = AsyncMock(return_value="fallback")
        
        adapter = LLMFallbackAdapter(primary, [secondary])
        
        res = await adapter.generate_response(Mock(), Mock())
        assert res == "fallback"


class TestTTSFallbackAdapter:
    """Test TTS fallback adapter."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_synthesis_failure(self):
        """Test fallback when primary TTS fails."""
        primary = AsyncMock()
        primary.synthesize = AsyncMock(side_effect=TTSException("TTS failed", retryable=True))
        
        secondary = AsyncMock()
        secondary.synthesize = AsyncMock(return_value=b"fallback_audio")
        
        adapter = TTSFallbackAdapter(primary, secondary)
        
        # optimize: synthesize takes (text, voice, format)
        audio = await adapter.synthesize("Hello", Mock(), Mock())
        
        assert audio == b"fallback_audio"
        secondary.synthesize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_primary_success(self):
        """Test primary TTS used when working."""
        primary = AsyncMock()
        primary.synthesize = AsyncMock(return_value=b"primary_audio")
        
        secondary = AsyncMock()
        
        adapter = TTSFallbackAdapter(primary, secondary)
        
        audio = await adapter.synthesize("Hello", Mock(), Mock())
        
        assert audio == b"primary_audio"
        primary.synthesize.assert_called_once()
        secondary.synthesize.assert_not_called()


class TestSTTFallbackAdapter:
    """Test STT fallback adapter."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_transcription_failure(self):
        """Test fallback when primary STT fails."""
        primary = AsyncMock()
        primary.transcribe = AsyncMock(side_effect=STTException("STT failed", retryable=True))
        
        secondary = AsyncMock()
        secondary.transcribe = AsyncMock(return_value="fallback transcription")
        
        adapter = STTFallbackAdapter(primary, secondary)
        
        # Updated signature: audio, format, language
        text = await adapter.transcribe(b"audio_data", Mock(), "es-MX")
        
        assert text == "fallback transcription"
        secondary.transcribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_both_adapters_fail(self):
        """Test graceful failure when both adapters fail."""
        primary = AsyncMock()
        primary.transcribe = AsyncMock(side_effect=STTException("Primary failed", retryable=True))
        
        secondary = AsyncMock()
        secondary.transcribe = AsyncMock(side_effect=STTException("Secondary failed", retryable=True))
        
        adapter = STTFallbackAdapter(primary, secondary)
        
        # Expect exception as per implementation logic
        with pytest.raises(STTException):
             await adapter.transcribe(b"audio_data", Mock(), "es-MX")
