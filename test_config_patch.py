import asyncio
import json
import httpx
from backend.infrastructure.config.settings import settings

async def main():
    payload = {
        "agent_id": "Victoria",
        "llm_provider": "elevenlabs",
        "voice_name": "",
        "voice_style": "",
        "tools_config": []
    }
    url = f"http://localhost:8000/api/config/?api_key={settings.VICTORIA_API_KEY}"
    print(f"PATCHing {url}")
    
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
