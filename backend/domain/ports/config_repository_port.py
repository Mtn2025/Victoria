"""
Port (Interface) for agent configuration persistence.

Hexagonal Architecture: Domain defines contract for config CRUD operations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConfigDTO:
    """
    Data Transfer Object for agent configuration.
    
    Represents flattened configuration combining:
    - LLM settings (provider, model, temperature)
    - TTS settings (voice, style, speed)
    - STT settings (language, timeouts)
    - Advanced features (tools, webhooks, analysis)
    - Telephony integration
    """
    # LLM Config
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 600
    system_prompt: str = ""
    first_message: str = ""
    first_message_mode: str = "text"

    # TTS Config
    tts_provider: str = "azure"
    voice_name: str = "es-MX-DaliaNeural"
    voice_style: str = "default"
    voice_style_degree: float = 1.0     # Style intensity (0.01 - 2.0)
    voice_speed: float = 1.0
    voice_pitch: int = 0                # Hz offset (-100 to +100)
    voice_volume: int = 100             # Volume level (0-100)
    voice_language: str = "es-MX"

    # Runtime client type — determines audio format across the pipeline
    # 'browser' = 24 kHz PCM  |  'twilio'/'telnyx' = 8 kHz mulaw
    client_type: str = "browser"

    # STT Config
    stt_provider: str = "azure"
    stt_language: str = "es-MX"
    silence_timeout_ms: int = 1000

    # VAD Config
    # These are the canonical defaults for Silero VAD.
    # All processors MUST read from this object — never hardcode.
    vad_threshold_start: float = 0.5      # Confidence to START speech detection
    vad_threshold_return: float = 0.35    # Confidence floor before declaring silence
    vad_min_speech_frames: int = 3        # Min consecutive speech frames before START event
    vad_confirmation_window_ms: int = 200 # Time window to confirm speech onset (ms)

    # Advanced
    enable_denoising: bool = True
    enable_backchannel: bool = False
    max_duration: int = 300

    # Telephony
    silence_timeout_ms_phone: Optional[int] = None
    silence_timeout_ms_telnyx: Optional[int] = None

    # Function Calling (Tools)
    tool_server_url: Optional[str] = None
    tool_server_secret: Optional[str] = None
    tools_schema: Optional[Any] = None
    async_tools: bool = False
    tool_timeout_ms: int = 5000

    # Analysis
    analysis_prompt: Optional[str] = None
    success_rubric: Optional[str] = None
    extraction_schema: Optional[Any] = None
    sentiment_analysis: bool = False
    webhook_url: Optional[str] = None
    log_webhook_url: Optional[str] = None

    # System
    concurrency_limit: int = 10
    spend_limit_daily: float = 50.0
    environment: str = "dev"
    privacy_mode: bool = False


class ConfigRepositoryPort(ABC):
    """
    Port for agent configuration persistence.
    
    Handles CRUD operations for agent config profiles.
    """

    @abstractmethod
    async def get_config(self, profile: str = "default") -> ConfigDTO:
        """
        Retrieve configuration by profile name.
        
        Args:
            profile: Config profile identifier (default: "default")
            
        Returns:
            Configuration DTO
            
        Raises:
            ConfigNotFoundException: If profile doesn't exist
        """
        pass

    @abstractmethod
    async def update_config(self, profile: str, **updates) -> ConfigDTO:
        """
        Update existing configuration.
        
        Args:
            profile: Profile to update
            **updates: Fields to update (key=value pairs)
            
        Returns:
            Updated ConfigDTO
            
        Raises:
            ConfigNotFoundException: If profile doesn't exist
        """
        pass

    @abstractmethod
    async def create_config(self, profile: str, config: ConfigDTO) -> ConfigDTO:
        """
        Create new configuration profile.
        
        Args:
            profile: New profile name
            config: Initial configuration values
            
        Returns:
            Created ConfigDTO
        """
        pass


class ConfigNotFoundException(Exception):
    """Exception raised when config profile not found."""
    pass
