"""
Static LLM Registry Adapter.
Part of the Infrastructure Layer.
Implements the LLMProviderRegistry port.
"""
from typing import List, Dict
from backend.domain.ports.llm_provider_registry import LLMProviderRegistry

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
        models_by_provider = {
            "groq": [
                {"id": "llama3-8b-8192", "name": "Llama 3 8B"},
                {"id": "llama3-70b-8192", "name": "Llama 3 70B"},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
            ],
            "azure": [
                {"id": "gpt-4o", "name": "GPT-4o"},
                {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo"}
            ],
            "openai": [
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
            ]
        }
        return models_by_provider.get(provider_id, [])
