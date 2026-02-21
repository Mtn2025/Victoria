"""
Central Registry for Supported LLM Models.
Single Source of Truth (SSoT) for the Victoria Project to prevent mismatched hardcodes
between UI presentation layers and LLM processing sub-systems.
"""
from typing import Dict, List, Any

# Format:
# Provider -> List of Dicts [{"id": model_id, "name": display_name, "voice_safe": bool}]
SUPPORTED_LLM_MODELS: Dict[str, List[Dict[str, Any]]] = {
    "groq": [
        {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "voice_safe": True},
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "voice_safe": True},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "voice_safe": True},
        {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "voice_safe": False},
    ],
    "azure": [
        {"id": "gpt-4o", "name": "GPT-4o", "voice_safe": True},
        {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo", "voice_safe": True}
    ],
    "openai": [
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "voice_safe": True},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "voice_safe": True}
    ]
}
