"""
Dependency Injection Configuration.
Provides repositories and services to Interface endpoints.
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.database.session import get_db_session
from backend.domain.ports.persistence_port import CallRepository, AgentRepository
from backend.infrastructure.database.repositories import SqlAlchemyCallRepository, SqlAlchemyAgentRepository

# Repository Providers

async def get_call_repository(
    db: AsyncSession = Depends(get_db_session)
) -> CallRepository:
    """Provide CallRepository implementation."""
    return SqlAlchemyCallRepository(db)

async def get_agent_repository(
    db: AsyncSession = Depends(get_db_session)
) -> AgentRepository:
    """Provide AgentRepository implementation."""
    return SqlAlchemyAgentRepository(db)
