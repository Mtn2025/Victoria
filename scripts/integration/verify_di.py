
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.infrastructure.database.session import get_db_session
from backend.interfaces.deps import get_call_repository, get_agent_repository
from backend.domain.ports.persistence_port import CallRepository, AgentRepository

async def verify_di():
    print("Verifying Dependency Injection...")
    
    # Simulate FastAPI Dependency Resolution (Manual)
    async for session in get_db_session():
        print("✅ DB Session created")
        
        # Resolve Repos
        call_repo = await get_call_repository(db=session)
        agent_repo = await get_agent_repository(db=session)
        
        # Verify Types
        if isinstance(call_repo, CallRepository):
            print(f"✅ CallRepository resolved to: {type(call_repo).__name__}")
        else:
            print(f"❌ CallRepository Type Mismatch: {type(call_repo)}")
            
        if isinstance(agent_repo, AgentRepository):
            print(f"✅ AgentRepository resolved to: {type(agent_repo).__name__}")
        else:
            print(f"❌ AgentRepository Type Mismatch: {type(agent_repo)}")
            
        # Optional: Try a simple valid operation
        try:
            total = await call_repo.get_calls(limit=1)
            print("✅ CallRepository.get_calls() executed successfully")
        except Exception as e:
            print(f"❌ CallRepository execution failed: {e}")

        break # Only need one session iteration

if __name__ == "__main__":
    asyncio.run(verify_di())
