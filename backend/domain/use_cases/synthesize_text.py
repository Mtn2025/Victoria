"""
Synthesize Text Use Case.

Domain Use Case: Convert text to speech audio without LLM generation.
Used for: greetings, errors, system messages.
"""
import logging
from typing import Optional

from backend.domain.ports.tts_port import TTSPort
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)


class SynthesizeTextUseCase:
    """
    Synthesize text to speech audio (bypass LLM).

    Use Case: Direct TTS synthesis for system messages.

    Use when:
    - Initial greetings
    - Error messages
    - System notifications
    - Pre-defined responses

    Example:
        >>> use_case = SynthesizeTextUseCase(tts_port)
        >>> audio = await use_case.execute(
        ...     text="Hello, how can I help you?",
        ...     voice_config=voice_config
        ... )
    """

    def __init__(self, tts_port: TTSPort):
        """
        Initialize use case.

        Args:
            tts_port: TTS provider (Azure, Google, ElevenLabs, etc.)
        """
        self.tts = tts_port

    async def execute(
        self,
        text: str,
        voice_config: VoiceConfig,
        trace_id: Optional[str] = None,
        audio_format: Optional[AudioFormat] = None,
    ) -> bytes:
        """
        Synthesize text to audio.

        Args:
            text:         Text to synthesize
            voice_config: Voice configuration (name, style, speed, pitch)
            trace_id:     Optional trace ID for logging
            audio_format: Output audio format. Defaults to AudioFormat.for_browser()
                          (PCM16 @ 24kHz) which is used for greetings sent to the
                          browser/simulator. Pass AudioFormat.for_telephony() for
                          Twilio/Telnyx calls.

        Returns:
            Audio bytes in the requested format

        Raises:
            Exception: If TTS synthesis fails
        """
        fmt = audio_format or AudioFormat.for_browser()

        logger.info(
            f"[{trace_id or 'no-trace'}] Synthesizing text: {text[:50]}... "
            f"(format={fmt.encoding}@{fmt.sample_rate}Hz)"
        )

        try:
            audio = await self.tts.synthesize(text, voice_config, fmt)

            audio_size = len(audio) if audio else 0
            logger.info(
                f"[{trace_id or 'no-trace'}] Synthesis complete: {audio_size} bytes"
            )

            return audio

        except Exception as e:
            logger.error(
                f"[{trace_id or 'no-trace'}] TTS synthesis failed: {e}",
                exc_info=True,
            )
            raise
