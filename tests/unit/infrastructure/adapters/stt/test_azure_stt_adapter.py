
import asyncio
import pytest
import threading
from unittest.mock import MagicMock, patch, call as mock_call, AsyncMock
import azure.cognitiveservices.speech as speechsdk

from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter, AzureSTTSession
from backend.domain.value_objects.audio_format import AudioFormat


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_recognizer():
    """Return a mock SpeechRecognizer with connectable event stubs."""
    mock = MagicMock()
    # .connect() is called on each event — just accept it silently
    mock.session_started = MagicMock()
    mock.recognized = MagicMock()
    mock.recognizing = MagicMock()
    mock.canceled = MagicMock()
    mock.session_stopped = MagicMock()
    return mock


def _make_mock_push_stream():
    return MagicMock()


# ---------------------------------------------------------------------------
# TestAzureSTTSession
# ---------------------------------------------------------------------------

class TestAzureSTTSession:

    @pytest.fixture
    def session(self):
        recognizer = _make_mock_recognizer()
        push_stream = _make_mock_push_stream()
        return AzureSTTSession(recognizer, push_stream)

    # --- Bug 1: Thread-safe bridge ---

    @pytest.mark.asyncio
    async def test_on_recognized_uses_thread_safe_bridge(self, session):
        """
        _on_recognized DEVE usar call_soon_threadsafe para meter el texto
        en la queue desde el hilo del SDK — no put_nowait directo.
        """
        evt = MagicMock()
        evt.result.reason = speechsdk.ResultReason.RecognizedSpeech
        evt.result.text = "Hola mundo"
        evt.result.duration.total_seconds.return_value = 1.2

        # Patch call_soon_threadsafe on the session's captured loop
        session._loop = MagicMock()

        session._on_recognized(evt)

        # Must have called call_soon_threadsafe with put_nowait and the text
        session._loop.call_soon_threadsafe.assert_called_once_with(
            session._queue.put_nowait, "Hola mundo"
        )

    @pytest.mark.asyncio
    async def test_on_session_stopped_uses_thread_safe_bridge(self, session):
        """_on_session_stopped no debe llamar stop_event.set() directamente."""
        evt = MagicMock()
        session._loop = MagicMock()

        session._on_session_stopped(evt)

        session._loop.call_soon_threadsafe.assert_called_once_with(
            session._stop_event.set
        )

    @pytest.mark.asyncio
    async def test_on_canceled_uses_thread_safe_bridge(self, session):
        """_on_canceled no debe llamar stop_event.set() directamente."""
        evt = MagicMock()
        evt.result.reason = speechsdk.CancellationReason.EndOfStream
        session._loop = MagicMock()

        session._on_canceled(evt)

        session._loop.call_soon_threadsafe.assert_called_once_with(
            session._stop_event.set
        )

    @pytest.mark.asyncio
    async def test_canceled_logs_error_details_on_error(self, session, caplog):
        """
        Cuando CancellationReason es Error, el log DEBE incluir
        error_code y error_details completos.
        """
        import logging
        evt = MagicMock()
        evt.result.reason = speechsdk.CancellationReason.Error
        evt.result.cancellation_details.error_code = "AuthenticationFailure"
        evt.result.cancellation_details.error_details = "Invalid subscription key"
        session._loop = MagicMock()

        with caplog.at_level(logging.ERROR, logger="backend.infrastructure.adapters.stt.azure_stt_adapter"):
            session._on_canceled(evt)

        assert "AuthenticationFailure" in caplog.text or "Invalid subscription key" in caplog.text

    @pytest.mark.asyncio
    async def test_thread_to_asyncio_bridge_delivers_text(self):
        """
        Microsimulación: un hilo externo (simula callback del SDK Azure)
        usa call_soon_threadsafe para meter texto en la queue.
        El consumer async debe recibirlo correctamente.
        """
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        received = []

        async def consumer():
            try:
                text = await asyncio.wait_for(queue.get(), timeout=1.0)
                received.append(text)
            except asyncio.TimeoutError:
                pass

        def fake_azure_callback():
            # Simula _on_recognized desde hilo C++ del SDK
            loop.call_soon_threadsafe(queue.put_nowait, "transcript_from_thread")

        t = threading.Thread(target=fake_azure_callback)
        t.start()
        t.join()

        await consumer()

        assert received == ["transcript_from_thread"], (
            "call_soon_threadsafe debe entregar el texto al consumer async"
        )

    @pytest.mark.asyncio
    async def test_process_audio_writes_to_push_stream(self, session):
        """process_audio debe delegar directamente al push_stream."""
        await session.process_audio(b"pcm_bytes")
        session._push_stream.write.assert_called_once_with(b"pcm_bytes")


# ---------------------------------------------------------------------------
# TestAzureSTTAdapter
# ---------------------------------------------------------------------------

class TestAzureSTTAdapter:

    @pytest.fixture
    def mock_speech_config(self):
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechConfig"):
            yield

    @pytest.mark.asyncio
    async def test_start_stream_creates_session_before_starting_recognition(self, mock_speech_config):
        """
        Bug 2 fix: La sesión (con sus callbacks registradas) debe existir
        ANTES de que start_continuous_recognition_async() sea llamado.
        Verificamos el orden usando call tracking.
        """
        call_order = []

        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.AzureSTTSession") as MockSession:

            # Track when session is created
            MockSession.side_effect = lambda *a, **kw: call_order.append("session_created") or MagicMock()

            # Track when recognition starts
            recog_instance = MockRecognizer.return_value
            original_start = recog_instance.start_continuous_recognition_async
            def tracked_start():
                call_order.append("recognition_started")
            recog_instance.start_continuous_recognition_async.side_effect = tracked_start

            adapter = AzureSTTAdapter()
            format = AudioFormat(sample_rate=24000, channels=1, encoding="pcm")
            await adapter.start_stream(format)

        assert call_order == ["session_created", "recognition_started"], (
            f"El orden debe ser session_created → recognition_started, "
            f"pero fue: {call_order}"
        )

    @pytest.mark.asyncio
    async def test_start_stream_returns_azure_stt_session(self, mock_speech_config):
        """start_stream debe retornar una instancia de AzureSTTSession."""
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"):

            MockRecognizer.return_value.session_started = MagicMock()
            MockRecognizer.return_value.recognized = MagicMock()
            MockRecognizer.return_value.recognizing = MagicMock()
            MockRecognizer.return_value.canceled = MagicMock()
            MockRecognizer.return_value.session_stopped = MagicMock()

            adapter = AzureSTTAdapter()
            format = AudioFormat(sample_rate=24000, channels=1, encoding="pcm")
            session = await adapter.start_stream(format)

            assert isinstance(session, AzureSTTSession)
            MockRecognizer.return_value.start_continuous_recognition_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_speech_config):
        """transcribe() debe retornar el texto cuando Azure reconoce speech."""
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"):

            mock_result = MagicMock()
            mock_result.reason = speechsdk.ResultReason.RecognizedSpeech
            mock_result.text = "Hello there"

            mock_future = MagicMock()
            mock_future.get.return_value = mock_result
            MockRecognizer.return_value.recognize_once_async.return_value = mock_future

            adapter = AzureSTTAdapter()
            format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")

            text = await adapter.transcribe(b"audio_bytes", format)

            assert text == "Hello there"
            MockRecognizer.return_value.recognize_once_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_no_match(self, mock_speech_config):
        """transcribe() debe retornar string vacío en NoMatch."""
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"):

            mock_result = MagicMock()
            mock_result.reason = speechsdk.ResultReason.NoMatch

            mock_future = MagicMock()
            mock_future.get.return_value = mock_result
            MockRecognizer.return_value.recognize_once_async.return_value = mock_future

            adapter = AzureSTTAdapter()
            format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")

            text = await adapter.transcribe(b"audio_bytes", format)
            assert text == ""
