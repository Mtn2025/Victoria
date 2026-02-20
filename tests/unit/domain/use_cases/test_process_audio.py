import pytest
from backend.domain.use_cases.process_audio import ProcessAudioUseCase
from backend.domain.entities.call import Call
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat
from tests.mocks.mock_ports import MockSTTPort

class TestProcessAudioUseCase:
    @pytest.fixture
    def call(self):
        return Call(
            id=CallId("call-1"),
            agent=Agent(name="agent", system_prompt="sys", voice_config=VoiceConfig(name="v")),
            conversation=Conversation()
        )

    @pytest.mark.asyncio
    async def test_process_valid_audio(self, call):
        stt_port = MockSTTPort()
        uc = ProcessAudioUseCase(stt_port)
        
        text = await uc.execute(audio_data=b"audio", call=call)
        assert text == "mock transcription"

    @pytest.mark.asyncio
    async def test_process_empty_audio(self, call):
        stt_port = MockSTTPort()
        uc = ProcessAudioUseCase(stt_port)
        
        text = await uc.execute(audio_data=b"", call=call)
        assert text == ""

    @pytest.mark.asyncio
    async def test_process_none_audio(self, call):
        stt_port = MockSTTPort()
        uc = ProcessAudioUseCase(stt_port)
        
        text = await uc.execute(audio_data=None, call=call)
        assert text == ""
