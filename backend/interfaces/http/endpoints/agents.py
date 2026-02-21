"""
Agents Endpoints.
Part of the Interfaces Layer (HTTP).
Provides agent lifecycle management: list, create, activate, get-active, update-config.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from backend.interfaces.deps import get_agent_repository
from backend.domain.ports.persistence_port import AgentRepository, AgentNotFoundError
from backend.interfaces.http.schemas.agent_schemas import (
    AgentListItem,
    AgentCreateRequest,
    AgentCreateResponse,
    ActiveAgentResponse,
    AgentUpdateNameRequest,
)
from backend.interfaces.http.schemas.config_schemas import ConfigUpdate
from backend.domain.use_cases.list_agents import ListAgentsUseCase
from backend.domain.use_cases.create_agent import CreateAgentUseCase
from backend.domain.use_cases.set_active_agent import SetActiveAgentUseCase
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

router = APIRouter(prefix="/agents", tags=["agents"], redirect_slashes=False)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# GET /agents
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[AgentListItem])
async def list_agents(
    repo: AgentRepository = Depends(get_agent_repository),
) -> list[AgentListItem]:
    """Return all registered agents ordered by creation date."""
    use_case = ListAgentsUseCase(repo)
    agents = await use_case.execute()
    return [
        AgentListItem(
            agent_uuid=a.agent_uuid,
            name=a.name,
            is_active=a.is_active,
            created_at=a.created_at,
        )
        for a in agents
    ]


# --------------------------------------------------------------------------- #
# POST /agents
# --------------------------------------------------------------------------- #
@router.post("", response_model=AgentCreateResponse, status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentCreateResponse:
    """Create a new agent with system-default configuration."""
    use_case = CreateAgentUseCase(repo)
    try:
        agent = await use_case.execute(name=request.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return AgentCreateResponse(
        agent_uuid=agent.agent_uuid,
        name=agent.name,
        is_active=agent.is_active,
        created_at=agent.created_at,
    )


# --------------------------------------------------------------------------- #
# GET /agents/active                                                            #
# IMPORTANT: This route must be declared BEFORE /{agent_uuid} to avoid        #
# "active" being captured as a UUID parameter.                                 #
# --------------------------------------------------------------------------- #
@router.get("/active", response_model=ActiveAgentResponse)
async def get_active_agent(
    repo: AgentRepository = Depends(get_agent_repository),
) -> ActiveAgentResponse:
    """
    Return the currently active agent with its full configuration.
    Returns 404 if no agent is marked active — never returns a fallback default.
    """
    agents = await repo.get_all_agents()
    active = next((a for a in agents if a.is_active), None)

    if not active:
        raise HTTPException(
            status_code=404,
            detail="No active agent found. Please activate an agent from the /agents panel.",
        )

    # active.metadata is always a dict (declared in the domain entity).

    return ActiveAgentResponse(
        agent_uuid=active.agent_uuid,
        name=active.name,
        is_active=active.is_active,
        created_at=active.created_at,
        system_prompt=active.system_prompt,
        first_message=active.first_message,
        silence_timeout_ms=active.silence_timeout_ms,
        voice={
            "name": active.voice_config.name,
            "style": active.voice_config.style,
            "speed": active.voice_config.speed,
            "pitch": active.voice_config.pitch,
            "volume": active.voice_config.volume,
        },
        llm_config=active.llm_config or {},
        stt_config=active.metadata.get("stt_config") or {},
        voice_config_json=active.metadata.get("voice_config_json") or {},
        # Read real tools_config from domain (never hardcoded)
        tools_config=active.tools[0] if active.tools else {},
    )


# --------------------------------------------------------------------------- #
# POST /agents/{agent_uuid}/activate                                           #
# --------------------------------------------------------------------------- #
@router.post("/{agent_uuid}/activate", response_model=AgentListItem)
async def activate_agent(
    agent_uuid: str,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentListItem:
    """Activate the given agent. Deactivates all others atomically."""
    use_case = SetActiveAgentUseCase(repo)
    try:
        agent = await use_case.execute(agent_uuid)
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_uuid} not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return AgentListItem(
        agent_uuid=agent.agent_uuid,
        name=agent.name,
        is_active=agent.is_active,
        created_at=agent.created_at,
    )


# --------------------------------------------------------------------------- #
# PATCH /agents/{agent_uuid}                                                   #
# Config update — replaces PATCH /config/ for new agent-aware flow             #
# --------------------------------------------------------------------------- #
@router.patch("/{agent_uuid}", status_code=200)
async def update_agent_config(
    agent_uuid: str,
    update: ConfigUpdate,
    repo: AgentRepository = Depends(get_agent_repository),
):
    """
    Update configuration for a specific agent identified by UUID.
    Delegates to the same ConfigUpdate schema used by /config/ for consistency.
    """
    agent = await repo.get_agent_by_uuid(agent_uuid)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_uuid} not found")

    # Apply updates (canonical keys — always llm_provider / llm_model in DB)
    if update.system_prompt is not None:
        agent.system_prompt = update.system_prompt
    if update.first_message is not None:
        agent.first_message = update.first_message
    if update.silence_timeout_ms is not None:
        agent.silence_timeout_ms = update.silence_timeout_ms

    if any([update.voice_name, update.voice_style is not None,
            update.voice_speed, update.voice_pitch is not None, update.voice_volume is not None]):
        agent.voice_config = VoiceConfig(
            name=update.voice_name or agent.voice_config.name,
            style=update.voice_style if update.voice_style is not None else agent.voice_config.style,
            speed=update.voice_speed or agent.voice_config.speed,
            pitch=update.voice_pitch if update.voice_pitch is not None else agent.voice_config.pitch,
            volume=update.voice_volume if update.voice_volume is not None else agent.voice_config.volume,
        )

    # Merge LLM config — ALWAYS use llm_provider / llm_model as canonical keys.
    # This eliminates the legacy ambiguity where /config/ stored them as 'provider'/'model'.
    llm_updates = {}
    if update.llm_provider is not None:
        llm_updates["llm_provider"] = update.llm_provider
    if update.llm_model is not None:
        llm_updates["llm_model"] = update.llm_model
    for field in ["max_tokens", "temperature", "responseLength", "conversationTone",
                  "conversationFormality", "conversationPacing", "contextWindow",
                  "frequencyPenalty", "presencePenalty", "toolChoice", "dynamicVarsEnabled",
                  "dynamicVars", "mode", "hallucination_blacklist"]:
        val = getattr(update, field, None)
        if val is not None:
            llm_updates[field] = val
    if llm_updates:
        agent.llm_config = {**(agent.llm_config or {}), **llm_updates}

    # Merge Voice extended config into metadata
    voice_ext_updates = {}
    for field in ["voiceStyleDegree", "voiceBgSound", "voiceBgUrl"]:
        val = getattr(update, field, None)
        if val is not None:
            voice_ext_updates[field] = val
    if voice_ext_updates:
        existing_voice = agent.metadata.get("voice_config_json") or {}
        agent.metadata["voice_config_json"] = {**existing_voice, **voice_ext_updates}

    # Merge STT config into metadata
    stt_updates = {}
    for field in ["sttProvider", "sttModel", "sttLang", "sttKeywords",
                  "interruption_threshold", "vadSensitivity"]:
        val = getattr(update, field, None)
        if val is not None:
            stt_updates[field] = val
    if update.silence_timeout_ms is not None:
        stt_updates["silence_timeout_ms"] = update.silence_timeout_ms
    if stt_updates:
        existing_stt = agent.metadata.get("stt_config") or {}
        agent.metadata["stt_config"] = {**existing_stt, **stt_updates}

    # Tools
    if update.tools_config is not None:
        agent.tools = [update.tools_config]

    await repo.update_agent(agent)
    return {"status": "ok", "agent_uuid": agent_uuid}


# --------------------------------------------------------------------------- #
# PATCH /agents/{agent_uuid}/name                                               #
# Rename an agent                                                               #
# --------------------------------------------------------------------------- #
@router.patch("/{agent_uuid}/name", response_model=AgentListItem)
async def rename_agent(
    agent_uuid: str,
    request: AgentUpdateNameRequest,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentListItem:
    """Rename an agent. Does not affect configuration or active status."""
    agent = await repo.get_agent_by_uuid(agent_uuid)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_uuid} not found")

    if not request.name or not request.name.strip():
        raise HTTPException(status_code=422, detail="Agent name cannot be empty")

    agent.name = request.name.strip()
    await repo.update_agent(agent)

    return AgentListItem(
        agent_uuid=agent.agent_uuid,
        name=agent.name,
        is_active=agent.is_active,
        created_at=agent.created_at,
    )


# --------------------------------------------------------------------------- #
# DELETE /agents/{agent_uuid}                                                   #
# --------------------------------------------------------------------------- #
@router.delete("/{agent_uuid}", status_code=200)
async def delete_agent(
    agent_uuid: str,
    repo: AgentRepository = Depends(get_agent_repository),
):
    """
    Delete an agent permanently.
    Returns HTTP 400 if the agent is currently active — deactivate it first.
    """
    agent = await repo.get_agent_by_uuid(agent_uuid)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_uuid} not found")

    if agent.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the active agent. Activate another agent first, then retry.",
        )

    await repo.delete_agent(agent_uuid)
    return {"status": "deleted", "agent_uuid": agent_uuid}
