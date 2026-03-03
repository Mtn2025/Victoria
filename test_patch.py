import urllib.request
import json

def main():
    try:
        req = urllib.request.Request("http://localhost:8000/api/agents/active")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            agent_id = data["agent_uuid"]
            print(f"Active Agent: {agent_id}")
            
            payload = {
                "silence_timeout_ms": 1000,
                "barge_in_phrases": ["Mm", "Ah"],
                "sttProvider": "azure"
            }
            
            patch_req = urllib.request.Request(
                f"http://localhost:8000/api/agents/{agent_id}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="PATCH"
            )
            
            try:
                with urllib.request.urlopen(patch_req) as p_res:
                    print("Status:", p_res.status)
                    print("Response:", p_res.read().decode())
            except urllib.error.HTTPError as e:
                print("Error Status:", e.code)
                print("Error Response:", e.read().decode())
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
