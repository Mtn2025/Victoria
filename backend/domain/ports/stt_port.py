"""
STT Port (Interface).
Part of the Domain Layer (Hexagonal Architecture).

Merged version combining Legacy's robust configuration with Victoria's clean Session pattern.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum

from backend.domain.value_objects.audio_format import AudioFormat


class STTResultReason(Enum):
    """Reason for STT result."""
    RECOGNIZED_SPEECH = "recognized"
    RECOGNIZING_SPEECH = "recognizing"
    CANCELED = "canceled"
    UNKNOWN = "unknown"


@dataclass
class STTEvent:
    """
    Event from STT recognition.
    
    Provides detailed information about recognition results.
    """
    reason: STTResultReason
    text: str
    duration: float = 0.0
    error_details: Optional[str] = None


@dataclass
class STTConfig:
    """
    Configuration for Speech-to-Text recognition.
    
    Supports both basic and advanced controls for real-time transcription.
    """
    language: str = "es-MX"
    audio_mode: str = "twilio"  # "twilio", "telnyx", "browser"
    initial_silence_ms: int = 5000
    segmentation_silence_ms: int = 1000
    
    # Advanced Controls
    model: str = "default"
    keywords: Optional[list] = None  # [{"word": "Keyword", "boost": 2.0}]
    silence_timeout: int = 500
    utterance_end_strategy: str = "default"
    
    # Formatting & Filters
    punctuation: bool = True
    profanity_filter: bool = True
    smart_formatting: bool = True
    
    # Features
    diarization: bool = False
    multilingual: bool = False


class STTSession(ABC):
    """
    Session object for continuous streaming recognition.
    
    Returned by `STTPort.start_stream()`. Provides both async generator
    pattern (get_results) and event subscription pattern.
    """
    
    @abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> None:
        """
        Push audio bytes to the recognizer.
        
        Args:
            audio_chunk: Raw audio bytes
        """
        pass
    
    @abstractmethod
    async def get_results(self) -> AsyncGenerator[str, None]:
        """
        Stream transcription results as an async generator.
        
        Yields:
            Finalized text segments
        """
        yield ""  # Placeholder for type hint
    
    @abstractmethod
    def subscribe(self, callback: Callable[[STTEvent], None]) -> None:
        """
        Subscribe to detailed STT events (optional pattern).
        
        Use this for more granular control over recognition events.
        
        Args:
            callback: Function to call with each STTEvent
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the session and cleanup resources."""
        pass


class STTPort(ABC):
    """
    Interface for Speech-to-Text providers.
    
    Supports both one-shot transcription and streaming recognition.
    """

    @abstractmethod
    async def transcribe(
        self, 
        audio: bytes, 
        format: AudioFormat, 
        language: str = "es-MX"
    ) -> str:
        """
        Transcribe a complete audio buffer (non-streaming).
        
        Args:
            audio: Raw audio bytes
            format: Audio format specification (Value Object)
            language: Language code
            
        Returns:
            Complete transcription text
            
        Raises:
            STTException: If transcription fails
        """
        pass

    @abstractmethod
    async def start_stream(
        self, 
        format: AudioFormat,
        config: Optional[STTConfig] = None,
        on_interruption_callback: Optional[Callable] = None
    ) -> STTSession:
        """
        Start a real-time recognition session.
        
        Args:
            format: Audio format for the incoming stream
            config: Optional STT configuration (uses defaults if None)
            on_interruption_callback: Optional callback for barge-in detection
            
        Returns:
            An active STTSession
            
        Raises:
            STTException: If session creation fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Cleanup provider resources.
        
        Called when shutting down the application.
        """
        pass


class STTException(Exception):
    """
    Base exception for STT-related errors.
    
    Provides structured error information including retry hints.
    
    Attributes:
        message: Human-readable error message
        retryable: Whether the error might succeed if retried
        provider: Provider that generated the error (e.g., "azure", "google")
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
