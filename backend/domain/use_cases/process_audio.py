"""
Process Audio Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from backend.domain.ports.stt_port import STTPort
from backend.domain.entities.call import Call
from backend.domain.value_objects.audio_format import AudioFormat

class ProcessAudioUseCase:
    """
    Coordinates audio processing.
    For discrete audio chunks (e.g. voicemail, captured utterance), 
    transforms audio to text using the STT Port.
    """

    def __init__(self, stt_port: STTPort):
        self.stt_port = stt_port

    async def execute(self, audio_data: bytes, call: Call) -> str:
        """
        Process the audio data and return transcription.
        
        Args:
            audio_data: Raw audio bytes.
            call: Context of the call (for configuration).
            
        Returns:
            Transcribed text.
        """
        if not audio_data:
            return ""

        # Determine format from call/agent config if available, 
        # or use standard telephony format (PCMU/8000)
        # For now, let's assume raw PCM and the STT adapter handles it
        # or we use a standard format VO.
        
        # We need an AudioFormat. Let's create one based on client type or default.
        # Ideally, Call entity should know the audio format of the stream.
        # Let's assume a default for now or pass it in.
        format = AudioFormat.for_client("telephony") # Default
        
        text = await self.stt_port.transcribe(audio_data, format)
        return text
