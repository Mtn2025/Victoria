import pytest
import asyncio
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.domain.value_objects.tool import ToolRequest, ToolDefinition

# Mock tools
async def async_tool(val):
    return f"Async: {val}"

def sync_tool(val):
    return f"Sync: {val}"

class ToolObj:
    definition = ToolDefinition(name="obj_tool", description="desc", parameters={})
    async def execute(self, request):
        return f"Obj: {request.arguments['val']}"

class TestExecuteTool:
    @pytest.fixture
    def use_case(self):
        tools = {
            "async_tool": async_tool,
            "sync_tool": sync_tool, 
            "obj_tool": ToolObj()
        }
        return ExecuteToolUseCase(tools)

    @pytest.mark.asyncio
    async def test_execute_async_tool(self, use_case):
        req = ToolRequest(tool_name="async_tool", arguments={"val": "test"})
        res = await use_case.execute(req)
        assert res.success is True
        assert res.result == "Async: test"

    @pytest.mark.asyncio
    async def test_execute_sync_tool(self, use_case):
        req = ToolRequest(tool_name="sync_tool", arguments={"val": "test"})
        res = await use_case.execute(req)
        assert res.success is True
        assert res.result == "Sync: test"

    @pytest.mark.asyncio
    async def test_execute_obj_tool(self, use_case):
        req = ToolRequest(tool_name="obj_tool", arguments={"val": "test"})
        res = await use_case.execute(req)
        assert res.success is True
        assert res.result == "Obj: test"

    @pytest.mark.asyncio
    async def test_tool_not_found(self, use_case):
        req = ToolRequest(tool_name="unknown", arguments={})
        res = await use_case.execute(req)
        assert res.success is False
        assert "not found" in res.error_message

    @pytest.mark.asyncio
    async def test_tool_timeout(self, use_case):
        async def slow_tool():
            await asyncio.sleep(0.2)
            return "too slow"
            
        uc = ExecuteToolUseCase({"slow": slow_tool})
        req = ToolRequest(tool_name="slow", arguments={}, timeout_seconds=0.1)
        res = await uc.execute(req)
        assert res.success is False
        assert "timed out" in res.error_message
