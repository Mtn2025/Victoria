import asyncio
import logging
from unittest.mock import patch
from backend.application.services.outbound_service import OutboundDialerService

logging.basicConfig(level=logging.INFO)

class MockConfig:
    agent_id = "agent-123"
    amd_enabled = True
    amd_action = "hangup"

class MockConfigRepo:
    async def get_config(self, agent_id):
        return MockConfig()

class MockResponse:
    status_code = 201
    def json(self): return {"sid": "CA12345"}

class MockAsyncClient:
    last_post_kwargs = {}
    def __init__(self, *args, **kwargs): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def post(self, url, **kwargs):
        MockAsyncClient.last_post_kwargs = kwargs
        return MockResponse()

async def test_outbound_dialer():
    repo = MockConfigRepo()
    dialer = OutboundDialerService(repo, agent_repo=repo, call_repo=repo)
    
    with patch("backend.application.services.outbound_service.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "AC123"
        mock_settings.TWILIO_AUTH_TOKEN = "token"
        mock_settings.TWILIO_PHONE_NUMBER = "+11234567"
        mock_settings.BASE_URL = "https://mock.com"
        
        with patch("backend.application.services.outbound_service.httpx.AsyncClient", new=MockAsyncClient):
            result = await dialer.create_call("agent-123", "+15555555555", "twilio")
            print("Success:", result)
            
            kwargs = MockAsyncClient.last_post_kwargs
            data = kwargs.get("data", {})
            
            assert data.get("MachineDetection") == "Enable", "AMD flag was not injected!"
            assert "AsyncAmdStatusCallback" in data, "AMD Callback missing!"
            print("TEST PASSED: Outbound Dialer successfully injects AMD configuration.")

if __name__ == "__main__":
    asyncio.run(test_outbound_dialer())
