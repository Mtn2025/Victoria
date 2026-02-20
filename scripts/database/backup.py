import shutil
import os
from datetime import datetime
from pathlib import Path
from backend.infrastructure.config.settings import settings

def backup_database():
    """
    Create a timestamped backup of the SQLite database.
    """
    # Parse DB path from URL (naive implementation for sqlite)
    # url format: sqlite+aiosqlite:///./victoria.db
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"victoria_backup_{timestamp}.db"
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created successfully: {backup_path}")
        
        # Cleanup old backups (keep last 5)
        backups = sorted(backup_dir.glob("victoria_backup_*.db"), key=os.path.getmtime)
        while len(backups) > 5:
            oldest = backups.pop(0)
            os.remove(oldest)
            print(f"🗑️ Removed old backup: {oldest}")
            
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    backup_database()
