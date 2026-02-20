from fastapi.testclient import TestClient
from backend.interfaces.http.main import app
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import logging

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Mock orchestrator
mock_orch = AsyncMock()
async def mock_gen(chunk):
    yield b"response_chunk"
# process_audio_input must be a MagicMock that returns the generator, NOT an AsyncMock (which implies awaitable)
mock_orch.process_audio_input = MagicMock(side_effect=mock_gen)
mock_orch.start_session = AsyncMock()
mock_orch.end_session = AsyncMock()

def run():
    print("Starting Debug Script")
    try:
        # Patch build_orchestrator
        with patch("backend.interfaces.websocket.endpoints.audio_stream.build_orchestrator", new=AsyncMock(return_value=mock_orch)):
            client = TestClient(app)
            print("Client created")
            
            with client.websocket_connect("/ws/media-stream?client=browser") as ws:
                print("Connected to WS")
                
                # 1. Send Start
                ws.send_json({"type": "start", "stream_id": "stream-123"})
                print("Sent Start")
                
                # 2. Send Audio
                ws.send_bytes(b"fake_audio")
                print("Sent Audio")
                
                # 3. Receive Response
                resp = ws.receive_bytes()
                print(f"Received: {resp}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
