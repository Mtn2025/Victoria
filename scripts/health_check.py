import sys
import time
import requests

def check_health(url, retries=5, delay=2):
    """
    Check if the service is up and running by pinging the health endpoint.
    """
    print(f"🏥 Checking health for: {url}")
    
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Service is UP! (Status: {response.status_code})")
                return True
            else:
                print(f"⚠️ Service returned {response.status_code}. Retrying ({i+1}/{retries})...")
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {e}. Retrying ({i+1}/{retries})...")
        
        time.sleep(delay)
    
    print("⛔ Service failed health check after retries.")
    return False

if __name__ == "__main__":
    # Default to local dev URL
    target_url = "http://localhost:8000/docs" # Swagger UI as health check for now
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    
    if check_health(target_url):
        sys.exit(0)
    else:
        sys.exit(1)
