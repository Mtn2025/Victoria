import pytest
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

class TestAgent:
    @pytest.fixture
    def valid_voice_config(self):
        return VoiceConfig(name="test-voice")

    def test_agent_creation(self, valid_voice_config):
        """Should create agent with valid config."""
        agent = Agent(
            name="test-agent",
            system_prompt="You are a helpful assistant",
            voice_config=valid_voice_config
        )
        assert agent.name == "test-agent"
        assert agent.system_prompt == "You are a helpful assistant"
        assert agent.voice_config == valid_voice_config
        assert agent.tools == []

    def test_update_system_prompt(self, valid_voice_config):
        """Should update system prompt correctly."""
        agent = Agent(
            name="test",
            system_prompt="old",
            voice_config=valid_voice_config
        )
        agent.update_system_prompt("new")
        assert agent.system_prompt == "new"

    def test_update_empty_system_prompt_raises_error(self, valid_voice_config):
        """Should raise ValueError for empty prompt."""
        agent = Agent(
            name="test",
            system_prompt="old",
            voice_config=valid_voice_config
        )
        with pytest.raises(ValueError):
            agent.update_system_prompt("")

    def test_get_greeting(self, valid_voice_config):
        """Should return greeting if present."""
        agent = Agent(
            name="test",
            system_prompt="sys",
            voice_config=valid_voice_config,
            first_message="Hello"
        )
        assert agent.get_greeting() == "Hello"

    def test_get_greeting_none(self, valid_voice_config):
        """Should return None if no greeting."""
        agent = Agent(
            name="test",
            system_prompt="sys",
            voice_config=valid_voice_config
        )
        assert agent.get_greeting() is None
