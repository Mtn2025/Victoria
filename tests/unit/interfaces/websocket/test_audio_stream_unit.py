"""
WebSocket audio_stream endpoint unit tests.
Updated to reflect the corrected audio pipeline:
  - start_session() now returns Optional[bytes] (greeting audio)
  - push_audio_frame() used instead of process_audio_input for pipeline clients
  - build_orchestrator() is async — must be awaited via side_effect
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from backend.interfaces.websocket.endpoints.audio_stream import router, build_orchestrator

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_orchestrator():
    mock = AsyncMock()
    # start_session returns None (no greeting / greeting sent separately)
    mock.start_session = AsyncMock(return_value=None)
    mock.end_session = AsyncMock()
    mock.push_audio_frame = AsyncMock()
    mock.pipeline = MagicMock()          # pipeline truthy → uses push_audio_frame path

    # process_audio_input: legacy fallback — not used when pipeline is set
    async def fake_generator(chunk):
        yield b"response_audio"
    mock.process_audio_input = fake_generator
    return mock


@patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator")
def test_audio_stream_twilio(mock_build, mock_orchestrator):
    """
    Twilio client: JSON 'start' triggers start_session, 'media' goes through
    push_audio_frame (pipeline path). No crash expected.
    """
    mock_build.return_value = mock_orchestrator

    with client.websocket_connect("/ws/media-stream?client=twilio") as websocket:
        # Protocol: connected → start → media → stop
        websocket.send_text('{"event": "connected", "protocol": "Call", "version": "1.0.0"}')
        websocket.send_text('{"event": "start", "start": {"streamSid": "stream-123"}}')
        websocket.send_text('{"event": "media", "media": {"payload": "aGVsbG8="}}')
        websocket.send_text('{"event": "stop"}')

    mock_orchestrator.start_session.assert_called_once()


@patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator")
def test_audio_stream_browser_bytes(mock_build, mock_orchestrator):
    """
    Browser client: binary bytes audio is routed to push_audio_frame (pipeline path).
    No response expected because output is handled asynchronously by the pipeline.
    """
    mock_build.return_value = mock_orchestrator

    with client.websocket_connect("/ws/media-stream?client=browser") as websocket:
        # Start event (JSON)
        websocket.send_text('{"event": "start", "stream_id": "browser-stream"}')
        # Binary audio chunk
        websocket.send_bytes(b"raw_audio_chunk")
        websocket.send_text('{"event": "stop"}')

    mock_orchestrator.push_audio_frame.assert_called()


@patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator")
def test_audio_stream_greeting_sent(mock_build, mock_orchestrator):
    """
    When start_session returns greeting audio bytes, they are sent to the client.
    """
    GREETING = b"hello_audio_bytes"
    mock_orchestrator.start_session = AsyncMock(return_value=GREETING)
    mock_build.return_value = mock_orchestrator

    with client.websocket_connect("/ws/media-stream?client=browser") as websocket:
        websocket.send_text('{"event": "start", "start": {"streamSid": "browser-12"}}')
        # The greeting should be sent immediately as binary
        greeting_resp = websocket.receive_bytes()
        assert greeting_resp == GREETING
        websocket.send_text('{"event": "stop"}')
