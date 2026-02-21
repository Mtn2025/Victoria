from backend.infrastructure.config.settings import Settings
try:
    s = Settings()
    print("LOADED ENV:", s.ENVIRONMENT)
except Exception as e:
    import traceback
    traceback.print_exc()
