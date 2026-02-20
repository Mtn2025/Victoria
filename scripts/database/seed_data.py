"""
Seed Data Script.
Populates the database with initial data for development/testing.
SAFETY: 
- Checks `settings.ENVIRONMENT`.
- Aborts if "production".
- Requires manual confirmation or --force flag if not in development.
"""
import sys
import os
import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.getcwd())

from backend.infrastructure.config.settings import settings
from backend.infrastructure.database.models import Base, AgentModel, CallModel, TranscriptModel
from backend.domain.value_objects.voice_config import VoiceConfig
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sync Engine for Seeding
DATABASE_URL = settings.DATABASE_URL.replace("+aiosqlite", "")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def confirm_execution():
    """Ensure we don't accidentally wipe production."""
    env = settings.ENVIRONMENT.lower()
    logger.info(f"Current Environment: {env}")
    
    if env == "production":
        logger.error("❌ CANNOT RUN SEED IN PRODUCTION WITHOUT STRICT OVERRIDE.")
        sys.exit(1)
        
    if env == "staging":
        response = input("⚠️  Running in STAGING. Are you sure? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            sys.exit(0)

def seed_agents(session):
    """Seed initial agents."""
    logger.info("Seeding Agents...")
    
    # Check if agents exist
    count = session.query(AgentModel).count()
    if count > 0:
        logger.info(f"Agents already exist ({count}). Skipping.")
        return

    # Default Agent
    default_agent = AgentModel(
        name="Victoria",
        system_prompt="Eres Victoria, una asistente virtual útil y amable.",
        voice_provider="azure",
        voice_name="en-US-JennyNeural",
        voice_style="frendly",
        voice_speed=1.0,
        voice_pitch=0.0,
        voice_volume=100.0,
        first_message="Hola, soy Victoria. ¿En qué puedo ayudarte?",
        silence_timeout_ms=1000,
        tools_config={},
        llm_config={"model": "llama3-70b-8192"}
    )
    
    session.add(default_agent)
    session.commit()
    logger.info("✅ Created default agent 'Victoria'.")
    return default_agent

def seed_calls_and_transcripts(session, agent):
    """Seed initial calls and transcripts."""
    logger.info("Seeding Calls & Transcripts...")
    
    if session.query(CallModel).count() > 0:
        logger.info("Calls already exist. Skipping.")
        return

    # Create a sample call
    start_time = datetime.utcnow() - timedelta(minutes=5)
    call = CallModel(
        session_id="seed-demo-session-001",
        agent_id=agent.id,
        status="completed",
        phone_number="+15550199",
        client_type="twilio",
        start_time=start_time,
        end_time=datetime.utcnow(),
        metadata_={"demo": True, "environment": settings.ENVIRONMENT}
    )
    session.add(call)
    session.commit()
    logger.info(f"✅ Created sample call {call.session_id}")

    # Create sample transcripts
    transcripts = [
        TranscriptModel(call_id=call.id, role="user", content="Hola Victoria", timestamp=start_time),
        TranscriptModel(call_id=call.id, role="assistant", content="Hola, soy Victoria. ¿En qué puedo ayudarte?", timestamp=start_time + timedelta(seconds=2)),
        TranscriptModel(call_id=call.id, role="user", content="Quiero agendar una cita", timestamp=start_time + timedelta(seconds=5)),
        TranscriptModel(call_id=call.id, role="assistant", content="Claro, ¿para qué día te gustaría?", timestamp=start_time + timedelta(seconds=7)),
    ]
    session.add_all(transcripts)
    session.commit()
    logger.info(f"✅ Created {len(transcripts)} sample transcripts.")

def run_seed():
    parser = argparse.ArgumentParser(description="Seed Database")
    parser.add_argument("--force", action="store_true", help="Force execution")
    args = parser.parse_args()
    
    if not args.force:
        confirm_execution()
        
    session = SessionLocal()
    try:
        agent = seed_agents(session)
        if agent is None:
            # If skipping creation, fetch the existing one
            agent = session.query(AgentModel).filter_by(name="Victoria").first()
        
        if agent:
            seed_calls_and_transcripts(session, agent)
            
        logger.info("✅ Seeding Complete.")
    except Exception as e:
        logger.error(f"❌ Seeding Failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_seed()
