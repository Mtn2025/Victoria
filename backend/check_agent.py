import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
load_dotenv()
from infrastructure.config.settings import settings
from infrastructure.config.settings import settings

async def check_agent():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT agent_uuid, name, provider, connectivity_config FROM agents WHERE agent_uuid = '46eb2ead-5fab-4d36-b8d6-b36ae9d09f1e'")
        )
        row = result.fetchone()
        if row:
            print(f"Agent: {row.name}")
            print(f"Provider: {row.provider}")
            print(f"Connectivity Config: {row.connectivity_config}")
        else:
            print("Agent not found.")

if __name__ == "__main__":
    asyncio.run(check_agent())
