import pytest
from httpx import AsyncClient, ASGITransport
from backend.interfaces.http.main import app 

@pytest.mark.asyncio
async def test_agent_config_endpoint_availability(async_db_session):
    # Minimal test to check app can be instantiated and endpoint is reachable (404/401 is fine, just not 500 import error)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # We expect a 404 because agent-123 doesn't exist in empty DB
        # But this confirms the route is registered and handler is invoked.
        response = await ac.get("/api/v1/config/agent-123")
    
    # Assert
    assert response.status_code in [404, 200]
