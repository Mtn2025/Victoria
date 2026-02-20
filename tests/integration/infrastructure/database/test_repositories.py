import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.infrastructure.database.repositories.call_repository import SqlAlchemyCallRepository
from backend.infrastructure.database.repositories.agent_repository import SqlAlchemyAgentRepository
from backend.domain.entities.call import Call, CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig

@pytest.fixture
def test_agent():
    return Agent(
        name="TestAgentRepo",
        system_prompt="You are a test agent.",
        voice_config=VoiceConfig(name="en-US-Neural"),
        first_message="Hello Test"
    )

@pytest.fixture
def test_call(test_agent):
    return Call(
        id=CallId("call-repo-test-1"),
        agent=test_agent,
        conversation=Conversation(),
        start_time=datetime.now(timezone.utc),
        status=CallStatus.INITIATED,
        metadata={"client_type": "integration_test"}
    )

@pytest.mark.asyncio
async def test_agent_repository_lifecycle(async_db_session: AsyncSession, test_agent: Agent):
    repo = SqlAlchemyAgentRepository(async_db_session)
    
    # 1. Update (Upsert)
    await repo.update_agent(test_agent)
    
    # 2. Get
    retrieved = await repo.get_agent(test_agent.name)
    assert retrieved is not None
    assert retrieved.name == test_agent.name
    assert retrieved.system_prompt == test_agent.system_prompt
    assert retrieved.first_message == test_agent.first_message

@pytest.mark.asyncio
async def test_call_repository_lifecycle(async_db_session: AsyncSession, test_call: Call):
    repo = SqlAlchemyCallRepository(async_db_session)
    agent_repo = SqlAlchemyAgentRepository(async_db_session)
    
    # Ensure agent exists first (FK constraint usually, though repository handles linking)
    await agent_repo.update_agent(test_call.agent)
    
    # 1. Save
    await repo.save(test_call)
    
    # 2. Get by ID
    retrieved = await repo.get_by_id(test_call.id)
    assert retrieved is not None
    assert retrieved.id.value == test_call.id.value
    assert retrieved.status == CallStatus.INITIATED
    
    # 3. Update status
    test_call.start() # Sets to IN_PROGRESS
    await repo.save(test_call)
    
    retrieved_2 = await repo.get_by_id(test_call.id)
    assert retrieved_2.status == CallStatus.IN_PROGRESS
    
    # 4. Get List
    calls, total = await repo.get_calls(limit=10, offset=0)
    assert total >= 1
    assert len(calls) >= 1
    assert calls[0].id.value == test_call.id.value
