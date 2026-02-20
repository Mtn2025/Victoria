from sqlalchemy import create_engine, inspect, text
import os

DB_PATH = "sqlite:///C:/Users/Martin/Desktop/Asistente Andrea/test_deploy.db"

def inspect_db():
    if not os.path.exists("C:/Users/Martin/Desktop/Asistente Andrea/instance/app.db"):
         print("File not found")
         return
    engine = create_engine(DB_PATH)
    inspector = inspect(engine)
    print(f"Tables in {DB_PATH}:", inspector.get_table_names())
    with engine.connect() as conn:
        for table in inspector.get_table_names():
            if table in ['agent_configs', 'calls', 'transcripts', 'agents']:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"{table}: {count} rows")
                except Exception as e:
                    print(f"{table}: Error {e}")

if __name__ == "__main__":
    inspect_db()
