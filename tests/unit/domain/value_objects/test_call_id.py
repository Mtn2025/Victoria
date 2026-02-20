import pytest
from backend.domain.value_objects.call_id import CallId

class TestCallId:
    def test_valid_call_id(self):
        """Should accept valid string identifiers."""
        call_id = CallId("test-id-123")
        assert call_id.value == "test-id-123"
        assert str(call_id) == "test-id-123"

    def test_empty_call_id_raises_error(self):
        """Should raise ValueError for empty strings."""
        with pytest.raises(ValueError, match="non-empty string"):
            CallId("")

    def test_none_call_id_raises_error(self):
        """Should raise ValueError for None."""
        with pytest.raises(ValueError, match="non-empty string"):
            CallId(None)

    def test_long_call_id_raises_error(self):
        """Should raise ValueError for strings > 255 chars."""
        long_id = "a" * 256
        with pytest.raises(ValueError, match="too long"):
            CallId(long_id)

    def test_immutability(self):
        """Should be immutable (frozen dataclass)."""
        call_id = CallId("test")
        with pytest.raises(AttributeError):
            call_id.value = "new-value"
