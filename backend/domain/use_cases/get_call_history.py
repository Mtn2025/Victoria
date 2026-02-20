"""
Get Call History Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from typing import List, Tuple, Optional, Dict, Any
from backend.domain.entities.call import Call
from backend.domain.ports.persistence_port import CallRepository

class GetCallHistoryUseCase:
    """
    Retrieves call history with pagination and filtering.
    """
    
    def __init__(self, call_repository: CallRepository):
        self.call_repository = call_repository
        
    async def execute(
        self, 
        page: int = 1, 
        limit: int = 20, 
        client_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the use case.
        
        Args:
            page: Page number (1-based)
            limit: Items per page
            client_type: Optional filter by client type
            
        Returns:
            Dict containing 'calls' (list of dicts), 'total', 'page', 'total_pages'
        """
        offset = (page - 1) * limit
        calls, total_count = await self.call_repository.get_calls(
            limit=limit, 
            offset=offset, 
            client_type=client_type
        )
        
        # Map Domain Entities to DTOs/Dicts for the Interface
        # (Or return Entities and let Interface map? 
        # Usually UseCase returns DTOs or Entities. 
        # Returning dicts here acts as a simple DTO)
        display_calls = []
        for c in calls:
            duration = 0.0
            if c.end_time and c.start_time:
                 duration = (c.end_time - c.start_time).total_seconds()
                 
            display_calls.append({
                "id": c.id.value,
                "start_time": c.start_time.isoformat() if c.start_time else None,
                "status": c.status.value,
                "client_type": c.metadata.get("client_type", "unknown"),
                "extracted_data": c.metadata.get("extracted_data", {}),
                "duration": duration,
                "metadata": c.metadata
            })
            
        import math
        total_pages = math.ceil(total_count / limit) if limit > 0 else 1
        
        return {
            "calls": display_calls,
            "total": total_count,
            "page": page,
            "total_pages": total_pages,
            "current_filter": client_type or 'all'
        }
