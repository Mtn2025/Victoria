"""
Voice Configuration Value Object.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass
from typing import Literal, Any, Dict, Optional

# Type aliases for better readability and type safety
VoiceStyle = Literal["default", "cheerful", "sad", "angry", "friendly", "terrified", "excited", "hopeful"]


@dataclass(frozen=True)
class VoiceConfig:
    """
    Immutable voice configuration value object.
    
    Domain Rule: VO must be self-validating and immutable.
    
    Attributes:
        name: Azure voice name (e.g., "es-MX-DaliaNeural")
        speed: Speech rate multiplier (0.5 - 2.0)
        pitch: Pitch offset in Hz (-100 to +100)
        volume: Volume level (0-100)
        style: Speaking style
        style_degree: Style intensity (0.01 - 2.0)
    """
    name: str
    speed: float = 1.0
    pitch: int = 0  # Hz offset
    volume: int = 100  # 0-100
    style: VoiceStyle = "default"
    style_degree: float = 1.0  # 0.01-2.0
    provider: str = "azure"
    bg_sound: str = "none"
    bg_url: Optional[str] = None
    
    # ElevenLabs specifics
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None
    style_exaggeration: Optional[float] = None
    speaker_boost: Optional[bool] = None
    multilingual: Optional[bool] = None

    def __post_init__(self) -> None:
        """Validate fields after initialization (Domain Invariant)."""
        self._validate()

    def _validate(self) -> None:
        """Internal validation logic."""
        if not (0.5 <= self.speed <= 2.0):
            raise ValueError(f"Speed must be between 0.5 and 2.0, got {self.speed}")

        if not (-100 <= self.pitch <= 100):
            raise ValueError(f"Pitch must be between -100 and +100 Hz, got {self.pitch}")

        if not (0 <= self.volume <= 100):
            raise ValueError(f"Volume must be between 0 and 100, got {self.volume}")

        if not (0.01 <= self.style_degree <= 2.0):
            raise ValueError(f"Style degree must be between 0.01 and 2.0, got {self.style_degree}")
            
        if not self.provider:
            raise ValueError("Voice provider cannot be empty")

    @classmethod
    def from_db_config(cls, db_config: Any) -> 'VoiceConfig':
        """
        Factory method to create VoiceConfig from database AgentConfig model.
        """
        voice_json = getattr(db_config, "voice_config_json", {}) or {}
        return cls(
            name=db_config.voice_name or "es-MX-DaliaNeural",
            speed=float(db_config.voice_speed or 1.0),
            pitch=int(db_config.voice_pitch or 0),
            volume=int(db_config.voice_volume or 100),
            style=db_config.voice_style or "default",
            style_degree=float(voice_json.get("voiceStyleDegree", db_config.voice_style_degree) if voice_json.get("voiceStyleDegree") is not None else (db_config.voice_style_degree or 1.0)),
            provider=getattr(db_config, "voice_provider", "azure") or "azure",
            bg_sound=voice_json.get("voiceBgSound", "none"),
            bg_url=voice_json.get("voiceBgUrl", None),
            stability=voice_json.get("voiceStability", None),
            similarity_boost=voice_json.get("voiceSimilarityBoost", None),
            style_exaggeration=voice_json.get("voiceStyleExaggeration", None),
            speaker_boost=voice_json.get("voiceSpeakerBoost", None),
            multilingual=voice_json.get("voiceMultilingual", None)
        )

    def to_ssml_params(self) -> Dict[str, Any]:
        """
        Convert to SSML builder parameters.
        Pure domain logic transformation.
        """
        return {
            "voice_name": self.name,
            "rate": self.speed,
            "pitch": self.pitch,
            "volume": self.volume,
            "style": self.style if self.style != "default" else None,
            "style_degree": self.style_degree if self.style != "default" else None
        }
