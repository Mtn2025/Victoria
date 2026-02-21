"""
VAD Processor.
Part of the Application Layer (Hexagonal Architecture).
"""
import logging
import time
import numpy as np
from typing import Optional, Any

from backend.application.processors.frames import Frame, AudioFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from backend.application.processors.frame_processor import FrameProcessor, FrameDirection
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase
from backend.infrastructure.adapters.vad.silero_vad import SileroVadAdapter

logger = logging.getLogger(__name__)

class VADProcessor(FrameProcessor):
    """
    Voice Activity Detection Processor.
    Uses Silero VAD to detect speech and manage turn-taking.
    """

    def __init__(self, config: Any, detect_turn_end: DetectTurnEndUseCase, vad_adapter: Optional[SileroVadAdapter] = None):
        super().__init__(name="VADProcessor")
        self.config = config
        self.detect_turn_end = detect_turn_end
        
        # Initialize Adapter
        self.vad_adapter = vad_adapter or SileroVadAdapter()
        
        # State
        self.buffer = bytearray()
        self.speaking = False
        self.silence_frames = 0
        self.speech_frames = 0
        self._voice_detected_at: Optional[float] = None
        
        # Parameters (Defaults from legacy)
        self.threshold_start = 0.5
        self.threshold_return = 0.35
        self.min_speech_frames = 3
        self.chunk_duration_ms = 32 # 512 samples @ 16k
        
        # Configurable params
        self.confirmation_window_ms = getattr(config, 'vad_confirmation_window_ms', 200)
        self.confirmation_enabled = getattr(config, 'vad_enable_confirmation', True)
        
        # Determine Sample Rate based on config usage in legacy
        # Assuming we can inspect config or default to something.
        # Legacy checked client_type.
        client_type = getattr(config, 'client_type', 'twilio')
        self.target_sr = 16000 if client_type == 'browser' else 8000

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, AudioFrame):
                # [PIPE-2] Audio frame arrived at VADProcessor
                logger.info(
                    f"[PIPE-2/VAD] AudioFrame received: {len(frame.data)}B "
                    f"sr={frame.sample_rate} ch={frame.channels}"
                )
                await self._process_audio(frame)
                await self.push_frame(frame, direction) # Pass audio through
            else:
                logger.debug(f"[PIPE-2/VAD] non-audio frame: {type(frame).__name__}")
                await self.push_frame(frame, direction)
        else:
            await self.push_frame(frame, direction)

    async def _process_audio(self, frame: AudioFrame):
        logger.info(
            f"[VAD ENTRY] buffer_before={len(self.buffer)} "
            f"frame_data={len(frame.data)} "
            f"vad_adapter={'OK' if self.vad_adapter else 'NONE'} "
            f"sample_rate={frame.sample_rate}"
        )

        if not self.vad_adapter:
            return

        # 1. Add to buffer
        self.buffer.extend(frame.data)
        
        # Use frame sample rate instead of hardcoded target_sr
        sample_rate = frame.sample_rate

        # 2. Process in correct chunk sizes (32ms of audio)
        # 8000Hz -> 256 samples | 16000Hz -> 512 samples | 24000Hz -> 768 samples
        if sample_rate == 24000:
            required_samples = 768
            target_sr = 16000
        elif sample_rate == 8000:
            required_samples = 256
            target_sr = 8000
        else:
            required_samples = 512
            target_sr = 16000

        chunk_size = required_samples * 2 # 16-bit = 2 bytes

        while len(self.buffer) >= chunk_size:
            chunk_bytes = self.buffer[:chunk_size]
            self.buffer = self.buffer[chunk_size:]

            # Convert bytes to float32 numpy array
            audio_int16 = np.frombuffer(chunk_bytes, dtype=np.int16)
            # Normalize to -1.0 to 1.0
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            # Resample 24k → 16k for Silero using linear interpolation.
            # np.arange(...).astype(int) truncates and creates irregular gaps
            # that distort the signal — Silero scores it as silence.
            # np.interp produces exactly 512 evenly-spaced samples.
            if sample_rate == 24000:
                x_old = np.arange(len(audio_float32))
                x_new = np.linspace(0, len(audio_float32) - 1, 512)
                audio_vad = np.interp(x_new, x_old, audio_float32)
            else:
                audio_vad = audio_float32

            logger.info(
                f"[VAD DEBUG] chunk_samples={len(audio_vad)} "
                f"sr_vad=16000 "
                f"min={float(audio_vad.min()):.4f} "
                f"max={float(audio_vad.max()):.4f} "
                f"rms={float(np.sqrt(np.mean(audio_vad**2))):.4f}"
            )

            # Log the exact chunk Silero receives — visible on any silent failure
            logger.info(
                f"[VAD SILERO IN] shape={audio_vad.shape} dtype={audio_vad.dtype} "
                f"min={float(audio_vad.min()):.4f} max={float(audio_vad.max()):.4f} "
                f"rms={float(np.sqrt(np.mean(audio_vad**2))):.4f} sr={target_sr}"
            )

            try:
                confidence = self.vad_adapter(audio_vad, target_sr)
            except Exception as e:
                logger.error(
                    f"[VAD SILERO ERROR] {e} — "
                    f"chunk shape={audio_vad.shape} dtype={audio_vad.dtype} "
                    f"min={float(audio_vad.min()):.4f} max={float(audio_vad.max()):.4f}"
                )
                confidence = 0.0

            logger.info(f"[VAD CONFIDENCE] conf={confidence:.4f} "
                        f"threshold={self.threshold_start}")

            # Smart Turn Logic
            if confidence > self.threshold_start:
                self.silence_frames = 0
                self.speech_frames += 1

                if not self.speaking and self.speech_frames >= self.min_speech_frames:
                    if not self._voice_detected_at:
                        self._voice_detected_at = time.time()
                        
                        if not self.confirmation_enabled or self.confirmation_window_ms <= 0:
                            await self._trigger_start_speaking(confidence, immediate=True)

                    elif self._voice_detected_at:
                        elapsed_ms = (time.time() - self._voice_detected_at) * 1000
                        if elapsed_ms >= self.confirmation_window_ms:
                            await self._trigger_start_speaking(confidence, immediate=False, elapsed=elapsed_ms)

            elif confidence < self.threshold_return:
                if self._voice_detected_at and not self.speaking:
                    elapsed_ms = (time.time() - self._voice_detected_at) * 1000
                    if elapsed_ms < self.confirmation_window_ms:
                        self._voice_detected_at = None
                        self.speech_frames = 0

                if self.speaking:
                    self.silence_frames += 1
                    
                    # Use Domain Use Case for Turn End Logic
                    # Logic: silence frames * chunk duration = total silence duration
                    silence_ms = self.silence_frames * self.chunk_duration_ms
                    
                    # Retrieve silence timeout from config
                    silence_timeout = getattr(self.config, 'silence_timeout_ms', 500)
                    
                    if self.detect_turn_end.execute(silence_ms, silence_timeout):
                        self.speaking = False
                        logger.info(f"User STOP speaking (Silence: {silence_ms}ms)")
                        await self.push_frame(UserStoppedSpeakingFrame(), FrameDirection.DOWNSTREAM)

    async def _trigger_start_speaking(self, confidence: float, immediate: bool, elapsed: float = 0):
        self.speaking = True
        self._voice_detected_at = None
        logger.info(f"User START speaking (Conf: {confidence:.2f})")
        await self.push_frame(UserStartedSpeakingFrame(), FrameDirection.DOWNSTREAM)
