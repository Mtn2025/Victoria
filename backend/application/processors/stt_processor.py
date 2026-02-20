"""
STT Processor.
Part of the Application Layer (Hexagonal Architecture).
"""
import asyncio
import logging
from typing import Optional

from backend.application.processors.frames import Frame, AudioFrame, TextFrame, DataFrame, ControlFrame
from backend.application.processors.frame_processor import FrameProcessor, FrameDirection
from backend.domain.ports.stt_port import STTPort, STTSession
from backend.domain.value_objects.audio_format import AudioFormat

logger = logging.getLogger(__name__)

class STTProcessor(FrameProcessor):
    """
    Speech-to-Text Processor.
    Consumes AudioFrames -> Pushes to STT Provider.
    Consumes Results from STT -> Pushes TextFrames downstream.
    """

    def __init__(self, stt_provider: STTPort, audio_format: AudioFormat = AudioFormat.for_telephony()):
        super().__init__(name="STTProcessor")
        self.stt_provider = stt_provider
        self.audio_format = audio_format
        self.session: Optional[STTSession] = None
        self._reader_task: Optional[asyncio.Task] = None

    async def start(self):
        """Initialize STT Session."""
        try:
            # Start the streaming session via the Port
            self.session = await self.stt_provider.start_stream(format=self.audio_format)
            
            # Start background reader for results
            self._reader_task = asyncio.create_task(self._read_results())
            logger.info("STTProcessor started.")
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
                if self.session:
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
