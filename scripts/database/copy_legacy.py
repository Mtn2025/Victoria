import shutil
import os
import glob

SOURCE_DIR = "C:/Users/Martin/Desktop/Asistente Andrea"
SOURCE_DB = "asistente.db"
DEST = "temp_legacy.db"

def copy_db():
    src_path = os.path.join(SOURCE_DIR, SOURCE_DB)
    if not os.path.exists(src_path):
        print(f"❌ Source not found: {src_path}")
        return

    # Copy main file
    print(f"Copying {src_path} to {DEST}...")
    shutil.copy2(src_path, DEST)
    
    # Copy WAL/SHM if exist
    for ext in [".wal", ".shm"]:
        wal_src = src_path + ext
        if os.path.exists(wal_src):
            print(f"Copying {wal_src}...")
            shutil.copy2(wal_src, DEST + ext)
            
    print(f"✅ Copied. Size: {os.path.getsize(DEST)} bytes")

if __name__ == "__main__":
    copy_db()
