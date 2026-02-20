"""
Unit tests for ExtractionService.
"""
import pytest
import json
from unittest.mock import AsyncMock, Mock

from backend.application.services.extraction_service import ExtractionService, ExtractionError
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.conversation_turn import ConversationTurn
from backend.domain.ports.llm_port import LLMPort, LLMResponseChunk
from backend.domain.value_objects.extraction_schema import ExtractionSchema, ExtractionResult


@pytest.fixture
def mock_llm_port():
    """Mock LLM port."""
    port = AsyncMock()
    # Ensure generate_stream is a Mock (not AsyncMock) so it can return an async generator directly
    # However, if we set it here, all tests must use it as Mock.
    # But some tests might not set side_effect.
    # Let's handle it in individual tests or here.
    # If we set it to Mock(), accessing it returns a Mock.
    # port.generate_stream = Mock() 
    return port


@pytest.fixture
def sample_conversation():
    """Sample conversation for testing."""
    conversation = Conversation()
    conversation.add_turn(ConversationTurn(
        role="user",
        content="Hola, quiero agendar una cita"
    ))
    conversation.add_turn(ConversationTurn(
        role="assistant",
        content="Claro, ¿para qué fecha?"
    ))
    conversation.add_turn(ConversationTurn(
        role="user",
        content="Para el 20 de febrero. Mi nombre es Juan Pérez"
    ))
    return conversation


class TestExtractionService:
    """Test suite for ExtractionService."""
    
    def test_initialization(self, mock_llm_port):
        """Test service initialization."""
        service = ExtractionService(llm_port=mock_llm_port)
        
        assert service.llm_port == mock_llm_port
        assert isinstance(service.schema, ExtractionSchema)
    
    def test_custom_schema(self, mock_llm_port):
        """Test service with custom schema."""
        custom_schema = ExtractionSchema(fields={"custom": "field"})
        service = ExtractionService(llm_port=mock_llm_port, schema=custom_schema)
        
        assert service.schema == custom_schema
    
    @pytest.mark.asyncio
    async def test_extract_from_conversation_success(self, mock_llm_port, sample_conversation):
        """Test successful extraction."""
        # Arrange
        extraction_data = {
            "summary": "Cliente solicita cita para 20 de febrero",
            "intent": "agendar_cita",
            "sentiment": "positive",
            "extracted_entities": {
                "name": "Juan Pérez",
                "appointment_date": "2024-02-20"
            },
            "next_action": "follow_up"
        }
        
        async def mock_stream(request):
            yield LLMResponseChunk(text=json.dumps(extraction_data))
            
        mock_llm_port.generate_stream = Mock(side_effect=mock_stream)
        
        service = ExtractionService(llm_port=mock_llm_port)
        
        # Act
        result = await service.extract_from_conversation(sample_conversation, call_id="test-123")
        
        # Assert
        assert isinstance(result, ExtractionResult)
        assert result.summary == "Cliente solicita cita para 20 de febrero"
        assert result.intent == "agendar_cita"
        assert result.sentiment == "positive"
        assert result.entities["name"] == "Juan Pérez"
        assert result.next_action == "follow_up"
        
        # Verify LLM was called
        mock_llm_port.generate_stream.assert_called_once()
        call_args = mock_llm_port.generate_stream.call_args[0][0]
        assert len(call_args.messages) == 2
        assert call_args.messages[0].role == "system"
        assert call_args.messages[1].role == "user"
        assert "DIÁLOGO" in call_args.messages[1].content
    
    @pytest.mark.asyncio
    async def test_empty_conversation_raises_error(self, mock_llm_port):
        """Test that empty conversation raises ValueError."""
        service = ExtractionService(llm_port=mock_llm_port)
        empty_conversation = Conversation()
        
        with pytest.raises(ValueError, match="empty conversation"):
            await service.extract_from_conversation(empty_conversation)
    
    @pytest.mark.asyncio
    async def test_invalid_json_raises_extraction_error(self, mock_llm_port, sample_conversation):
        """Test that invalid JSON response raises ExtractionError."""
        # Arrange
        async def mock_stream(request):
            yield LLMResponseChunk(text="This is not JSON")
        
        mock_llm_port.generate_stream = Mock(side_effect=mock_stream)
        
        service = ExtractionService(llm_port=mock_llm_port)
        
        # Act & Assert
        with pytest.raises(ExtractionError, match="Failed to parse extraction JSON"):
            await service.extract_from_conversation(sample_conversation)
    
    @pytest.mark.asyncio
    async def test_llm_error_raises_extraction_error(self, mock_llm_port, sample_conversation):
        """Test that LLM errors are wrapped in ExtractionError."""
        # Arrange
        mock_llm_port.generate_stream = Mock(side_effect=Exception("LLM API error"))
        
        service = ExtractionService(llm_port=mock_llm_port)
        
        # Act & Assert
        with pytest.raises(ExtractionError, match="Extraction failed"):
            await service.extract_from_conversation(sample_conversation)
    
    @pytest.mark.asyncio
    async def test_invalid_intent_defaults_to_irrelevante(self, mock_llm_port, sample_conversation):
        """Test that invalid intent values are normalized."""
        # Arrange
        extraction_data = {
            "summary": "Test",
            "intent": "invalid_intent",  # Invalid
            "sentiment": "positive",
            "extracted_entities": {},
            "next_action": "do_nothing"
        }
        
        async def mock_stream(request):
            yield LLMResponseChunk(text=json.dumps(extraction_data))
            
        mock_llm_port.generate_stream = Mock(side_effect=mock_stream)
        
        service = ExtractionService(llm_port=mock_llm_port)
        
        # Act
        result = await service.extract_from_conversation(sample_conversation)
        
        # Assert
        assert result.intent == "irrelevante"  # Normalized
    
    @pytest.mark.asyncio
    async def test_conversation_formatting(self, mock_llm_port):
        """Test conversation formatting for LLM."""
        # Arrange
        conversation = Conversation()
        conversation.add_turn(ConversationTurn(role="user", content="Hola"))
        conversation.add_turn(ConversationTurn(role="assistant", content="Bienvenido"))
        
        async def mock_stream(request):
            yield LLMResponseChunk(text=json.dumps({
                "summary": "Test",
                "intent": "consulta",
                "sentiment": "neutral",
                "extracted_entities": {},
                "next_action": "do_nothing"
            }))
            
        mock_llm_port.generate_stream = Mock(side_effect=mock_stream)
        
        service = ExtractionService(llm_port=mock_llm_port)
        
        # Act
        await service.extract_from_conversation(conversation)
        
        # Assert
        call_args = mock_llm_port.generate_stream.call_args[0][0]
        user_message = call_args.messages[1].content
        
        assert "USUARIO: Hola" in user_message
        assert "ASISTENTE: Bienvenido" in user_message
