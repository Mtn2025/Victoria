"""
Barge-In Integration Example.

Demonstrates how to integrate HandleBargeInUseCase with CallOrchestrator
for handling user interruptions during assistant speech.

This is a reference implementation showing the integration pattern.
The actual integration should be done in the call orchestrator or
frame pipeline based on Victoria's architecture.
"""
import logging
from typing import Optional

from backend.domain.use_cases.handle_barge_in import HandleBargeInUseCase, BargeInCommand

logger = logging.getLogger(__name__)


class BargeInIntegrationExample:
    """
    Example integration of barge-in handling.
    
    Shows how to:
    1. Detect user interruption (VAD, user speech)
    2. Execute HandleBargeInUseCase
    3. Act on BargeInCommand (clear pipeline, interrupt audio)
    """
    
    def __init__(self):
        self.barge_in_use_case = HandleBargeInUseCase()
        self._is_speaking = False
    
    async def on_user_speech_detected(self, reason: str = "vad_detected"):
        """
        Called when user speech is detected during assistant playback.
        
        Args:
            reason: Interruption reason ("vad_detected", "user_spoke", etc.)
        """
        if not self._is_speaking:
            logger.debug("User spoke but assistant not speaking, no barge-in needed")
            return
        
        # Execute barge-in use case (Domain logic)
        command = self.barge_in_use_case.execute(reason)
        
        logger.info(
            f"🛑 Barge-in triggered: {command.reason} "
            f"(clear_pipeline={command.clear_pipeline}, "
            f"interrupt_audio={command.interrupt_audio})"
        )
        
        # Execute infrastructure actions based on command
        await self._execute_barge_in_command(command)
    
    async def _execute_barge_in_command(self, command: BargeInCommand):
        """
        Execute barge-in command on infrastructure.
        
        This is where Application layer translates Domain decisions
        into infrastructure actions.
        """
        # 1. Interrupt audio playback
        if command.interrupt_audio:
            await self._interrupt_audio_playback()
        
        # 2. Clear pipeline if requested
        if command.clear_pipeline:
            await self._clear_output_pipeline()
        
        # 3. Reset state
        self._is_speaking = False
    
    async def _interrupt_audio_playback(self):
        """
        Stop current audio playback.
        
        Integration points:
        - Send CancelFrame to audio output processor
        - Clear audio buffer in TTS adapter
        - Stop audio stream to telephony/websocket
        """
        logger.info("🔇 Interrupting audio playback")
        
        # Example: Send cancel signal
        # await self.audio_manager.interrupt()
        # await self.pipeline.push_frame(CancelFrame())
        pass
    
    async def _clear_output_pipeline(self):
        """
        Clear pending frames in output pipeline.
        
        Integration points:
        - Clear frame queue in pipeline
        - Cancel pending TTS synthesis
        - Reset LLM generation task
        """
        logger.info("🗑️ Clearing output pipeline")
        
        # Example: Clear pipeline
        # await self.pipeline.clear_output_queue()
        # if self.llm_task and not self.llm_task.done():
        #     self.llm_task.cancel()
        pass


# Integration into CallOrchestrator pattern:
# 
# class EnhancedCallOrchestrator(CallOrchestrator):
#     def __init__(self, ..., barge_in_uc: HandleBargeInUseCase):
#         super().__init__(...)
#         self.barge_in_uc = barge_in_uc
#         self._assistant_speaking = False
#     
#     async def on_vad_user_speech(self):
#         """Called by VAD when user speaks."""
#         if self._assistant_speaking:
#             command = self.barge_in_uc.execute("user_spoke")
#             
#             if command.interrupt_audio:
#                 # Stop audio playback
#                 await self.audio_output.interrupt()
#             
#             if command.clear_pipeline:
#                 # Clear pending TTS frames
#                 await self.pipeline.clear_downstream()
#     
#     async def process_audio_input(self, ...):
#         # Existing logic + barge-in hook
#         if self._assistant_speaking:
#             await self.on_vad_user_speech()
#         
#         # Continue with STT -> LLM -> TTS
#         ...


"""
INTEGRATION NOTES FOR VICTORIA:

Victoria uses a frame-based pipeline architecture with processors:
- STTProcessor: Handles speech-to-text
- LLMProcessor: LLM generation (already handles CancelFrame on line 66-69)
- TTSProcessor: Text-to-speech

Barge-in integration should happen at:

1. **VAD Detection Level** (if implemented):
   - When VAD detects user speech during assistant playback
   - Trigger barge-in use case
   - Send CancelFrame downstream

2. **LLMProcessor** (already partially implemented):
   - Lines 54-55: Cancels previous generation on new user input
   - This IS barge-in behavior: user speaks -> cancel assistant

3. **Frame Pipeline**:
   - CancelFrame already exists and is handled
   - HandleBargeInUseCase can decide WHEN to send CancelFrame

RECOMMENDED APPROACH:

Since LLMProcessor already cancels on new user input (line 54-55),
the barge-in logic is ALREADY IMPLEMENTED at the execution level.

HandleBargeInUseCase adds VALUE by:
- Centralizing interruption decision logic (Domain)
- Allowing different strategies (full vs partial clear)
- Making barge-in behavior testable

To fully integrate:
1. Add HandleBargeInUseCase to LLMProcessor constructor
2. Replace hardcoded cancel logic with use case call
3. Use BargeInCommand to determine cancel vs clear

Example:
```python
# In LLMProcessor.__init__:
self.barge_in_uc = handle_barge_in_uc

# In LLMProcessor.process_frame (line 50-58):
if frame.is_final and frame.role == "user":
    if self._current_task and not self._current_task.done():
        # Execute barge-in use case
        command = self.barge_in_uc.execute("user_spoke")
        
        if command.interrupt_audio:
            self._current_task.cancel()
            await self.push_frame(CancelFrame(), direction)
```

This makes the interruption logic explicit and domain-driven.
"""
