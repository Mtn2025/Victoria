
import pytest
import pytest_asyncio
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.infrastructure.database.models import Base
from backend.infrastructure.database.repositories import SqlAlchemyCallRepository, SqlAlchemyAgentRepository
from backend.domain.entities.call import Call, CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.conversation_turn import ConversationTurn
from backend.domain.value_objects.voice_config import VoiceConfig

DB_FILE = "test_call_integration.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    if os.path.exists(DB_FILE):
        try: os.remove(DB_FILE)
        except: pass
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    if os.path.exists(DB_FILE):
        try: os.remove(DB_FILE)
        except: pass

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    SessionLocal = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_agent():
    return Agent(name="CallAgent", system_prompt="x", voice_config=VoiceConfig(name="v"))

@pytest.mark.asyncio
async def test_save_and_get_call_full_graph(db_session, sample_agent):
    """Verify saving a Call preserves relationships (Agent + Transcripts)."""
    call_repo = SqlAlchemyCallRepository(db_session)
    agent_repo = SqlAlchemyAgentRepository(db_session)
    
    # 1. Persist Agent first
    await agent_repo.update_agent(sample_agent)
    
    # 2. Create Call with Transcripts
    call_id = CallId(str(uuid.uuid4()))
    conv = Conversation()
    conv.add_turn(ConversationTurn(role="user", content="Hello"))
    conv.add_turn(ConversationTurn(role="assistant", content="Hi there"))
    
    call = Call(id=call_id, agent=sample_agent, conversation=conv, status=CallStatus.IN_PROGRESS)
    call.metadata = {"priority": "high", "client_type": "twilio"} # Mock metadata injection for strict checking
    
    await call_repo.save(call)
    
    # 3. Retrieve
    retrieved = await call_repo.get_by_id(call_id)
    
    assert retrieved is not None
    assert retrieved.id == call_id
    assert retrieved.status == CallStatus.IN_PROGRESS
    assert retrieved.agent.name == "CallAgent"
    assert len(retrieved.conversation.turns) == 2
    assert retrieved.conversation.turns[0].content == "Hello"
    assert retrieved.conversation.turns[1].role == "assistant"
    # Metadata check
    assert retrieved.metadata.get("priority") == "high"

@pytest.mark.asyncio
async def test_get_calls_pagination_and_filter(db_session, sample_agent):
    """Verify filtering by client_type and pagination."""
    call_repo = SqlAlchemyCallRepository(db_session)
    agent_repo = SqlAlchemyAgentRepository(db_session)
    await agent_repo.update_agent(sample_agent)
    
    # Create 3 calls: 2 twilio, 1 web
    base_time = datetime.utcnow()
    
    for i, c_type in enumerate(["twilio", "twilio", "web"]):
        cid = CallId(str(uuid.uuid4()))
        c = Call(id=cid, agent=sample_agent, conversation=Conversation())
        c.start_time = base_time - timedelta(minutes=i) # Diff start times
        c.end_time = datetime.utcnow()
        # In domain model, client_type is usually in metadata or derived. 
        # The repo implementation looks at metadata['client_type'] to populate the DB column.
        c.metadata = {"client_type": c_type} 
        await call_repo.save(c)
        
    # Test Filter: Twilio
    results, total = await call_repo.get_calls(limit=10, client_type="twilio")
    assert total == 2
    assert len(results) == 2
    assert all(r.metadata.get("client_type") == "twilio" for r in results)
    
    # Test Filter: Web
    results_web, total_web = await call_repo.get_calls(limit=10, client_type="web")
    assert total_web == 1
    
    # Test Pagination (All)
    results_page, total_all = await call_repo.get_calls(limit=1, offset=0, client_type="all")
    assert total_all == 3
    assert len(results_page) == 1

@pytest.mark.asyncio
async def test_delete_call(db_session, sample_agent):
    """Verify delete operation."""
    call_repo = SqlAlchemyCallRepository(db_session)
    agent_repo = SqlAlchemyAgentRepository(db_session)
    await agent_repo.update_agent(sample_agent)
    
    cid = CallId(str(uuid.uuid4()))
    c = Call(id=cid, agent=sample_agent, conversation=Conversation())
    await call_repo.save(c)
    
    # Verify exists
    assert await call_repo.get_by_id(cid) is not None
    
    # Delete
    await call_repo.delete(cid)
    
    # Verify gone
    assert await call_repo.get_by_id(cid) is None
