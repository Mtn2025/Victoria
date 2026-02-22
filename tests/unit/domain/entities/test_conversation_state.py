"""
Unit tests for ConversationFSM.

Tests state transitions, validation, and guard methods.
"""
import pytest

from backend.domain.entities.conversation_state import (
    ConversationFSM,
    ConversationState
)


class TestConversationFSM:
    """Test FSM state management and transitions."""
    
    @pytest.mark.asyncio
    async def test_initial_state_idle(self):
        """Test FSM starts in IDLE state."""
        fsm = ConversationFSM()
        
        assert fsm.state == ConversationState.IDLE
    
    @pytest.mark.asyncio
    async def test_valid_transition_idle_to_listening(self):
        """Test valid transition from IDLE to LISTENING."""
        fsm = ConversationFSM()
        
        result = await fsm.transition(ConversationState.LISTENING, "session_started")
        
        assert result is True
        assert fsm.state == ConversationState.LISTENING
    
    @pytest.mark.asyncio
    async def test_invalid_transition_idle_to_speaking(self):
        """Test invalid transition from IDLE to SPEAKING."""
        fsm = ConversationFSM()
        
        result = await fsm.transition(ConversationState.SPEAKING, "invalid")
        
        assert result is False
        assert fsm.state == ConversationState.IDLE  # Unchanged
    
    @pytest.mark.asyncio
    async def test_can_speak_from_listening(self):
        """Test can_speak returns True from LISTENING."""
        fsm = ConversationFSM(ConversationState.LISTENING)
        
        can = await fsm.can_speak()
        
        assert can is True
    
    @pytest.mark.asyncio
    async def test_cannot_speak_from_idle(self):
        """Test can_speak returns False from IDLE."""
        fsm = ConversationFSM(ConversationState.IDLE)
        
        can = await fsm.can_speak()
        
        assert can is False
    
    @pytest.mark.asyncio
    async def test_can_interrupt_from_speaking(self):
        """Test can_interrupt returns True from SPEAKING."""
        fsm = ConversationFSM(ConversationState.SPEAKING)
        
        can = await fsm.can_interrupt()
        
        assert can is True
    
    @pytest.mark.asyncio
    async def test_can_late_interrupt_from_listening_after_speaking(self):
        """Test can_interrupt returns True from LISTENING if the assistant just spoke (late barge-in allowed)."""
        fsm = ConversationFSM()
        await fsm.transition(ConversationState.LISTENING, "start")
        await fsm.transition(ConversationState.SPEAKING, "tts")
        await fsm.transition(ConversationState.LISTENING, "audio_done")
        
        can = await fsm.can_interrupt()
        assert can is True

    @pytest.mark.asyncio
    async def test_cannot_late_interrupt_twice(self):
        """Test can_interrupt returns False from LISTENING if a barge-in already occurred."""
        fsm = ConversationFSM()
        await fsm.transition(ConversationState.LISTENING, "start")
        await fsm.transition(ConversationState.SPEAKING, "tts")
        await fsm.transition(ConversationState.INTERRUPTED, "user_barge_in")
        await fsm.transition(ConversationState.LISTENING, "ready_for_input")
        
        can = await fsm.can_interrupt()
        assert can is False
    
    @pytest.mark.asyncio
    async def test_barge_in_flow(self):
        """Test full barge-in flow: SPEAKING → INTERRUPTED → LISTENING."""
        fsm = ConversationFSM(ConversationState.SPEAKING)
        
        # Can interrupt?
        assert await fsm.can_interrupt() is True
        
        # Interrupt
        result1 = await fsm.transition(
            ConversationState.INTERRUPTED,
            "user_spoke"
        )
        assert result1 is True
        assert fsm.state == ConversationState.INTERRUPTED
        
        # Return to listening
        result2 = await fsm.transition(
            ConversationState.LISTENING,
            "ready_for_input"
        )
        assert result2 is True
        assert fsm.state == ConversationState.LISTENING
    
    @pytest.mark.asyncio
    async def test_any_state_to_ended(self):
        """Test any state can transition to ENDED."""
        for state in [ConversationState.IDLE, ConversationState.LISTENING, 
                       ConversationState.SPEAKING, ConversationState.PROCESSING]:
            fsm = ConversationFSM(state)
            
            result = await fsm.transition(ConversationState.ENDED, "call_ended")
            
            assert result is True
            assert fsm.state == ConversationState.ENDED
    
    @pytest.mark.asyncio
    async def test_ended_is_terminal(self):
        """Test ENDED state cannot transition to other states."""
        fsm = ConversationFSM(ConversationState.ENDED)
        
        result = await fsm.transition(ConversationState.LISTENING, "invalid")
        
        assert result is False
        assert fsm.state == ConversationState.ENDED
    
    @pytest.mark.asyncio
    async def test_reset_to_idle(self):
        """Test reset returns FSM to IDLE."""
        fsm = ConversationFSM(ConversationState.SPEAKING)
        
        fsm.reset()
        
        assert fsm.state == ConversationState.IDLE
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test complete conversation flow."""
        fsm = ConversationFSM()
        
        # Start session
        await fsm.transition(ConversationState.LISTENING, "session_started")
        assert fsm.state == ConversationState.LISTENING
        
        # User speaks, start processing
        await fsm.transition(ConversationState.PROCESSING, "user_spoke")
        assert fsm.state == ConversationState.PROCESSING
        
        # LLM generates, start speaking
        await fsm.transition(ConversationState.SPEAKING, "tts_started")
        assert fsm.state == ConversationState.SPEAKING
        
        # Speech ends, return to listening
        await fsm.transition(ConversationState.LISTENING, "speech_ended")
        assert fsm.state == ConversationState.LISTENING
        
        # End call
        await fsm.transition(ConversationState.ENDED, "user_hung_up")
        assert fsm.state == ConversationState.ENDED
