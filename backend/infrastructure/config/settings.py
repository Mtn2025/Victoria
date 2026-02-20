"""
Application Settings.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """
    GROQ_API_KEY: Optional[str] = None
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
    
    # --- Database config (Punto A6) ---
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: Optional[str] = None
    
    DATABASE_URL: Optional[str] = None

    @model_validator(mode='after')
    def assemble_db_url(self) -> 'Settings':
        """Assembles database URL from POSTGRES_ variables if DATABASE_URL is not provided directly."""
        if not self.DATABASE_URL:
            if self.POSTGRES_USER and self.POSTGRES_SERVER and self.POSTGRES_DB:
                pwd = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
                self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}{pwd}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            else:
                # Default fallback
                self.DATABASE_URL = "sqlite+aiosqlite:///data/victoria.db" if self.ENVIRONMENT == "production" else "sqlite+aiosqlite:///./victoria.db"
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
