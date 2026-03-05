import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=".env")

from infrastructure.database.session import AsyncSessionLocal
from infrastructure.database.models.agent import AgentModel
from sqlalchemy import select

async def migrate_telnyx_keys():
    print("Iniciando migración de llaves camelCase a snake_case E2E en DB...")
    async with AsyncSessionLocal() as session:
        stmt = select(AgentModel)
        result = await session.execute(stmt)
        agents = result.scalars().all()
        
        migrated_count = 0
        for agent in agents:
            if agent.connectivity_config is None:
                continue
            
            conn = dict(agent.connectivity_config)
            changed = False
            
            # Mapeo de Telnyx Connection ID
            if "telnyxConnectionId" in conn:
                conn["telnyx_connection_id"] = conn.pop("telnyxConnectionId")
                changed = True
            elif "connection_id" in conn:
                conn["telnyx_connection_id"] = conn.pop("connection_id")
                changed = True
                
            # Mapeo de Telnyx Phone Number
            if "callerIdTelnyx" in conn:
                conn["telnyx_phone_number"] = conn.pop("callerIdTelnyx")
                changed = True
            elif "outbound_phone_number" in conn:
                conn["telnyx_phone_number"] = conn.pop("outbound_phone_number")
                changed = True
                
            # Others
            if "enableRecordingTelnyx" in conn:
                conn["enable_recording_telnyx"] = conn.pop("enableRecordingTelnyx")
                changed = True
            if "recordingChannelsTelnyx" in conn:
                conn["recording_channels_telnyx"] = conn.pop("recordingChannelsTelnyx")
                changed = True
            
            if changed:
                print(f"Migrando agente UUID: {agent.agent_uuid} ({agent.name})")
                print(f" - Configuración vieja: {agent.connectivity_config}")
                print(f" - Configuración nueva: {conn}")
                agent.connectivity_config = conn
                migrated_count += 1
                
        if migrated_count > 0:
            await session.commit()
            print(f"¡Migración exitosa! {migrated_count} agentes actualizados a snake_case.")
        else:
            print("No se encontraron agentes que requieran migración.")

if __name__ == "__main__":
    asyncio.run(migrate_telnyx_keys())
