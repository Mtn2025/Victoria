import asyncio
from dotenv import load_dotenv
load_dotenv('../.env')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from infrastructure.config.settings import settings

async def check():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(
            text("SELECT agent_uuid, name, provider, connectivity_config FROM agents WHERE agent_uuid = '46eb2ead-5fab-4d36-b8d6-b36ae9d09f1e'")
        )
        row = result.fetchone()
        if row:
            print("AGENT FOUND:")
            print(f"UUID: {row[0]}")
            print(f"Name: {row[1]}")
            print(f"Provider: {row[2]}")
            print(f"Connectivity Config: {row[3]}")
        else:
            print("Agent not found in DB.")

if __name__ == "__main__":
    asyncio.run(check())
