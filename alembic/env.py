"""
Alembic environment — async mode for asyncpg (production PostgreSQL).

Uses async_engine_from_config so that asyncpg drivers work correctly.
The DATABASE_URL is read from os.environ at runtime — never hardcoded.
"""
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project root to sys.path so backend.* imports work
sys.path.append(os.getcwd())

# Alembic Config object — provides access to values in alembic.ini
config = context.config

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all SQLAlchemy models so Alembic's autogenerate can detect them
from backend.infrastructure.database.models import Base  # noqa: E402

target_metadata = Base.metadata


def get_url() -> str:
    """
    Return the database URL for Alembic migrations.

    Priority:
    1. DATABASE_URL environment variable (production / Coolify)
    2. settings.DATABASE_URL (fallback — works for local dev with .env)

    The URL must use a synchronous or async-compatible driver.
    For asyncpg URLs (postgresql+asyncpg://...) we keep them as-is
    because async_engine_from_config handles the async driver natively.

    For aiosqlite URLs (sqlite+aiosqlite://...) used in CI we strip
    the +aiosqlite suffix so SQLite works with the sync offline mode.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fallback: read from settings (picks up .env / .env.local)
        from backend.infrastructure.config.settings import settings
        url = settings.DATABASE_URL

    # aiosqlite → sqlite for offline/sync compatibility
    # asyncpg stays as-is — async_engine_from_config supports it natively
    url = url.replace("+aiosqlite", "")
    return url


# --------------------------------------------------------------------------- #
# Offline mode (generates SQL without a live DB connection)                    #
# --------------------------------------------------------------------------- #

def run_migrations_offline() -> None:
    """Emit migration SQL to stdout without connecting to the database."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# --------------------------------------------------------------------------- #
# Online mode (runs against a live DB via asyncpg)                             #
# --------------------------------------------------------------------------- #

def do_run_migrations(connection) -> None:
    """Run migrations synchronously within an async connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations.

    Uses NullPool so that the engine is fully disposed after the migration
    run — no connection leaks in a one-shot container startup.
    """
    # Override the sqlalchemy.url from alembic.ini with the real env URL
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration — wraps the async run in asyncio."""
    asyncio.run(run_async_migrations())


# --------------------------------------------------------------------------- #
# Dispatch                                                                      #
# --------------------------------------------------------------------------- #

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
