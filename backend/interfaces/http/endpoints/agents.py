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
    AgentCloneRequest,
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
    provider: str = None,
    repo: AgentRepository = Depends(get_agent_repository),
) -> list[AgentListItem]:
    """Return all registered agents ordered by creation date."""
    use_case = ListAgentsUseCase(repo)
    agents = await use_case.execute(provider)
    return [
        AgentListItem(
            agent_uuid=a.agent_uuid,
            name=a.name,
            language=a.language,
            is_active=a.is_active,
            provider=a.provider,
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
        agent = await use_case.execute(name=request.name, language=request.language, provider=request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return AgentCreateResponse(
        agent_uuid=agent.agent_uuid,
        name=agent.name,
        language=agent.language,
        is_active=agent.is_active,
        provider=agent.provider,
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

    return ActiveAgentResponse(
        agent_uuid=active.agent_uuid,
        name=active.name,
        language=active.language,
        is_active=active.is_active,
        provider=active.provider,
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
        flow_config=active.metadata.get("flow_config") or {},
        analysis_config=active.metadata.get("analysis_config") or {},
        system_config=active.metadata.get("system_config") or {},
        connectivity_config=active.connectivity_config or {},
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
        language=agent.language,
        is_active=agent.is_active,
        provider=agent.provider,
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
    from backend.domain.use_cases.update_agent_config import UpdateAgentConfigUseCase
    from backend.domain.ports.persistence_port import AgentNotFoundError

    # _apply_hipaa_to_telnyx vive aquí (interfaces), no en el dominio
    # El use case recibe el callable como dependencia para mantener pureza hexagonal
    async def _apply_hipaa_to_telnyx() -> None:
        try:
            from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
            import logging
            client = TelnyxClient()
            await client.configure_hipaa()
            await client.close()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(f"HIPAA apply error: {exc}")

    use_case = UpdateAgentConfigUseCase(repo, on_hipaa_enabled=_apply_hipaa_to_telnyx)
    try:
        await use_case.execute(agent_uuid, update)
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_uuid} not found")

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
        language=agent.language,
        is_active=agent.is_active,
        provider=agent.provider,
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


# --------------------------------------------------------------------------- #
# POST /agents/{agent_uuid}/clone                                              #
# --------------------------------------------------------------------------- #
@router.post("/{agent_uuid}/clone", response_model=AgentListItem)
async def clone_agent(
    agent_uuid: str,
    request: AgentCloneRequest,
    repo: AgentRepository = Depends(get_agent_repository),
) -> AgentListItem:
    """
    Clones an existing agent into a new UUID for the requested provider.
    This effectively isolates the 'browser' agent into 'telnyx' or 'twilio'.
    """
    from backend.domain.use_cases.clone_agent import CloneAgentUseCase
    
    use_case = CloneAgentUseCase(repo)
    try:
        new_agent = await use_case.execute(agent_uuid, request.provider)
    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Source agent {agent_uuid} not found")

    return AgentListItem(
        agent_uuid=new_agent.agent_uuid,
        name=new_agent.name,
        language=new_agent.language,
        is_active=new_agent.is_active,
        provider=new_agent.provider,
        created_at=new_agent.created_at,
    )
