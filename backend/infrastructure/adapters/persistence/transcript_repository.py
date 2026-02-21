"""
SQLAlchemy Transcript Repository - Implementation of TranscriptRepositoryPort.

Hexagonal Architecture: Infrastructure adapter for transcript persistence.
Uses async queue pattern for non-blocking transcript saves.
"""
import asyncio
import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.ports.transcript_repository_port import TranscriptRepositoryPort

logger = logging.getLogger(__name__)


class SQLAlchemyTranscriptRepository(TranscriptRepositoryPort):
    """
    SQLAlchemy implementation of transcript repository.
    
    Features:
    - Async queue to prevent blocking main loop during high traffic
    - Background worker for batch processing
    - Graceful degradation on persistence errors
    
    Use case:
        >>> repo = SQLAlchemyTranscriptRepository(session_factory)
        >>> await repo.start_worker()  # Start background processor
        >>> await repo.save(call_id=123, role="user", content="Hello")
        >>> await repo.save(call_id=123, role="assistant", content="Hi there!")
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initialize transcript repository.
        
        Args:
            session_factory: Callable that returns AsyncSession
                           (e.g., from backend.infrastructure.database.session)
        """
        self.session_factory = session_factory
        # Async Queue for non-blocking persistence
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    async def start_worker(self):
        """Start the background persistence worker."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("📝 Transcript persistence worker started")

    async def save(self, call_id: str, role: str, content: str) -> None:
        """
        Enqueue transcript for async saving.
        
        Non-blocking operation - transcript is queued and persisted
        by background worker.
        """
        if not call_id:
            logger.warning(f"⚠️ Cannot save transcript: No Call ID (role={role})")
            return

        # Ensure worker is running (lazy init)
        if self._worker_task is None:
            await self.start_worker()

        # Non-blocking enqueue
        try:
            self._queue.put_nowait((call_id, role, content))
        except Exception as e:
            logger.error(f"❌ Failed to enqueue transcript: {e}")

    async def _worker_loop(self):
        """
        Background loop to process transcript queue.
        
        Runs continuously, processing transcripts from queue
        and persisting to database.
        """
        logger.info("📝 Transcript persistence worker started")
        while True:
            try:
                call_id, role, content = await self._queue.get()

                # Persist to database
                try:
                    async with self.session_factory() as session:
                        await self._persist_transcript(
                            session=session,
                            call_id=call_id,
                            role=role,
                            content=content
                        )
                except Exception as e:
                    logger.error(f"❌ DB Error saving transcript: {e}")

                self._queue.task_done()

            except asyncio.CancelledError:
                logger.info("📝 Transcript worker shutting down")
                break
            except Exception as e:
                logger.error(f"❌ Transcript worker error: {e}")
                await asyncio.sleep(1)  # Backoff on error

    async def _persist_transcript(
        self,
        session: AsyncSession,
        call_id: str,
        role: str,
        content: str
    ):
        """
        Persist single transcript to database.
        
        Uses Victoria's TranscriptModel to insert into transcripts table.
        First resolves session_id (str) to DB PK (int).
        """
        from backend.infrastructure.database.models import TranscriptModel, CallModel
        from sqlalchemy import select
        from datetime import datetime, timezone
        
        try:
            # Resolve session_id (UUID string) to internal DB ID (int)
            stmt = select(CallModel.id).where(CallModel.session_id == call_id)
            result = await session.execute(stmt)
            db_id = result.scalar_one_or_none()
            
            if not db_id:
                logger.warning(f"⚠️ Transcript skipped: Call {call_id} not found in DB")
                return

            # Create transcript entry
            transcript = TranscriptModel(
                call_id=db_id,
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc)
            )
            
            session.add(transcript)
            await session.commit()
            
            logger.debug(
                f"✅ [Transcript] Persisted: call_id={call_id} (pk={db_id}), "
                f"role={role}, content_len={len(content)}"
            )
        except Exception as e:
            # logger.error(f"❌ Failed to persist transcript: {e}") # Let caller handle logging
            await session.rollback()
            raise
