"""
Prompt Builder Service.
Part of the Application Layer (Hexagonal Architecture).
"""
import logging
import json
from typing import Any, Dict

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Constructs the dynamic System Prompt based on configuration.
    """

    @staticmethod
    def build_system_prompt(config: Any, context: Dict[str, Any] | None = None) -> str:
        """
        Combines base system prompt with dynamic style instructions AND context variables.
        """
        # Safe attribute access using getattr to support dict or object
        def get_cfg(key, default=None):
            if isinstance(config, dict):
                return config.get(key, default)
            return getattr(config, key, default)

        base_prompt = get_cfg('system_prompt', '') or "Eres un asistente útil."

        # 1. Parsing Configuration
        # Keys stored by PATCH endpoint in llm_config as camelCase (responseLength, etc.).
        # ConfigDTO exposes them via _agent_to_config_dto() under snake_case too.
        # Try both to support both storage formats.
        def get_cfg_multi(*keys, default=None):
            for key in keys:
                v = get_cfg(key)
                if v is not None:
                    return v
            return default

        length    = get_cfg_multi('response_length',           'responseLength',          default='short')
        tone      = get_cfg_multi('conversation_tone',         'conversationTone',        default='warm')
        formality = get_cfg_multi('conversation_formality',    'conversationFormality',   default='semi_formal')

        # 2. Instruction Maps
        length_instructions = {
            "very_short": "Responde de forma extremadamente concisa (máximo 10 palabras).",
            "short": "Mantén las respuestas cortas y directas (1-2 frases).",
            "medium": "Da explicaciones equilibradas, ni muy cortas ni muy largas.",
            "long": "Desarróllate libremente, da respuestas completas.",
            "detailed": "Provee tanto detalle como sea posible, sé exhaustivo."
        }

        tone_instructions = {
            "professional": "Mantén un tono estrictamente profesional, objetivo y corporativo.",
            "friendly": "Sé amigable y cercano, como un colega.",
            "warm": "Usa un tono cálido, empático y acogedor, haz sentir bien al usuario.",
            "enthusiastic": "Muestra energía y entusiasmo, sé motivador.",
            "neutral": "Sé neutral y desapegado, solo hechos.",
            "empathetic": "Muestra profunda comprensión y cuidado por las emociones."
        }

        formality_instructions = {
            "very_formal": "Usa un lenguaje muy formal y respetuoso (trata de 'usted', vocabulario elevado).",
            "formal": "Trata de 'usted' y mantén la etiqueta.",
            "semi_formal": "Equilibrado: respetuoso pero accesible (puedes usar 'usted' o 'tú' según contexto).",
            "casual": "Trata de 'tú', sé relajado y natural.",
            "very_casual": "Usa jerga coloquial, sé muy informal, como un amigo."
        }

        # 3. Construct Overrides
        style_block = []
        if length in length_instructions:
            style_block.append(f"- Longitud: {length_instructions[length]}")
        
        if tone in tone_instructions:
            style_block.append(f"- Tono: {tone_instructions[tone]}")
        
        if formality in formality_instructions:
            style_block.append(f"- Formalidad: {formality_instructions[formality]}")

        dynamic_instructions = "\n".join(style_block)

        final_prompt = f"""{base_prompt}

<dynamic_style_overrides>
{dynamic_instructions}
</dynamic_style_overrides>
"""
        # 4. Inject Context Variables
        if context:
            try:
                # Format as structured block
                context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])
                final_prompt += f"""
<context_data>
{context_str}
</context_data>
"""
            except Exception as e:
                logger.warning(f"Error injecting context: {e}")

        # 5. Inject Dynamic Variables ({placeholder})
        dynamic_vars_enabled = get_cfg('dynamic_vars_enabled', False)
        if dynamic_vars_enabled:
            dynamic_vars = get_cfg('dynamic_vars', None)
            if dynamic_vars:
                try:
                    if isinstance(dynamic_vars, str):
                        dynamic_vars = json.loads(dynamic_vars)
                    
                    for key, value in dynamic_vars.items():
                        placeholder = f"{{{key}}}"
                        final_prompt = final_prompt.replace(placeholder, str(value))
                except Exception as e:
                    logger.warning(f"Error injecting dynamic variables: {e}")

        return final_prompt
