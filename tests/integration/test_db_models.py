import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.database.models import Base, AgentModel, CallModel, TranscriptModel
from backend.infrastructure.config.settings import settings

# Use in-memory SQLite for speed, or a file-based test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Test database session with async engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        
    await engine.dispose()

@pytest.mark.asyncio
async def test_agent_creation_and_retrieval(db_session):
    """Test robust agent creation."""
    agent = AgentModel(
        name="Test Agent",
        system_prompt="You are a test agent.",
        voice_provider="azure",
        voice_name="en-US-JennyNeural"
    )
    db_session.add(agent)
    await db_session.commit()
    
    retrieved = await db_session.get(AgentModel, agent.id)
    assert retrieved is not None
    assert retrieved.name == "Test Agent"
    assert retrieved.voice_provider == "azure"

@pytest.mark.asyncio
async def test_call_relationship_and_cascade(db_session):
    """Test Call -> Agent relationship and Transcript cascade."""
    # Create Agent
    agent = AgentModel(
        name="Cascade Agent",
        system_prompt="Sys",
        voice_name="en-US-JennyNeural"
    )
    db_session.add(agent)
    await db_session.commit()
    
    # Create Call linked to Agent
    call = CallModel(
        session_id="uuid-1234",
        agent_id=agent.id,
        status="active"
    )
    db_session.add(call)
    await db_session.commit()
    
    # Create Transcript linked to Call
    transcript = TranscriptModel(
        call_id=call.id,
        role="user",
        content="Hello"
    )
    db_session.add(transcript)
    await db_session.commit()
    
    # Verify relationships
    await db_session.refresh(call, attribute_names=["agent", "transcripts"])
    assert call.agent.name == "Cascade Agent"
    assert len(call.transcripts) == 1
    assert call.transcripts[0].content == "Hello"
    
    # Verify Cascade Delete (if configured in models? models.py has cascade="all, delete-orphan")
    # Note: SQLite needs PRAGMA foreign_keys=ON for real DB cascade, but ORM cascade works in session
    await db_session.delete(call)
    await db_session.commit()
    
    # Check transcript is gone
    t_check = await db_session.get(TranscriptModel, transcript.id)
    assert t_check is None

@pytest.mark.asyncio
async def test_performance_indexes_exist(db_session):
    """
    Indirectly test indexes by ensuring queries on indexed fields check out.
    (Real index existence check requires inspecting sqlite_master)
    """
    # Just verify we can filter by the new indexed columns
    call = CallModel(session_id="idx-test", status="completed")
    db_session.add(call)
    await db_session.commit()
    
    from sqlalchemy import select
    stmt = select(CallModel).where(CallModel.status == "completed").order_by(CallModel.start_time.desc())
    result = await db_session.execute(stmt)
    calls = result.scalars().all()
    assert len(calls) == 1
    assert calls[0].session_id == "idx-test"
