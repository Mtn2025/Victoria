
import pytest
from datetime import datetime, timedelta
import time

from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent
from backend.domain.entities.call import Call, CallStatus
from backend.domain.value_objects.conversation_turn import ConversationTurn
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber

class TestConversation:
    def test_add_turn(self):
        conv = Conversation()
        turn = ConversationTurn(role="user", content="Hi")
        conv.add_turn(turn)
        assert len(conv.turns) == 1
        assert conv.turns[0] == turn

    def test_context_window(self):
        conv = Conversation()
        for i in range(15):
            conv.add_turn(ConversationTurn(role="user", content=str(i)))
        
        window = conv.get_context_window(limit=10)
        assert len(window) == 10
        assert window[-1].content == "14"
        assert window[0].content == "5"

    def test_invalid_turn(self):
        conv = Conversation()
        with pytest.raises(TypeError):
            conv.add_turn("Not a turn object")

class TestAgent:
    def test_agent_creation(self):
        vc = VoiceConfig(name="test-voice")
        agent = Agent(name="Bond", system_prompt="You are 007", voice_config=vc)
        assert agent.name == "Bond"
        assert agent.system_prompt == "You are 007"
        assert agent.voice_config == vc

    def test_update_prompt(self):
        vc = VoiceConfig(name="test-voice")
        agent = Agent(name="Bond", system_prompt="Original", voice_config=vc)
        agent.update_system_prompt("New Mission")
        assert agent.system_prompt == "New Mission"
        
        with pytest.raises(ValueError):
            agent.update_system_prompt("")

class TestCall:
    @pytest.fixture
    def valid_call(self):
        vc = VoiceConfig(name="test-voice")
        agent = Agent(name="Bond", system_prompt="You are 007", voice_config=vc)
        conv = Conversation()
        cid = CallId("call-123")
        return Call(id=cid, agent=agent, conversation=conv)

    def test_call_lifecycle(self, valid_call):
        assert valid_call.status == CallStatus.INITIATED
        
        valid_call.start()
        assert valid_call.status == CallStatus.IN_PROGRESS
        
        valid_call.end(reason="hangup")
        assert valid_call.status == CallStatus.COMPLETED
        assert valid_call.metadata["termination_reason"] == "hangup"
        assert valid_call.end_time is not None

    def test_duration(self, valid_call):
        valid_call.start()
        time.sleep(0.1)
        duration = valid_call.duration_seconds
        assert duration > 0
        
        valid_call.end()
        final_duration = valid_call.duration_seconds
        assert final_duration >= duration
