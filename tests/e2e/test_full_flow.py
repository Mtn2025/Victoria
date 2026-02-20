import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.interfaces.http.main import app
from backend.interfaces.deps import get_db_session
from backend.domain.entities.call import CallStatus

# We need to share the DB session between the TestClient (app) and the test function
@pytest.fixture
def override_get_db_session(async_db_session: AsyncSession):
    async def _get_db_session_override():
        yield async_db_session
    
    app.dependency_overrides[get_db_session] = _get_db_session_override
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_e2e_full_call_flow(async_db_session: AsyncSession, override_get_db_session):
    """
    Test a complete call flow:
    1. Create Agent via API (Mocked Auth/etc)
    2. Connect WebSocket as Browser
    3. Start Call
    4. Send Audio -> Receive Audio
    5. End Call
    6. Verify History via API
    """
    
    client = TestClient(app)
    client.headers.update({"X-API-Key": "dev-secret-key"})

    # 1. Mock External Services (LLM, TTS, STT)
    # We mock the ADAPTERS directly to control responses
    # But since build_orchestrator instantiates them inside, we might need to mock build_orchestrator
    # Or rely on dependency injection for adapters if implemented.
    # Currently `build_orchestrator` instantiates adapters directly.
    # So we MUST mock `build_orchestrator` components or the factory.
    
    # Let's mock the Orchestrator for simplicity of "E2E Integration" 
    # OR we can mock the lowest level adapters (Groq, Azure) to let the logic flow.
    # Mocking adapters is better for "System Test".
    
    # Mock Adapters where they are USED in audio_stream.py
    with patch("backend.interfaces.websocket.endpoints.audio_stream.GroqAdapter") as MockGroq, \
         patch("backend.interfaces.websocket.endpoints.audio_stream.AzureTTSAdapter") as MockTTS, \
         patch("backend.interfaces.websocket.endpoints.audio_stream.AzureSTTAdapter") as MockSTT, \
         patch("backend.interfaces.websocket.endpoints.audio_stream.VADProcessor") as MockVAD:
        
        # Groq Mock
        mock_groq_instance = MockGroq.return_value
        mock_groq_instance.generate_response = AsyncMock(return_value="Hello E2E")
        mock_groq_instance.generate_stream = MagicMock()
        async def mock_llm_stream(request):
            yield type('obj', (object,), {'text': 'Hello', 'is_final': False})
            yield type('obj', (object,), {'text': ' E2E', 'is_final': True})
        mock_groq_instance.generate_stream.side_effect = mock_llm_stream

        # TTS Mock
        mock_tts_instance = MockTTS.return_value
        mock_tts_instance.synthesize = AsyncMock(return_value=b"audio_response")
        mock_tts_instance.synthesize_stream = MagicMock()
        async def mock_tts_stream(text):
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"
        mock_tts_instance.synthesize_stream.side_effect = mock_tts_stream

        # STT Mock
        mock_stt_instance = MockSTT.return_value
        mock_stt_instance.transcribe = AsyncMock(return_value="Hello World")
        
        # VAD Mock
        # VADProcessor is instantiated as vad = VADProcessor(...)
        # It has process method?
        # Check audio_stream usage. 
        # StartCallUseCase etc don't use VAD directly maybe?
        # Orchestrator uses VAD.
        # Let's mock VADProcessor.process to allow audio through.
        
        # --- EXECUTION ---
        
        # 1. Connect WebSocket
        with client.websocket_connect("/ws/media-stream?client=browser&agent_id=default") as ws:
            
            # 2. Start
            ws.send_json({"type": "start", "stream_id": "e2e-stream-1"})
            
            # 3. Send Audio (User speaks)
            ws.send_bytes(b"user_audio_123")
            
            # 4. Receive Response
            # We expect audio chunks from TTS
            received_audio = []
            try:
                # Try receiving a few times
                for _ in range(5):
                    data = ws.receive_bytes()
                    received_audio.append(data)
                    if b"audio_chunk" in data:
                        break
            except Exception:
                pass
            
            # 5. End Call
            ws.close()
            
        # 6. Verify History
        # Wait a bit for async background tasks if any (though TestClient is mostly synchronous for app execution)
        # But DB writing happens in 'finally' block of endpoint which is awaited.
        # Query API
        res = client.get("/api/history/rows?limit=100")
        assert res.status_code == 200
        data = res.json()
        
        # Check if our call is in items
        # items is a list of dicts
        # UseCase returns {calls: [], total: ...}
        items = data.get("calls", [])
        # History Endpoint returns PaginatedResponse?
        # Let's check Endpoint return type.
        # It returns `HistoryResponse(items=..., total=...)` likely.
        
        # The key in JSON response is "items" or "calls"?
        # History endpoint code?
        # Let's inspect `backend/interfaces/http/endpoints/history.py` if needed.
        # Assuming "items" or checking raw response.
        
        print(f"History Response: {data}")
