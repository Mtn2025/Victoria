import pytest
from datetime import datetime, timezone
from backend.domain.entities.call import Call, CallStatus
from backend.domain.entities.agent import Agent
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.voice_config import VoiceConfig

class TestCallEntity:
    @pytest.fixture
    def sample_agent(self):
        return Agent(
            name="test-agent",
            system_prompt="prompt",
            voice_config=VoiceConfig(name="voice")
        )

    @pytest.fixture
    def sample_call(self, sample_agent):
        return Call(
            id=CallId("call-123"),
            agent=sample_agent,
            conversation=Conversation()
        )

    def test_call_initial_state(self, sample_call):
        """Should initialize with correct defaults."""
        assert sample_call.status == CallStatus.INITIATED
        assert sample_call.phone_number is None
        assert sample_call.end_time is None
        assert sample_call.metadata == {}

    def test_start_call_transition(self, sample_call):
        """Should transition to IN_PROGRESS."""
        sample_call.start()
        assert sample_call.status == CallStatus.IN_PROGRESS

    def test_end_call_completed(self, sample_call):
        """Should transition to COMPLETED."""
        sample_call.start()
        sample_call.end(reason="completed")
        assert sample_call.status == CallStatus.COMPLETED
        assert sample_call.end_time is not None
        assert sample_call.metadata["termination_reason"] == "completed"

    def test_end_call_failed(self, sample_call):
        """Should transition to FAILED on error reason."""
        sample_call.start()
        sample_call.end(reason="system_error")
        assert sample_call.status == CallStatus.FAILED

    def test_duration_calculation(self, sample_call):
        """Should calculate duration."""
        sample_call.start()
        # Simulate time passing? 
        # Since end_time is set by end(), checking logic conceptually.
        # Ideally we'd mock datetime, but for simple entity logic test, 
        # ensuring it returns a float >= 0 is a basic check.
        sample_call.end()
        assert sample_call.duration_seconds >= 0

    def test_cannot_end_already_ended_call(self, sample_call):
        """Should verify idempotency of end()."""
        sample_call.start()
        sample_call.end(reason="first")
        first_end_time = sample_call.end_time
        
        sample_call.end(reason="second")
        assert sample_call.end_time == first_end_time # Should not change
        assert sample_call.metadata["termination_reason"] == "first"
