from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.infrastructure.database.session import get_db_session
import logging

router = APIRouter(prefix="/health", tags=["monitoring"])
logger = logging.getLogger(__name__)

@router.get("/live")
async def liveness_probe():
    """
    K8s Liveness Probe.
    Returns 200 if the service is running.
    """
    return {"status": "ok", "service": "victoria-backend"}

@router.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db_session)):
    """
    K8s Readiness Probe.
    Checks dependencies: Database.
    """
    try:
        # Simple query to check DB connection
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}
