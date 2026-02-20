"""
Barge-In Use Case - Domain Logic.

Hexagonal Architecture: Pure domain use case for handling user interruptions.
Handles user interruption during assistant speech, coordinating
state cleanup decisions and interruption signals.
"""
import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass
class BargeInCommand:
    """
    Command returned by Use Case for orchestrator to execute.
    
    Represents the domain decision of how to handle the interruption.
    The orchestrator/application layer executes the actual infrastructure actions.
    """
    clear_pipeline: bool = True
    interrupt_audio: bool = True
    reason: str = ""


class AudioManagerProtocol(Protocol):
    """
    Protocol for audio manager dependency (if needed in future versions).
    
    Currently unused - kept for reference if use case needs to query state.
    """
    async def interrupt_speaking(self) -> None:
        """Interrupt current audio playback."""
        ...


class PipelineProtocol(Protocol):
    """
    Protocol for pipeline dependency (if needed in future versions).
    
    Currently unused - kept for reference if use case needs to query state.
    """
    async def clear_output_queue(self) -> None:
        """Clear pending output frames."""
        ...


class HandleBargeInUseCase:
    """
    Domain Use Case: Handle user interruption (barge-in).
    
    Pure domain logic - NO infrastructure dependencies.
    Returns command for orchestrator to execute.
    
    Use case:
        When user speaks while assistant is playing audio,
        determine what cleanup actions should be taken based
        on the interruption reason or context.
        
    Example:
        >>> use_case = HandleBargeInUseCase()
        >>> command = use_case.execute(reason="vad_detected")
        >>> assert command.clear_pipeline is True
        >>> assert command.interrupt_audio is True
    """

    def execute(self, reason: str) -> BargeInCommand:
        """
        Process barge-in event.
        
        Args:
            reason: Interruption reason (e.g., "user_spoke", "vad_detected", "silence_timeout")
            
        Returns:
            BargeInCommand with actions to perform
        """
        logger.info(f"[Barge-In Use Case] Triggered: {reason}")

        # Domain logic: determine what to clean up based on reason
        if "vad" in reason.lower() or "user" in reason.lower():
            # User speech detected - full interruption
            # Clear pending TTS audio and reset pipeline
            return BargeInCommand(
                clear_pipeline=True,
                interrupt_audio=True,
                reason=reason
            )
        
        # Other reasons - conservative interruption
        # Interrupt audio but keep pipeline state (e.g., for error recovery)
        return BargeInCommand(
            clear_pipeline=False,
            interrupt_audio=True,
            reason=reason
        )
