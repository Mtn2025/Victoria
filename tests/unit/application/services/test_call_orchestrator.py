
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.application.services.call_orchestrator import CallOrchestrator
from backend.domain.entities.call import Call
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig

@pytest.fixture
def mock_use_cases():
    return {
        "start_call": AsyncMock(),
        "process_audio": AsyncMock(),
        "generate_response": MagicMock(), # Returns async generator
        "end_call": AsyncMock()
    }

@pytest.mark.asyncio
async def test_start_session(mock_use_cases):
    # Arrange
    orch = CallOrchestrator(
        mock_use_cases["start_call"],
        mock_use_cases["process_audio"],
        mock_use_cases["generate_response"],
        mock_use_cases["end_call"]
    )
    
    mock_call = Call(
        id=CallId("test-stream"),
        agent=Agent(
            name="Bond", 
            system_prompt="You are James Bond", 
            voice_config=VoiceConfig(
                name="en-US-JennyNeural", 
                provider="azure", 
                style="friendly"
            ),
            first_message="Hello"
        ),
        conversation=Conversation()
    )
    mock_use_cases["start_call"].execute.return_value = mock_call
    
    # Act
    await orch.start_session("agent-1", "test-stream")
    
    # Assert
    mock_use_cases["start_call"].execute.assert_called_once_with(
        agent_id="agent-1",
        call_id_value="test-stream",
        from_number=None,
        to_number=None
    )
    assert orch.current_call == mock_call

@pytest.mark.asyncio
async def test_process_audio_flow(mock_use_cases):
    # Arrange
    orch = CallOrchestrator(
        mock_use_cases["start_call"],
        mock_use_cases["process_audio"],
        mock_use_cases["generate_response"],
        mock_use_cases["end_call"]
    )
    
    # Initialize session
    mock_call = Call(
        id=CallId("test-stream"),
        agent=Agent(
            name="Bond", 
            system_prompt="You are James Bond", 
            voice_config=VoiceConfig(
                name="en-US-JennyNeural", 
                provider="azure", 
                style="friendly"
            ),
            first_message="Hello"
        ),
        conversation=Conversation()
    )
    orch.current_call = mock_call
    
    # Mock Process Audio -> "Hello"
    mock_use_cases["process_audio"].execute.return_value = "Hello"
    
    # Mock Generate Response -> [b"chunk1", b"chunk2"]
    async def response_gen(text, call):
        yield b"chunk1"
        yield b"chunk2"
    
    mock_use_cases["generate_response"].execute.side_effect = response_gen
    
    # Act
    chunks = []
    async for chunk in orch.process_audio_input(b"audio_bytes"):
        chunks.append(chunk)
        
    # Assert
    mock_use_cases["process_audio"].execute.assert_called_once_with(b"audio_bytes", mock_call)
    mock_use_cases["generate_response"].execute.assert_called_once_with("Hello", mock_call)
    assert chunks == [b"chunk1", b"chunk2"]

@pytest.mark.asyncio
async def test_end_session(mock_use_cases):
    # Arrange
    orch = CallOrchestrator(
        mock_use_cases["start_call"],
        mock_use_cases["process_audio"],
        mock_use_cases["generate_response"],
        mock_use_cases["end_call"]
    )
    mock_call = Call(
        id=CallId("test"), 
        agent=Agent(
            name="A", 
            system_prompt="Sys", 
            voice_config=VoiceConfig(name="v", provider="azure")
        ), 
        conversation=Conversation()
    )
    orch.current_call = mock_call
    
    # Act
    await orch.end_session("user_hangup")
    
    # Assert
    mock_use_cases["end_call"].execute.assert_called_once_with(mock_call, "user_hangup")
    assert orch.current_call is None
