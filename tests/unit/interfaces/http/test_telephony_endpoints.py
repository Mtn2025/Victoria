
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, patch, AsyncMock

from backend.interfaces.http.endpoints.telephony import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_twilio_incoming_call():
    response = client.post("/telephony/twilio/incoming-call", headers={"Host": "testserver"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert "<Stream url=\"wss://testserver/api/v1/ws/media-stream\" />" in response.text

@patch("backend.interfaces.http.endpoints.telephony.telnyx_adapter")
def test_telnyx_call_initiated(mock_adapter):
    # Setup AsyncMock
    mock_adapter.answer_call = AsyncMock()
    
    payload = {
        "data": {
            "event_type": "call.initiated",
            "payload": {
                "call_control_id": "call-123"
            }
        }
    }
    response = client.post("/telephony/telnyx/call-control", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "received", "event_type": "call.initiated"}
    
    # Verify use case execution via adapter mock
    mock_adapter.answer_call.assert_called_with("call-123")

@patch("backend.interfaces.http.endpoints.telephony.telnyx_adapter")
def test_telnyx_call_answered(mock_adapter):
    # Setup AsyncMock
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
    
    # Start streaming should be called
    mock_adapter.start_streaming.assert_called()
    call_args = mock_adapter.start_streaming.call_args
    assert call_args[0][0] == "call-123"
    assert "wss://testserver/api/v1/ws/media-stream" in call_args[0][1]
