import os
import pytest
from unittest.mock import MagicMock
from backend.infrastructure.config.settings import settings

@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    """
    Override settings directly to ensure adapters see the values
    even if settings were already loaded.
    """
    # Backup
    original_azure_key = settings.AZURE_SPEECH_KEY
    original_groq_key = settings.GROQ_API_KEY
    original_telnyx_key = settings.TELNYX_API_KEY
    
    # Override
    settings.AZURE_SPEECH_KEY = "fake_azure_key"
    settings.AZURE_SPEECH_REGION = "eastus"
    settings.GROQ_API_KEY = "fake_groq_key"
    settings.TELNYX_API_KEY = "fake_telnyx_key"
    # Provide Redis URL if checked
    # settings.REDIS_URL = "redis://localhost:6379/0" 
    
    yield
    
    # Restore (optional)
    settings.AZURE_SPEECH_KEY = original_azure_key
    settings.GROQ_API_KEY = original_groq_key
    settings.TELNYX_API_KEY = original_telnyx_key
