"""
History Schemas.
Part of the Interfaces Layer.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class TranscriptLineResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    role: str
    content: str
    timestamp: Optional[datetime] = None


class HistoryBackendCall(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    client_type: str = "unknown"
    status: Optional[str] = None
    duration: float = 0.0
    extracted_data: Dict[str, Any] = {}


class CallDetailResponse(BaseModel):
    call: HistoryBackendCall
    transcripts: List[TranscriptLineResponse]
