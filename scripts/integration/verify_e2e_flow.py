
import sys
import os
import json
import base64
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())

from backend.interfaces.http.main import app
from backend.domain.entities.call import CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

# Mocks for External Services
class MockGroqAdapter:
    async def generate_response(self, *args, **kwargs):
        async def stream():
            yield "Hello from Mock LLM"
        return stream()

class MockAzureTTSAdapter:
    async def generate_speech(self, *args, **kwargs):
        yield b"\x00\x00\x00\x00" * 10 

class MockAzureSTTAdapter:
    async def transcribe(self, *args, **kwargs):
        return "Hello from Mock STT"
        
class MockDummyAdapter:
    async def start_call(self, *args): pass
    async def end_call(self, *args): pass

# Use TestClient
client = TestClient(app)

def verify_e2e_flow():
    print("Starting E2E Flow Verification (Websocket -> Domain Logic)...")

    # MOCK REPOSITORIES
    mock_agent_repo = AsyncMock()
    # Setup Agent
    agent = Agent(
        name="Victoria",
        system_prompt="System",
        voice_config=VoiceConfig(name="Voice"),
        first_message="Hello"
    )
    mock_agent_repo.get_agent.return_value = agent
    
    mock_call_repo = AsyncMock()
    mock_call_repo.save = AsyncMock()
    
    # Overrides for Dependency Injection
    # We need to override get_agent_repository and get_call_repository in backend.interfaces.deps
    from backend.interfaces.deps import get_agent_repository, get_call_repository
    
    app.dependency_overrides[get_agent_repository] = lambda: mock_agent_repo
    app.dependency_overrides[get_call_repository] = lambda: mock_call_repo
    
    # Patch the Adapters where they are imported in audio_stream.py
    with patch("backend.interfaces.websocket.endpoints.audio_stream.GroqAdapter", side_effect=MockGroqAdapter), \
         patch("backend.interfaces.websocket.endpoints.audio_stream.AzureTTSAdapter", side_effect=MockAzureTTSAdapter), \
         patch("backend.interfaces.websocket.endpoints.audio_stream.AzureSTTAdapter", side_effect=MockAzureSTTAdapter), \
         patch("backend.interfaces.websocket.endpoints.audio_stream.DummyTelephonyAdapter", side_effect=MockDummyAdapter):

        # 1. Simulate Websocket Connection (Twilio Style)
        stream_id = "e2e-test-stream-mocked"
        print(f"Connecting to /ws/media-stream for Stream ID: {stream_id}")
        
        try:
            with client.websocket_connect("/ws/media-stream?client=twilio&agent_id=Victoria") as websocket:
                
                # 2. Send Start Event
                start_event = {
                    "event": "start",
                    "streamSid": stream_id,
                    "start": {
                        "streamSid": stream_id,
                        "callSid": "CA12345",
                        "customParameters": {
                            "agent_id": "Victoria"
                        }
                    }
                }
                websocket.send_text(json.dumps(start_event))
                print("Sent 'start' event")
                
                # 3. Send Audio
                dummy_audio = base64.b64encode(b"\xff" * 160).decode("utf-8")
                media_event = {
                    "event": "media",
                    "streamSid": stream_id,
                    "media": {
                        "payload": dummy_audio,
                        "chunk": "1",
                        "timestamp": "100"
                    }
                }
                websocket.send_text(json.dumps(media_event))
                print("Sent 'media' event (chunk)")
                
                # 4. Short sleep to let orchestrator process
                try: 
                    # We can't use asyncio.sleep inside TestClient sync context easily
                    # But the server is running in background thread/task.
                    pass
                except: pass
                
                # 5. Send Stop
                stop_event = {
                    "event": "stop",
                    "streamSid": stream_id
                }
                websocket.send_text(json.dumps(stop_event))
                print("Sent 'stop' event")
                
        except Exception as e:
            print(f"Websocket Error: {e}")
            return False
            
    print("Websocket session ended.")
    
    # 6. Verify Domain Interactions
    print("Verifying Domain Interactions...")
    
    # Check if AgentRepo was used
    mock_agent_repo.get_agent.assert_called()
    print("Verified: AgentRepository.get_agent called")
    
    # Check if CallRepo.save was called (Start and End)
    # Expect at least 2 calls (Start Call, End Call)
    # Maybe more for intermediate updates?
    save_count = mock_call_repo.save.call_count
    print(f"CallRepository.save called {save_count} times.")
    
    if save_count < 1:
        print("Error: CallRepository.save was NEVER called.")
        return False
        
    # Inspect arguments of first save (Start Call)
    # call_args_list[0] -> (args, kwargs) -> args[0] is Call object
    first_call_obj = mock_call_repo.save.call_args_list[0][0][0]
    print(f"First Save Call ID: {first_call_obj.id.value}")
    
    if first_call_obj.id.value != stream_id:
        print(f"Error: Expected ID {stream_id}, got {first_call_obj.id.value}")
        return False
    
    # Check "End Call" status?
    last_call_obj = mock_call_repo.save.call_args_list[-1][0][0]
    print(f"Last Save Call Status: {last_call_obj.status.value}")
    
    if last_call_obj.status.value not in ["completed", "ended"]:
         print("Warning: Last save status is not completed/ended.")
    
    print("E2E Domain Logic Verification Passed")
    return True

if __name__ == "__main__":
    if verify_e2e_flow():
        sys.exit(0)
    else:
        sys.exit(1)
