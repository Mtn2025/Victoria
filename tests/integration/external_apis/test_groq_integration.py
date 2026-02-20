import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from backend.infrastructure.adapters.llm.groq_adapter import GroqLLMAdapter
from backend.domain.ports.llm_port import LLMRequest, LLMMessage

@pytest.mark.asyncio
class TestGroqIntegration:

    async def test_groq_initialization_from_env(self):
        """Verify Adapter initializes with correct API Key from env."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key-integration"}):
            with patch("backend.infrastructure.adapters.llm.groq_adapter.AsyncGroq") as MockGroq:
                # Mock return value of AsyncGroq constructor
                mock_client_instance = AsyncMock()
                MockGroq.return_value = mock_client_instance
                
                adapter = GroqLLMAdapter(api_key="test-key-integration")
                
                assert MockGroq.called
                # Check call args. Adapter calls AsyncGroq(api_key=...)
                args, kwargs = MockGroq.call_args
                assert kwargs.get('api_key') == "test-key-integration"

    async def test_groq_streaming_integration_flow(self):
        """
        Simulate a full streaming flow with mocked client response structure.
        """
        # Mock the chunk object from Groq (nested structure)
        # chunk.choices[0].delta.content
        mock_chunk_1 = MagicMock()
        mock_chunk_1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        
        mock_chunk_2 = MagicMock()
        mock_chunk_2.choices = [MagicMock(delta=MagicMock(content=" World"))]
        
        # Async Iterator for stream
        async def mock_stream_gen(**kwargs):
            yield mock_chunk_1
            yield mock_chunk_2

        # Mock Client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = mock_stream_gen
        
        # Patch AsyncGroq to return our mock_client
        with patch("backend.infrastructure.adapters.llm.groq_adapter.AsyncGroq", return_value=mock_client):
            adapter = GroqLLMAdapter(api_key="mock-key")
            
            request = LLMRequest(
                messages=[LLMMessage(role="user", content="Hi")],
                model="llama-3.3-70b",
                temperature=0.5
            )
            
            chunks = []
            async for chunk in adapter.generate_stream(request):
                chunks.append(chunk)

            # Verify interaction
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            
            assert call_kwargs['model'] == "llama-3.3-70b"
            assert call_kwargs['temperature'] == 0.5
            assert call_kwargs['stream'] is True
            
            # Verify Output
            # Note: The adapter implementation viewed in Step 2502 yields LLMResponseChunk
            # Line 75: yield LLMResponseChunk(text=content, is_final=False)
            # Line 78: yield LLMResponseChunk(text="", is_final=True)
            
            assert len(chunks) == 3 # Hello, World, Empty
            assert chunks[0].text == "Hello"
            assert chunks[1].text == " World"
            assert chunks[2].is_final is True
