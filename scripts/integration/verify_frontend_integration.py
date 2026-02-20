
import sys
import os
import requests
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())
from backend.interfaces.http.main import app

client = TestClient(app)

def verify_frontend_integration():
    print("🚀 Starting Frontend Integration Smoke Test...")
    results = {"passed": [], "failed": []}

    # 1. Config Options (Used by configService.ts)
    print("\n1. Testing Config Options (Frontend: getLanguages, getVoices)...")
    
    endpoints = [
        ("/api/config/options/tts/languages", "GET"),
        ("/api/config/options/tts/voices", "GET")
    ]
    
    for path, method in endpoints:
        print(f"   Checking {method} {path}...", end=" ")
        try:
            res = client.get(path)
            if res.status_code == 200:
                print("✅ OK")
                results["passed"].append(path)
            else:
                print(f"❌ FAILED ({res.status_code})")
                results["failed"].append(path)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results["failed"].append(path)

    # 2. Config Update (Used by configService.ts)
    # Frontend now calls PATCH /api/config/
    print("\n2. Testing Config Update (Frontend: updateBrowserConfig)...")
    path = "/api/config/"
    print(f"   Checking PATCH {path}...", end=" ")
    try:
        # Payload matching BackendConfigUpdate
        payload = {
            "agent_id": "Victoria",
            "voice_name": "en-US-JennyNeural",
            "temperature": 0.7
        }
        res = client.patch(path, json=payload)
        if res.status_code == 200:
             print("✅ OK")
             results["passed"].append(path)
        else:
             print(f"❌ FAILED ({res.status_code})")
             print(f"   Response: {res.text}")
             results["failed"].append(path)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["failed"].append(path)

    # 3. History (Used by historyService.ts)
    # Frontend now uses /api/history/rows
    print("\n3. Testing History Endpoints...")
    
    # Check what Frontend wants (Refactored)
    path_frontend = "/api/history/rows"
    print(f"   Checking Frontend Expected: GET {path_frontend}...", end=" ")
    res = client.get(path_frontend)
    if res.status_code == 200:
        print("✅ OK")
        results["passed"].append(path_frontend)
    else:
        print(f"❌ FAILED ({res.status_code})")
        results["failed"].append(path_frontend)

    # Summary
    print("\n=== Integration Summary ===")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed/Missing: {len(results['failed'])}")
    
    if len(results['failed']) > 0:
        print("\nGAP ANALYSIS:")
        if "/api/config/update-json" in results['failed']:
            print("- Config Update Mismatch: Frontend POST /update-json vs Backend PATCH /config/")
        if "/api/history/list" in results['failed']:
            print("- History List Mismatch: Frontend GET /history/list vs Backend GET /history/rows")
            
    return len(results['failed']) == 0

if __name__ == "__main__":
    verify_frontend_integration()
