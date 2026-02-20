"""
Application Settings.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"
    ENVIRONMENT: str = "development" # development, staging, production
    
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: str = "eastus"

    # --- Telephony ---
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    
    TELNYX_API_KEY: Optional[str] = None
    TELNYX_API_BASE: str = "https://api.telnyx.com/v2"
    TELNYX_PUBLIC_KEY: Optional[str] = None
    
    # Webhook Security
    TELEPHONY_WEBHOOK_SECRET: str = "victoria-secret-key-change-me"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./victoria.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
