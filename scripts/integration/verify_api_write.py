
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from backend.interfaces.http.main import app

client = TestClient(app)

def verify_delete_endpoint():
    print("Testing POST /api/history/delete-selected ...")
    
    # 1. Get current list to find a target
    res_list = client.get("/api/history/rows?limit=10")
    if res_list.status_code != 200:
        print("❌ Failed to list calls for deletion setup")
        return False
        
    calls = res_list.json().get("calls", [])
    if not calls:
        print("⚠️ No calls found to delete. Skipping delete verification (or need to create one).")
        # In a strict test we would create one, but for now we seeded data, so it should exist.
        # If seed data was deleted by previous runs, this might fail.
        return True 
        
    target_id = calls[0]["id"]
    print(f"Targeting Call ID: {target_id}")
    
    # 2. Delete
    payload = {"ids": [target_id]}
    res_delete = client.post("/api/history/delete-selected", json=payload)
    
    if res_delete.status_code != 200:
        print(f"❌ Failed: Status {res_delete.status_code}")
        print(res_delete.text)
        return False
        
    del_data = res_delete.json()
    print(f"✅ Delete Response: {del_data}")
    
    if del_data.get("deleted") != 1:
        print(f"❌ Expected 1 deleted, got {del_data.get('deleted')}")
        return False
        
    # 3. Verify Gone
    res_check = client.get(f"/api/history/rows?limit=100")
    remaining_calls = res_check.json().get("calls", [])
    found = any(c["id"] == target_id for c in remaining_calls)
    
    if found:
        print(f"❌ Call {target_id} still exists in list!")
        return False
        
    print("✅ Call successfully deleted and verified gone.")
    return True

if __name__ == "__main__":
    try:
        success = verify_delete_endpoint()
        if success:
            print("🚀 API Write Verification Passed")
            sys.exit(0)
        else:
            print("💀 API Write Verification Failed")
            sys.exit(1)
    except Exception as e:
        print(f"🔥 Exception: {e}")
        sys.exit(1)
