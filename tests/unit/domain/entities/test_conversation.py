import pytest
from backend.domain.entities.conversation import Conversation
from backend.domain.value_objects.conversation_turn import ConversationTurn

class TestConversation:
    def test_conversation_starts_empty(self):
        """Should start with no turns."""
        conv = Conversation()
        assert len(conv.turns) == 0
        assert conv.turn_count == 0

    def test_add_turn(self):
        """Should add valid turns."""
        conv = Conversation()
        turn = ConversationTurn(role="user", content="Hi")
        conv.add_turn(turn)
        assert len(conv.turns) == 1
        assert conv.turns[0] == turn

    def test_add_invalid_turn_raises_error(self):
        """Should raise TypeError for non-ConversationTurn objects."""
        conv = Conversation()
        with pytest.raises(TypeError):
            conv.add_turn("not a turn")

    def test_get_context_window(self):
        """Should return last N turns."""
        conv = Conversation()
        for i in range(15):
            conv.add_turn(ConversationTurn(role="user", content=str(i)))
        
        window = conv.get_context_window(limit=10)
        assert len(window) == 10
        assert window[-1].content == "14"
        assert window[0].content == "5"

    def test_get_history_as_dicts(self):
        """Should return list of dicts."""
        conv = Conversation()
        conv.add_turn(ConversationTurn(role="user", content="Hi"))
        history = conv.get_history_as_dicts()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hi"
