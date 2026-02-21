import pytest
from backend.domain.value_objects.audio_format import AudioFormat

class TestAudioFormat:
    def test_browser_factory_method(self):
        """Should create correct browser audio format — 24kHz PCM16 (matches frontend AudioWorklet)."""
        format = AudioFormat.for_browser()
        assert format.sample_rate == 24000
        assert format.channels == 1
        assert format.encoding == "pcm"
        assert format.is_browser is True

    def test_telephony_factory_method(self):
        """Should create correct telephony audio format."""
        format = AudioFormat.for_telephony()
        assert format.sample_rate == 8000
        assert format.channels == 1
        assert format.encoding == "mulaw"
        assert format.is_telephony is True

    def test_client_factory_method(self):
        """Should create correct format based on client string."""
        browser = AudioFormat.for_client("browser")
        assert browser.is_browser is True
        
        twilio = AudioFormat.for_client("twilio")
        assert twilio.is_telephony is True
        
        telnyx = AudioFormat.for_client("telnyx")
        assert telnyx.is_telephony is True
        
        unknown = AudioFormat.for_client("unknown")
        assert unknown.is_telephony is True # Default fallback

    def test_immutability(self):
        """Should be immutable."""
        format = AudioFormat.for_browser()
        with pytest.raises(AttributeError):
            format.sample_rate = 44100
