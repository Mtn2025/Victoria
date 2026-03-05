import asyncio
import os
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Asegúrate de cargar las variables de entorno para conectarte a PostgreSQL
load_dotenv(dotenv_path=".env")

from infrastructure.database.session import AsyncSessionLocal
from sqlalchemy import select
from infrastructure.database.models import AgentModel

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(AgentModel).where(AgentModel.is_active == True)
        result = await session.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            print("No active agent")
            return
            
        print(f"Active Agent: {agent.name} (UUID: {agent.agent_uuid})")
        print(f"Connectivity Config inside DB: {agent.connectivity_config}")

if __name__ == "__main__":
    asyncio.run(main())
