"""
Execute Tool Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
import logging
import time
import asyncio
import traceback
from typing import Callable, Dict, Any, List

from backend.domain.value_objects.tool import ToolRequest, ToolResponse, ToolDefinition

logger = logging.getLogger(__name__)

class ExecuteToolUseCase:
    """
    Executes a requested tool function.
    """
    def __init__(self, tools: Dict[str, Any]):
        """
        Args:
            tools: Dictionary mapping tool names to callables or objects with 'execute' method.
        """
        self.tools = tools
        
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Return list of ToolDefinitions for the available tools."""
        defs = []
        for name, tool in self.tools.items():
            if hasattr(tool, 'get_definition'):
                defs.append(tool.get_definition())
            elif hasattr(tool, 'definition'):
                defs.append(tool.definition)
            elif isinstance(tool, ToolDefinition):
                defs.append(tool)
        return defs

    @property
    def tool_count(self) -> int:
        return len(self.tools)

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """
        Execute the tool with the given request.
        """
        start_time = time.time()
        tool_name = request.tool_name
        
        if tool_name not in self.tools:
            return ToolResponse(
                tool_name=tool_name,
                result=None,
                success=False,
                error_message=f"Tool '{tool_name}' not found",
                trace_id=request.trace_id
            )
            
        tool = self.tools[tool_name]
        
        try:
            # Execute with timeout
            # ToolPort interface requires 'execute(request: ToolRequest)'
            if hasattr(tool, 'execute'):
                 # Check if async
                if asyncio.iscoroutinefunction(tool.execute):
                    result_response = await asyncio.wait_for(tool.execute(request), timeout=request.timeout_seconds)
                else:
                    result_response = tool.execute(request)
                
                # If tool returns ToolResponse directly (as per ToolPort)
                if isinstance(result_response, ToolResponse):
                    return result_response
                
                # If tool returns raw result (legacy or simple callable), wrap it
                result = result_response
            elif callable(tool):
                # Simple callable support (legacy)
                if asyncio.iscoroutinefunction(tool):
                     result = await asyncio.wait_for(tool(**request.arguments), timeout=request.timeout_seconds)
                else:
                     result = tool(**request.arguments)
            else:
                 raise ValueError(f"Tool {tool_name} is not executable")

            # Wrap raw result if needed
            execution_time = (time.time() - start_time) * 1000
            return ToolResponse(
                tool_name=tool_name,
                result=result,
                success=True,
                execution_time_ms=execution_time,
                trace_id=request.trace_id
            )



        except asyncio.TimeoutError:
            logger.error(f"Tool {tool_name} timed out after {request.timeout_seconds}s")
            return ToolResponse(
                tool_name=tool_name,
                result=None,
                success=False,
                error_message="Execution timed out",
                trace_id=request.trace_id
            )
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            logger.debug(traceback.format_exc())
            return ToolResponse(
                tool_name=tool_name,
                result=None,
                success=False,
                error_message=str(e),
                trace_id=request.trace_id
            )
