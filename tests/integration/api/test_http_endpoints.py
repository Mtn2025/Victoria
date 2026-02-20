"""
Integration Tests for HTTP API Endpoints.
Verifies /config and /history endpoints using TestClient and Real Mocks.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import os

from backend.interfaces.http.main import create_app
from backend.infrastructure.database.session import get_db_session
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.infrastructure.database.repositories import SqlAlchemyAgentRepository, SqlAlchemyCallRepository

# Mock AzureTTSAdapter globally for this module
# We need to patch where it is imported/used.
# In config.py: from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
# We will use dependency overrides or patching.

@pytest.fixture
def client(async_db_session):
    """
    TestClient with database dependency override.
    """
    app = create_app()
    
    # Override Database Dependency
    async def override_get_db():
        yield async_db_session
        
    app.dependency_overrides[get_db_session] = override_get_db
    
    # Create Client
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_azure_adapter():
    """High Fidelity Mock for AzureTTSAdapter."""
    with patch("backend.interfaces.http.endpoints.config.AzureTTSAdapter") as MockAdapter:
        # Instance mock
        instance = MockAdapter.return_value
        
        # Mock get_available_voices
        async def mock_voices(lang=None):
            # Return fake objects with __dict__ as expected by endpoint
            v1 = MagicMock()
            v1.__dict__ = {"name": "en-US-JennyNeural", "locale": "en-US"}
            return [v1]
            
        instance.get_available_voices = AsyncMock(side_effect=mock_voices)
        instance.get_available_languages = AsyncMock(return_value=["en-US", "es-MX"])
        
        yield instance

class TestConfigEndpoints:
    
    def test_get_agent_config_not_found(self, client):
        response = client.get("/api/config/NonExistentAgent")
        assert response.status_code == 404
        
    def test_update_and_get_agent_config(self, client):
        # 1. Update (creates if not exists)
        payload = {
            "agent_id": "IntegrationTestAgent",
            "system_prompt": "Updated Prompt",
            "voice_name": "en-US-GuyNeural"
        }
        response = client.patch("/api/config/", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        
        # 2. Get
        response = client.get("/api/config/IntegrationTestAgent")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "IntegrationTestAgent"
        assert data["system_prompt"] == "Updated Prompt"
        assert data["voice"]["name"] == "en-US-GuyNeural"

    def test_get_tts_options_mocked(self, client, mock_azure_adapter):
        # Voices
        response = client.get("/api/config/options/tts/voices")
        assert response.status_code == 200
        assert "voices" in response.json()
        assert response.json()["voices"][0]["name"] == "en-US-JennyNeural"
        
        # Languages
        response = client.get("/api/config/options/tts/languages")
        assert response.status_code == 200
        assert "en-US" in response.json()["languages"]


class TestHistoryEndpoints:
    
    @pytest.fixture
    def mock_templates_dir(self):
        # Ensure templates exist or are mocked if copy failed
        # But we assume copy step succeeded or we check availability.
        pass

    def test_get_history_rows_json(self, client):
        """
        Test that /history/rows returns JSON data.
        """
        response = client.get("/api/history/rows?page=1&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify JSON structure
        assert "calls" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["calls"], list)
        
        # If DB is empty, calls is empty list
        if data["calls"]:
            assert "id" in data["calls"][0]
            assert "start_time" in data["calls"][0]
            assert "status" in data["calls"][0]

    def test_delete_selected(self, client):
        """Test deletion endpoint."""
        # 1. We need to create a call first to delete, to be proper Integration.
        # But for basics, we can try deleting non-existent IDs.
        
        payload = {"ids": ["uuid-1", "uuid-2"]}
        response = client.post("/api/history/delete-selected", json=payload)
        
        assert response.status_code == 200
        # Endpoint returns count of processed IDs regardless of existence (idempotent)
        assert response.json()["deleted"] == 2

    def test_clear_history(self, client):
        response = client.post("/api/history/clear")
        assert response.status_code == 200

class TestTelephonyEndpoints:
    
    @pytest.fixture
    def mock_telnyx_adapter(self):
        """Mock the global telnyx_adapter in telephony module."""
        with patch("backend.interfaces.http.endpoints.telephony.telnyx_adapter") as mock_adapter:
            # Setup AsyncMock for methods
            mock_adapter.answer_call = AsyncMock()
            mock_adapter.start_streaming = AsyncMock()
            yield mock_adapter

    def test_twilio_webhook(self, client):
        """Test Twilio incoming call webhook logic."""
        response = client.post("/telephony/twilio/incoming-call", headers={"Host": "testserver"})
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Stream url=\"wss://testserver/ws/media-stream\" />" in response.text

    def test_telnyx_webhook_initiated(self, client, mock_telnyx_adapter):
        """Test Telnyx call.initiated event triggers answer."""
        payload = {
            "data": {
                "event_type": "call.initiated",
                "payload": {"call_control_id": "call-123"}
            }
        }
        # Authorized request
        headers = {"X-Victoria-Key": "victoria-secret-key-change-me"} # Default secret
        response = client.post("/telephony/telnyx/call-control", json=payload, headers=headers)
        
        assert response.status_code == 200
        # Check if background task was added. 
        # Integration tests with TestClient usually execute background tasks?
        # Starlette/FastAPI TestClient runs background tasks synchronously after response.
        mock_telnyx_adapter.answer_call.assert_called_once_with("call-123")

    def test_telnyx_webhook_answered(self, client, mock_telnyx_adapter):
        """Test Telnyx call.answered event triggers streaming."""
        payload = {
            "data": {
                "event_type": "call.answered",
                "payload": {
                    "call_control_id": "call-123",
                    "client_state": "state-xyz"
                }
            }
        }
        headers = {"X-Victoria-Key": "victoria-secret-key-change-me"}
        response = client.post("/telephony/telnyx/call-control", json=payload, headers=headers)
        
        assert response.status_code == 200
        mock_telnyx_adapter.start_streaming.assert_called_once()
        args = mock_telnyx_adapter.start_streaming.call_args
        assert args[0][0] == "call-123"
        assert "wss://testserver" in args[0][1] # streaming url
        assert args[0][2] == "state-xyz"
