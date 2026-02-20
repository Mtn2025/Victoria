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
    # 1. Initial State
    # Note: The endpoint is /api/config/{agent_id}. Let's assume 'default' agent.
    
    # First, we need to create the agent or assume get handles it?
    # The GET endpoint raises 404 if not found.
    # The PATCH endpoint creates it if not found ("Upsert" logic).
    # So we PATCH first to ensure it exists, then GET.
    
    agent_id = "default"
    
    # 2. Update (and Create)
    new_config = {
        "agent_id": agent_id,
        "voice_name": "en-US-JennyNeural",
        "system_prompt": "You are a helpful E2E test assistant.",
        "voice_style": "cheerful",
        "voice_speed": "1.0",
        "voice_pitch": "0",
        "voice_volume": "100",
        "silence_timeout_ms": 5000
    }
    
    # Use trailing slash if Router prefix is /config and include prefix is /api, and patch is "/"
    # Router("/config") + Patch("/") = "/config/"
    # Include("/api") -> "/api/config/"
    response = await client.patch("/api/config/", json=new_config)
    assert response.status_code == 200, f"Error: {response.text}"
    
    # 3. Verify Persistence
    response = await client.get(f"/api/config/{agent_id}")
    assert response.status_code == 200
    final_config = response.json()
    
    assert final_config["voice"]["name"] == "en-US-JennyNeural"
    assert final_config["system_prompt"] == "You are a helpful E2E test assistant."
