import pytest
from backend.domain.use_cases.end_call import EndCallUseCase
from backend.domain.entities.call import Call, CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig
from tests.mocks.mock_ports import MockCallRepository, MockTelephonyPort

class TestEndCallUseCase:
    @pytest.fixture
    def call(self):
        call = Call(
            id=CallId("call-1"),
            agent=Agent(name="agent", system_prompt="sys", voice_config=VoiceConfig(name="v")),
            conversation=Conversation()
        )
        call.start()
        return call

    @pytest.mark.asyncio
    async def test_end_call_success(self, call):
        call_repo = MockCallRepository()
        telephony_port = MockTelephonyPort()
        
        # Pre-save call to mock repo
        await call_repo.save(call)
        
        uc = EndCallUseCase(call_repo, telephony_port)
        await uc.execute(call, reason="user_hangup")
        
        # Verify call status
        assert call.status == CallStatus.COMPLETED
        
        # Verify persistence
        saved_call = await call_repo.get_by_id(call.id)
        assert saved_call.status == CallStatus.COMPLETED
        
        # Verify telephony interaction
        assert "call-1" in telephony_port.ended_calls
