import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from backend.interfaces.http.main import app
from backend.application.services.call_orchestrator import CallOrchestrator

@pytest.fixture
def mock_orchestrator():
    orchestrator = AsyncMock(spec=CallOrchestrator)
    # Mock async generator for process_audio_input
    async def mock_gen(chunk):
        yield b"response_chunk"
    orchestrator.process_audio_input = MagicMock(side_effect=mock_gen)
    return orchestrator

def test_websocket_connect_disconnect():
    # Patch to avoid real adapter initialization (Groq API Key error)
    with patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator", new=AsyncMock()):
        client = TestClient(app)
        with client.websocket_connect("/ws/media-stream?client=browser") as websocket:
            # Just connect and close
            pass
    # No exception means success

def test_websocket_browser_flow(mock_orchestrator):
    # Patch the build_orchestrator to return our mock
    with patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator", new=AsyncMock(return_value=mock_orchestrator)):
        client = TestClient(app)
        with client.websocket_connect("/ws/media-stream?client=browser") as websocket:
            # 1. Send Start
            websocket.send_json({
                "type": "start",
                "stream_id": "stream-123"
            })
            
            # verify orchestrator started
            # Since TestClient runs synchronous in thread, we can't easily assert async mock calls *inside* the with block 
            # unless we use async test client or rely on side effects.
            # But we can check response if any.
            
            # 2. Send Audio (Simulated as bytes)
            # Browser sends raw bytes usually? Or text event with 'bytes' key if using our protocol wrapper?
            # Code says: if "bytes" in message: ... chnk = message["bytes"]
            # TestClient send_bytes sends raw bytes.
            websocket.send_bytes(b"fake_audio_pcm")
            
            # Expect response
            response = websocket.receive_bytes()
            assert response == b"response_chunk"
