import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.append(".")

from backend.infrastructure.database.session import AsyncSessionLocal
from backend.infrastructure.database.models import CallModel

async def cleanup_old_calls(days: int = 30):
    """
    Delete calls older than N days.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    print(f"🧹 Cleaning up calls older than {cutoff_date.isoformat()}...")
    
    async with AsyncSessionLocal() as session:
        stmt = delete(CallModel).where(CallModel.start_time < cutoff_date)
        result = await session.execute(stmt)
        await session.commit()
        
        print(f"✅ Deleted {result.rowcount} old calls.")

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    
    asyncio.run(cleanup_old_calls(days))
