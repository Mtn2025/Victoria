import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from backend.interfaces.http.main import app
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.infrastructure.database.repositories import SqlAlchemyAgentRepository

@pytest.fixture
def client(async_db_session):
    """
    TestClient with encapsulated DB session override.
    """
    from backend.infrastructure.database.session import get_db_session
    
    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as c:
        # Auth Header for Protected Routes
        c.headers.update({"X-API-Key": "dev-secret-key"})
        yield c
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
class TestConfigEndpointsE2E:

    async def test_health_check(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "victoria-backend"}

    async def test_agent_config_lifecycle(self, client, async_db_session):
        # 1. Seed DB
        repo = SqlAlchemyAgentRepository(async_db_session)
        agent = Agent(
            name="e2e-agent",
            system_prompt="E2E System Prompt",
            voice_config=VoiceConfig(name="en-US-JennyNeural"),
            first_message="E2E Hello"
        )
        await repo.update_agent(agent)
        
        # 2. GET Agent Config
        response = client.get("/api/config/e2e-agent")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "e2e-agent"
        assert data["system_prompt"] == "E2E System Prompt"
        assert data["voice"]["name"] == "en-US-JennyNeural"

        # 3. PATCH Agent Config
        update_payload = {
            "agent_id": "e2e-agent",
            "system_prompt": "Updated E2E Prompt",
            "voice_speed": 1.5
        }
        response = client.patch("/api/config/", json=update_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "updated"
        
        # 4. Verify Update via GET
        response = client.get("/api/config/e2e-agent")
        data = response.json()
        assert data["system_prompt"] == "Updated E2E Prompt"
        assert data["voice"]["speed"] == 1.5

    async def test_tts_options(self, client):
        # Mock Azure Adapter within the endpoint
        with patch("backend.interfaces.http.endpoints.config.AzureTTSAdapter") as MockAdapter:
            mock_instance = MockAdapter.return_value
            # Define simple mock return objects
            mock_voice = MagicMock()
            mock_voice.__dict__ = {"name": "TestVoice", "locale": "en-US"}
            mock_instance.get_available_voices = AsyncMock(return_value=[mock_voice])
            mock_instance.get_available_languages = AsyncMock(return_value=["en-US", "es-ES"])

            # Test Voices
            response = client.get("/api/config/options/tts/voices")
            assert response.status_code == 200
            assert response.json()["voices"][0]["name"] == "TestVoice"
            
            # Test Languages
            response = client.get("/api/config/options/tts/languages")
            assert response.status_code == 200
            assert "en-US" in response.json()["languages"]
