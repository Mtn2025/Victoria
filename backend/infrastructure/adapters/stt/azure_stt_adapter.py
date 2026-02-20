"""
Azure STT Adapter.
Part of the Infrastructure Layer (Hexagonal Architecture).
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
    """
    def __init__(self, recognizer: speechsdk.SpeechRecognizer, push_stream: speechsdk.audio.PushAudioInputStream):
        self._recognizer = recognizer
        self._push_stream = push_stream
        self._queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._callbacks = []  # Event subscribers
        
        # Wire events
        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.canceled.connect(self._on_canceled)
        self._recognizer.session_stopped.connect(self._on_session_stopped)

    def _on_recognized(self, evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text
            if text:
                self._queue.put_nowait(text)
                # Emit event to subscribers
                event = STTEvent(
                    reason=STTResultReason.RECOGNIZED_SPEECH,
                    text=text,
                    duration=evt.result.duration.total_seconds() if evt.result.duration else 0.0
                )
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"[AzureSTT] Callback error: {e}")

    def _on_canceled(self, evt):
        logger.warning(f"[AzureSTT] Canceled: {evt.result.reason}")
        self._stop_event.set()

    def _on_session_stopped(self, evt):
        logger.info("[AzureSTT] Session stopped")
        self._stop_event.set()

    async def process_audio(self, audio_chunk: bytes) -> None:
        self._push_stream.write(audio_chunk)

    def subscribe(self, callback: Callable[[STTEvent], None]) -> None:
        """Subscribe to detailed STT events."""
        self._callbacks.append(callback)
    
    async def get_results(self) -> AsyncGenerator[str, None]:
        while not self._stop_event.is_set():
            try:
                # Wait for text or stop signal
                # We use a small timeout to check stop_event periodically
                text = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                yield text
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[AzureSTT] Error retrieving results: {e}")
                break

    async def close(self) -> None:
        self._push_stream.close()
        self._recognizer.stop_continuous_recognition()
        self._stop_event.set()


class AzureSTTAdapter(STTPort):
    """
    Adapter for Azure Speech-to-Text.
    """

    def __init__(self):
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.service_region = settings.AZURE_SPEECH_REGION
        
        if not self.speech_key:
             logger.warning("Azure Speech Key missing. Adapter may fail.")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.service_region
        )

    async def transcribe(self, audio: bytes, format: AudioFormat, language: str = "es-MX") -> str:
        """
        One-shot transcription using Azure RecognizeOnceAsync.
        """
        # Configure Audio
        audio_config = self._create_audio_config(format, push=False)
        
        # We need a way to pass the bytes to the PullStream or use a file.
        # Verify if we can just pass bytes directly? No, usually need a stream.
        # But for 'RecognizeOnce', it often expects a file or a stream.
        # Simplest way: wrapper around bytes.
        
        try:
             # Create a specialized stream for one-shot is tricky with Azure Python SDK 
             # without a file. 
             # Let's use PushStream but close it immediately.
             
            stream_format = speechsdk.audio.AudioStreamFormat(
                samples_per_second=format.sample_rate,
                bits_per_sample=format.bits_per_sample,
                channels=format.channels
            )
            push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
            audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
            
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config,
                language=language
            )
            
            # Write data and close
            push_stream.write(audio)
            push_stream.close()
            
            # Recognize
            loop = asyncio.get_running_loop()
            
            def _blocking_recognize():
                return recognizer.recognize_once_async().get()
                
            result = await loop.run_in_executor(None, _blocking_recognize)
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.info("[AzureSTT] No speech could be recognized")
                return ""
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"[AzureSTT] Transcription canceled: {cancellation_details.reason}")
                logger.error(f"[AzureSTT] Error details: {cancellation_details.error_details}")
                return ""
                
        except Exception as e:
            logger.error(f"[AzureSTT] Transcription error: {e}")
            raise

        return ""

    async def start_stream(
        self, 
        format: AudioFormat,
        config: Optional[STTConfig] = None,
        on_interruption_callback: Optional[Callable] = None
    ) -> STTSession:
        """
        Start continuous recognition with optional config and barge-in callback.
        """
        # Use config or defaults
        if config is None:
            config = STTConfig()  # Default config
        
        language = config.language
        stream_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=format.sample_rate,
            bits_per_sample=format.bits_per_sample,
            channels=format.channels
        )
        push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
        
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, 
            audio_config=audio_config,
            language=language
        )
        
        # Apply config settings to recognizer if available
        # Azure SDK has limited runtime config, most settings are compile-time
        # Future: Apply config.punctuation, config.profanity_filter, etc. if Azure supports
        
        # Start async
        recognizer.start_continuous_recognition_async()
        
        session = AzureSTTSession(recognizer, push_stream)
        
        # Subscribe interruption callback if provided
        if on_interruption_callback:
            session.subscribe(lambda event: on_interruption_callback())
        
        return session

    async def close(self) -> None:
        """
        Cleanup provider resources.
        """
        # Azure SDK doesn't require explicit cleanup at adapter level
        # Sessions handle their own cleanup
        logger.info("[AzureSTT] Adapter closed")

    def _create_audio_config(self, format: AudioFormat, push: bool = True):
        # Helper (concept only, not used directly in methods above to be explicit)
        pass
