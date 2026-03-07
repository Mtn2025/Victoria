"""
Campaigns Endpoint.
Part of the Interfaces Layer (HTTP).
Provides outbound campaign management: launch campaigns from CSV, track status.
"""
import csv
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.interfaces.deps import get_agent_repository
from backend.domain.ports.persistence_port import AgentRepository

router = APIRouter(prefix="/campaigns", tags=["campaigns"], redirect_slashes=False)
logger = logging.getLogger(__name__)


class CampaignLaunchResponse(BaseModel):
    status: str
    campaign_name: str
    total_contacts: int
    queued: int
    message: str


@router.post("/outbound", response_model=CampaignLaunchResponse)
async def launch_outbound_campaign(
    campaign_name: str = Form(...),
    agent_id: str = Form(...),
    csv_file: UploadFile = File(...),
    repo: AgentRepository = Depends(get_agent_repository),
) -> CampaignLaunchResponse:
    """
    Launch an outbound call campaign from a CSV file.
    
    CSV format expected:
    phone_number, name (optional), custom_field (optional)
    
    Each row triggers an outbound call via the active agent.
    """
    if not csv_file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    # Validate agent exists
    agents = await repo.get_all_agents()
    agent = next((a for a in agents if a.agent_uuid == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")

    # Parse CSV
    content = await csv_file.read()
    try:
        decoded = content.decode('utf-8-sig')  # Handles BOM from Excel-generated CSVs
        reader = csv.DictReader(io.StringIO(decoded))
        rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty or has no data rows.")

    # Validate that phone_number column exists
    if rows and 'phone_number' not in rows[0]:
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have a 'phone_number' column. Found columns: {list(rows[0].keys())}"
        )

    total = len(rows)
    queued = 0

    # Import telephony service for outbound calls
    try:
        from backend.application.services.outbound_service import OutboundCallService
        from backend.infrastructure.adapters.telephony.telnyx_adapter import TelnyxAdapter
        from backend.infrastructure.config.settings import settings

        telnyx_adapter = TelnyxAdapter(
            api_key=settings.TELNYX_API_KEY,
            connection_id=settings.TELNYX_CONNECTION_ID,
            from_number=settings.TELNYX_FROM_NUMBER,
        )
        outbound_service = OutboundCallService(telnyx_adapter)

        for row in rows:
            phone = row.get('phone_number', '').strip()
            if not phone:
                logger.warning(f"[Campaign:{campaign_name}] Skipping row with empty phone_number")
                continue
            try:
                await outbound_service.initiate_outbound_call(
                    agent_id=agent_id,
                    to_number=phone,
                    from_number=settings.TELNYX_FROM_NUMBER,
                    agent=agent,
                )
                queued += 1
                logger.info(f"[Campaign:{campaign_name}] Queued call to {phone}")
            except Exception as e:
                logger.error(f"[Campaign:{campaign_name}] Failed to queue {phone}: {e}")

    except ImportError as e:
        logger.error(f"[Campaign] Outbound service import error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Outbound call service is not available. Ensure Telnyx is configured correctly."
        )

    logger.info(f"[Campaign:{campaign_name}] Launched: {queued}/{total} calls queued for agent {agent_id}")

    return CampaignLaunchResponse(
        status="success",
        campaign_name=campaign_name,
        total_contacts=total,
        queued=queued,
        message=f"Campaign '{campaign_name}' launched: {queued}/{total} calls queued."
    )
