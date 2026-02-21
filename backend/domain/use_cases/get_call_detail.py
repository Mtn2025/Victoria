"""
Get Call Detail Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from typing import Dict, Any, Optional

from backend.domain.ports.persistence_port import CallRepository
from backend.domain.value_objects.call_id import CallId


class GetCallDetailUseCase:
    """
    Retrieves full details of a specific call, including transcripts.
    """
    
    def __init__(self, call_repository: CallRepository):
        self.call_repository = call_repository
        
    async def execute(self, call_id_str: str) -> Optional[Dict[str, Any]]:
        """
        Execute the use case.
        
        Args:
            call_id_str: The UUID string of the call.
            
        Returns:
            Dict representing CallDetailResponse, or None if not found.
        """
        call_id = CallId(call_id_str)
        
        # The repository get_by_id currently returns Call populated with conversation turns.
        call = await self.call_repository.get_by_id(call_id)
        if not call:
            return None
            
        duration = 0.0
        if call.end_time and call.start_time:
             duration = (call.end_time - call.start_time).total_seconds()
             
        # Map Transcript Lines
        transcripts = []
        for turn in call.conversation.turns:
            transcripts.append({
                "role": turn.role,
                "content": turn.content,
                "timestamp": turn.timestamp.isoformat() if turn.timestamp else None
            })
             
        call_data = {
            "id": call.id.value,
            "start_time": call.start_time.isoformat() if call.start_time else None,
            "end_time": call.end_time.isoformat() if call.end_time else None,
            "status": call.status.value,
            "client_type": call.metadata.get("client_type", "unknown"),
            "extracted_data": call.metadata.get("extracted_data", {}),
            "duration": duration,
            "metadata": call.metadata
        }
        
        return {
            "call": call_data,
            "transcripts": transcripts
        }
