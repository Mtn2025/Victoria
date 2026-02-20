"""
Integration tests for Repository System.

Tests config and transcript repositories with Victoria DB models.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from backend.domain.ports.config_repository_port import ConfigDTO, ConfigNotFoundException
from backend.domain.ports.transcript_repository_port import TranscriptRepositoryPort
from backend.infrastructure.adapters.persistence.config_repository import SQLAlchemyConfigRepository
from backend.infrastructure.adapters.persistence.transcript_repository import SQLAlchemyTranscriptRepository
from backend.infrastructure.database.models import Base, AgentModel, CallModel, TranscriptModel


@pytest.fixture
def mock_session_factory(async_db_session):
    """
    Creates a session factory that yields the SHARED session.
    Vital for tests where setup and main logic must share a transaction (in-memory DB).
    """
    class SharedSessionContext:
        def __init__(self, session):
            self.session = session
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Do NOT close the shared session here.
            # It is managed by the function-scoped fixture in conftest.
            pass 
    
    return lambda: SharedSessionContext(async_db_session)

@pytest.fixture
async def seed_test_agent(async_db_session):
    """Seed database with test agent."""
    session = async_db_session
    agent = AgentModel(
        name="test_agent",
        system_prompt="You are a test assistant",
        voice_provider="azure",
        voice_name="es-MX-DaliaNeural",
        voice_style="default",
        voice_speed=1.0,
        first_message="Hello!",
        silence_timeout_ms=1000,
        llm_config={
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.7,
            "max_tokens": 600
        },
        tools_config={
            "enabled": True,
            "timeout_ms": 5000
        }
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    
    return agent


@pytest.fixture
async def seed_test_call(async_db_session, seed_test_agent):
    """Seed database with test call."""
    session = async_db_session
    call = CallModel(
        session_id="test-call-123",
        agent_id=seed_test_agent.id,
        status="active",
        phone_number="+1234567890",
        client_type="browser",
        start_time=datetime.utcnow()
    )
    session.add(call)
    await session.commit()
    await session.refresh(call)
    
    return call


class TestConfigRepository:
    """Test config repository integration with AgentModel."""
    
    @pytest.mark.asyncio
    async def test_get_config(self, mock_session_factory, seed_test_agent):
        """Test retrieving config from database."""
        repo = SQLAlchemyConfigRepository(mock_session_factory)
        
        config = await repo.get_config(profile="test_agent")
        
        assert isinstance(config, ConfigDTO)
        assert config.llm_provider == "groq"
        assert config.llm_model == "llama-3.3-70b-versatile"
        assert config.tts_provider == "azure"
        assert config.voice_name == "es-MX-DaliaNeural"
        assert config.async_tools is True
    
    @pytest.mark.asyncio
    async def test_get_config_not_found(self, mock_session_factory):
        """Test error when config profile doesn't exist."""
        repo = SQLAlchemyConfigRepository(mock_session_factory)
        
        with pytest.raises(ConfigNotFoundException):
            await repo.get_config(profile="nonexistent")
    
    @pytest.mark.asyncio
    async def test_update_config(self, mock_session_factory, seed_test_agent):
        """Test updating config in database."""
        repo = SQLAlchemyConfigRepository(mock_session_factory)
        
        updated = await repo.update_config(
            profile="test_agent",
            voice_speed=1.5,
            system_prompt="Updated prompt"
        )
        
        assert updated.voice_speed == 1.5
        
        # Verify persistence
        config = await repo.get_config(profile="test_agent")
        assert config.voice_speed == 1.5
    
    @pytest.mark.asyncio
    async def test_create_config(self, mock_session_factory):
        """Test creating new config profile."""
        repo = SQLAlchemyConfigRepository(mock_session_factory)
        
        new_config = ConfigDTO(
            llm_provider="openai",
            llm_model="gpt-4",
            tts_provider="elevenlabs",
            voice_name="Rachel",
            system_prompt="New agent prompt"
        )
        
        created = await repo.create_config(profile="new_agent", config=new_config)
        
        assert created.llm_provider == "openai"
        assert created.llm_model == "gpt-4"
        
        # Verify can retrieve
        retrieved = await repo.get_config(profile="new_agent")
        assert retrieved.llm_provider == "openai"


class TestTranscriptRepository:
    """Test transcript repository integration with TranscriptModel."""
    
    @pytest.mark.asyncio
    async def test_save_transcript(self, mock_session_factory, seed_test_call, async_db_session):
        """Test saving transcript to database."""
        repo = SQLAlchemyTranscriptRepository(mock_session_factory)
        await repo.start_worker()
        
        # Save transcript
        await repo.save(
            call_id=seed_test_call.session_id,
            role="user",
            content="Hello, how are you?"
        )
        
        # Wait for async processing
        await repo._queue.join()
        
        # Verify in database
        from sqlalchemy import select
        
        result = await async_db_session.execute(
            select(TranscriptModel).where(TranscriptModel.call_id == seed_test_call.id)
        )
        transcripts = result.scalars().all()
        
        assert len(transcripts) == 1
        assert transcripts[0].role == "user"
        assert transcripts[0].content == "Hello, how are you?"
    
    @pytest.mark.asyncio
    async def test_save_multiple_transcripts(self, mock_session_factory, seed_test_call, async_db_session):
        """Test saving multiple transcripts asynchronously."""
        repo = SQLAlchemyTranscriptRepository(mock_session_factory)
        await repo.start_worker()
        
        # Save multiple
        await repo.save(seed_test_call.session_id, "user", "First message")
        await repo.save(seed_test_call.session_id, "assistant", "Response")
        await repo.save(seed_test_call.session_id, "user", "Follow up")
        
        # Wait for processing
        await repo._queue.join()
        
        # Verify in database
        from sqlalchemy import select
        
        result = await async_db_session.execute(
            select(TranscriptModel).where(TranscriptModel.call_id == seed_test_call.id)
        )
        transcripts = result.scalars().all()
        
        # Sort by id or insertion order
        # Assuming order is preserved
        assert len(transcripts) == 3
        # We can't guarantee order without order_by, but likely reliable in single thread test
    
    @pytest.mark.asyncio
    async def test_save_without_call_id(self, mock_session_factory):
        """Test graceful handling when call_id is missing."""
        repo = SQLAlchemyTranscriptRepository(mock_session_factory)
        await repo.start_worker()
        
        # Should log warning, not crash
        await repo.save(call_id=0, role="user", content="Test")
        await repo.save(call_id=None, role="user", content="Test 2")
        
        # Queue should be empty (messages not queued)
        assert repo._queue.qsize() == 0
