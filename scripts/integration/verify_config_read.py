
import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())

from backend.interfaces.http.main import app

client = TestClient(app)

def verify_config_endpoint():
    print("Testing GET /api/config/Victoria ...")
    response = client.get("/api/config/Victoria")
    
    if response.status_code != 200:
        print(f"❌ Failed: Status {response.status_code}")
        print(response.text)
        return False
        
    data = response.json()
    print("✅ Status 200 OK")
    
    # Validation
    if data.get("name") != "Victoria":
         print(f"❌ Name Mismatch: {data.get('name')}")
         return False
         
    if "voice" not in data:
         print("❌ Voice config missing")
         return False
         
    print(f"✅ Retrieved Agent: {data['name']}")
    print(f"✅ Voice: {data['voice'].get('name')} ({data['voice'].get('style')})")
    
    return True

if __name__ == "__main__":
    if verify_config_endpoint():
        print("🚀 Config API Verification Passed")
        sys.exit(0)
    else:
        print("💀 Config API Verification Failed")
        sys.exit(1)
