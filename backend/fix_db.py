import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'victoria.db')
print(f"Fixing DB at {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE alembic_version SET version_num='9a2e70821b1c'")
    conn.commit()
    conn.close()
    print("Fixed alembic_version to 9a2e70821b1c")
except Exception as e:
    print(f"Error: {e}")
