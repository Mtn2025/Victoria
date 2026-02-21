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
    
    # LLM Settings
    responseLength: Optional[str] = None
    conversationTone: Optional[str] = None
    conversationFormality: Optional[str] = None
    conversationPacing: Optional[str] = None
    contextWindow: Optional[int] = None
    frequencyPenalty: Optional[float] = None
    presencePenalty: Optional[float] = None
    toolChoice: Optional[str] = None
    dynamicVarsEnabled: Optional[bool] = None
    dynamicVars: Optional[str] = None
    mode: Optional[str] = None
    hallucination_blacklist: Optional[str] = None
    
    # Text-to-Speech
    voice_name: Optional[str] = None
    voice_style: Optional[str] = None
    voice_speed: Optional[float] = None
    voice_pitch: Optional[float] = None
    voice_volume: Optional[float] = None
    voiceStyleDegree: Optional[float] = None
    voiceBgSound: Optional[str] = None
    voiceBgUrl: Optional[str] = None
    
    # STT Settings
    sttProvider: Optional[str] = None
    sttModel: Optional[str] = None
    sttLang: Optional[str] = None
    sttKeywords: Optional[str] = None
    interruption_threshold: Optional[float] = None
    vadSensitivity: Optional[float] = None
    
    # VAD / Silence
    silence_timeout_ms: Optional[int] = None
    
    # Agent identity — optional when patching via /agents/{uuid} (UUID is already in the URL).
    # Still accepted if sent by legacy callers.
    agent_id: Optional[str] = None
    
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

