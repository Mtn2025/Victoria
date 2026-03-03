"""
Agent Schemas.
Part of the Interfaces Layer (HTTP).
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AgentListItem(BaseModel):
    """Lightweight representation of an agent for list views."""
    model_config = ConfigDict(from_attributes=True)

    agent_uuid: str
    name: str
    language: str
    is_active: bool
    provider: str
    created_at: datetime


class AgentCreateRequest(BaseModel):
    """Request schema for creating a new agent."""
    name: str = Field(..., min_length=1, max_length=100,
                      description="Display name for the new agent")
    language: str = Field(default="es-MX", description="Root language code of the agent")
    provider: str = Field(default="browser", description="Network provider context for the agent (browser, twilio, telnyx)")


class AgentCreateResponse(BaseModel):
    """Response after successfully creating an agent."""
    agent_uuid: str
    name: str
    language: str
    is_active: bool
    provider: str
    created_at: datetime


class ActiveAgentResponse(BaseModel):
    """
    Full configuration response for the active agent.
    Includes agent identity fields and full config.
    """
    agent_uuid: str
    name: str
    language: str
    is_active: bool
    provider: str
    created_at: datetime

    # Core config
    system_prompt: str
    first_message: str
    silence_timeout_ms: int

    # Voice (flat fields from DB columns)
    voice: Dict[str, Any]

    # JSON blob configs
    llm_config: Dict[str, Any]
    stt_config: Dict[str, Any]
    voice_config_json: Dict[str, Any]
    tools_config: Dict[str, Any]
    flow_config: Dict[str, Any]
    analysis_config: Dict[str, Any]
    system_config: Dict[str, Any]
    connectivity_config: Dict[str, Any]


class AgentCloneRequest(BaseModel):
    """Request schema for cloning an agent to a specific provider."""
    provider: str = Field(..., description="Target provider for the cloned agent (e.g. telnyx, twilio)")
    flow_config: Dict[str, Any]
    analysis_config: Dict[str, Any]
    system_config: Dict[str, Any]


class AgentUpdateNameRequest(BaseModel):
    """Request to rename an agent."""
    name: str = Field(..., min_length=1, max_length=100,
                      description="New display name for the agent")
