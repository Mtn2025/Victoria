import pytest
from backend.domain.use_cases.generate_response import GenerateResponseUseCase
from backend.domain.entities.call import Call
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig
from tests.mocks.mock_ports import MockLLMPort, MockTTSPort

class TestGenerateResponseUseCase:
    @pytest.fixture
    def call(self):
        return Call(
            id=CallId("call-1"),
            agent=Agent(name="agent", system_prompt="sys", voice_config=VoiceConfig(name="v")),
            conversation=Conversation()
        )

    @pytest.mark.asyncio
    async def test_generate_response(self, call):
        llm_port = MockLLMPort()
        tts_port = MockTTSPort()
        uc = GenerateResponseUseCase(llm_port, tts_port)
        
        # Consume generator
        generated_audio = []
        async for chunk in uc.execute("user input", call):
            generated_audio.append(chunk)
        
        # Verify audio chunks
        assert len(generated_audio) > 0
        assert generated_audio[0] == b"mock audio bytes"
        
        # Verify conversation update
        # 1. User turn added
        assert call.conversation.turn_count == 2
        user_turn = call.conversation.turns[-2]
        assert user_turn.role == "user"
        assert user_turn.content == "user input"

        # 2. Assistant turn added
        asst_turn = call.conversation.turns[-1]
        assert asst_turn.role == "assistant"
        assert asst_turn.content == "mock response"
