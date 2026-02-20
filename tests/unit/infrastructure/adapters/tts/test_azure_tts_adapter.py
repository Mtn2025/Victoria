
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import azure.cognitiveservices.speech as speechsdk

from backend.infrastructure.adapters.tts.azure_tts_adapter import AzureTTSAdapter
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat

class TestAzureTTSAdapter:
    
    @pytest.fixture
    def mock_speech_config(self):
         with patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.SpeechConfig") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_synthesize_success(self, mock_speech_config):
        with patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.SpeechSynthesizer") as MockSynthesizer, \
             patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.audio.AudioStreamFormat"):
            
            mock_synth_instance = MockSynthesizer.return_value
            
            # Mock Result
            mock_result = MagicMock()
            mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
            mock_result.audio_data = b"synthetic_audio"
            
            # Use side effect or return value for blocking call
            mock_future = MagicMock()
            mock_future.get.return_value = mock_result
            mock_synth_instance.speak_ssml_async.return_value = mock_future
            
            adapter = AzureTTSAdapter()
            vc = VoiceConfig(name="test")
            format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")
            
            audio = await adapter.synthesize("Hello", vc, format)
            
            assert audio == b"synthetic_audio"
            mock_synth_instance.speak_ssml_async.assert_called_once()


    @pytest.mark.asyncio
    async def test_synthesize_stream(self, mock_speech_config):
         with patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.SpeechSynthesizer") as MockSynthesizer, \
             patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.audio.AudioConfig"), \
             patch("backend.infrastructure.adapters.tts.azure_tts_adapter.speechsdk.audio.AudioStreamFormat"):

            mock_synth_instance = MockSynthesizer.return_value
            mock_result = MagicMock()
            mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
            mock_result.audio_data = b"12345678" * 1000 # Large chunk
            
            mock_future = MagicMock()
            mock_future.get.return_value = mock_result
            mock_synth_instance.speak_ssml_async.return_value = mock_future
            
            adapter = AzureTTSAdapter()
            vc = VoiceConfig(name="test")
            format = AudioFormat(sample_rate=16000, channels=1, encoding="pcm")
            
            chunks = []
            async for chunk in adapter.synthesize_stream("Hello", vc, format):
                chunks.append(chunk)
                
            assert b"".join(chunks) == b"12345678" * 1000
