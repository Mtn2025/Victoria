"""
E2E Backend Flow: Config Updates.
Verifies that configuration changes are persisted and retrieved correctly.
Uses AsyncClient (httpx) to be loop-safe with AsyncSession.
"""
import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from backend.interfaces.http.main import create_app
from backend.infrastructure.database.session import get_db_session

@pytest.fixture
async def client(async_db_session):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: async_db_session
    # Use ASGITransport for direct app call
    # Use ASGITransport for direct app call
    transport = ASGITransport(app=app)
    # Auth Header for Protected Routes
    headers = {"X-API-Key": "dev-secret-key"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as c:
        yield c

@pytest.mark.asyncio
async def test_config_update_flow(client):
    """
    Scenario:
    1. GET /api/config/default -> Check defaults.
    2. PATCH /api/config/ -> Update settings.
    3. GET /api/config/default -> Verify updates.
    """
    # 1. Create agent
    headers = {"X-API-Key": "dev-secret-key"}
    response = await client.post("/api/agents", json={"name": "E2ETestAgent"}, headers=headers)
    assert response.status_code == 201, f"Error: {response.text}"
    agent_id = response.json()["agent_uuid"]
    
    # 2. Update config
    new_config = {
        "voice_name": "en-US-JennyNeural",
        "system_prompt": "You are a helpful E2E test assistant.",
        "voice_style": "cheerful",
        "voice_speed": 1.0,
        "voice_pitch": 0.0,
        "voice_volume": 100.0,
        "silence_timeout_ms": 5000
    }
    
    response = await client.patch(f"/api/agents/{agent_id}", json=new_config, headers=headers)
    assert response.status_code == 200, f"Error: {response.text}"
    
    # 3. Verify Persistence via active agent
    await client.post(f"/api/agents/{agent_id}/activate", headers=headers)
    response = await client.get("/api/agents/active", headers=headers)
    assert response.status_code == 200
    final_config = response.json()
    
    assert final_config["voice"]["name"] == "en-US-JennyNeural"
    assert final_config["system_prompt"] == "You are a helpful E2E test assistant."
