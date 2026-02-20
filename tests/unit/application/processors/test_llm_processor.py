
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from backend.application.processors.llm_processor import LLMProcessor
from backend.application.processors.frames import TextFrame
from backend.application.processors.frame_processor import FrameDirection
from backend.domain.ports.llm_port import LLMPort, LLMRequest, LLMResponseChunk
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.domain.value_objects.tool import ToolResponse

class MockConfig:
    system_prompt = "SysPrompt"
    llm_model = "gpt-mock"

@pytest.fixture
def mock_llm_port():
    port = MagicMock(spec=LLMPort)
    async def stream_gen(request):
        yield LLMResponseChunk(text="Hello", is_final=False)
        yield LLMResponseChunk(text=" World.", is_final=True)
    port.generate_stream.side_effect = stream_gen
    return port

@pytest.mark.asyncio
async def test_llm_process_text(mock_llm_port):
    history = []
    processor = LLMProcessor(mock_llm_port, MockConfig(), history)
    
    downstream = AsyncMock()
    processor.link(downstream)
    
    frame = TextFrame(text="Hi AI", role="user", is_final=True)
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    
    # Wait for background task
    await asyncio.sleep(0.1)
    
    # Verify history updated
    assert len(history) >= 1
    assert history[0]["content"] == "Hi AI"
    
    # Verify downstream received "Hello World." (likely split or flushed)
    # Our simple logic flushes "Hello World." because of period
    frames = [call.args[0] for call in downstream.process_frame.call_args_list if isinstance(call.args[0], TextFrame)]
    # 0: User Input (passed through)
    # 1: Assistant Response
    
    assistant_frames = [f for f in frames if f.role == "assistant"]
    assert len(assistant_frames) > 0
    assert "Hello World." in "".join([f.text for f in assistant_frames])

@pytest.mark.asyncio
async def test_llm_function_call(mock_llm_port):
    # Setup Tool Use Case
    mock_execute = MagicMock(spec=ExecuteToolUseCase)
    mock_execute.get_tool_definitions.return_value = []
    mock_execute.execute = AsyncMock(return_value=ToolResponse("test_tool", "ResultXYZ", True))
    
    # Setup Protocol to emit Function Call then Text
    async def stream_gen(request):
        if not request.messages or request.messages[-1].role != "function":
             # First call: Emit function call
             from backend.domain.ports.llm_port import LLMFunctionCall
             call = LLMFunctionCall(name="test_tool", arguments={"arg": 1})
             yield LLMResponseChunk(function_call=call)
        else:
             # Second call (after tool result): Emit text
             yield LLMResponseChunk(text="Tool executed.", is_final=True)

    mock_llm_port.generate_stream.side_effect = stream_gen
    
    history = []
    processor = LLMProcessor(mock_llm_port, MockConfig(), history, execute_tool_use_case=mock_execute)
    downstream = AsyncMock()
    processor.link(downstream)
    
    frame = TextFrame(text="Run tool", role="user", is_final=True)
    await processor.process_frame(frame, FrameDirection.DOWNSTREAM)
    await asyncio.sleep(0.1)
    
    # Verify Tool Execution
    mock_execute.execute.assert_called_once()
    
    # Verify History contains Tool Call and Result (and Assistant response)
    # 1. User: Run tool
    # 2. Assistant: [TOOL_CALL: test_tool]
    # 3. Assistant: Tool executed.
    
    assert history[-2]["content"] == "[TOOL_CALL: test_tool]"
    assert history[-1]["content"] == "Tool executed."
