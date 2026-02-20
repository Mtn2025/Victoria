
import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.infrastructure.database.models import Base
from backend.infrastructure.database.repositories import SqlAlchemyAgentRepository
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

# Use a distinct file for Agent tests to ensure isolation if running in parallel
DB_FILE = "test_agent_integration.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create engine and tables once per module."""
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except PermissionError:
            pass
        
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    await engine.dispose()
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except PermissionError:
            pass

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Provide a session for each test."""
    SessionLocal = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_create_new_agent(db_session):
    """Verify creating a new agent from domain entity."""
    repo = SqlAlchemyAgentRepository(db_session)
    
    voice = VoiceConfig(name="azure-1", style="cheerful", speed=1.1)
    agent = Agent(
        name="AgentZero", 
        system_prompt="You are a test helper.", 
        voice_config=voice,
        first_message="Hello!",
        silence_timeout_ms=500
    )
    
    # Action
    await repo.update_agent(agent)
    
    # Verify
    retrieved = await repo.get_agent("AgentZero")
    assert retrieved is not None
    assert retrieved.name == "AgentZero"
    assert retrieved.system_prompt == "You are a test helper."
    assert retrieved.voice_config.name == "azure-1"
    assert retrieved.voice_config.speed == 1.1
    assert retrieved.silence_timeout_ms == 500

@pytest.mark.asyncio
async def test_update_existing_agent(db_session):
    """Verify updating fields of an existing agent."""
    repo = SqlAlchemyAgentRepository(db_session)
    
    # Setup
    voice = VoiceConfig(name="azure-1")
    agent = Agent(name="AgentUpdate", system_prompt="Old Prompt", voice_config=voice)
    await repo.update_agent(agent)
    
    # Action: Change Prompt and Voice
    agent.system_prompt = "New Prompt"
    agent.voice_config = VoiceConfig(name="azure-2", pitch=5.0)
    await repo.update_agent(agent)
    
    # Verify
    updated = await repo.get_agent("AgentUpdate")
    assert updated.system_prompt == "New Prompt"
    assert updated.voice_config.name == "azure-2"
    assert updated.voice_config.pitch == 5.0

@pytest.mark.asyncio
async def test_persist_json_configs(db_session):
    """Verify JSON fields (tools, llm_config) are persisted."""
    repo = SqlAlchemyAgentRepository(db_session)
    
    tools = [{"type": "function", "name": "get_weather"}]
    llm_config = {"model": "llama-3", "temperature": 0.7}
    voice = VoiceConfig(name="azure-json")
    
    agent = Agent(name="AgentJSON", system_prompt=".", tools=tools, llm_config=llm_config, voice_config=voice)
    
    await repo.update_agent(agent)
    
    fetched = await repo.get_agent("AgentJSON")
    assert fetched.llm_config["model"] == "llama-3"
    assert len(fetched.tools) == 1
    assert fetched.tools[0]["name"] == "get_weather"
