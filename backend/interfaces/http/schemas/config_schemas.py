"""
Configuration Schemas.
Part of the Interfaces Layer.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any

class ConfigUpdate(BaseModel):
    """
    Unified configuration update schema.
    Supports partial updates for various profiles.
    """
    # LLM
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    first_message: Optional[str] = None
    
    # Text-to-Speech
    voice_name: Optional[str] = None
    voice_style: Optional[str] = None
    voice_speed: Optional[float] = None
    voice_pitch: Optional[float] = None
    voice_volume: Optional[float] = None
    
    # VAD / Silence
    silence_timeout_ms: Optional[int] = None
    
    # Agent
    agent_id: str = "default" # Default agent to update
    
    # Dynamic/Extra
    tools_config: Optional[Dict[str, Any]] = None

    @model_validator(mode='before')
    @classmethod
    def cast_empty_strings_to_none(cls, data: Any) -> Any:
        """
        Frontend sometimes sends empty strings `""` for optional numbers.
        This intercepts the raw JSON Dict and converts `""` to `None` 
        before Pydantic tries to cast it to Float/Int and crashes.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data

class VoicePreviewRequest(BaseModel):
    """
    Schema for voice preview synthesis.
    """
    voice_name: str
    voice_speed: float = 1.0
    voice_pitch: int = 0
    voice_volume: int = 100
    voice_style: Optional[str] = None
    voice_style_degree: Optional[float] = 1.0
    provider: str = "azure"

