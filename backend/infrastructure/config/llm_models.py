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
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "voice_safe": True},
        {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "voice_safe": True},
        {"id": "openai/gpt-oss-20b", "name": "GPT-OSS 20B", "voice_safe": True},
        {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout 17B", "voice_safe": True},
        {"id": "qwen/qwen3-32b", "name": "Qwen3 32B", "voice_safe": True}
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
