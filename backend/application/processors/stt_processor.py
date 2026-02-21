"""
STT Processor.
Part of the Application Layer (Hexagonal Architecture).

NOTA: audio_format DEBE ser pasado explícitamente por PipelineFactory.
Ningún formato se asume por defecto (ver contrato en audio_format.py).
"""
import asyncio
import logging
from typing import Any, Optional

from backend.application.processors.frames import Frame, AudioFrame, TextFrame, DataFrame, ControlFrame
from backend.application.processors.frame_processor import FrameProcessor, FrameDirection
from backend.domain.ports.stt_port import STTPort, STTSession, STTConfig
from backend.domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)

class STTProcessor(FrameProcessor):
    """
    Speech-to-Text Processor.
    Consumes AudioFrames -> Pushes to STT Provider.
    Consumes Results from STT -> Pushes TextFrames downstream.
    """

    def __init__(self, stt_provider: STTPort, audio_format: Optional[AudioFormat] = None, config: Any = None):
        super().__init__(name="STTProcessor")
        self.stt_provider = stt_provider
        self.audio_format = audio_format
        self.config = config  # ConfigDTO — used to build STTConfig at session start
        self.session: Optional[STTSession] = None
        self._reader_task: Optional[asyncio.Task] = None
        logger.info(
            f"[STT INIT] audio_format declared: "
            f"sr={audio_format.sample_rate if audio_format else 'NONE'} "
            f"bits={audio_format.bits_per_sample if audio_format else 'NONE'} "
            f"enc={audio_format.encoding if audio_format else 'NONE'}"
        )

    async def start(self):
        """Initialize STT Session."""
        # --- Fast-fail: formato obligatorio ---
        if self.audio_format is None:
            raise ValueError(
                "STTProcessor requires an explicit audio_format. "
                "PipelineFactory must pass AudioFormat.for_client(config.client_type). "
                "No default format is assumed to avoid silent mismatch with the STT provider."
            )

        # --- Build STTConfig from ConfigDTO (SSoT: DB → ConfigDTO → here) ---
        def _get(key, default=None):
            if self.config is None:
                return default
            if isinstance(self.config, dict):
                return self.config.get(key, default)
            return getattr(self.config, key, default)

        stt_config = STTConfig(
            language         = _get('stt_language', 'es-MX'),
            silence_timeout  = _get('silence_timeout_ms', 1000),
        )
        logger.info(
            f"[STT CFG] language={stt_config.language!r} "
            f"silence_timeout={stt_config.silence_timeout}ms"
        )

        try:
            # Start the streaming session via the Port
            self.session = await self.stt_provider.start_stream(
                format=self.audio_format,
                config=stt_config,
            )
            # Start background reader for results
            self._reader_task = asyncio.create_task(self._read_results())
            logger.info(
                f"STTProcessor started. "
                f"Format: sr={self.audio_format.sample_rate} "
                f"bits={self.audio_format.bits_per_sample} "
                f"enc={self.audio_format.encoding}"
            )
        except Exception as e:
            logger.error(f"Failed to start STTProcessor: {e}")
            raise

    async def stop(self):
        """Close session and cleanup."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("STTProcessor stopped.")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Handle frames.
        DOWNSTREAM: Audio -> STT
        UPSTREAM: Just pass through
        """
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, AudioFrame):
                # [PIPE-4] AudioFrame arrived at STTProcessor
                logger.debug(
                    f"[PIPE-4/STT] AudioFrame: {len(frame.data)}B "
                    f"sr={frame.sample_rate} session={'ACTIVE' if self.session else 'NONE'}"
                )
                # --- Mismatch guard: detecta discrepancia de formato en runtime ---
                if self.audio_format and frame.sample_rate != self.audio_format.sample_rate:
                    logger.warning(
                        f"[STT MISMATCH] Frame sample_rate={frame.sample_rate} "
                        f"!= declared format sample_rate={self.audio_format.sample_rate}. "
                        f"Azure recibirá audio ininteligible. "
                        f"Verifica client_type en la configuración del agente."
                    )
                if self.session:
                    # [PIPE-5] Bytes entering Azure push_stream
                    logger.debug(
                        f"[PIPE-5/STT→AZURE] sending {len(frame.data)}B "
                        f"to session.process_audio()"
                    )
                    # Push content to STT
                    await self.session.process_audio(frame.data)
                    
                    # Also pass audio downstream (e.g. for VAD or saving)
                    await self.push_frame(frame, direction)
                else:
                    logger.warning("STT Session not active, dropping audio.")
            else:
                # Pass other frames (Control, System, etc.)
                await self.push_frame(frame, direction)
        else:
            # Pass UPSTREAM frames
            await self.push_frame(frame, direction)

    async def _read_results(self):
        """
        Background task to read text from STT Session and inject into pipeline.
        """
        if not self.session:
            return

        try:
            async for text in self.session.get_results():
                if text:
                    logger.debug(f"STT Recognized: {text}")
                    # Create TextFrame
                    # TODO: Determine if final or interim. 
                    # The Port interface `get_results` docstring says "Yields finalized text segments".
                    # So we assume is_final=True for now.
                    frame = TextFrame(
                        text=text,
                        is_final=True,
                        role="user", 
                        metadata={"source": "stt"}
                    )
                    # Push downstream (to LLM/Aggregator)
                    await self.push_frame(frame, FrameDirection.DOWNSTREAM)
        except asyncio.CancelledError:
            logger.debug("STT result reader cancelled.")
        except Exception as e:
            logger.error(f"Error reading STT results: {e}")
