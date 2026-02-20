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
    VICTORIA_API_KEY: Optional[str] = None
    WS_MEDIA_STREAM_PATH: str = "/ws/media-stream"
    
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
        
        # If DATABASE_URL is already provided and not empty, we MUST use it directly.
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            return self

        # Otherwise, attempt to construct it from separate variables
        if self.POSTGRES_USER and self.POSTGRES_SERVER and self.POSTGRES_DB:
            pwd = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
            
            # Check if POSTGRES_PORT is provided, otherwise fallback to 5432
            port = self.POSTGRES_PORT if self.POSTGRES_PORT else "5432"
            
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}{pwd}@{self.POSTGRES_SERVER}:{port}/{self.POSTGRES_DB}"
        else:
            if self.ENVIRONMENT == "production":
                missing_vars = []
                if not self.POSTGRES_USER: missing_vars.append("POSTGRES_USER")
                if not self.POSTGRES_SERVER: missing_vars.append("POSTGRES_SERVER")
                if not self.POSTGRES_DB: missing_vars.append("POSTGRES_DB")
                
                raise ValueError(
                    f"Production environment strictly requires DATABASE_URL or PostgreSQL configuration variables. "
                    f"Missing: {', '.join(missing_vars)}. "
                )
            # Default fallback for local development and tests
            self.DATABASE_URL = "sqlite+aiosqlite:///./victoria.db"
            
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
