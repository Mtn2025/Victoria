
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.conversation_turn import ConversationTurn

from backend.domain.ports.llm_port import LLMRequest, LLMMessage

class TestGroqLLMAdapter:
    
    @pytest.fixture
    def conversation(self):
        c = Conversation()
        c.add_turn(ConversationTurn(role="user", content="Hola"))
        return c

    @pytest.fixture
    def agent(self):
        vc = VoiceConfig(name="test")
        return Agent(name="Bond", system_prompt="You are a spy", voice_config=vc)

    @pytest.mark.asyncio
    async def test_generate_response_success(self, conversation, agent):
        with patch("backend.infrastructure.adapters.llm.groq_adapter.AsyncGroq") as MockClient:
            # Setup Mock
            mock_instance = MockClient.return_value
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = "Hola, soy Bond."
            
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            adapter = GroqLLMAdapter(api_key="fake-key")
            response = await adapter.generate_response(conversation, agent)
            
            assert response == "Hola, soy Bond."
            
            # Verify call args
            mock_instance.chat.completions.create.assert_awaited_once()
            call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
            assert call_kwargs["messages"][0]["role"] == "system"
            assert call_kwargs["messages"][0]["content"] == "You are a spy"
            assert call_kwargs["messages"][1]["role"] == "user"
            assert call_kwargs["messages"][1]["content"] == "Hola"

    @pytest.mark.asyncio
    async def test_stream_response_success(self, conversation, agent):
        with patch("backend.infrastructure.adapters.llm.groq_adapter.AsyncGroq") as MockClient:
             # Setup Mock for Streaming
            mock_instance = MockClient.return_value
            
            # Mock Chunk 1
            chunk1 = MagicMock()
            chunk1.choices = [MagicMock()]
            chunk1.choices[0].delta.content = "Hola"
            
            # Mock Chunk 2
            chunk2 = MagicMock()
            chunk2.choices = [MagicMock()]
            chunk2.choices[0].delta.content = " mundo"
            
            # Async Iterator Mock
            async def async_iter():
                yield chunk1
                yield chunk2
                
            mock_instance.chat.completions.create = AsyncMock(return_value=async_iter())
            
            adapter = GroqLLMAdapter(api_key="fake-key")
            
            # Construct LLMRequest
            request = LLMRequest(
                messages=[LLMMessage(role="user", content="Hola")],
                model="llama3-70b-8192",
                system_prompt="You are a spy"
            )
            
            chunks = []
            async for chunk in adapter.generate_stream(request):
                chunks.append(chunk.text)
                
            assert "".join(chunks) == "Hola mundo"
