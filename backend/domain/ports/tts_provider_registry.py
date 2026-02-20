"""
TTS Provider Registry Port (Interface).
Part of the Domain Layer (Hexagonal Architecture).
"""
from abc import ABC, abstractmethod
from typing import List
from backend.domain.ports.tts_port import TTSPort

class TTSProviderRegistry(ABC):
    """
    Registry for resolving TTS providers to their respective TTSPort adapters.
    """

    @abstractmethod
    def get_provider_adapter(self, provider_id: str) -> TTSPort:
        """
        Get the TTS adapter for a specific provider.
        
        Args:
            provider_id: The ID of the TTS provider (e.g., "azure", "elevenlabs").
            
        Returns:
            The corresponding TTSPort adapter.
            
        Raises:
            ValueError: If the provider is not supported or not configured.
        """
        pass

    @abstractmethod
    def get_supported_providers(self) -> List[str]:
        """
        Get a list of supported TTS provider IDs.
        """
        pass
