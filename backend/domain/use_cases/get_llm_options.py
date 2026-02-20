"""
Get LLM Options Use Case.
Part of the Application Layer.
Returns available LLM providers and models.
"""
from typing import List, Dict, Any

class GetLLMOptionsUseCase:
    """
    Returns available LLM platforms and their supported models.
    """
    def __init__(self):
        # We define a static list mapping based on what adapters exist in the system.
        # Ideally, this could interact with llm_port directly if adapters exposed a method,
        # but for simplicity, we mock the available endpoints here aligning with standard adapters.
        pass

    async def get_providers(self) -> List[Dict[str, str]]:
        """Return available providers."""
        return [
            {"id": "groq", "name": "Groq"},
            {"id": "azure", "name": "Azure OpenAI"},
            {"id": "openai", "name": "OpenAI"},
        ]

    async def get_models(self, provider_id: str) -> List[Dict[str, str]]:
        """Return available models given a provider."""
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

