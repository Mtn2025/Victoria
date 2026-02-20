
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.database.models import Base, CallModel, AgentModel, TranscriptModel
from backend.infrastructure.database.models.call import CallModel
from backend.infrastructure.database.models.agent import AgentModel
from backend.infrastructure.database.models.transcript import TranscriptModel
from datetime import datetime

# Use in-memory SQLite for strict isolation
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Test database session with fresh schema."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_all_models_create(db_session):
    """Test that all models can be created and persisted."""
    # Agent
    agent = AgentModel(
        name="Test Agent",
        system_prompt="Test Prompt",
        voice_provider="azure",
        voice_name="en-US-JennyNeural",
        voice_style="frendly",
        voice_speed=1.0,
        voice_pitch=0.0,
        voice_volume=100.0,
        first_message="Hello",
        silence_timeout_ms=1000,
        tools_config={},
        llm_config={"model": "llama3"}
    )
    db_session.add(agent)
    db_session.commit()
    assert agent.id is not None
    
    # Call with Agent relationship
    call = CallModel(
        session_id="test-session-123",
        agent_id=agent.id,
        status="initiated",
        phone_number="+1234567890",
        client_type="twilio",
        start_time=datetime.utcnow()
    )
    db_session.add(call)
    db_session.commit()
    assert call.id is not None
    assert call.agent.name == "Test Agent"
    
    # Transcript with Call relationship
    transcript = TranscriptModel(
        call_id=call.id,
        role="user",
        content="Hello Agent",
        timestamp=datetime.utcnow()
    )
    db_session.add(transcript)
    db_session.commit()
    assert transcript.id is not None
    assert transcript.call.session_id == "test-session-123"

def test_constraints_and_indexes(db_session):
    """Verify key constraints behave as expected."""
    # Unique constraint on session_id
    call1 = CallModel(session_id="unique-id", status="init")
    db_session.add(call1)
    db_session.commit()
    
    call2 = CallModel(session_id="unique-id", status="dup")
    db_session.add(call2)
    try:
        db_session.commit()
        pytest.fail("Should have raised IntegrityError for unique session_id")
    except Exception:
        db_session.rollback()

def test_cascade_orphans(db_session):
    """Test cascade delete (if configured)."""
    # Assuming CallModel -> TranscriptModel has cascade
    agent = AgentModel(
        name="Agent X",
        system_prompt="Required Prompt",
        # other fields rely on defaults or are optional, but let's be safe
        voice_provider="azure",
        voice_name="en-US-JennyNeural",
        voice_style="frendly",
        voice_speed=1.0,
        voice_pitch=0.0,
        voice_volume=100.0,
        first_message="Hello",
        silence_timeout_ms=1000,
        tools_config={},
        llm_config={}
    )
    db_session.add(agent)
    db_session.commit()
    
    call = CallModel(session_id="cascade-test", agent_id=agent.id)
    db_session.add(call)
    db_session.commit()
    
    transcript = TranscriptModel(call_id=call.id, role="system", content="hi")
    db_session.add(transcript)
    db_session.commit()
    
    # Delete Call
    db_session.delete(call)
    db_session.commit()
    
    # Verify Transcript is deleted
    t = db_session.query(TranscriptModel).filter_by(id=transcript.id).first()
    assert t is None, "Transcript should be deleted by cascade"
