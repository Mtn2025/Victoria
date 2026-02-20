import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter, AzureSTTSession
from backend.domain.value_objects.audio_format import AudioFormat

@pytest.fixture
def mock_speech_sdk():
    """Mock Azure Cognitive Services Speech SDK."""
    with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk") as mock_sdk:
        # Mock Enums - Must be accessible as properties
        # We need to ensure that when the adapter accesses speechsdk.ResultReason.RecognizedSpeech, it gets a value
        mock_sdk.ResultReason.RecognizedSpeech = "RecognizedSpeech"
        mock_sdk.ResultReason.NoMatch = "NoMatch"
        mock_sdk.ResultReason.Canceled = "Canceled"
        
        # Audio Config Mocks
        mock_sdk.audio.AudioStreamFormat.return_value = MagicMock()
        mock_sdk.audio.PushAudioInputStream.return_value = MagicMock()
        mock_sdk.audio.AudioConfig.return_value = MagicMock()
        
        # Speech Config
        mock_sdk.SpeechConfig.return_value = MagicMock()
        
        yield mock_sdk

@pytest.mark.asyncio
async def test_transcribe_success(mock_speech_sdk):
    """Test one-shot transcription success."""
    # Setup Mock Recognizer
    mock_recognizer = MagicMock()
    
    # Mock the result object returned by .get()
    mock_result = MagicMock()
    mock_result.reason = mock_speech_sdk.ResultReason.RecognizedSpeech
    mock_result.text = "Hello World"
    
    # recognize_once_async returns a future-like object with .get()
    mock_future = MagicMock()
    mock_future.get.return_value = mock_result
    
    # Wire it up
    mock_recognizer.recognize_once_async.return_value = mock_future
    
    # Return this recognizer when instantiated
    mock_speech_sdk.SpeechRecognizer.return_value = mock_recognizer
    
    adapter = AzureSTTAdapter()
    format = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
    
    # We need to mock the internal blocking call wrapper because loop.run_in_executor runs it in thread
    # The mock setup above works for the inner code, but we must ensure objects are thread-safe or reachable.
    # unittest.mock objects are generally fine.
    
    result = await adapter.transcribe(b"fake_audio", format)
    
    assert result == "Hello World"
    
    # Verify interaction
    mock_speech_sdk.SpeechRecognizer.assert_called()
    mock_recognizer.recognize_once_async.assert_called_once()


@pytest.mark.asyncio
async def test_start_stream_processing(mock_speech_sdk):
    """Test streaming session initialization."""
    mock_recognizer = MagicMock()
    mock_speech_sdk.SpeechRecognizer.return_value = mock_recognizer
    
    adapter = AzureSTTAdapter()
    format = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
    
    session = await adapter.start_stream(format)
    
    assert isinstance(session, AzureSTTSession)
    mock_recognizer.start_continuous_recognition_async.assert_called_once()
    
    # Verify callbacks were connected
    # Accessing the bound method arguments is tricky if not saved, but we can verify calls
    mock_recognizer.recognized.connect.assert_called()
    mock_recognizer.canceled.connect.assert_called()
    mock_recognizer.session_stopped.connect.assert_called()
    
    await session.close()


@pytest.mark.asyncio
async def test_session_get_results(mock_speech_sdk):
    """Test result retrieval from session via queue."""
    mock_recognizer = MagicMock()
    mock_speech_sdk.SpeechRecognizer.return_value = mock_recognizer
    
    adapter = AzureSTTAdapter()
    format = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
    
    session = await adapter.start_stream(format)
    
    # Create a mock event to simulate 'recognized' callback
    mock_evt = MagicMock()
    mock_evt.result.reason = mock_speech_sdk.ResultReason.RecognizedSpeech
    mock_evt.result.text = "Streamed Text"
    # duration is a timedelta-like object in SDK, mocked here as object with total_seconds
    mock_evt.result.duration.total_seconds.return_value = 1.5
    
    # Inject event directly into the callback handler
    # This bypasses the actual specific 'recognized' signal emission of the mock
    # but tests the logic inside _on_recognized
    session._on_recognized(mock_evt)
    
    # Now consume from get_results
    # Since get_results is an async generator, we treat it as such
    
    # We need to fetch just one item to avoid hanging, as queue is empty after 1
    # The adapter loop has a timeout/wait strategy
    
    gen = session.get_results()
    text = await anext(gen) # python 3.10+
    
    assert text == "Streamed Text"
    
    await session.close()

