"""
Port (Interface) for agent configuration persistence.

Hexagonal Architecture: Domain defines contract for config CRUD operations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Union


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
    
    # Extended LLM Settings
    responseLength: Optional[str] = None
    conversationTone: Optional[str] = None
    conversationFormality: Optional[str] = None
    conversationPacing: Optional[str] = None
    contextWindow: int = 10
    frequencyPenalty: float = 0.0
    presencePenalty: float = 0.0
    toolChoice: str = "auto"
    dynamicVarsEnabled: bool = False
    dynamicVars: Optional[str] = None
    hallucination_blacklist: Optional[str] = None

    # TTS Config
    tts_provider: str = "azure"
    voice_name: str = "es-MX-DaliaNeural"
    voice_style: str = "default"
    voice_speed: float = 1.0
    voice_pitch: int = 0                # Hz offset (-100 to +100)
    voice_volume: int = 100             # Volume level (0-100)
    voice_language: str = "es-MX"
    
    # Advanced / Multi-provider Voice Controls
    voice_style_degree: float = 1.0
    voice_bg_sound: str = "none"
    voice_bg_url: Optional[str] = None
    voice_stability: Optional[float] = None
    voice_similarity_boost: Optional[float] = None
    voice_style_exaggeration: Optional[float] = None
    voice_speaker_boost: Optional[bool] = None
    voice_multilingual: Optional[bool] = None

    # Runtime client type — determines audio format across the pipeline
    # 'browser' = 24 kHz PCM  |  'twilio'/'telnyx' = 8 kHz mulaw
    client_type: str = "browser"

    # STT Config
    stt_provider: str = "azure"
    stt_language: str = "es-MX"
    silence_timeout_ms: int = 1000

    # Flow Config (Barge-in, AMD, Pacing)
    barge_in_enabled: bool = True
    barge_in_sensitivity: float = 0.5
    barge_in_phrases: list[str] = field(default_factory=list)
    amd_enabled: bool = False
    amd_sensitivity: float = 0.5
    amd_action: str = "hangup"
    amd_message: str = "Hola, he detectado un buzón. Por favor devuelva la llamada."
    pacing_response_delay_ms: int = 0
    pacing_wait_for_greeting: bool = False
    pacing_hyphenation: bool = False
    pacing_end_call_phrases: list[str] = field(default_factory=list)

    # VAD Config
    # These are the canonical defaults for Silero VAD.
    # All processors MUST read from this object — never hardcode.
    vad_threshold_start: float = 0.5      # Confidence to START speech detection
    vad_threshold_return: float = 0.35    # Confidence floor before declaring silence
    vad_min_speech_frames: int = 3        # Min consecutive speech frames before START event
    vad_confirmation_window_ms: int = 200 # Time window to confirm speech onset (ms)

    # Advanced
    enable_denoising: bool = True
    noise_suppression_level: str = "balanced"
    audio_codec: str = "PCMU"
    enable_backchannel: bool = False
    max_duration: int = 300
    max_retries: int = 1
    idle_message: Union[str, list[str]] = "¿Hola? ¿Sigues ahí?"
    end_call_enabled: bool = False
    end_call_phrases: list[str] = field(default_factory=list)
    end_call_instructions: Optional[str] = None

    # Telephony
    silence_timeout_ms_phone: Optional[int] = None
    silence_timeout_ms_telnyx: Optional[int] = None

    # Function Calling (Tools)
    tool_server_url: Optional[str] = None
    tool_server_secret: Optional[str] = None
    tools_schema: Optional[Any] = None
    async_tools: bool = False
    tool_timeout_ms: int = 5000
    tool_retry_count: int = 0
    tool_error_msg: str = "Lo siento, hubo un error con la herramienta."
    redact_params: Optional[str] = None
    transfer_whitelist: Optional[str] = None
    state_injection_enabled: bool = False

    # Analysis
    analysis_prompt: Optional[str] = None
    success_rubric: Optional[str] = None
    extraction_schema: Optional[Any] = None
    sentiment_analysis: bool = False
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    log_webhook_url: Optional[str] = None
    pii_redaction_enabled: bool = False
    cost_tracking_enabled: bool = False
    retention_days: int = 30
    crm_enabled: bool = False

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
