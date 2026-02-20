import pytest
import time
from backend.domain.value_objects.tool import ToolDefinition, ToolRequest, ToolResponse

class TestToolValueObjects:
    def test_tool_definition_openai_format(self):
        """Should correct format to OpenAI schema."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test tool",
            parameters={"type": "string"},
            required=["param1"]
        )
        schema = tool.to_openai_format()
        assert schema["name"] == "test_tool"
        assert schema["parameters"]["required"] == ["param1"]

    def test_tool_request_creation(self):
        """Should correct create ToolRequest."""
        req = ToolRequest(
            tool_name="test_tool",
            arguments={"arg1": "value"},
            trace_id="trace-123"
        )
        assert req.tool_name == "test_tool"
        assert req.timeout_seconds == 10.0 # Default

    def test_tool_response_creation(self):
        """Should correct create ToolResponse."""
        res = ToolResponse(
            tool_name="test_tool",
            result="Success",
            success=True,
            execution_time_ms=100.0,
            trace_id="trace-123"
        )
        assert res.success is True
        assert res.result == "Success"
