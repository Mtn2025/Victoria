"""
Static LLM Registry Adapter.
Part of the Infrastructure Layer.
Implements the LLMProviderRegistry port.
"""
from typing import List, Dict
from backend.domain.ports.llm_provider_registry import LLMProviderRegistry
from backend.infrastructure.config.llm_models import SUPPORTED_LLM_MODELS

class StaticLLMRegistryAdapter(LLMProviderRegistry):
    """
    Returns available LLM platforms and their supported models statically configured.
    Ideally, this would dynamically check which API keys are present.
    """
    async def get_providers(self) -> List[Dict[str, str]]:
        return [
            {"id": "groq", "name": "Groq"},
            {"id": "azure", "name": "Azure OpenAI"},
            {"id": "openai", "name": "OpenAI"},
        ]

    async def get_models(self, provider_id: str) -> List[Dict[str, str]]:
        models = SUPPORTED_LLM_MODELS.get(provider_id, [])
        return [{"id": m["id"], "name": m["name"]} for m in models]
