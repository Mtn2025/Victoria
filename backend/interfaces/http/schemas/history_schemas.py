"""
History Schemas.
Part of the Interfaces Layer.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TranscriptLineResponse(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HistoryBackendCall(BaseModel):
    id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    client_type: str = "unknown"
    status: Optional[str] = None
    duration: float = 0.0
    extracted_data: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CallDetailResponse(BaseModel):
    call: HistoryBackendCall
    transcripts: List[TranscriptLineResponse]
