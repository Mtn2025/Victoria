from backend.infrastructure.config.settings import settings

class FeatureFlags:
    """
    Centralized Feature Flags logic.
    Determines availability of features based on environment configuration.
    """
    
    @property
    def is_simulator_enabled(self) -> bool:
        """Browser simulator is always enabled in dev/staging."""
        return True 

    @property
    def is_twilio_enabled(self) -> bool:
        """Twilio is enabled only if credentials are present."""
        return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)

    @property
    def is_telnyx_enabled(self) -> bool:
        """Telnyx is enabled only if API key is present."""
        return bool(settings.TELNYX_API_KEY)
    
    @property
    def is_audio_logging_enabled(self) -> bool:
        """Enable audio logging in non-production environments."""
        return settings.ENVIRONMENT != "production"

    def get_all(self) -> dict:
        """Return all feature flags as a dictionary."""
        return {
            "simulator": self.is_simulator_enabled,
            "twilio": self.is_twilio_enabled,
            "telnyx": self.is_telnyx_enabled,
            "audio_logging": self.is_audio_logging_enabled,
            "environment": settings.ENVIRONMENT
        }

features = FeatureFlags()
