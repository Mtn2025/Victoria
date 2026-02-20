import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.infrastructure.factories.tool_factory import (
    create_tools_registry,
    create_execute_tool_use_case,
    ToolFactoryConfig
)
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.infrastructure.adapters.tools import DatabaseToolAdapter, APIToolAdapter

class MockConfig:
    @property
    def property_api_url(self) -> str:
        return "https://mock-api.com"
    
    @property
    def property_api_key(self) -> str | None:
        return "mock-key"

@pytest.fixture
def mock_session_factory():
    return Mock()

def test_create_tools_registry_success(mock_session_factory):
    """Test creating tools registry with valid config."""
    config = MockConfig()
    
    tools = create_tools_registry(mock_session_factory, config)
    
    assert "query_database" in tools
    assert isinstance(tools["query_database"], DatabaseToolAdapter)
    
    assert "fetch_property_price" in tools
    assert isinstance(tools["fetch_property_price"], APIToolAdapter)

def test_create_tools_registry_no_config(mock_session_factory):
    """Test creating tools registry without config (defaults)."""
    tools = create_tools_registry(mock_session_factory, None)
    
    # DB tool should still exist
    assert "query_database" in tools
    
    # API tool might exist with defaults if APIToolAdapter allows None key (it does based on code)
    assert "fetch_property_price" in tools
    # Verify default URL if possible, or just presence

def test_create_execute_tool_use_case(mock_session_factory):
    """Test creating the Use Case."""
    config = MockConfig()
    tools = create_tools_registry(mock_session_factory, config)
    use_case = create_execute_tool_use_case(tools)
    
    assert isinstance(use_case, ExecuteToolUseCase)
    assert use_case.tool_count >= 2

@patch("backend.infrastructure.factories.tool_factory.DatabaseToolAdapter")
def test_create_tools_handle_db_error(MockDBAdapter, mock_session_factory):
    """Test registry creation handles DB tool failure gracefully."""
    MockDBAdapter.side_effect = Exception("DB Init Error")
    
    tools = create_tools_registry(mock_session_factory, None)
    
    assert "query_database" not in tools
    # API tool should still be there
    assert "fetch_property_price" in tools

@patch("backend.infrastructure.factories.tool_factory.APIToolAdapter")
def test_create_tools_handle_api_error(MockAPIAdapter, mock_session_factory):
    """Test registry creation handles API tool failure gracefully."""
    MockAPIAdapter.side_effect = Exception("API Init Error")
    
    tools = create_tools_registry(mock_session_factory, None)
    
    assert "fetch_property_price" not in tools
    assert "query_database" in tools
