
from fastapi.testclient import TestClient
from backend.interfaces.http.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_router_mounting():
    # Check if routes are registered
    routes = [route.path for route in app.routes]
    assert "/api/config/{agent_id}" in routes or "/api/config/{agent_id}/" in routes
    assert "/api/history/rows" in routes
    assert "/telephony/twilio/incoming-call" in routes
