"""
Get LLM Options Use Case.
Part of the Application Layer.
Returns available LLM providers and models.
"""
from typing import List, Dict

from backend.domain.ports.llm_provider_registry import LLMProviderRegistry

class GetLLMOptionsUseCase:
    """
    Retrieves available LLM options using an injected registry port.
    """
    def __init__(self, registry: LLMProviderRegistry):
        self.registry = registry

    async def get_providers(self) -> List[Dict[str, str]]:
        """Return available providers."""
        return await self.registry.get_providers()

    async def get_models(self, provider_id: str) -> List[Dict[str, str]]:
        """Return available models given a provider."""
        return await self.registry.get_models(provider_id)

