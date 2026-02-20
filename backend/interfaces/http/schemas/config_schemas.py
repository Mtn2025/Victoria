"""
Configuration Schemas.
Part of the Interfaces Layer.
"""
from pydantic import BaseModel, Field
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
