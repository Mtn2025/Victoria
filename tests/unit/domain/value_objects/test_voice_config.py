import pytest
from backend.domain.value_objects.voice_config import VoiceConfig

class TestVoiceConfig:
    def test_valid_voice_config(self):
        """Should accept valid configuration."""
        config = VoiceConfig(
            name="en-US-JennyNeural",
            speed=1.0,
            pitch=0,
            volume=100,
            style="friendly"
        )
        assert config.name == "en-US-JennyNeural"
        assert config.speed == 1.0

    def test_invalid_speed_raises_error(self):
        """Should raise ValueError for invalid speed."""
        with pytest.raises(ValueError, match="Speed"):
            VoiceConfig(name="test", speed=0.1)
            
        with pytest.raises(ValueError, match="Speed"):
            VoiceConfig(name="test", speed=2.1)

    def test_invalid_pitch_raises_error(self):
        """Should raise ValueError for invalid pitch."""
        with pytest.raises(ValueError, match="Pitch"):
            VoiceConfig(name="test", pitch=-101)

    def test_invalid_volume_raises_error(self):
        """Should raise ValueError for invalid volume."""
        with pytest.raises(ValueError, match="Volume"):
            VoiceConfig(name="test", volume=-1)

    def test_ssml_params_conversion(self):
        """Should correct convert to SSML dict."""
        config = VoiceConfig(name="test", style="sad")
        params = config.to_ssml_params()
        assert params["voice_name"] == "test"
        assert params["style"] == "sad"
        
    def test_default_style_handling(self):
        """Should handle default style correctly in SSML."""
        config = VoiceConfig(name="test", style="default")
        params = config.to_ssml_params()
        assert params["style"] is None
