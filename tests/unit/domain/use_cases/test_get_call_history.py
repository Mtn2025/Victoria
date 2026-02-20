import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from backend.domain.use_cases.get_call_history import GetCallHistoryUseCase
from backend.domain.entities.call import Call, CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.ports.persistence_port import CallRepository

@pytest.fixture
def mock_agent():
    return Agent(
        name="Test Agent",
        system_prompt="System Prompt",
        voice_config=VoiceConfig(name="Voice", style="Style")
    )

@pytest.fixture
def mock_conversation():
    return Conversation()

@pytest.mark.asyncio
async def test_get_call_history_returns_list(mock_agent, mock_conversation):
    # Arrange
    mock_repo = AsyncMock(spec=CallRepository)
    
    # Mock return values must return a tuple (calls, total_count)
    fake_calls = [
        Call(id=CallId("call-1"), agent=mock_agent, conversation=mock_conversation, start_time=datetime.now(timezone.utc), status=CallStatus.COMPLETED, metadata={"client_type": "browser"}),
        Call(id=CallId("call-2"), agent=mock_agent, conversation=mock_conversation, start_time=datetime.now(timezone.utc), status=CallStatus.FAILED, metadata={"client_type": "phone"})
    ]
    mock_repo.get_calls.return_value = (fake_calls, 2)
    
    use_case = GetCallHistoryUseCase(mock_repo)

    # Act
    result = await use_case.execute(limit=10, page=1)

    # Assert
    assert result["total"] == 2
    assert len(result["calls"]) == 2
    assert result["calls"][0]["id"] == "call-1"
    assert result["calls"][1]["id"] == "call-2"
    mock_repo.get_calls.assert_awaited_once_with(limit=10, offset=0, client_type=None)

@pytest.mark.asyncio
async def test_get_call_history_empty():
    # Arrange
    mock_repo = AsyncMock(spec=CallRepository)
    mock_repo.get_calls.return_value = ([], 0)
    
    use_case = GetCallHistoryUseCase(mock_repo)

    # Act
    result = await use_case.execute()

    # Assert
    assert result["calls"] == []
    assert result["total"] == 0
