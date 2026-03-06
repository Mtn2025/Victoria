"""
Conversation State - FSM for managing conversation lifecycle.

Domain Entity: Pure business logic for state management.
Prevents audio ghosting, manages transitions, validates operations.
"""
from enum import Enum
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """
    Conversation states in voice interaction lifecycle.
    
    Flow:
        IDLE → LISTENING → PROCESSING → SPEAKING → LISTENING
        Any state → INTERRUPTED (user barge-in) → LISTENING
    """
    IDLE = "idle"                    # No active conversation
    LISTENING = "listening"          # Waiting for user input
    PROCESSING = "processing"        # LLM generating response
    SPEAKING = "speaking"            # TTS playing audio
    INTERRUPTED = "interrupted"      # User interrupted assistant
    ENDED = "ended"                  # Call ended


class ConversationFSM:
    """
    Finite State Machine for conversation flow management.
    
    Responsibilities:
    - Track current conversation state
    - Validate state transitions
    - Determine if operations are allowed (speak, interrupt, etc.)
    - Prevent audio ghosting (speaking when shouldn't)
    
    Example:
        >>> fsm = ConversationFSM()
        >>> await fsm.transition(ConversationState.LISTENING, "user_connected")
        >>> if await fsm.can_speak():
        ...     # Generate TTS
        >>> await fsm.transition(ConversationState.SPEAKING, "tts_started")
    """
    
    def __init__(self, initial_state: ConversationState = ConversationState.IDLE):
        """
        Initialize FSM with initial state.
        
        Args:
            initial_state: Starting state (default: IDLE)
        """
        self._state = initial_state
        self._can_late_interrupt = False  # Track if we can do a late barge-in against frontend buffer
        self._lock = asyncio.Lock()
        logger.info(f"🎯 FSM initialized: {initial_state.value}")
    
    @property
    def state(self) -> ConversationState:
        """Get current state."""
        return self._state
    
    async def transition(
        self,
        new_state: ConversationState,
        reason: str = ""
    ) -> bool:
        """
        Transition to new state if valid.
        
        Args:
            new_state: Target state
            reason: Transition reason for logging
            
        Returns:
            True if transition succeeded, False otherwise
        """
        async with self._lock:
            # Validate transition
            if not self._is_valid_transition(self._state, new_state):
                logger.warning(
                    f"❌ Invalid transition: {self._state.value} → {new_state.value} "
                    f"(reason: {reason})"
                )
                return False
            
            old_state = self._state
            self._state = new_state
            
            # Track allowance for late interruptions (barge-in against frontend slow playback)
            if new_state in (ConversationState.SPEAKING, ConversationState.PROCESSING):
                self._can_late_interrupt = True
            elif new_state == ConversationState.INTERRUPTED:
                self._can_late_interrupt = False
            
            logger.info(
                f"🔄 State transition: {old_state.value} → {new_state.value} "
                f"(reason: {reason})"
            )
            
            return True
    
    def _is_valid_transition(
        self,
        from_state: ConversationState,
        to_state: ConversationState
    ) -> bool:
        """
        Check if transition is valid.
        
        Transition rules:
        - IDLE → LISTENING (call start)
        - LISTENING → PROCESSING (user spoke)
        - PROCESSING → SPEAKING (LLM generated)
        - SPEAKING → LISTENING (speech ended)
        - SPEAKING/PROCESSING → INTERRUPTED (user barged in)
        - INTERRUPTED → LISTENING (ready for new input)
        - Any → ENDED (call end)
        """
        # ENDED is terminal
        if from_state == ConversationState.ENDED:
            return False
        
        # Any state can transition to ENDED
        if to_state == ConversationState.ENDED:
            return True
        
        # Define valid transitions
        valid_transitions = {
            ConversationState.IDLE: {
                ConversationState.LISTENING,
            },
            ConversationState.LISTENING: {
                ConversationState.PROCESSING,
                ConversationState.SPEAKING,  # Direct speak (greeting)
                ConversationState.INTERRUPTED, # Late barge-in against frontend playback
            },
            ConversationState.PROCESSING: {
                ConversationState.SPEAKING,
                ConversationState.INTERRUPTED,
                ConversationState.LISTENING,  # No response needed
            },
            ConversationState.SPEAKING: {
                ConversationState.LISTENING,
                ConversationState.INTERRUPTED,
            },
            ConversationState.INTERRUPTED: {
                ConversationState.LISTENING,
                ConversationState.PROCESSING,
            },
        }
        
        allowed = valid_transitions.get(from_state, set())
        return to_state in allowed
    
    async def can_speak(self) -> bool:
        """
        Check if assistant can speak in current state.
        
        Returns:
            True if speaking is allowed
            
        Use this before generating TTS to prevent audio ghosting.
        """
        async with self._lock:
            allowed_states = {
                ConversationState.LISTENING,
                ConversationState.PROCESSING,
                ConversationState.SPEAKING,  # Can continue speaking
            }
            
            can = self._state in allowed_states
            
            if not can:
                logger.debug(
                    f"🚫 Speaking blocked - state: {self._state.value}"
                )
            
            return can
    
    async def can_interrupt(self) -> bool:
        """
        Check if user interruption is allowed in current state.
        
        Returns:
            True if interruption is allowed
            
        Only allow interruption when assistant is speaking/processing.
        """
        async with self._lock:
            allowed_states = {
                ConversationState.SPEAKING,
                ConversationState.PROCESSING,
            }
            
            can = self._state in allowed_states
            
            # Allow late interruption from LISTENING only once after speaking/processing
            if self._state == ConversationState.LISTENING and self._can_late_interrupt:
                can = True
            
            if not can:
                logger.debug(
                    f"🚫 Interrupt blocked - state: {self._state.value}"
                )
            
            return can
    
    async def can_process(self) -> bool:
        """
        Check if can process user input.
        
        Returns:
            True if processing is allowed
        """
        async with self._lock:
            allowed_states = {
                ConversationState.LISTENING,
                ConversationState.INTERRUPTED,
            }
            
            return self._state in allowed_states
    
    async def reset(self):
        """Reset FSM to IDLE state."""
        async with self._lock:
            self._state = ConversationState.IDLE
            logger.info("🔄 FSM reset to IDLE")
