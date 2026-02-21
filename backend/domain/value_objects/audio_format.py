"""
Audio Format Value Object.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class AudioFormat:
    """
    Audio format specification (immutable).
    Consolidates functionality from legacy AudioFormat and AudioConfig.

    Attributes:
        sample_rate: Sampling rate in Hz (8000, 16000, 24000, etc.)
        channels: Number of audio channels (1=mono, 2=stereo)
        bits_per_sample: Bits per sample (8, 16, 24, 32)
        encoding: Audio encoding format
    """
    sample_rate: int
    channels: int = 1
    bits_per_sample: int = 16
    encoding: Literal["pcm", "mulaw", "alaw"] = "mulaw"

    def __post_init__(self) -> None:
        """Validate audio format parameters."""
        valid_sample_rates = [8000, 16000, 22050, 24000, 44100, 48000]
        if self.sample_rate not in valid_sample_rates:
            raise ValueError(f"Invalid sample_rate: {self.sample_rate}. Must be one of {valid_sample_rates}")
        
        if self.channels < 1 or self.channels > 2:
            raise ValueError(f"Invalid channels: {self.channels}. Must be 1 (mono) or 2 (stereo)")
        
        valid_bits = [8, 16, 24, 32]
        if self.bits_per_sample not in valid_bits:
            raise ValueError(f"Invalid bits_per_sample: {self.bits_per_sample}. Must be one of {valid_bits}")
    
    @property
    def is_telephony(self) -> bool:
        """
        Check if this is telephony format (8kHz mulaw/alaw).
        
        Returns:
            True for Twilio/Telnyx formats
        """
        return self.sample_rate == 8000 and self.encoding in ["mulaw", "alaw"]
    
    @property
    def is_browser(self) -> bool:
        """
        Check if this is browser-compatible format (24kHz PCM).

        Returns:
            True for browser WebSocket formats
        """
        return self.sample_rate == 24000 and self.encoding == "pcm"

    @classmethod
    def for_browser(cls) -> 'AudioFormat':
        """
        Factory for Browser usage (24kHz PCM16 — matches frontend AudioContext).

        The frontend captures microphone audio at 24kHz PCM16 via AudioWorklet
        and sends it base64-encoded inside JSON media events.
        """
        return cls(
            sample_rate=24000,
            encoding="pcm",
            channels=1,
            bits_per_sample=16
        )

    @classmethod
    def for_telephony(cls) -> 'AudioFormat':
        """Factory for Telephony Standard (8kHz MuLaw)."""
        return cls(
            sample_rate=8000,
            encoding="mulaw",
            channels=1,
            bits_per_sample=8
        )

    @classmethod
    def for_client(cls, client_type: str) -> 'AudioFormat':
        """
        Factory method to create AudioFormat based on client type.
        
        Args:
            client_type: "browser", "twilio", or "telnyx"
        """
        if client_type == "browser":
            return cls.for_browser()
        if client_type in ["twilio", "telnyx"]:
            return cls.for_telephony()
        # Default fallback
        return cls.for_telephony()
