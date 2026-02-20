from typing import List
from backend.domain.ports.persistence_port import CallRepository
from backend.domain.value_objects.call_id import CallId

class DeleteSelectedCallsUseCase:
    def __init__(self, call_repository: CallRepository):
        self.call_repository = call_repository

    async def execute(self, call_ids: List[str]) -> int:
        deleted_count = 0
        for cid in call_ids:
            try:
                # Assuming CallId validation happens here or inside repo
                await self.call_repository.delete(CallId(cid))
                deleted_count += 1
            except Exception:
                # Log or handle individual failure? Port doesn't specify return
                pass
        return deleted_count

class ClearHistoryUseCase:
    def __init__(self, call_repository: CallRepository):
        self.call_repository = call_repository

    async def execute(self) -> int:
        return await self.call_repository.clear()
