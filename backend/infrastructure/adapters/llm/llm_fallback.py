"""
LLM Fallback Adapter - Resiliencia automática con failover.

Implementa failover automático entre múltiples proveedores LLM.
Patrón Decorador: Envuelve LLMPort primario + fallbacks.
"""
import logging
from typing import AsyncIterator

from backend.domain.ports.llm_port import (
    LLMPort,
    LLMRequest,
    LLMResponseChunk,
    LLMException
)
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent

logger = logging.getLogger(__name__)


class LLMFallbackAdapter(LLMPort):
    """
    Adaptador LLM con degradación elegante (graceful degradation).
    
    Intenta el proveedor primario primero, recurre a proveedores secundarios
    en caso de fallos reintentables.
    
    Ejemplo:
        >>> from backend.infrastructure.adapters.llm.groq_adapter import GroqAdapter
        >>> primary = GroqAdapter()
        >>> fallback1 = GroqAdapter()  # Otra instancia como backup
        >>> 
        >>> llm = LLMFallbackAdapter(primary=primary, fallbacks=[fallback1])
        >>> # Si primary falla (retryable), automáticamente usa fallback1
    """

    def __init__(self, primary: LLMPort, fallbacks: list[LLMPort]):
        """
        Inicializar LLM con fallbacks.
        
        Args:
            primary: Proveedor LLM primario (ej: Groq)
            fallbacks: Lista ordenada de proveedores fallback
        """
        self.primary = primary
        self.fallbacks = fallbacks
        
        logger.info(
            f"[LLM Fallback] Inicializado - Primary: {type(primary).__name__}, "
            f"Fallbacks: {len(fallbacks)}"
        )

    async def generate_stream(
        self,
        conversation: Conversation,
        agent: Agent
    ) -> AsyncIterator[LLMResponseChunk]:
        """
        Generar stream desde primario, fallback en fallos reintentables.
        
        Args:
            conversation: Conversación actual
            agent: Configuración del agente
            
        Yields:
            LLMResponseChunk: Chunks de respuesta (texto, tool_calls, etc)
            
        Raises:
            LLMException: Si todos los proveedores fallan
        """
        # Intentar primario primero
        try:
            logger.debug("[LLM Fallback] Intentando proveedor primario")
            async for chunk in self.primary.generate_stream(conversation, agent):
                yield chunk
            return  # Éxito - no se necesita fallback

        except LLMException as e:
            if not e.retryable or not self.fallbacks:
                # No reintentable o sin fallbacks disponibles
                logger.error(f"[LLM Fallback] Primario falló (no retryable): {e}")
                raise

            logger.warning(
                f"[LLM Fallback] Primario falló (retryable): {e}. "
                f"Intentando {len(self.fallbacks)} fallback(s)..."
            )

        # Intentar fallbacks
        for i, fallback in enumerate(self.fallbacks):
            try:
                logger.info(
                    f"[LLM Fallback] Intentando fallback {i+1}/{len(self.fallbacks)}: "
                    f"{type(fallback).__name__}"
                )
                async for chunk in fallback.generate_stream(conversation, agent):
                    yield chunk
                logger.info(f"[LLM Fallback] Fallback {i+1} exitoso")
                return  # Éxito

            except LLMException as e:
                if i == len(self.fallbacks) - 1:
                    # Último fallback falló - propagar error
                    logger.error("[LLM Fallback] Todos los proveedores fallaron")
                    raise

                # Intentar siguiente fallback
                logger.warning(f"[LLM Fallback] Fallback {i+1} falló: {e}")
                continue

    async def generate_response(self, conversation: Conversation, agent: Agent) -> str:
        """
        Generar respuesta simple (Legacy) con fallback.
        """
        # Intentar primario
        try:
            return await self.primary.generate_response(conversation, agent)
        except LLMException as e:
            if not e.retryable or not self.fallbacks:
                raise

            logger.warning(f"[LLM Fallback] Primario falló (retryable): {e}. Usando fallback.")

        # Intentar fallbacks
        for i, fallback in enumerate(self.fallbacks):
            try:
                return await fallback.generate_response(conversation, agent)
            except LLMException as e:
                if i == len(self.fallbacks) - 1:
                    raise
                continue

    async def get_available_models(self) -> list[str]:
        """
        Obtener modelos disponibles del proveedor primario.
        
        Returns:
            Lista de IDs de modelos disponibles
        """
        return await self.primary.get_available_models()

    def is_model_safe_for_voice(self, model: str) -> bool:
        """
        Verificar si modelo es seguro para voz del proveedor primario.
        
        Args:
            model: ID del modelo a verificar
            
        Returns:
            True si el modelo es seguro para uso en voz
        """
        return self.primary.is_model_safe_for_voice(model)
