import pytest
from backend.domain.value_objects.phone_number import PhoneNumber

class TestPhoneNumber:
    def test_valid_e164_number(self):
        """Should accept valid E.164 numbers."""
        phone = PhoneNumber("+14155552671")
        assert phone.value == "+14155552671"
        assert str(phone) == "+14155552671"

    def test_valid_sip_uri(self):
        """Should accept SIP URIs."""
        uri = "sip:user@domain.com"
        phone = PhoneNumber(uri)
        assert phone.value == uri

    def test_invalid_number_format(self):
        """Should raise ValueError for invalid formats."""
        invalid_numbers = [
            "14155552671", # Missing +
            "+1", # Too short
            "+1234567890123456", # Too long (>15 digits)
            "invalid-string",
            "",
            None
        ]
        for num in invalid_numbers:
            with pytest.raises(ValueError):
                PhoneNumber(num)

    def test_immutability(self):
        """Should be immutable."""
        phone = PhoneNumber("+1234567890")
        with pytest.raises(AttributeError):
            phone.value = "+0987654321"
