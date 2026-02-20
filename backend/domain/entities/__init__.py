"""
Domain Entities - FASE 3 exports.
"""
from backend.domain.entities.call import Call
from backend.domain.entities.conversation_state import ConversationFSM, ConversationState

__all__ = [
    'Call',
    'ConversationFSM',
    'ConversationState',
]
