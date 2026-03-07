
from fastapi.testclient import TestClient
from backend.interfaces.http.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_router_mounting():
    # Check if routes are registered
    route_paths = [route.path for route in app.routes]
    assert "/api/agents" in route_paths or "/api/agents/" in route_paths
    assert "/api/telephony/telnyx/call-control" in route_paths
    assert "/api/telephony/twilio/incoming-call" in route_paths
