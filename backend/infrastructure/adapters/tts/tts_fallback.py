"""
TTS Fallback Adapter - Resiliencia con Circuit Breaker.

Implementa failover automático con patrón Circuit Breaker para TTS.
Después de N fallos consecutivos, cambia automáticamente a modo fallback.
"""
import logging
from typing import AsyncIterator, Optional

from backend.domain.ports.tts_port import (
    TTSPort,
    TTSRequest,
    TTSException,
    VoiceMetadata
)
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)


class TTSFallbackAdapter(TTSPort):
    """
    Adaptador TTS con fallback automático y Circuit Breaker.
    
    Patrón de Resiliencia: Circuit Breaker + Fallback
    
    Comportamiento:
    1. Siempre intentar TTS primario primero
    2. En caso de fallo, usar TTS fallback
    3. Después de 3 fallos consecutivos, cambiar a modo fallback
    4. Auto-recuperación al primario después de éxito
    
    Ejemplo:
        >>> from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
        >>> primary = AzureTTSAdapter()
        >>> fallback = AzureTTSAdapter()  # Otra instancia
        >>> 
        >>> tts = TTSFallbackAdapter(primary=primary, fallback=fallback)
        >>> # Si Azure falla 3 veces, automáticamente cambia a fallback
    """

    def __init__(self, primary: TTSPort, fallback: TTSPort, failure_threshold: int = 3):
        """
        Inicializar TTS con fallback.
        
        Args:
            primary: Adaptador TTS primario (ej: AzureTTSAdapter)
            fallback: Adaptador TTS fallback (ej: GoogleTTSAdapter)
            failure_threshold: Número de fallos antes de activar modo fallback
        """
        self.primary = primary
        self.fallback = fallback

        # Estado circuit breaker
        self._primary_failures = 0
        self._failure_threshold = failure_threshold
        self._fallback_active = False

        logger.info(
            f"[TTS Fallback] Inicializado - Primary: {type(primary).__name__}, "
            f"Fallback: {type(fallback).__name__}, "
            f"Threshold: {failure_threshold}"
        )

    async def synthesize(
        self,
        text: str,
        voice: VoiceConfig,
        format: AudioFormat
    ) -> bytes:
        """
        Sintetizar voz con fallback automático.
        
        Args:
            text: Texto a sintetizar
            voice: Configuración de voz
            format: Formato de audio deseado
            
        Returns:
            Audio bytes completo
            
        Raises:
            TTSException: Si AMBOS primario Y fallback fallan
        """
        # Auto-recuperación: Resetear modo fallback si primario funciona
        if self._fallback_active and self._primary_failures == 0:
            self._fallback_active = False
            logger.info("[TTS Fallback] Primario recuperado, volviendo desde fallback")

        # Intentar primario si no está en modo fallback
        if not self._fallback_active:
            try:
                logger.debug(f"[TTS Fallback] Usando PRIMARY: {type(self.primary).__name__}")
                audio = await self.primary.synthesize(text, voice, format)
                
                # Éxito - resetear contador de fallos
                self._primary_failures = 0
                return audio

            except TTSException as e:
                self._primary_failures += 1

                logger.warning(
                    f"[TTS Fallback] Primario falló ({self._primary_failures}/{self._failure_threshold}): {e}, "
                    f"usando fallback"
                )

                # Cambiar a modo fallback después del umbral
                if self._primary_failures >= self._failure_threshold:
                    self._fallback_active = True
                    logger.error(
                        f"[TTS Fallback] Primario falló {self._failure_threshold}x, "
                        f"CAMBIANDO A MODO FALLBACK"
                    )

        # Usar fallback (ya sea que estaba en modo fallback, o primario acaba de fallar)
        try:
            logger.info(f"[TTS Fallback] Usando FALLBACK: {type(self.fallback).__name__}")
            return await self.fallback.synthesize(text, voice, format)

        except TTSException as fallback_error:
            logger.error(f"[TTS Fallback] AMBOS primario Y fallback fallaron! {fallback_error}")
            raise TTSException(
                message=f"TTS fallo completo - Primary: {type(self.primary).__name__}, "
                        f"Fallback: {type(self.fallback).__name__}",
                retryable=False,
                provider="fallback"
            ) from fallback_error

    async def synthesize_request(self, request: TTSRequest) -> bytes:
        """
        Sintetizar usando TTSRequest estructurado (método avanzado).
        
        Args:
            request: Request de síntesis TTS
            
        Returns:
            Audio bytes
        """
        # Delegar a synthesize() con circuit breaker logic
        # (se podría implementar lógica específica aquí si es necesario)
        voice = VoiceConfig(
            name=request.voice_id,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            style=request.style
        )
        
        # Parsear formato
        if "16000" in request.format or "16k" in request.format:
            audio_format = AudioFormat(sample_rate=16000, channels=1, bits_per_sample=16, encoding="pcm")
        elif "8000" in request.format or "8k" in request.format:
            audio_format = AudioFormat(sample_rate=8000, channels=1, bits_per_sample=8, encoding="mulaw")
        else:
            audio_format = AudioFormat(sample_rate=16000, channels=1, bits_per_sample=16, encoding="pcm")
        
        return await self.synthesize(request.text, voice, audio_format)

    async def synthesize_ssml(self, ssml: str) -> bytes:
        """
        Sintetizar directamente desde markup SSML con estrategia fallback.
        
        Args:
            ssml: Markup SSML
            
        Returns:
            Audio bytes
        """
        try:
            return await self.primary.synthesize_ssml(ssml)
        except TTSException as e:
            logger.warning(f"[TTS Fallback] SSML primario falló: {e}. Intentando fallback.")
            return await self.fallback.synthesize_ssml(ssml)

    async def synthesize_stream(
        self,
        text: str,
        voice: VoiceConfig,
        format: AudioFormat
    ) -> AsyncIterator[bytes]:
        """
        Stream de síntesis con capacidades fallback.
        
        Args:
            text: Texto a sintetizar
            voice: Configuración de voz
            format: Formato de audio
            
        Yields:
            Chunks de audio
        """
        # Auto-recuperación
        if self._fallback_active and self._primary_failures == 0:
            self._fallback_active = False
            logger.info("[TTS Fallback] Primario recuperado, volviendo desde fallback")

        # INTENTAR PRIMARIO
        if not self._fallback_active:
            try:
                async for chunk in self.primary.synthesize_stream(text, voice, format):
                    yield chunk

                self._primary_failures = 0
                return

            except TTSException as e:
                self._primary_failures += 1
                logger.warning(
                    f"[TTS Fallback] Primario falló ({self._primary_failures}/{self._failure_threshold}): {e}. "
                    f"Cambiando a fallback."
                )
                if self._primary_failures >= self._failure_threshold:
                    self._fallback_active = True
                    logger.error(f"[TTS Fallback] Umbral primario alcanzado. Mode=FALLBACK.")

        # INTENTAR FALLBACK
        try:
            logger.info(f"[TTS Fallback] Usando FALLBACK: {type(self.fallback).__name__}")
            async for chunk in self.fallback.synthesize_stream(text, voice, format):
                yield chunk

        except TTSException as fallback_error:
            logger.error(f"[TTS Fallback] Fallo Crítico: Ambos proveedores fallaron. {fallback_error}")
            raise TTSException(
                message=f"TTS fallo completo",
                retryable=False,
                provider="fallback"
            ) from fallback_error

    async def get_available_voices(self, language: Optional[str] = None) -> list[VoiceMetadata]:
        """
        Obtener voces disponibles del proveedor primario.
        
        Args:
            language: Código de idioma opcional para filtrar
            
        Returns:
            Lista de metadatos de voces
        """
        # Delegar al primario (voces fallback pueden diferir)
        return await self.primary.get_available_voices(language)

    def get_voice_styles(self, voice_id: str) -> list[str]:
        """
        Obtener estilos de voz del proveedor primario.
        
        Args:
            voice_id: ID de voz
            
        Returns:
            Lista de estilos disponibles
        """
        return self.primary.get_voice_styles(voice_id)

    async def close(self) -> None:
        """Cerrar ambos proveedores primario y fallback."""
        await self.primary.close()
        await self.fallback.close()
        logger.info("[TTS Fallback] Ambos proveedores cerrados")

    @property
    def is_using_fallback(self) -> bool:
        """Verificar si actualmente está en modo fallback."""
        return self._fallback_active

    @property
    def failure_count(self) -> int:
        """Obtener contador actual de fallos."""
        return self._primary_failures
