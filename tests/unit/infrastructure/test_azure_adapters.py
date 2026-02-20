import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import azure.cognitiveservices.speech as speechsdk

# Import adapters
from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter, AzureSTTSession
from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter

# Import Domain objects
from backend.domain.value_objects.audio_format import AudioFormat
from backend.domain.value_objects.voice_config import VoiceConfig

class TestAzureSTTAdapter:
    @pytest.fixture
    def mock_speech_config(self):
        with patch("azure.cognitiveservices.speech.SpeechConfig") as mock_cls:
            yield mock_cls

    @pytest.fixture
    def mock_audio_config(self):
        with patch("azure.cognitiveservices.speech.audio.AudioConfig") as mock_cls:
            yield mock_cls
            
    @pytest.fixture
    def mock_push_stream_cls(self):
        with patch("azure.cognitiveservices.speech.audio.PushAudioInputStream") as mock_cls:
            yield mock_cls

    @pytest.fixture
    def mock_recognizer_cls(self):
        with patch("azure.cognitiveservices.speech.SpeechRecognizer") as mock_cls:
            yield mock_cls

    @pytest.fixture
    def adapter(self, mock_speech_config):
        # Patch settings if needed, but constructor uses them directly
        return AzureSTTAdapter()

    def test_transcribe_success(self, adapter, mock_recognizer_cls, mock_push_stream_cls, mock_audio_config):
        # Arrange
        mock_recognizer = mock_recognizer_cls.return_value
        mock_future = MagicMock()
        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.RecognizedSpeech
        mock_result.text = "Hello world"
        
        mock_future.get.return_value = mock_result
        mock_recognizer.recognize_once_async.return_value = mock_future
        
        audio_data = b"fake_audio"
        format = AudioFormat.for_browser()
        
        # Act
        text = asyncio.run(adapter.transcribe(audio_data, format))
        
        # Assert
        assert text == "Hello world"
        mock_recognizer_cls.assert_called_once()
        mock_recognizer.recognize_once_async.assert_called_once()

    def test_transcribe_no_match(self, adapter, mock_recognizer_cls, mock_push_stream_cls, mock_audio_config):
        # Arrange
        mock_recognizer = mock_recognizer_cls.return_value
        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.NoMatch
        mock_recognizer.recognize_once_async.return_value.get.return_value = mock_result
        
        # Act
        text = asyncio.run(adapter.transcribe(b"audio", AudioFormat.for_browser()))
        
        # Assert
        assert text == ""

    @pytest.mark.asyncio
    async def test_start_stream(self, adapter, mock_recognizer_cls, mock_push_stream_cls, mock_audio_config):
        # Arrange
        mock_recognizer = mock_recognizer_cls.return_value
        mock_push_stream = mock_push_stream_cls.return_value
        
        # Act
        session = await adapter.start_stream(AudioFormat.for_browser())
        
        # Assert
        assert isinstance(session, AzureSTTSession)
        mock_recognizer.start_continuous_recognition_async.assert_called_once()

class TestAzureTTSAdapter:
    @pytest.fixture
    def mock_speech_config(self):
        with patch("azure.cognitiveservices.speech.SpeechConfig") as mock_cls:
            yield mock_cls

    @pytest.fixture
    def mock_synthesizer_cls(self):
        with patch("azure.cognitiveservices.speech.SpeechSynthesizer") as mock_cls:
            yield mock_cls
            
    @pytest.fixture
    def adapter(self, mock_speech_config):
        return AzureTTSAdapter()

    @pytest.mark.asyncio
    async def test_synthesize_success(self, adapter, mock_synthesizer_cls):
        # Arrange
        mock_synthesizer = mock_synthesizer_cls.return_value
        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
        mock_result.audio_data = b"synth_audio"
        
        mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_result
        
        voice = VoiceConfig(name="en-US-JennyNeural")
        format = AudioFormat.for_browser()
        
        # Act
        audio = await adapter.synthesize("Hello", voice, format)
        
        # Assert
        assert audio == b"synth_audio"
        mock_synthesizer.speak_ssml_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_canceled(self, adapter, mock_synthesizer_cls):
        # Arrange
        mock_synthesizer = mock_synthesizer_cls.return_value
        mock_result = MagicMock()
        mock_result.reason = speechsdk.ResultReason.Canceled
        mock_result.cancellation_details.reason = "Error"
        mock_result.cancellation_details.error_details = "Detail"
        
        mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_result
        
        voice = VoiceConfig(name="en-US-JennyNeural")
        format = AudioFormat.for_browser()
        
        # Act & Assert
        with pytest.raises(Exception, match="Synthesis failed"):
            await adapter.synthesize("Hello", voice, format)
