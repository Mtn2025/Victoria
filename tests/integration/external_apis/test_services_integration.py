"""
Integration Tests for External Services using High Fidelity Mocks.
Verified: Groq, Azure TTS, Redis.
Forbidden: Real Network Calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.infrastructure.adapters.cache.redis_adapter import RedisCacheAdapter
from backend.domain.value_objects.audio_format import AudioFormat

@pytest.fixture
def mock_groq_client():
    with patch("backend.infrastructure.adapters.llm.groq_adapter.AsyncGroq") as MockClient:
        instance = MockClient.return_value
        
        # Mock Completion Response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Mocked Response"))]
        
        # Mock create method
        instance.chat.completions.create = AsyncMock(return_value=mock_completion)
        yield instance

@pytest.mark.asyncio
async def test_groq_adapter_flow(mock_groq_client):
    """Verify Groq Adapter handles client interaction correctly."""
    adapter = GroqLLMAdapter(api_key="fake-key")
    
    agent = Agent(name="Test", system_prompt="Sys", voice_config=VoiceConfig(name="default"))
    conversation = Conversation()
    
    response = await adapter.generate_response(conversation, agent)
    
    assert response == "Mocked Response"
    mock_groq_client.chat.completions.create.assert_called_once()
    
    # Verify args
    call_kwargs = mock_groq_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["stream"] is False
    assert len(call_kwargs["messages"]) > 0

@pytest.fixture
def mock_speech_sdk():
    with patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk") as mock_sdk:
        # Mock Result
        mock_result = MagicMock()
        mock_result.reason = mock_sdk.ResultReason.SynthesizingAudioCompleted
        mock_result.audio_data = b"RIFF_FAKE_AUDIO"
        
        # Mock Synthesizer
        mock_synthesizer_instance = mock_sdk.SpeechSynthesizer.return_value
        
        # Mock speak_ssml_async().get()
        # speak_ssml_async returns a future-like object with .get()
        mock_future = MagicMock()
        mock_future.get.return_value = mock_result
        mock_synthesizer_instance.speak_ssml_async.return_value = mock_future
        
        yield mock_sdk

@pytest.mark.asyncio
async def test_azure_tts_adapter_flow(mock_speech_sdk):
    """Verify Azure TTS Adapter flow with blocked network."""
    adapter = AzureTTSAdapter()
    
    voice = VoiceConfig(name="en-US-JennyNeural")
    format = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
    
    audio = await adapter.synthesize("Hello", voice, format)
    
    assert audio == b"RIFF_FAKE_AUDIO"
    mock_speech_sdk.SpeechSynthesizer.assert_called()


@pytest.fixture
def mock_redis_client():
    with patch("backend.infrastructure.cache.get_redis_client") as mock_get:
        client_instance = AsyncMock()
        mock_get.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
async def test_redis_adapter_flow(mock_redis_client):
    """Verify Redis Adapter interaction."""
    adapter = RedisCacheAdapter()
    
    # Test Set
    await adapter.set("key", "value", ttl=60)
    mock_redis_client.set.assert_awaited_with("key", "value", ttl=60)
    
    # Test Get
    mock_redis_client.get.return_value = "value"
    val = await adapter.get("key")
    assert val == "value"
    mock_redis_client.get.assert_awaited_with("key")
