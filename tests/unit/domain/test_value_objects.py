
import pytest
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.value_objects.audio_format import AudioFormat

class TestVoiceConfig:
    def test_valid_config(self):
        """Happy Path: Standard valid configuration."""
        vc = VoiceConfig(name="test-voice", speed=1.0, pitch=0)
        assert vc.name == "test-voice"
        assert vc.speed == 1.0

    def test_validation_logic(self):
        """Validation: Should raise ValueError on invalid range."""
        with pytest.raises(ValueError, match="Speed"):
            VoiceConfig(name="test", speed=5.0)  # Invalid Speed

        with pytest.raises(ValueError, match="Pitch"):
            VoiceConfig(name="test", pitch=200)  # Invalid Pitch

        with pytest.raises(ValueError, match="Volume"):
            VoiceConfig(name="test", volume=-10)  # Invalid Volume

    def test_immutability(self):
        """Domain Rule: Value Objects are immutable."""
        vc = VoiceConfig(name="test")
        with pytest.raises(Exception): # Frozen dataclass raises FrozenInstanceError
            vc.speed = 2.0

class TestAudioFormat:
    def test_factories(self):
        """Factories: Should create correct presets."""
        browser = AudioFormat.for_browser()
        assert browser.sample_rate == 16000
        assert browser.encoding == "pcm"
        assert browser.is_browser

        telephony = AudioFormat.for_telephony()
        assert telephony.sample_rate == 8000
        assert telephony.encoding == "mulaw"
        assert telephony.is_telephony

    def test_client_factory(self):
        """Factory: Client based selection."""
        assert AudioFormat.for_client("browser").is_browser
        assert AudioFormat.for_client("twilio").is_telephony
        assert AudioFormat.for_client("telnyx").is_telephony
        assert AudioFormat.for_client("unknown").is_telephony # Default

from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber
from backend.domain.value_objects.conversation_turn import ConversationTurn

class TestCallId:
    def test_valid_id(self):
        cid = CallId("12345")
        assert cid.value == "12345"
        assert str(cid) == "12345"

    def test_validation(self):
        with pytest.raises(ValueError, match="non-empty"):
            CallId("")
        with pytest.raises(ValueError, match="too long"):
            CallId("a" * 256)

class TestPhoneNumber:
    def test_valid_e164(self):
        pn = PhoneNumber("+14155552671")
        assert pn.value == "+14155552671"

    def test_valid_sip(self):
        pn = PhoneNumber("sip:alice@example.com")
        assert pn.value == "sip:alice@example.com"

    def test_invalid_numbers(self):
        with pytest.raises(ValueError):
            PhoneNumber("123") # No plus
        with pytest.raises(ValueError):
            PhoneNumber("+1") # Too short
        with pytest.raises(ValueError):
            PhoneNumber("invalid")

class TestConversationTurn:
    def test_valid_turn(self):
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
    
    def test_invalid_role(self):
        with pytest.raises(ValueError, match="Invalid role"):
            ConversationTurn(role="hacker", content="Hello")
            
    def test_to_dict(self):
        turn = ConversationTurn(role="assistant", content="Hi")
        assert turn.to_dict() == {"role": "assistant", "content": "Hi"}

