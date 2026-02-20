
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from backend.interfaces.http.main import app
from backend.infrastructure.database.session import get_db_session

# We will use the sync TestClient which wraps the async app
# Note: TestClient handles async app in sync context seamlessly for basics,
# but for database interaction in the same loop, we might need care.
# However, standard TestClient usage is fine for functional verification.

client = TestClient(app)

def verify_history_endpoint():
    print("Testing GET /api/history/rows ...")
    response = client.get("/api/history/rows?limit=5")
    
    if response.status_code != 200:
        print(f"❌ Failed: Status {response.status_code}")
        print(response.text)
        return False
        
    data = response.json()
    print("✅ Status 200 OK")
    
    # Verify Structure
    required_keys = ["calls", "total", "page", "total_pages"]
    for key in required_keys:
        if key not in data:
            print(f"❌ Missing key: {key}")
            return False
            
    calls = data["calls"]
    print(f"✅ Retrieved {len(calls)} calls (Total: {data['total']})")
    
    if len(calls) > 0:
        sample = calls[0]
        print(f"Sample Call: ID={sample.get('id')}, Status={sample.get('status')}")
        
        if "metadata" not in sample:
             print("❌ 'metadata' field missing in call object")
             return False
             
    return True

if __name__ == "__main__":
    try:
        success = verify_history_endpoint()
        if success:
            print("🚀 API Read Verification Passed")
            sys.exit(0)
        else:
            print("💀 API Read Verification Failed")
            sys.exit(1)
    except Exception as e:
        print(f"🔥 Exception: {e}")
        sys.exit(1)
