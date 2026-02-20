
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import azure.cognitiveservices.speech as speechsdk

from backend.infrastructure.adapters.stt.azure_stt_adapter import AzureSTTAdapter, AzureSTTSession
from backend.domain.value_objects.audio_format import AudioFormat

class TestAzureSTTAdapter:
    
    @pytest.fixture
    def mock_speech_config(self):
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechConfig") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_speech_config):
        # Patch SpeechRecognizer specifically within the scope
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"):
             
            mock_recog_instance = MockRecognizer.return_value
            
            # Mock result
            mock_result = MagicMock()
            mock_result.reason = speechsdk.ResultReason.RecognizedSpeech
            mock_result.text = "Hello there"
            
            # Mock recognize_once_async returning a future-like object
            mock_future = MagicMock()
            mock_future.get.return_value = mock_result
            mock_recog_instance.recognize_once_async.return_value = mock_future
            
            adapter = AzureSTTAdapter()
            format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")
            
            text = await adapter.transcribe(b"audio_bytes", format)
            
            assert text == "Hello there"
            mock_recog_instance.recognize_once_async.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_transcribe_no_match(self, mock_speech_config):
         with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"):

            mock_recog_instance = MockRecognizer.return_value
             # Mock result
            mock_result = MagicMock()
            mock_result.reason = speechsdk.ResultReason.NoMatch
            
            mock_future = MagicMock()
            mock_future.get.return_value = mock_result
            mock_recog_instance.recognize_once_async.return_value = mock_future
            
            adapter = AzureSTTAdapter()
            format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")
            
            text = await adapter.transcribe(b"audio_bytes", format)
            assert text == ""

    @pytest.mark.asyncio
    async def test_start_stream(self, mock_speech_config):
        with patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.SpeechRecognizer") as MockRecognizer, \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.PushAudioInputStream"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.stt.azure_stt_adapter.speechsdk.audio.AudioStreamFormat"):
             
             adapter = AzureSTTAdapter()
             format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")
             
             session = await adapter.start_stream(format)
             
             assert isinstance(session, AzureSTTSession)
             MockRecognizer.return_value.start_continuous_recognition_async.assert_called_once()
