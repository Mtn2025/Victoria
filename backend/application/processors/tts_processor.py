"""
TTS Processor.
Part of the Application Layer (Hexagonal Architecture).
"""
import asyncio
import logging
from typing import Any, Optional, Tuple

from backend.application.processors.frames import Frame, TextFrame, AudioFrame, CancelFrame
from backend.application.processors.frame_processor import FrameProcessor, FrameDirection
from backend.domain.ports.tts_port import TTSPort
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)

class TTSProcessor(FrameProcessor):
    """
    Text-to-Speech Processor.
    Consumes TextFrames (Assistant) -> Synthesizes Audio -> Delivers via output_callback.
    Includes serialization queue to prevent overlapping speech.

    CRITICAL: TTS is the DOWNSTREAM END of the pipeline chain.
    Synthesized audio MUST go to the caller via output_callback, NOT push_frame(DOWNSTREAM)
    because DOWNSTREAM at the end of chain is silently discarded by FrameProcessor.push_frame().
    The output_callback is set by CallOrchestrator to route audio back to the WebSocket.
    """

    def __init__(self, tts_port: TTSPort, config: Any, output_callback=None):
        super().__init__(name="TTSProcessor")
        self.tts_port = tts_port
        self.config = config
        # Coroutine callback: async def cb(audio_bytes: bytes) -> None
        # Set by CallOrchestrator to route TTS output back to WebSocket transport.
        self.output_callback = output_callback
        
        # Internal Queue for serial synthesis
        self._tts_queue: asyncio.Queue[Tuple[str, str]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self):
        """Start TTS worker."""
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("TTSProcessor started.")

    async def stop(self):
        """Stop TTS worker."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        await super().stop()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, TextFrame):
                # Ensure worker running
                if not self._is_running:
                    await self.start()
                    
                # Only synthesize Assistant text
                if frame.role == "assistant":
                    logger.debug(f"Queuing TTS for: {frame.text[:30]}...")
                    await self._tts_queue.put((frame.text, frame.trace_id))
                else:
                    # Pass through user text (maybe for logging downstream)
                    await self.push_frame(frame, direction)
                    
            elif isinstance(frame, CancelFrame):
                logger.info("Received CancelFrame. Clearing TTS queue.")
                await self._clear_queue()
                await self.push_frame(frame, direction)
                
            else:
                await self.push_frame(frame, direction)
        else:
            await self.push_frame(frame, direction)

    async def _worker(self):
        """Consume text and synthesize serially."""
        while self._is_running:
            try:
                text, trace_id = await self._tts_queue.get()
                await self._synthesize(text, trace_id)
                self._tts_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TTS Worker Error: {e}")

    async def _clear_queue(self):
        """Flush pending items."""
        while not self._tts_queue.empty():
            try:
                self._tts_queue.get_nowait()
                self._tts_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # Ideally, we should also cancel the current interaction with the Port 
        # but the Port interface doesn't expose a 'cancel' method on the generator easily
        # without breaking the loop in _synthesize.
        # We can restart the worker?
        # For simple robust implementation, simply clearing queue prevents FUTURE speech.
        # To stop CURRENT speech, we depend on _synthesize checking a flag or simple restart.
        
        # Restart worker to kill current synthesis logic if stuck or active
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                 await self._worker_task
            except asyncio.CancelledError:
                 pass
            if self._is_running:
                self._worker_task = asyncio.create_task(self._worker())

    async def _synthesize(self, text: str, trace_id: str):
        if not text:
            return

        # Config is always a ConfigDTO (converted from Agent via _agent_to_config_dto
        # in call_orchestrator). All voice fields are flat attributes on ConfigDTO.
        # SSoT chain: DB → Agent.voice_config → ConfigDTO.voice_name → here.
        def get_cfg(key, default=None):
            if isinstance(self.config, dict):
                return self.config.get(key, default)
            return getattr(self.config, key, default)

        voice_config = VoiceConfig(
            name         = get_cfg('voice_name',         'es-MX-DaliaNeural'),
            speed        = get_cfg('voice_speed',        1.0),
            pitch        = int(get_cfg('voice_pitch',    0)),
            volume       = int(get_cfg('voice_volume',   100)),
            style        = get_cfg('voice_style',        'default'),
            style_degree = float(get_cfg('voice_style_degree', 1.0)),
        )
        
        client_type = get_cfg('client_type', 'browser')  # browser=24kHz PCM; twilio=8kHz mulaw
        audio_format = AudioFormat.for_client(client_type)
        
        logger.info(f"Synthesizing: {text[:30]}... (Voice: {voice_config.name})")
        # [PIPE-9] TTS synthesis starting
        logger.info(
            f"[PIPE-9/TTS] Synthesizing: {text[:50]!r} "
            f"voice={voice_config.name} fmt=sr={audio_format.sample_rate}"
        )


        try:
            async for audio_chunk in self.tts_port.synthesize_stream(text, voice_config, audio_format):
                if audio_chunk:
                    if self.output_callback:
                        # PRIMARY PATH: send directly to transport (WebSocket/Telephony)
                        # TTS is the LAST downstream processor — push_frame(DOWNSTREAM)
                        # would be silently dropped. output_callback bypasses this.
                        try:
                            await self.output_callback(audio_chunk)
                        except Exception as cb_err:
                            logger.error(f"[TTS] output_callback error: {cb_err}")
                    else:
                        # FALLBACK: push upstream for any processor that wants to intercept
                        # (e.g. recording, metrics). Not used in production path.
                        await self.push_frame(
                            AudioFrame(
                                data=audio_chunk,
                                sample_rate=audio_format.sample_rate,
                                channels=audio_format.channels,
                                metadata={"trace_id": trace_id}
                            ),
                            FrameDirection.UPSTREAM
                        )
        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            print(f"DEBUG: Synthesis failed: {e}")
