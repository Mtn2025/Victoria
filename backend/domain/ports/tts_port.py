"""
TTS Port (Interface).
Part of the Domain Layer (Hexagonal Architecture).

Merged version combining Legacy's structured request model with Victoria's clean VoiceConfig pattern.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List
from dataclasses import dataclass, field

from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat


@dataclass
class VoiceMetadata:
    """
    Metadata for an available voice.
    
    Used for voice discovery and UI display.
    """
    id: str
    name: str
    gender: str
    locale: str


@dataclass
class TTSRequest:
    """
    Voice synthesis request (Domain Model).
    
    Generic parameters work with all TTS providers.
    Vendor-specific options go in provider_options dict.
    """
    text: str
    voice_id: str
    language: str = "es-MX"
    
    # Generic parameters
    pitch: int = 0
    speed: float = 1.0
    volume: float = 100.0
    # Format string: 'pcm_24000' for browser, 'pcm_8000_mulaw' for telephony
    # SSoT: client_type in ConfigDTO determines this — default is browser (24kHz PCM)
    format: str = "pcm_24000"
    style: Optional[str] = None
    backpressure_detected: bool = False
    
    # Provider-specific options
    provider_options: dict = field(default_factory=dict)
    
    # Metadata
    metadata: dict = field(default_factory=dict)


class TTSPort(ABC):
    """
    Interface for Text-to-Speech providers.
    
    Supports both simple synthesis and advanced SSML-based generation.
    """

    @abstractmethod
    async def synthesize(
        self, 
        text: str, 
        voice: VoiceConfig, 
        format: AudioFormat
    ) -> bytes:
        """
        Synthesize text to audio (simple method using VoiceConfig VO).
        
        Args:
            text: Text to speak
            voice: Voice configuration (name, speed, pitch, style)
            format: Desired output audio format
            
        Returns:
            Raw audio bytes
            
        Raises:
            TTSException: If synthesis fails
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self, 
        text: str, 
        voice: VoiceConfig, 
        format: AudioFormat
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized audio chunks.
        
        Args:
            text: Text to speak
            voice: Voice configuration
            format: Desired output format
            
        Yields:
            Audio chunks (e.g., 20ms frames)
            
        Raises:
            TTSException: If streaming synthesis fails
        """
        yield b""  # Placeholder for generator type hint

    @abstractmethod
    async def synthesize_request(self, request: TTSRequest) -> bytes:
        """
        Synthesize using structured TTSRequest (advanced method).
        
        Provides more control including provider-specific options.
        
        Args:
            request: Synthesis parameters
            
        Returns:
            Audio in bytes
            
        Raises:
            TTSException: If synthesis fails
        """
        pass

    @abstractmethod
    async def synthesize_ssml(self, ssml: str) -> bytes:
        """
        Synthesize directly from SSML markup.
        
        For fine-grained control over prosody, breaks, etc.
        
        Args:
            ssml: Complete SSML markup
            
        Returns:
            Audio in bytes
            
        Raises:
            TTSException: If SSML synthesis fails
        """
        pass
    
    @abstractmethod
    async def get_available_voices(
        self, 
        language: Optional[str] = None
    ) -> List[VoiceMetadata]:
        """
        Get list of available voices from this provider.
        
        Args:
            language: Filter by language (optional)
            
        Returns:
            List of voice metadata
            
        Raises:
            TTSException: If voice list retrieval fails
        """
        pass

    @abstractmethod
    async def get_voice_styles(self, voice_id: str) -> List[str]:
        """
        Get available styles for a specific voice.
        
        Args:
            voice_id: Voice ID
            
        Returns:
            List of supported styles (e.g., ["cheerful", "sad", "angry"])
            
        Raises:
            TTSException: If style retrieval fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Cleanup provider resources.
        
        Called when shutting down the application.
        """
        pass


class TTSException(Exception):
    """
    Base exception for TTS-related errors.
    
    Provides structured error information including retry hints.
    
    Attributes:
        message: Human-readable error message
        retryable: Whether the error might succeed if retried
        provider: Provider that generated the error (e.g., "azure", "elevenlabs")
        original_error: Original exception from the SDK (if any)
    """

    def __init__(
        self,
        message: str,
        retryable: bool = False,
        provider: str = "unknown",
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.retryable = retryable
        self.provider = provider
        self.original_error = original_error

    def __str__(self):
        retry_hint = "(retryable)" if self.retryable else "(not retryable)"
        return f"[{self.provider}] {super().__str__()} {retry_hint}"
