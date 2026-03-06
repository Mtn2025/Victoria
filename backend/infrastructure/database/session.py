"""
Database Session Management.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.infrastructure.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Determine engine arguments
engine_kwargs = {
    "echo": False,
    "future": True,
}

# Only PostgreSQL supports pool_size and max_overflow in AsyncEngine default pools
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
    engine_kwargs["pool_size"] = 10
    engine_kwargs["pool_timeout"] = 30
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 1800  # recycle connections every 30 min

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
logger.info("✅ [DB] AsyncEngine initialized (pool_size=10, max_overflow=20)")

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency — yields an AsyncSession and ensures cleanup.

    NOTE: AsyncSessionLocal() is used as an async context manager.
    Its __aexit__ already calls session.close().
    We must NOT call session.close() explicitly in the finally block,
    or SQLAlchemy raises:
      IllegalStateChangeError: Method 'close()' can't be called here;
      method '_connection_for_bind()' is already in progress
    """
    async with AsyncSessionLocal() as session:
        yield session
        # ← session.close() NOT called here: async with handles it
