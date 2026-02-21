"""
History Endpoints.
Part of the Interfaces Layer (HTTP).
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Body

from backend.infrastructure.database.session import get_db_session
from backend.interfaces.deps import get_call_repository
from backend.domain.ports.persistence_port import CallRepository
from backend.domain.value_objects.call_id import CallId
from backend.interfaces.http.schemas.history_schemas import CallDetailResponse

router = APIRouter(prefix="/history", tags=["history"])
logger = logging.getLogger(__name__)

@router.get("/rows")
async def get_history_rows(
    request: Request,
    page: int = 1,
    limit: int = 20,
    client_type: Optional[str] = None,
    repo: CallRepository = Depends(get_call_repository)
) -> Dict[str, Any]:
    """
    Get history rows as JSON data.
    """
    from backend.domain.use_cases.get_call_history import GetCallHistoryUseCase
    
    use_case = GetCallHistoryUseCase(repo)
    return await use_case.execute(page=page, limit=limit, client_type=client_type)

@router.get("/{call_id}/detail", response_model=CallDetailResponse)
async def get_call_detail(
    request: Request,
    call_id: str,
    repo: CallRepository = Depends(get_call_repository)
):
    """
    Get full details of a specific call including transcripts.
    Protected implicitly by main router middleware or Security deps.
    """
    from backend.domain.use_cases.get_call_detail import GetCallDetailUseCase
    
    use_case = GetCallDetailUseCase(repo)
    detail_data = await use_case.execute(call_id)
    
    if not detail_data:
        raise HTTPException(status_code=404, detail="Call not found")
        
    return detail_data

@router.post("/delete-selected")
async def delete_selected(
    request: Request,
    repo: CallRepository = Depends(get_call_repository)
):
    """
    Delete calls. Expects JSON {"ids": ["uuid1", "uuid2"]}
    """
    from backend.domain.use_cases.manage_history import DeleteSelectedCallsUseCase
    
    body = await request.json()
    ids = body.get("ids", [])
    
    use_case = DeleteSelectedCallsUseCase(repo)
    deleted = await use_case.execute(ids)
        
    return {"status": "ok", "deleted": deleted}

@router.post("/clear")
async def clear_history(repo: CallRepository = Depends(get_call_repository)):
    from backend.domain.use_cases.manage_history import ClearHistoryUseCase
    use_case = ClearHistoryUseCase(repo)
    count = await use_case.execute()
    return {"status": "ok", "deleted": count}
