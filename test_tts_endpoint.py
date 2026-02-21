import asyncio
from backend.infrastructure.config.settings import settings
import httpx

async def test_endpoint():
    url = f"http://localhost:8000/api/config/options/tts/languages?provider=azure&api_key={settings.VICTORIA_API_KEY}"
    print(f"Calling: {url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            
        url2 = f"http://localhost:8000/api/config/options/tts/voices?provider=azure&language=es-MX&api_key={settings.VICTORIA_API_KEY}"
        print(f"\nCalling voices: {url2}")
        async with httpx.AsyncClient() as client:
            resp2 = await client.get(url2, timeout=10.0)
            print(f"Status: {resp2.status_code}")
            print(f"Response: {resp2.text[:500]}...") # Truncated
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoint())
