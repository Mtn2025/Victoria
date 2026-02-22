"""
LLM Processor.
Part of the Application Layer (Hexagonal Architecture).
"""
import asyncio
import logging
import re
import uuid
from typing import Any, Callable, Dict, List, Optional

from backend.application.processors.frames import Frame, TextFrame, CancelFrame, EndTaskFrame, UserStartedSpeakingFrame
from backend.application.processors.frame_processor import FrameProcessor, FrameDirection
from backend.domain.ports.llm_port import LLMPort, LLMRequest, LLMMessage
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.domain.value_objects.tool import ToolRequest, ToolResponse

logger = logging.getLogger(__name__)

class LLMProcessor(FrameProcessor):
    """
    LLM Processor.
    Consumes TextFrames (User), streams response from LLMPort, produces TextFrames (Assistant).
    Handles conversation history and tool execution.
    """

    def __init__(
        self, 
        llm_port: LLMPort, 
        config: Any, 
        conversation_history: List[Dict[str, str]], 
        execute_tool_use_case: Optional[ExecuteToolUseCase] = None,
        on_interruption_callback: Optional[Callable] = None,
        context: Optional[Dict[str, Any]] = None,
        transcript_callback = None,      # async def cb(role: str, text: str) -> None
    ):
        super().__init__(name="LLMProcessor")
        self.llm_port = llm_port
        self.config = config
        self.conversation_history = conversation_history
        self.execute_tool = execute_tool_use_case
        self.on_interruption_callback = on_interruption_callback
        self.context = context or {}
        # Transcript callback — sends real-time STT/LLM turns to the Simulator panel.
        # async def transcript_callback(role: str, text: str) -> None
        self.transcript_callback = transcript_callback
        
        # State
        self.trace_id = str(uuid.uuid4())
        self._current_task: Optional[asyncio.Task] = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, TextFrame):
                # We process all user transcripts (interim to cancel TTS, final to generate)
                if frame.role == "user":
                    # [PIPE-8] TextFrame (user transcript) reached LLMProcessor
                    logger.info(
                        f"[PIPE-8/LLM] TextFrame received: "
                        f"role={frame.role!r} is_final={frame.is_final} "
                        f"text={frame.text[:50]!r}"
                    )
                    
                    # Report interruption (barge-in) to Orchestrator on ANY user speech
                    if self.on_interruption_callback:
                        await self.on_interruption_callback(frame.text)
                        
                    # ONLY Start new generation if this is a FINAL transcript
                    if frame.is_final:
                        logger.info(f"Processing Final User Input: {frame.text[:30]}...")
                        self._current_task = asyncio.create_task(self._handle_user_text(frame.text))
                
                # We do NOT pass the user frame downstream? 
                # Aggregator/Reporter usually handles the "User" transcript visibility.
                # If we pass it, TTS might try to speak it? No, TTS listens for "assistant" role.
                # Pass it for logging/metrics.
                await self.push_frame(frame, direction)
                
            elif isinstance(frame, CancelFrame):
                logger.info("Received CancelFrame. Stopping generation.")
                if self._current_task and not self._current_task.done():
                    self._current_task.cancel()
                await self.push_frame(frame, direction)
                
            elif isinstance(frame, UserStartedSpeakingFrame):
                # Eager Barge-in: Report upstream instantly on VAD trigger
                logger.info(f"🛑 [Eager Barge-In] VAD trigger received, notifying Orchestrator")
                if self.on_interruption_callback:
                    await self.on_interruption_callback("vad-trigger")
                        
                await self.push_frame(frame, direction)
            
            else:
                await self.push_frame(frame, direction)
        else:
            await self.push_frame(frame, direction)

    async def _handle_user_text(self, text: str):
        """Main LLM Loop: Update history -> Generate -> Execute Tools -> Repeat."""
        # Notify Simulator: user transcript (STT final)
        if self.transcript_callback:
            try:
                await self.transcript_callback("user", text)
            except Exception:
                pass  # non-fatal

        # Update History
        if not self.conversation_history or self.conversation_history[-1].get("content") != text:
            self.conversation_history.append({"role": "user", "content": text})
            
        try:
            await self._generate_llm_response()
        except asyncio.CancelledError:
            logger.info("Generation cancelled.")
        except Exception as e:
            logger.error(f"LLM Error: {e}", exc_info=True)

    async def _generate_llm_response(self, tool_result_message: Optional[Dict[str, Any]] = None):
        """Generate response recursively (handling tools)."""
        
        # Build Messages
        messages = [LLMMessage(role=msg["role"], content=msg["content"]) for msg in self.conversation_history]
        
        if tool_result_message:
            messages.append(LLMMessage(role=tool_result_message["role"], content=tool_result_message["content"]))
            
        # Build Request
        from backend.application.services.prompt_builder import PromptBuilder
        system_prompt = PromptBuilder.build_system_prompt(self.config, self.context)
        
        # Get Tools
        tools = None
        if self.execute_tool:
             # Convert ToolDefinitions to dicts if needed, depending on LLMPort expectation.
             # LLMPort `LLMRequest` expects `tools` list.
             # Legacy `LLMRequest` in `port.py` expects `list[dict]`.
             # `ExecuteToolUseCase.get_tool_definitions` returns `list[ToolDefinition]`.
             # We convert them.
             tools = [t.to_openai_format() for t in self.execute_tool.get_tool_definitions()]

        # Helper to get config safely
        def get_cfg(key, default=None):
            if isinstance(self.config, dict):
                return self.config.get(key, default)
            return getattr(self.config, key, default)

        request = LLMRequest(
            messages=messages,
            model=get_cfg('llm_model', 'llama-3.3-70b-versatile'),
            temperature=get_cfg('temperature', 0.7),
            max_tokens=get_cfg('max_tokens', 600),
            system_prompt=system_prompt,
            tools=tools,
            metadata={"trace_id": self.trace_id}
        )
        
        full_response_buffer = ""
        sentence_buffer = ""
        should_end_call = False
        
        # Streaming
        async for chunk in self.llm_port.generate_stream(request):
            # Function Call
            if chunk.has_function_call:
                logger.info(f"Function Call: {chunk.function_call.name}")
                
                # Execute Tool
                if self.execute_tool:
                    tool_response = await self.execute_tool.execute(ToolRequest(
                        tool_name=chunk.function_call.name,
                        arguments=chunk.function_call.arguments,
                        trace_id=self.trace_id,
                        context=self.context
                    ))
                    
                    # Add execution to history (as implicit assistant step usually, or function step)
                    # Standard: 
                    # 1. Assistant: Function Call (Already done in chunk? No, chunk is partial?)
                    # OpenAI pattern: Message(role=assistant, tool_calls=[...]) -> Message(role=tool, result=...)
                    
                    # We need to append the Assistant's "Call" message first?
                    # `chunk.function_call` implies the LLM decided to call.
                    # We simulate that the assistant output was the function call.
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": f"[TOOL_CALL: {chunk.function_call.name}]" 
                    })
                    
                    result_content = str(tool_response.result) if tool_response.success else tool_response.error_message
                    
                    # Re-enter generation with tool result
                    await self._generate_llm_response(tool_result_message={
                        "role": "function",   # or 'tool'
                        "content": result_content
                    })
                    return # Exit current loop, recursion handles the rest
                
            # Text Content
            if chunk.has_text:
                text = chunk.text
                full_response_buffer += text
                
                # Check End Call
                if "[END_CALL]" in text:
                    should_end_call = True
                    text = text.replace("[END_CALL]", "")
                
                sentence_buffer += text
                
                # Splits
                if len(sentence_buffer) > 10 and re.search(r'[.?!]\s+$', sentence_buffer):
                     tts_text = sentence_buffer
                     await self.push_frame(TextFrame(text=tts_text, role="assistant", is_final=True), FrameDirection.DOWNSTREAM)
                     # Notify Simulator: assistant sentence (real-time)
                     if self.transcript_callback:
                         try:
                             await self.transcript_callback("assistant", tts_text)
                         except Exception:
                             pass  # non-fatal
                     sentence_buffer = ""
                     
        # Flush remaining
        if sentence_buffer.strip():
             await self.push_frame(TextFrame(text=sentence_buffer, role="assistant", is_final=True), FrameDirection.DOWNSTREAM)
             
        # Update History
        if full_response_buffer.strip():
            self.conversation_history.append({"role": "assistant", "content": full_response_buffer})
            
        # End Signal
        if should_end_call:
            await self.push_frame(EndTaskFrame(), FrameDirection.DOWNSTREAM) # Use EndTask or EndFrame? EndTaskFrame used in legacy.
