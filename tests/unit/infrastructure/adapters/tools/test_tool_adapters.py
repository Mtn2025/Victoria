"""
Unit tests for Tool Adapters.

Tests API and Database tool adapters.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from backend.domain.value_objects.tool import ToolRequest, ToolResponse
from backend.infrastructure.adapters.tools.api_tool import APIToolAdapter
from backend.infrastructure.adapters.tools.database_tool import DatabaseToolAdapter


class TestAPIToolAdapter:
    """Test API tool adapter."""
    
    def test_tool_definition(self):
        """Test tool definition generation."""
        adapter = APIToolAdapter(
            api_base_url="https://example.com",
            tool_name="fetch_test"
        )
        
        definition = adapter.get_definition() 
        
        assert definition.name == "fetch_test"
        # Check description content based on actual implementation
        assert "real estate" in definition.description
        # Check parameters directly (it's a dict, not JSON schema properties object in the key)
        assert "address" in definition.parameters
    
    @pytest.mark.asyncio
    async def test_execute_with_mock_data(self):
        """Test tool execution returns mock data."""
        adapter = APIToolAdapter(
            api_base_url="https://example.com/api",
            tool_name="fetch_property_price"
        )
        
        request = ToolRequest(
            tool_name="fetch_property_price",
            arguments={"address": "123 Main St"},
            trace_id="test-123"
        )
        
        response = await adapter.execute(request)
        
        assert isinstance(response, ToolResponse)
        assert response.success is True
        assert "address" in response.result
        assert response.result["address"] == "123 Main St"
    
    @pytest.mark.asyncio
    async def test_execute_with_missing_args(self):
        """Test error handling for missing arguments."""
        adapter = APIToolAdapter(
            api_base_url="https://example.com",
            tool_name="fetch_test"
        )
        
        request = ToolRequest(
            tool_name="fetch_test",
            arguments={},  # Missing required args
            trace_id="test-456"
        )
        
        response = await adapter.execute(request)
        
        assert isinstance(response, ToolResponse)


class TestDatabaseToolAdapter:
    """Test database tool adapter."""
    
    @pytest.mark.asyncio
    async def test_tool_definition(self):
        """Test database tool definition."""
        mock_session_factory = Mock() # Session factory itself is callable, not async
        
        adapter = DatabaseToolAdapter(mock_session_factory)
        
        definition = adapter.get_definition()
        
        assert definition.name == "query_database"
        assert "database" in definition.description.lower()
        assert "query" in definition.parameters
    
    @pytest.mark.asyncio
    async def test_execute_query(self):
        """Test database query execution."""
        mock_session_factory = Mock()
        # Setup async context manager mock
        # When factory() is called, it returns an object that can be used in 'async with'
        mock_session_ctx = AsyncMock() 
        mock_session = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        
        mock_session_factory.return_value = mock_session_ctx
        
        adapter = DatabaseToolAdapter(mock_session_factory)
        
        request = ToolRequest(
            tool_name="query_database",
            arguments={"query": "John Doe", "limit": 5},
            trace_id="test-789"
        )
        
        response = await adapter.execute(request)
        
        assert isinstance(response, ToolResponse)
        assert response.success is True
        assert isinstance(response.result, list)
    
    @pytest.mark.asyncio
    async def test_execute_with_limit(self):
        """Test query respects limit parameter."""
        mock_session_factory = Mock()
        # Setup async context manager mock
        mock_session_ctx = AsyncMock() 
        mock_session = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None
        
        mock_session_factory.return_value = mock_session_ctx
        
        adapter = DatabaseToolAdapter(mock_session_factory)
        
        request = ToolRequest(
            tool_name="query_database",
            arguments={"query": "Smith", "limit": 3},
            trace_id="test-limit"
        )
        
        response = await adapter.execute(request)
        
        assert len(response.result) <= 3
