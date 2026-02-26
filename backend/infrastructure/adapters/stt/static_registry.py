"""
Static STT Registry Adapter.
Part of the Infrastructure Layer.

Provides dynamic detection of available STT providers based on environment variables.
Follows the same pattern as TTS/LLM registries for consistency.
"""
import os
from typing import List, Dict, Any

class StaticSTTRegistryAdapter:
    """
    Adapter that detects and returns available Speech-to-Text providers.
    
    It checks for the presence of necessary API keys in the environment
    to dynamically populate the list of providers sent to the frontend.
    """
    
    async def get_providers(self) -> List[Dict[str, Any]]:
        """
        Returns a list of available STT providers based on configured API keys.
        """
        providers = []
        
        # Azure Speech STT (Always check key)
        if os.environ.get("AZURE_SPEECH_KEY"):
            providers.append({
                "id": "azure",
                "name": "Azure Speech",
                "features": ["streaming", "multilingual"]
            })
            
        # Deepgram STT (Fallback / Alternative)
        if os.environ.get("DEEPGRAM_API_KEY"):
            providers.append({
                "id": "deepgram",
                "name": "Deepgram",
                "features": ["streaming", "semantic_endpointing"]
            })
            
        return providers
