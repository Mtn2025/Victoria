import os
import sys
from pathlib import Path

# Required variables
REQUIRED_VARS = [
    "GROQ_API_KEY",
    "AZURE_SPEECH_KEY",
    "AZURE_SPEECH_REGION",
    "DATABASE_URL",
    "TELEPHONY_WEBHOOK_SECRET",
    "VITE_API_URL",
    "VITE_WS_URL"
]

def load_env(env_path: Path):
    """Simple .env loader to avoid dependencies in this script"""
    if not env_path.exists():
        print(f"❌ Error: Environment file not found at {env_path}")
        return False
        
    print(f"🔍 Checking configuration from: {env_path}")
    
    missing = []
    with open(env_path, encoding="utf-8") as f:
        content = f.read()
        
    # Basic check - parsing can be more robust with python-dotenv if available
    # This is a lightweight check
    for var in REQUIRED_VARS:
        if f"{var}=" not in content and var not in os.environ:
             missing.append(var)
    
    if missing:
        print("❌ Missing required variables:")
        for v in missing:
            print(f"   - {v}")
        return False
    
    print("✅ Configuration is valid!")
    return True

if __name__ == "__main__":
    # Default to .env.local if no argument
    target_env = Path("config/environments/.env.local")
    if len(sys.argv) > 1:
        target_env = Path(sys.argv[1])
        
    if not load_env(target_env):
        sys.exit(1)
    sys.exit(0)
