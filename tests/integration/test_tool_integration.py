"""
Integration tests for Tool System.

Tests the complete flow: Tool Factory → ExecuteToolUseCase → LLMProcessor
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from backend.domain.value_objects.tool import ToolRequest, ToolResponse
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.infrastructure.factories.tool_factory import (
    create_execute_tool_use_case,
    create_tools_registry,
)


@pytest.fixture
def mock_session_factory():
    """Mock SQLAlchemy session factory."""
    def factory():
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        return mock_session
    return factory


@pytest.fixture
def mock_config():
    """Mock configuration for tool factory."""
    config = Mock()
    config.property_api_url = "https://api.test.com"
    config.property_api_key = "test-key-123"
    return config


class TestToolFactory:
    """Test tool factory creation and registration."""
    
    def test_create_tools_registry(self, mock_session_factory, mock_config):
        """Test tools registry creation."""
        tools = create_tools_registry(mock_session_factory, mock_config)
        
        assert len(tools) == 2
        assert "query_database" in tools
        assert "fetch_property_price" in tools
        
    def test_create_execute_tool_use_case(self, mock_session_factory, mock_config):
        """Test ExecuteToolUseCase creation with tools."""
        tools = create_tools_registry(mock_session_factory, mock_config)
        execute_tool = create_execute_tool_use_case(tools)
        
        assert isinstance(execute_tool, ExecuteToolUseCase)
        assert execute_tool.tool_count == 2
        
        definitions = execute_tool.get_tool_definitions()
        assert len(definitions) == 2


class TestToolIntegration:
    """Integration tests for tool execution."""
    
    @pytest.mark.asyncio
    async def test_database_tool_execution(self, mock_session_factory):
        """Test database tool can execute queries."""
        # Manually create registry with just DB tool (config=None)
        tools = create_tools_registry(mock_session_factory)
        execute_tool = create_execute_tool_use_case(tools)
        
        request = ToolRequest(
            tool_name="query_database",
            arguments={"query": "John Smith", "limit": 5},
            trace_id="test-123"
        )
        
        response = await execute_tool.execute(request)
        
        # Debug output
        print(f"DEBUG Response: success={response.success}, type={type(response.success)}")
        print(f"DEBUG Result: {response.result}")
        print(f"DEBUG Error: {response.error_message}")

        # Should return successfully (even if mock data)
        assert isinstance(response, ToolResponse)
        assert response.tool_name == "query_database"
        # Mock returns filtered contacts
        assert response.success
    
    @pytest.mark.asyncio
    async def test_api_tool_execution(self, mock_session_factory, mock_config):
        """Test API tool can execute calls."""
        tools = create_tools_registry(mock_session_factory, mock_config)
        execute_tool = create_execute_tool_use_case(tools)
        
        request = ToolRequest(
            tool_name="fetch_property_price",
            arguments={"address": "123 Main St, New York, NY"},
            trace_id="test-456"
        )
        
        response = await execute_tool.execute(request)
        
        # Should return successfully (mock implementation)
        assert isinstance(response, ToolResponse)
        assert response.tool_name == "fetch_property_price"
        assert response.success is True
        assert "address" in response.result
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self, mock_session_factory):
        """Test error handling for non-existent tool."""
        tools = create_tools_registry(mock_session_factory)
        execute_tool = create_execute_tool_use_case(tools)
        
        request = ToolRequest(
            tool_name="nonexistent_tool",
            arguments={},
            trace_id="test-789"
        )
        
        response = await execute_tool.execute(request)
        
        assert response.success is False
        assert "not found" in response.error_message.lower()


class TestLLMProcessorToolIntegration:
    """Test LLMProcessor integration with tools."""
    
    @pytest.mark.asyncio
    async def test_llm_processor_has_tools(self, mock_session_factory):
        """Test LLMProcessor can access tool definitions."""
        from backend.application.processors.llm_processor import LLMProcessor
        from backend.domain.ports.llm_port import LLMPort
        
        # Create mock LLM port
        mock_llm = Mock(spec=LLMPort)
        
        # Create execute_tool use case
        tools = create_tools_registry(mock_session_factory)
        execute_tool = create_execute_tool_use_case(tools)
        
        # Create processor
        processor = LLMProcessor(
            llm_port=mock_llm,
            config={"llm_model": "test-model"},
            conversation_history=[],
            execute_tool_use_case=execute_tool
        )
        
        # Verify tools are accessible
        assert processor.execute_tool is not None
        # Both DB and API tools are registered now (API uses defaults if config None)
        assert processor.execute_tool.tool_count == 2
        
        # Verify tool definitions can be retrieved
        definitions = processor.execute_tool.get_tool_definitions()
        assert len(definitions) == 2
        
        # Verify OpenAI format conversion
        tool_definitions_dict = [t.to_openai_format() for t in definitions]
        assert all("name" in t for t in tool_definitions_dict)
        assert all("description" in t for t in tool_definitions_dict)
        assert all("parameters" in t for t in tool_definitions_dict)
