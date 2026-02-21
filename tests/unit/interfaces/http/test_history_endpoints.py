
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch, MagicMock
from backend.interfaces.http.endpoints.history import router
from backend.interfaces.deps import get_call_repository
from backend.domain.entities.call import Call, CallStatus
from backend.domain.value_objects.call_id import CallId
from datetime import datetime, timezone

app = FastAPI()
app.include_router(router)
client = TestClient(app)

mock_repo = AsyncMock()
async def override_repo():
    return mock_repo

app.dependency_overrides[get_call_repository] = override_repo

def test_get_history_rows():
    # Arrange
    call = Call(
        id=CallId("call-1"), 
        start_time=datetime.now(timezone.utc), 
        status=CallStatus.COMPLETED,
        agent=MagicMock(),
        conversation=MagicMock()
    )
    mock_repo.get_calls.return_value = ([call], 1)
    
    # Act
    response = client.get("/history/rows?page=1")
    
    # Assert
    assert response.status_code == 200
    mock_repo.get_calls.assert_called_once()
    
    data = response.json()
    assert data["total"] == 1
    assert len(data["calls"]) == 1
    assert data["calls"][0]["id"] == "call-1"

@pytest.mark.asyncio
async def test_delete_selected():
    # Arrange
    payload = {"ids": ["call-1", "call-2"]}
    
    # Act
    response = client.post("/history/delete-selected", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert mock_repo.delete.call_count == 2
    
@pytest.mark.asyncio
async def test_clear_history():
    mock_repo.clear.return_value = 10
    response = client.post("/history/clear")
    assert response.status_code == 200
    assert response.json()["deleted"] == 10
