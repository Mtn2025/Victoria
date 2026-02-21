"""
Azure TTS Adapter.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
import asyncio
import logging
import time
from typing import AsyncIterator, List, Optional
import azure.cognitiveservices.speech as speechsdk

from backend.domain.ports.tts_port import TTSPort, VoiceMetadata, TTSRequest, TTSException
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat
from backend.infrastructure.config.settings import settings
from backend.infrastructure.adapters.tts.azure_voice_styles import get_voice_styles_spanish

logger = logging.getLogger(__name__)

class AzureTTSAdapter(TTSPort):
    """
    Adapter for Azure Text-to-Speech.
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

    async def synthesize(self, text: str, voice: VoiceConfig, format: AudioFormat) -> bytes:
        """
        Synthesize text to audio bytes.
        """
        try:
            # 1. Configure Output Format
            self._configure_format(self.speech_config, format)
            
            # 2. Create Synthesizer
            # Null output to prevent playback
            audio_config = speechsdk.audio.AudioConfig(filename="/dev/null") 
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )

            # 3. Build SSML
            ssml = self._build_ssml(text, voice)
            
            # 4. Synthesize
            loop = asyncio.get_running_loop()
            
            def _blocking_synthesis():
                result = synthesizer.speak_ssml_async(ssml).get()
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    return result.audio_data
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    logger.error(f"[AzureTTS] Canceled: {cancellation_details.reason} - {cancellation_details.error_details}")
                    return None
                return None

            audio_data = await loop.run_in_executor(None, _blocking_synthesis)
            
            if audio_data is None:
                raise Exception("Synthesis failed or canceled")
                
            return audio_data

        except Exception as e:
            logger.error(f"[AzureTTS] Synthesis error: {e}")
            raise

    async def synthesize_stream(self, text: str, voice: VoiceConfig, format: AudioFormat) -> AsyncIterator[bytes]:
        """
        Stream synthesized audio.
        """
        # For now, we reuse the implementation effectively buffering logic 
        # because true streaming requires handling pull streams or push streams carefully.
        # To respect the interface, we yield chunks.
        
        full_audio = await self.synthesize(text, voice, format)
        
        chunk_size = 4096
        for i in range(0, len(full_audio), chunk_size):
            yield full_audio[i:i+chunk_size]
            # Simulate async yield if needed, but not strictly required if data is already here.
            # await asyncio.sleep(0) 

    def _configure_format(self, speech_config, format: AudioFormat):
        """
        Map AudioFormat VO to Azure SpeechSynthesisOutputFormat enum.

        IMPORTANT: Raw* formats produce bare PCM bytes (no header) — used for
        real-time pipeline streaming via WebSocket where the receiver handles
        the raw PCM directly (e.g. browser AudioWorklet, Twilio μ-law stream).

        Riff* formats include the WAV header and are only used for the preview
        endpoint (synthesize_for_preview) where the browser plays via new Audio().
        """
        enc = format.encoding
        sr  = format.sample_rate

        if enc == "pcm" and sr == 24000:
            # Browser via AudioWorklet: Int16Array(arraybuffer) expects PCM16@24kHz raw
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm
            )
        elif enc == "pcm" and sr == 16000:
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
            )
        elif enc in ("mulaw", "ulaw"):
            # Twilio / Telnyx: 8kHz μ-law
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw8Khz8BitMonoMULaw
            )
        else:
            # Safe fallback for unknown formats
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw8Khz8BitMonoMULaw
            )

    def _configure_format_for_preview(self, speech_config):
        """
        Configure output format for browser HTML5 audio preview.

        Uses Riff16Khz16BitMonoPcm (not Raw*) because:
        - Raw formats produce bare PCM bytes with no RIFF/WAV header.
        - Browsers require the RIFF header to parse the WAV container.
        - The Riff* variants in Azure SDK prepend the 44-byte header automatically.
        """
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )

    async def synthesize_for_preview(self, text: str, voice: VoiceConfig) -> bytes:
        """
        Synthesize text to WAV bytes suitable for browser preview.

        Uses Riff16Khz16BitMonoPcm so the output includes the RIFF/WAV header
        expected by HTML5 Audio and new Audio(). Regular synthesize() uses Raw*
        formats (no header) intended for real-time streaming pipelines.
        """
        self._configure_format_for_preview(self.speech_config)
        audio_config = speechsdk.audio.AudioConfig(filename="/dev/null")
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )
        ssml = self._build_ssml(text, voice)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: synthesizer.speak_ssml_async(ssml).get()
        )
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        details = result.cancellation_details
        raise Exception(f"Azure TTS preview failed: {details.reason} — {details.error_details}")

    def _build_ssml(self, text: str, voice: VoiceConfig) -> str:
        """
        Construct SSML with voice configuration.
        """
        style_tag = ""
        style_close = ""
        
        if voice.style and voice.style.lower() != "default":
            # Note: Azure style handling usually requires specific style names
            # style_degree usage is supported in some voices.
            style_tag = f'<mstts:express-as style="{voice.style}" styledegree="{voice.style_degree}">'
            style_close = '</mstts:express-as>'

        # Params
        rate = f"{voice.speed}"
        pitch = f"{voice.pitch:+.0f}Hz"
        # Azure supports absolute volume 0-100 (e.g. volume="75")
        volume = f"{voice.volume}"

        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="es-MX">'
            f'<voice name="{voice.name}">'
            f'{style_tag}'
            f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
            f'{text}'
            f'</prosody>'
            f'{style_close}'
            f'</voice>'
            f'</speak>'
        )
        return ssml

    async def get_available_voices(self, language: str | None = None) -> List[VoiceMetadata]:
        """
        Get list of available voices from Azure.
        """
        # For simplicity, we can fetch dynamically or return a static list if key is missing.
        # But Phase 9 requirements imply real connection.
        
        loop = asyncio.get_running_loop()
        
        def _fetch_blocking():
             # Basic synth to fetch voices
             synth = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
             result = synth.get_voices_async().get()
             if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                 return result.voices
             return []

        try:
             voices = await loop.run_in_executor(None, _fetch_blocking)
             
             metadata_list = []
             for v in voices:
                 if language and v.locale != language:
                     continue
                 
                 # Append to list
                 metadata_list.append(VoiceMetadata(
                     id=v.name,
                     name=v.local_name,
                     gender=v.gender.name,
                     locale=v.locale
                 ))
             return metadata_list
             
        except Exception as e:
             logger.error(f"Error fetching voices: {e}")
             return []

    async def get_available_languages(self) -> List[str]:
         # Fetch voices and extract locales
         voices = await self.get_available_voices()
         locales = {v.locale for v in voices}
         return sorted(list(locales))

    async def get_voice_styles(self, voice_id: str) -> List[str]:
        # Minimal implementation: Fetch specific voice and check styles
        # Optimally we should cache this as in legacy.
        # For Phase 9 MVP, we fetch fresh or return empty if complex.
        # Legacy had a cache. We can skip cache for now or implement simple cache.
        
         loop = asyncio.get_running_loop()
         def _fetch_blocking():
             synth = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
             result = synth.get_voices_async(voice_id).get() # Does get_voices_async take filtering? No.
             # It returns all. We must filter.
             # Actually get_voices_async("") returns all.
             result = synth.get_voices_async().get()
             if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                 for v in result.voices:
                     if v.name == voice_id:
                         return v.style_list
             return []

         try:
             styles = await loop.run_in_executor(None, _fetch_blocking)
             return styles or []
         except Exception:
             return []
    async def synthesize_request(self, request: TTSRequest) -> bytes:
        """
        Synthesize using structured request.
        """
        voice = VoiceConfig(
            name=request.voice_id, # Map ID to name? Azure uses name.
            speed=request.speed,
            pitch=request.pitch,
            volume=int(request.volume), # Cast to int if needed
            style=request.style or "default"
        )
        # Format
        # We need to map string format to AudioFormat object or handle it.
        # TTSRequest has format: str
        # synthesize takes AudioFormat
        # We need a mapper. For now default to 16kHz PCM.
        format_obj = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
        
        return await self.synthesize(request.text, voice, format_obj)

    async def synthesize_ssml(self, ssml: str) -> bytes:
        """
        Synthesize directly from SSML.
        """
        try:
            # Configure default format (or pass as arg? Port signature doesn't have format arg for ssml?)
            # Port says: async def synthesize_ssml(self, ssml: str) -> bytes:
            # We use default config.
            
            # Create Synthesizer
            audio_config = speechsdk.audio.AudioConfig(filename="/dev/null") 
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            loop = asyncio.get_running_loop()
            
            def _blocking_synthesis():
                 result = synthesizer.speak_ssml_async(ssml).get()
                 if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                     return result.audio_data
                 return None

            audio_data = await loop.run_in_executor(None, _blocking_synthesis)
            if audio_data is None:
                 raise Exception("SSML Synthesis failed")
            return audio_data
            
        except Exception as e:
            logger.error(f"[AzureTTS] SSML error: {e}")
            raise

    async def close(self) -> None:
        """Cleanup."""
        pass
