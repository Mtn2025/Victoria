"""
Azure STT Adapter.
Part of the Infrastructure Layer (Hexagonal Architecture).

THREADING CONTRACT:
  El Azure Speech SDK dispara callbacks (_on_recognized, _on_canceled,
  _on_session_stopped) desde hilos internos del SDK C++, NUNCA desde el
  event loop de asyncio.

  Regla: cualquier operación sobre asyncio.Queue o asyncio.Event DEBE
  usar loop.call_soon_threadsafe() para cruzar el límite thread → asyncio.
  Sin esto, los transcripts nunca llegan al consumer async (silencio total).
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional, Callable

import azure.cognitiveservices.speech as speechsdk

from backend.domain.ports.stt_port import STTPort, STTSession, STTConfig, STTEvent, STTResultReason, STTException
from backend.domain.value_objects.audio_format import AudioFormat
from backend.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class AzureSTTSession(STTSession):
    """
    Manages an active Azure Speech Recognition session.

    Thread safety: Azure SDK callbacks run in C++ SDK threads.
    All asyncio primitive operations use loop.call_soon_threadsafe()
    to safely bridge from those threads into the asyncio event loop.
    """

    def __init__(
        self,
        recognizer: speechsdk.SpeechRecognizer,
        push_stream: speechsdk.audio.PushAudioInputStream,
    ):
        self._recognizer = recognizer
        self._push_stream = push_stream
        self._callbacks = []  # Event subscribers

        # Capture the running event loop NOW (in the async context where
        # AzureSTTSession is created). This loop reference is the ONLY safe
        # way to schedule work from Azure's internal C++ threads.
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()

        # Use thread-safe primitives: asyncio.Queue and asyncio.Event are
        # NOT thread-safe. All writes from callbacks go via call_soon_threadsafe.
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._stop_event = asyncio.Event()

        # Wire events BEFORE recognition starts (caller must call
        # start_continuous_recognition_async() AFTER creating this session)
        self._recognizer.session_started.connect(self._on_session_started)
        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.recognizing.connect(self._on_recognizing)
        self._recognizer.canceled.connect(self._on_canceled)
        self._recognizer.session_stopped.connect(self._on_session_stopped)

    # ------------------------------------------------------------------
    # Azure SDK Callbacks — called from C++ SDK threads
    # ALL asyncio operations MUST use call_soon_threadsafe
    # ------------------------------------------------------------------

    def _on_session_started(self, evt):
        """Azure confirmed the session opened successfully."""
        logger.info("[AzureSTT] ✅ Session started — recognizer is active and listening")

    def _on_recognizing(self, evt):
        """Interim / partial recognition result (not final)."""
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            text = evt.result.text
            if text:
                logger.debug(f"[AzureSTT] Recognizing (partial): {text!r}")
                self._loop.call_soon_threadsafe(self._queue.put_nowait, (text, False))

    def _on_recognized(self, evt):
        """Final recognition result — bridge to asyncio via call_soon_threadsafe."""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text
            if text:
                # [PIPE-7] Azure fired a recognized event — transcript available
                logger.info(f"[PIPE-7/AZURE→STT] ✅ Recognized: {text!r}")

                logger.info(f"[AzureSTT] ✅ Recognized: {text!r}")

                # --- THREAD-SAFE BRIDGE ---
                # put_nowait called via call_soon_threadsafe so it is
                # scheduled on the event loop, not called directly from
                # the Azure C++ thread (which would be unsafe).
                self._loop.call_soon_threadsafe(self._queue.put_nowait, (text, True))

                # Emit event to subscribers (sync callbacks only)
                duration = evt.result.duration.total_seconds() if evt.result.duration else 0.0
                event = STTEvent(
                    reason=STTResultReason.RECOGNIZED_SPEECH,
                    text=text,
                    duration=duration,
                )
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"[AzureSTT] Subscriber callback error: {e}")

        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logger.debug(
                f"[AzureSTT] NoMatch — audio received but no speech recognized. "
                f"NoMatchReason={evt.result.no_match_details.reason if hasattr(evt.result, 'no_match_details') else 'unknown'}"
            )

    def _on_canceled(self, evt):
        """
        Cancellation event — may indicate auth errors, network issues, or
        stream closure. Logs full error_details to make silent failures visible.
        """
        reason = evt.result.reason
        logger.warning(f"[AzureSTT] ❌ Canceled: reason={reason}")

        if reason == speechsdk.CancellationReason.Error:
            cancellation = evt.result.cancellation_details
            logger.error(
                f"[AzureSTT] Cancellation error detail: "
                f"code={cancellation.error_code} "
                f"details={cancellation.error_details!r}"
            )

        # --- THREAD-SAFE BRIDGE ---
        self._loop.call_soon_threadsafe(self._stop_event.set)

    def _on_session_stopped(self, evt):
        """Azure closed the recognition session."""
        logger.info("[AzureSTT] Session stopped")
        # --- THREAD-SAFE BRIDGE ---
        self._loop.call_soon_threadsafe(self._stop_event.set)

    # ------------------------------------------------------------------
    # STTSession protocol (asyncio-safe methods)
    # ------------------------------------------------------------------

    async def process_audio(self, audio_chunk: bytes) -> None:
        """Write PCM bytes into the Azure push stream."""
        # [PIPE-6] Confirm bytes reaching the push_stream at the Azure boundary
        logger.debug(
            f"[PIPE-6/AZURE] push_stream.write({len(audio_chunk)}B)"
        )
        self._push_stream.write(audio_chunk)

    def subscribe(self, callback: Callable[[STTEvent], None]) -> None:
        """Subscribe to detailed STT events (sync callback)."""
        self._callbacks.append(callback)

    async def get_results(self) -> AsyncGenerator[tuple[str, bool], None]:
        """
        Async generator that yields finalized transcript segments.
        Polls the thread-safe queue until the session stops.
        """
        while not self._stop_event.is_set():
            try:
                text, is_final = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                yield text, is_final
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[AzureSTT] Error retrieving results: {e}")
                break

    async def close(self) -> None:
        """Close stream, stop recognizer, and signal the generator to exit."""
        logger.info("[AzureSTT] Closing session...")
        self._push_stream.close()
        self._recognizer.stop_continuous_recognition()
        # Safe to call from async context (we ARE on the event loop here)
        self._stop_event.set()
        logger.info("[AzureSTT] Session closed")


class AzureSTTAdapter(STTPort):
    """
    Adapter for Azure Speech-to-Text.
    Implements STTPort (Domain Layer) using the Azure Cognitive Services SDK.
    """

    def __init__(self):
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.service_region = settings.AZURE_SPEECH_REGION

        if not self.speech_key:
            logger.warning(
                "[AzureSTT] AZURE_SPEECH_KEY is missing. "
                "Recognition will fail with CancellationReason.Error."
            )

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.service_region,
        )

    async def transcribe(self, audio: bytes, format: AudioFormat, language: str = "es-MX") -> str:
        """One-shot transcription using Azure RecognizeOnceAsync."""
        try:
            stream_format = speechsdk.audio.AudioStreamFormat(
                samples_per_second=format.sample_rate,
                bits_per_sample=format.bits_per_sample,
                channels=format.channels,
            )
            push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
            audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config,
                language=language,
            )

            push_stream.write(audio)
            push_stream.close()

            loop = asyncio.get_running_loop()

            def _blocking_recognize():
                return recognizer.recognize_once_async().get()

            result = await loop.run_in_executor(None, _blocking_recognize)

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.info("[AzureSTT] No speech recognized (one-shot)")
                return ""
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(
                    f"[AzureSTT] One-shot canceled: "
                    f"code={cancellation.error_code} "
                    f"details={cancellation.error_details!r}"
                )
                return ""

        except Exception as e:
            logger.error(f"[AzureSTT] Transcription error: {e}", exc_info=True)
            raise

        return ""

    async def start_stream(
        self,
        format: AudioFormat,
        config: Optional[STTConfig] = None,
        on_interruption_callback: Optional[Callable] = None,
    ) -> STTSession:
        """
        Start a continuous recognition session.

        ORDERING CONTRACT:
          1. Build recognizer + audio config
          2. Create AzureSTTSession (registers all callbacks on recognizer)
          3. Call start_continuous_recognition_async() — AFTER callbacks are wired
          This ensures no recognized events are missed in the startup gap.
        """
        if config is None:
            config = STTConfig()

        language = config.language
        logger.info(
            f"[AzureSTT] Starting stream: lang={language!r} "
            f"sr={format.sample_rate} bits={format.bits_per_sample} enc={format.encoding!r}"
        )

        stream_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=format.sample_rate,
            bits_per_sample=format.bits_per_sample,
            channels=format.channels,
        )
        push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
            language=language,
        )

        # --- FIX Bug 2: Create session FIRST (registers callbacks), THEN start ---
        session = AzureSTTSession(recognizer, push_stream)

        if on_interruption_callback:
            session.subscribe(lambda event: on_interruption_callback())

        # Now safe to start — all callbacks are registered
        recognizer.start_continuous_recognition_async()
        logger.info("[AzureSTT] Recognition started — waiting for audio")

        return session

    async def close(self) -> None:
        """Cleanup adapter-level resources (sessions manage their own cleanup)."""
        logger.info("[AzureSTT] Adapter closed")

    def _create_audio_config(self, format: AudioFormat, push: bool = True):
        """Helper — reserved for future use."""
        pass
