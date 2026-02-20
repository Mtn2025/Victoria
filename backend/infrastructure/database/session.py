"""
Database Session Management.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
from collections.abc import AsyncGenerator
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.infrastructure.config.settings import settings

# Create Async Engine
# echo=False in production, can be set to True for debugging
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
import os
print(f"DEBUG: Session Engine initialized with URL: {settings.DATABASE_URL}, CWD: {os.getcwd()}")

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    Dependency to get a database session.
    Yields an AsyncSession and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
