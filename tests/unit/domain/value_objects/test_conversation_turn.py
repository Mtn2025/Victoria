import pytest
from backend.domain.value_objects.conversation_turn import ConversationTurn

class TestConversationTurn:
    def test_valid_turn_creation(self):
        """Should create valid conversation turn."""
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.timestamp is not None

    def test_invalid_role_raises_error(self):
        """Should raise ValueError for invalid role."""
        with pytest.raises(ValueError, match="Invalid role"):
            ConversationTurn(role="admin", content="Hello")

    def test_content_can_be_empty_for_tool_call(self):
        """Content can be empty string if tool calls exist."""
        turn = ConversationTurn(role="assistant", content="", tool_calls=[{"name": "test"}])
        assert turn.content == ""

    def test_to_dict_conversion(self):
        """Should convert to dictionary correctly."""
        turn = ConversationTurn(role="user", content="Hello")
        d = turn.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"
