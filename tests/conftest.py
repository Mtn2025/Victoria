import pytest
import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Add backend to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.infrastructure.database.models import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh in-memory SQLite database for each test function.
    Yields an AsyncSession.
    """
    # Use aiosqlite for async sqlite
    from sqlalchemy.pool import StaticPool
    # Use aiosqlite for async sqlite with StaticPool for shared memory state
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", 
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Session Maker
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback() # Rollback to ensure clean slate if needed, though memory DB is fresh? 
        # Actually with :memory:, each engine connect might be fresh IF we recreated engine.
        # But we create engine inside fixture. Scope is function. 
        # So each test gets a NEW engine = NEW in-memory DB.
        
    await engine.dispose()

@pytest.fixture
def mock_call_id_value():
    return "call-12345-abcde"

@pytest.fixture
def mock_phone_number_value():
    return "+15550001234"

@pytest.fixture(autouse=True)
def mock_redis():
    """
    Global Redis mock to prevent connection attempts in all tests (Unit, Integration, E2E).
    Patches redis.from_url to return an AsyncMock.
    """
    from unittest.mock import AsyncMock, patch, MagicMock
    
    # Create a mock Redis client
    # Create a mock Redis client
    mock_client = AsyncMock()
    redis_data = {}
    
    async def get_mock(key):
        return redis_data.get(key)
        
    async def set_mock(key, value, ttl=None):
        redis_data[key] = value
        return True
        
    async def setex_mock(key, ttl, value):
        redis_data[key] = value
        return True
        
    async def delete_mock(*keys):
        count = 0
        for k in keys:
             if k in redis_data:
                 del redis_data[k]
                 count += 1
        return count
    
    mock_client.get.side_effect = get_mock
    mock_client.set.side_effect = set_mock
    mock_client.setex.side_effect = setex_mock
    mock_client.delete.side_effect = delete_mock
    mock_client.ping.return_value = True
    mock_client.close.return_value = None
    
    # Mock scan_iter (async generator)
    async def mock_scan_iter(match=None, **kwargs):
        # Simple glob matching if needed, or just yield all keys
        for k in redis_data:
            yield k
    mock_client.scan_iter.side_effect = mock_scan_iter

    # Patch redis.from_url where it is used in the codebase
    # Note: redis_client.py imports 'redis.asyncio' as 'redis' (if installed)
    # We patch the module where RedisClient defines it.
    with patch("backend.infrastructure.cache.redis_client.redis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_client
        yield mock_client
