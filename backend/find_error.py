import sys
import traceback

def test_imports():
    try:
        print("Importing config_schemas...")
        import backend.interfaces.http.schemas.config_schemas
        
        print("Importing agents endpoints...")
        import backend.interfaces.http.endpoints.agents
        
        print("Importing domain entities...")
        import backend.domain.entities.agent
        
        print("Importing Value Objects...")
        import backend.domain.value_objects.audio_format
        import backend.domain.value_objects.voice_config
        
        print("Importing DTOS...")
        import backend.domain.ports.config_repository_port
        
        print("All imports successful!")
    except Exception as e:
        print("EXCEPTION CAUGHT!")
        traceback.print_exc()

if __name__ == "__main__":
    test_imports()
