"""
Repository Factory - Creates and configures repository instances.

Hexagonal Architecture: Infrastructure factory for repository dependency injection.
"""
import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.ports.config_repository_port import ConfigRepositoryPort
from backend.domain.ports.transcript_repository_port import TranscriptRepositoryPort
from backend.infrastructure.adapters.persistence.config_repository import SQLAlchemyConfigRepository
from backend.infrastructure.adapters.persistence.transcript_repository import SQLAlchemyTranscriptRepository

logger = logging.getLogger(__name__)


def create_config_repository(
    session_factory: Callable[[], AsyncSession]
) -> ConfigRepositoryPort:
    """
    Create config repository instance.
    
    Args:
        session_factory: Async SQLAlchemy session factory
        
    Returns:
        ConfigRepositoryPort implementation
        
    Example:
        >>> from backend.infrastructure.database.session import get_async_session
        >>> config_repo = create_config_repository(get_async_session)
        >>> config = await config_repo.get_config("default")
    """
    repo = SQLAlchemyConfigRepository(session_factory)
    logger.info("✅ Config repository created")
    return repo


async def create_transcript_repository(
    session_factory: Callable[[], AsyncSession]
) -> TranscriptRepositoryPort:
    """
    Create and initialize transcript repository.
    
    Args:
        session_factory: Async SQLAlchemy session factory
        
    Returns:
        TranscriptRepositoryPort implementation with worker started
        
    Example:
        >>> repo = await create_transcript_repository(session_factory)
        >>> await repo.save(call_id=123, role="user", content="Hello")
    """
    repo = SQLAlchemyTranscriptRepository(session_factory)
    await repo.start_worker()
    logger.info("✅ Transcript repository created with worker started")
    return repo
