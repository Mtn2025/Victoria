import sqlite3
import os

VICTORIA_DB = "victoria.db"
LEGACY_DB_1 = "C:/Users/Martin/Desktop/Asistente Andrea/asistente.db"
LEGACY_DB_2 = "C:/Users/Martin/Desktop/Asistente Andrea/instance/app.db"

def inspect_db(db_path, label):
    print(f"\n--- Inspector: {label} ({db_path}) ---")
    if not os.path.exists(db_path):
        print("❌ File not found")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tablas encontradas: {len(tables)}")
        
        for table in tables:
            t_name = table[0]
            if t_name == "sqlite_sequence": continue
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
            count = cursor.fetchone()[0]
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({t_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"  - {t_name}: {count} rows. Cols: {columns}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error inspecting {label}: {e}")

if __name__ == "__main__":
    inspect_db(VICTORIA_DB, "VICTORIA")
    inspect_db(LEGACY_DB_1, "LEGACY (Root)")
    inspect_db("temp_legacy.db", "TEMP LEGACY (Local)")
    inspect_db(LEGACY_DB_2, "LEGACY (Instance)")
