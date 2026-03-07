
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, patch, AsyncMock

from backend.interfaces.http.endpoints.telephony import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_twilio_incoming_call():
    from backend.infrastructure.config.settings import settings
    response = client.post("/telephony/twilio/incoming-call", headers={"Host": "testserver"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert f"<Stream url=\"wss://testserver{settings.WS_MEDIA_STREAM_PATH}\" />" in response.text

@pytest.mark.asyncio
@patch("backend.interfaces.http.endpoints.telephony.asyncio.create_task")
@patch("backend.interfaces.http.endpoints.telephony.verify_telnyx_signature", new_callable=AsyncMock)
@patch("backend.interfaces.http.endpoints.telephony.TelnyxClient")
async def test_telnyx_call_initiated(MockClient, mock_verify, mock_create_task):
    mock_verify.return_value = True
    mock_adapter = MockClient.return_value
    mock_adapter.answer_call = AsyncMock()
    
    payload = {
        "data": {
            "event_type": "call.initiated",
            "payload": {
                "call_control_id": "call-123",
                "direction": "inbound"
            }
        }
    }
    response = client.post("/telephony/telnyx/call-control", json=payload)
    assert response.status_code == 200
    
    coro = mock_create_task.call_args[0][0]
    
    class MockSessionMaker:
        async def __aenter__(self): return MagicMock()
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    with patch("backend.infrastructure.database.session.AsyncSessionLocal", return_value=MockSessionMaker()):
        await coro
        
    mock_adapter.answer_call.assert_called_with("call-123")

@pytest.mark.asyncio
@patch("backend.interfaces.http.endpoints.telephony.asyncio.create_task")
@patch("backend.interfaces.http.endpoints.telephony.verify_telnyx_signature", new_callable=AsyncMock)
@patch("backend.interfaces.http.endpoints.telephony.TelnyxClient")
async def test_telnyx_call_answered(MockClient, mock_verify, mock_create_task):
    mock_verify.return_value = True
    mock_adapter = MockClient.return_value
    mock_adapter.start_streaming = AsyncMock()
    
    payload = {
        "data": {
            "event_type": "call.answered",
            "payload": {
                "call_control_id": "call-123",
                "client_state": "state-xyz"
            }
        }
    }
    response = client.post("/telephony/telnyx/call-control", json=payload)
    assert response.status_code == 200
    
    coro = mock_create_task.call_args[0][0]
    
    class MockSessionMaker:
        async def __aenter__(self): return MagicMock()
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        
    with patch("backend.infrastructure.database.session.AsyncSessionLocal", return_value=MockSessionMaker()):
        await coro
        
    mock_adapter.start_streaming.assert_called()
    call_args = mock_adapter.start_streaming.call_args
    assert call_args[0][0] == "call-123"
    assert "wss://testserver/ws/media-stream" in call_args[0][1]
