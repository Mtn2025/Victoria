"""
Migrar datos de Legacy a Victoria.
"""
import logging
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.infrastructure.database.models import Base, AgentModel, CallModel, TranscriptModel
from backend.infrastructure.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy DB Path (Copied locally mainly to avoid path spaces issues)
LEGACY_DB_PATH = "temp_legacy.db"
LEGACY_URL = f"sqlite:///{LEGACY_DB_PATH}"

# Victoria URL (Sync)
VICTORIA_URL = settings.DATABASE_URL.replace("+aiosqlite", "")

def migrate_data():
    if not os.path.exists(LEGACY_DB_PATH):
        logger.error(f"Legacy DB not found at {LEGACY_DB_PATH}")
        return

    logger.info(f"Connecting to Legacy: {LEGACY_URL}")
    logger.info(f"Connecting to Victoria: {VICTORIA_URL}")

    legacy_engine = create_engine(LEGACY_URL)
    victoria_engine = create_engine(VICTORIA_URL)

    LegacySession = sessionmaker(bind=legacy_engine)
    VictoriaSession = sessionmaker(bind=victoria_engine)

    legacy_session = LegacySession()
    victoria_session = VictoriaSession()

    try:
        # 1. Migrate Agents
        logger.info("Migrating Agents...")
        agents = legacy_session.execute(text("SELECT * FROM agent_configs")).fetchall()
        
        for row in agents:
            data = dict(row._mapping)
            # Map legacy columns to Victoria model
            # Legacy has broad columns, Victoria generic ones + JSON configs
            
            # Check if agent exists
            existing = victoria_session.query(AgentModel).filter_by(name=data['name']).first()
            if existing:
                logger.info(f"Skipping existing agent: {data['name']}")
                continue

            new_agent = AgentModel(
                name=data['name'],
                system_prompt=data.get('system_prompt', ''),
                voice_provider=data.get('voice_provider', 'azure'),
                voice_name=data.get('voice_name', 'en-US-JennyNeural'),
                voice_style=data.get('voice_style'),
                voice_speed=data.get('voice_speed', 1.0),
                voice_pitch=data.get('voice_pitch', 0.0),
                voice_volume=data.get('voice_volume', 100.0), # Legacy float/int
                first_message=data.get('first_message', ''),
                silence_timeout_ms=data.get('silence_timeout_ms', 1000),
                # Map other legacy fields to JSON if needed
                # tools_config={}, llm_config={}
            )
            victoria_session.add(new_agent)
        
        victoria_session.commit()
        logger.info(f"✅ Migrated {len(agents)} agents.")

        # 2. Migrate Calls
        logger.info("Migrating Calls...")
        calls = legacy_session.execute(text("SELECT * FROM calls")).fetchall()
        count_calls = 0
        
        # Need agent mapping if IDs differ (they shouldn't if we just inserted, but auto-increment might differ)
        # For simplicity, lookup agent by name or assume single agent if likely.
        # Actually, let's look up agent ID by name from legacy if possible, but legacy uses ID FK.
        # We need a map of older_id -> new_id
        
        agent_map = {} # old_id -> new_id
        # Reload agents from both to build map
        leg_agents = legacy_session.execute(text("SELECT id, name FROM agent_configs")).fetchall()
        for la in leg_agents:
            va = victoria_session.query(AgentModel).filter_by(name=la.name).first()
            if va:
                agent_map[la.id] = va.id

        for row in calls:
            data = dict(row._mapping)
            
            existing = victoria_session.query(CallModel).filter_by(session_id=data['session_id']).first()
            if existing:
                continue

            # Resolve Agent ID
            old_agent_id = data.get('agent_id')
            new_agent_id = agent_map.get(old_agent_id)

            new_call = CallModel(
                session_id=data['session_id'],
                agent_id=new_agent_id,
                status=data.get('status', 'ended'),
                phone_number=data.get('phone_number'),
                client_type=data.get('client_type', 'unknown'),
                start_time=data.get('start_time'), # DateTime conversion might be needed if string
                end_time=data.get('end_time'),
                # metadata_=data.get('metadata') # JSON field
            )
            victoria_session.add(new_call)
            count_calls += 1
            
        victoria_session.commit()
        logger.info(f"✅ Migrated {count_calls} calls.")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        victoria_session.rollback()
        raise
    finally:
        legacy_session.close()
        victoria_session.close()

if __name__ == "__main__":
    migrate_data()
