"""
Static LLM Registry Adapter.
Part of the Infrastructure Layer.
Implements the LLMProviderRegistry port.
"""
import os
from typing import List, Dict
from backend.domain.ports.llm_provider_registry import LLMProviderRegistry
from backend.infrastructure.config.llm_models import SUPPORTED_LLM_MODELS

class StaticLLMRegistryAdapter(LLMProviderRegistry):
    """
    Returns available LLM platforms and their supported models dynamically filtered
    by checking which API keys are present in the environment variables.
    """
    async def get_providers(self) -> List[Dict[str, str]]:
        providers = []
        
        # Groq
        if os.environ.get("GROQ_API_KEY"):
            providers.append({"id": "groq", "name": "Groq"})
            
        # Azure OpenAI
        if os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
            providers.append({"id": "azure", "name": "Azure OpenAI"})
            
        # Si no hay ninguno configurado, devolver al menos un indicador o la lista vacía
        if not providers:
            # Fallback for debugging, but typically should be empty if strictly enforcing keys
            return [{"id": "none", "name": "No API Keys Configured"}]
            
        return providers

    async def get_models(self, provider_id: str) -> List[Dict[str, str]]:
        models = SUPPORTED_LLM_MODELS.get(provider_id, [])
        return [{"id": m["id"], "name": m["name"]} for m in models]
