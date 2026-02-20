"""
STT Fallback Adapter - Resiliencia automática para reconocimiento de voz.

Implementa failover automático para speech recognition.
"""
import logging
from typing import Optional, Callable

from backend.domain.ports.stt_port import (
    STTPort,
    STTSession,
    STTConfig,
    STTException
)
from backend.domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)


class STTFallbackAdapter(STTPort):
    """
    Adaptador STT con degradación elegante (graceful degradation).
    
    Recurre a proveedor STT alternativo en caso de fallos.
    
    Ejemplo:
        >>> from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter
        >>> primary = AzureSTTAdapter()
        >>> fallback = AzureSTTAdapter()  # Otra instancia
        >>> 
        >>> stt = STTFallbackAdapter(primary=primary, fallback=fallback)
        >>> # Si primary falla, automáticamente usa fallback
    """

    def __init__(self, primary: STTPort, fallback: Optional[STTPort] = None):
        """
        Inicializar STT con fallback.
        
        Args:
            primary: Proveedor STT primario (ej: Azure)
            fallback: Proveedor fallback opcional (ej: Google)
        """
        self.primary = primary
        self.fallback = fallback
        
        logger.info(
            f"[STT Fallback] Inicializado - Primary: {type(primary).__name__}, "
            f"Fallback: {type(fallback).__name__ if fallback else 'None'}"
        )

    async def transcribe(self, audio: bytes, format: AudioFormat, language: str = "es-MX") -> str:
        """
        Transcribir audio con fallback.
        
        Args:
            audio: Audio bytes
            format: Formato de audio
            language: Idioma
            
        Returns:
            Texto transcrito
            
        Raises:
            STTException: Si ambos proveedores fallan
        """
        try:
            logger.debug("[STT Fallback] Transcribiendo con primario")
            return await self.primary.transcribe(audio, format, language)

        except STTException as e:
            if not e.retryable or not self.fallback:
                logger.error(f"[STT Fallback] Primario falló (no retryable o sin fallback): {e}")
                raise

            logger.warning(
                f"[STT Fallback] Primario falló (retryable): {e}. "
                f"Usando fallback..."
            )
            return await self.fallback.transcribe(audio, format, language)

    async def start_stream(
        self,
        config: STTConfig,
        on_final_result: Callable[[str], None],
        on_partial_result: Optional[Callable[[str], None]] = None
    ) -> STTSession:
        """
        Iniciar sesión de reconocimiento continuo con fallback.
        
        Args:
            config: Configuración STT
            on_final_result: Callback para resultados finales
            on_partial_result: Callback opcional para resultados parciales
            
        Returns:
            Sesión STT activa
            
        Raises:
            STTException: Si ambos proveedores fallan al crear sesión
        """
        try:
            logger.info("[STT Fallback] Creando sesión stream con primario")
            return await self.primary.start_stream(
                config,
                on_final_result,
                on_partial_result
            )

        except STTException as e:
            if not e.retryable or not self.fallback:
                logger.error(
                    f"[STT Fallback] Primario falló al crear sesión "
                    f"(no retryable o sin fallback): {e}"
                )
                raise

            logger.warning(
                f"[STT Fallback] Primario falló al crear sesión: {e}. "
                f"Intentando fallback..."
            )
            return await self.fallback.start_stream(
                config,
                on_final_result,
                on_partial_result
            )

    async def close(self) -> None:
        """Cerrar ambos proveedores."""
        await self.primary.close()
        if self.fallback:
            await self.fallback.close()
        logger.info("[STT Fallback] Proveedores cerrados")
