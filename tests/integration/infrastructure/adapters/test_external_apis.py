import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.conversation_turn import ConversationTurn
from backend.domain.value_objects.voice_config import VoiceConfig

@pytest.fixture
def test_conversation():
    conv = Conversation()
    conv.add_turn(ConversationTurn(role="user", content="Hello"))
    return conv

@pytest.fixture
def test_agent():
    return Agent(
        name="TestAgent",
        system_prompt="You are a test bot.",
        voice_config=VoiceConfig(name="en-US-Neural")
    )

@pytest.mark.asyncio
async def test_groq_adapter_generate_response_success(test_conversation, test_agent):
    # Arrange
    adapter = GroqLLMAdapter(api_key="fake-key")
    
    # Mock the internal client calls
    adapter.client = AsyncMock()
    
    # helper to build the deep mock for choices[0].message.content
    mock_completion = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Mocked Response"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    
    adapter.client.chat.completions.create.return_value = mock_completion
    
    # Act
    response = await adapter.generate_response(test_conversation, test_agent)
    
    # Assert
    assert response == "Mocked Response"
    adapter.client.chat.completions.create.assert_awaited_once()
    
    # Verify args
    call_args = adapter.client.chat.completions.create.await_args
    assert call_args.kwargs["model"] == "llama3-70b-8192" # Default
    assert len(call_args.kwargs["messages"]) == 2 # System + User

@pytest.mark.asyncio
async def test_groq_adapter_api_failure(test_conversation, test_agent):
    # Arrange
    adapter = GroqLLMAdapter(api_key="fake-key")
    adapter.client = AsyncMock()
    adapter.client.chat.completions.create.side_effect = Exception("API Error")
    
    # Act & Assert
    with pytest.raises(Exception, match="API Error"):
        await adapter.generate_response(test_conversation, test_agent)
