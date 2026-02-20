"""
LLM Provider Registry Port.
Part of the Domain Layer (Hexagonal Architecture).
"""
from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProviderRegistry(ABC):
    """
    Interface for querying available LLM Providers and Models across the system.
    """
    @abstractmethod
    async def get_providers(self) -> List[Dict[str, str]]:
        """Return available providers as [{'id': 'groq', 'name': 'Groq'}, ...]"""
        pass

    @abstractmethod
    async def get_models(self, provider_id: str) -> List[Dict[str, str]]:
        """Return available models for a given provider id."""
        pass
