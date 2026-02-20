import asyncio
import sys
import os

# Add the root directory to sys.path so backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.infrastructure.database.session import AsyncSessionLocal
from backend.infrastructure.database.models.agent import AgentModel
from sqlalchemy.future import select

async def seed_default_agent():
    print("🌱 Iniciando seeder del agente por defecto...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if default agent exists
            result = await session.execute(select(AgentModel).where(AgentModel.name == "default"))
            existing_agent = result.scalar_one_or_none()

            if existing_agent:
                print(f"✅ El agente '{existing_agent.name}' ya existe en la base de datos (ID: {existing_agent.id}). No se requiere acción.")
                return

            # Create default agent
            print("Creando agente 'default'...")
            default_agent = AgentModel(
                name="default",
                system_prompt=(
                    "Eres Victoria, un asistente virtual profesional y amable. "
                    "Responde siempre de forma concisa, educada y útil. "
                    "Tu objetivo es ayudar al usuario con su consulta de forma eficiente."
                ),
                voice_provider="azure",
                voice_name="es-MX-DaliaNeural", # Default Azure Voice
                voice_style="chat",
                voice_speed=1.0,
                voice_pitch=0.0,
                voice_volume=100.0,
                first_message="Hola, soy Victoria. ¿En qué puedo ayudarte hoy?",
                silence_timeout_ms=1000,
                # JSON fields empty or with default structure
                tools_config={},
                llm_config={"model": "llama3-70b-8192", "temperature": 0.5}
            )

            session.add(default_agent)
            await session.commit()
            print(f"🎉 ¡Agente 'default' creado exitosamente! (ID asignado: {default_agent.id})")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error al crear el agente: {e}")
        finally:
            await session.close()

if __name__ == "__main__":
    # Workaround for async event loop in Windows vs Linux
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(seed_default_agent())
