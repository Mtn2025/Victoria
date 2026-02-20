"""
Tool Factory - Creates and registers tool instances.

Hexagonal Architecture: Infrastructure factory for tool dependency injection.
Centralizes tool creation and configuration.
"""
import logging
from collections.abc import Callable
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.ports.tool_port import ToolPort
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.infrastructure.adapters.tools import APIToolAdapter, DatabaseToolAdapter

logger = logging.getLogger(__name__)


class ToolFactoryConfig(Protocol):
    """Protocol for tool factory configuration."""
    
    @property
    def property_api_url(self) -> str:
        """Property API base URL."""
        ...
    
    @property
    def property_api_key(self) -> str | None:
        """Property API key (optional)."""
        ...


def create_tools_registry(
    session_factory: Callable[[], AsyncSession],
    config: ToolFactoryConfig | None = None
) -> dict[str, ToolPort]:
    """
    Create registry of available tools.
    
    Args:
        session_factory: Async SQLAlchemy session factory for database tools
        config: Optional configuration for tool initialization
        
    Returns:
        Dictionary mapping tool names to tool instances
        
    Example:
        >>> from backend.infrastructure.database.session import get_async_session
        >>> tools = create_tools_registry(get_async_session, config)
        >>> print(tools.keys())
        dict_keys(['query_database', 'fetch_property_price'])
    """
    tools: dict[str, ToolPort] = {}
    
    # Database Tool
    try:
        db_tool = DatabaseToolAdapter(session_factory)
        tools[db_tool.name] = db_tool
        logger.info(f"✅ Registered tool: {db_tool.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register database tool: {e}")
    
    # API Tool (Property Prices)
    try:
        if config:
            api_url = getattr(config, "property_api_url", "https://api.example.com")
            api_key = getattr(config, "property_api_key", None)
        else:
            api_url = "https://api.example.com"
            api_key = None
        
        api_tool = APIToolAdapter(
            api_base_url=api_url,
            api_key=api_key,
            tool_name="fetch_property_price"
        )
        tools[api_tool.name] = api_tool
        logger.info(f"✅ Registered tool: {api_tool.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register API tool: {e}")
    
    logger.info(f"📦 Tool registry created with {len(tools)} tools")
    return tools


def create_execute_tool_use_case(
    tools: dict[str, ToolPort]
) -> ExecuteToolUseCase:
    """
    Create ExecuteToolUseCase with injected tools.
    
    Args:
        tools: Dictionary binding tool names to tool instances (Ports)
        
    Returns:
        ExecuteToolUseCase instance ready for use
        
    Example:
        >>> tools = create_tools_registry(session_factory, config)
        >>> execute_tool = create_execute_tool_use_case(tools)
    """
    use_case = ExecuteToolUseCase(tools)
    
    logger.info(
        f"🔧 ExecuteToolUseCase created with {use_case.tool_count} tools"
    )
    
    return use_case
