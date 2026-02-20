import pytest
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig

class TestDetectTurnEnd:
    @pytest.fixture
    def agent(self):
        return Agent(
            name="test",
            system_prompt="sys",
            voice_config=VoiceConfig(name="voice"), # Helper needed?
            silence_timeout_ms=1000
        )

    def test_silence_below_threshold(self, agent):
        """Should return False if silence < threshold."""
        uc = DetectTurnEndUseCase()
        assert uc.execute(silence_duration_ms=500, threshold_ms=agent.silence_timeout_ms) is False

    def test_silence_above_threshold(self, agent):
        """Should return True if silence >= threshold."""
        uc = DetectTurnEndUseCase()
        assert uc.execute(silence_duration_ms=1000, threshold_ms=agent.silence_timeout_ms) is True
        assert uc.execute(silence_duration_ms=1500, threshold_ms=agent.silence_timeout_ms) is True

    def test_negative_silence_raises_error(self, agent):
        """Should raise ValueError for negative duration."""
        uc = DetectTurnEndUseCase()
        with pytest.raises(ValueError):
            uc.execute(silence_duration_ms=-1, threshold_ms=agent.silence_timeout_ms)
