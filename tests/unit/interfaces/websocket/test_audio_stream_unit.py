
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket
from unittest.mock import AsyncMock, patch, MagicMock
from backend.interfaces.websocket.endpoints.audio_stream import router, build_orchestrator

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def mock_orchestrator():
    mock = AsyncMock()
    mock.start_session = AsyncMock()
    mock.end_session = AsyncMock()
    # process_audio_input returns async generator
    async def fake_generator(chunk):
        yield b"response_audio"
    mock.process_audio_input = fake_generator
    return mock

@patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator")
def test_audio_stream_twilio(mock_build, mock_orchestrator):
    mock_build.return_value = mock_orchestrator
    
    with client.websocket_connect("/ws/media-stream?client=twilio") as websocket:
        # 1. Connected
        websocket.send_text('{"event": "connected", "protocol": "Call", "version": "1.0.0"}')
        # 2. Start
        websocket.send_text('{"event": "start", "start": {"streamSid": "stream-123"}}')
        # 3. Media
        websocket.send_text('{"event": "media", "media": {"payload": "aGVsbG8="}}')
        
        response = websocket.receive_text()
        assert "media" in response
        
        websocket.send_text('{"event": "stop"}')
    
    mock_orchestrator.start_session.assert_called()

@patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator")
def test_audio_stream_browser_bytes(mock_build, mock_orchestrator):
    mock_build.return_value = mock_orchestrator
    
    # Simulate browser sending bytes
    with client.websocket_connect("/ws/media-stream?client=browser") as websocket:
        # Send Start (JSON)
        websocket.send_text('{"event": "start", "stream_id": "browser-stream"}')
        
        # Send Bytes
        websocket.send_bytes(b"raw_audio_chunk")
        
        # Expect Bytes back
        response = websocket.receive_bytes()
        assert response == b"response_audio"
        
        websocket.send_text('{"event": "stop"}')
