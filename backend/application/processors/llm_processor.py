"""
LLM Processor.
Part of the Application Layer (Hexagonal Architecture).
"""
import asyncio
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from backend.application.processors.frames import Frame, TextFrame, CancelFrame, EndTaskFrame
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
        handle_barge_in_uc: Optional[Any] = None,  # HandleBargeInUseCase
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name="LLMProcessor")
        self.llm_port = llm_port
        self.config = config
        self.conversation_history = conversation_history
        self.execute_tool = execute_tool_use_case
        self.barge_in_uc = handle_barge_in_uc
        self.context = context or {}
        
        # State
        self.trace_id = str(uuid.uuid4())
        self._current_task: Optional[asyncio.Task] = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, TextFrame):
                # Only process final user transcripts
                if frame.is_final and frame.role == "user":
                    logger.info(f"Processing User Input: {frame.text[:30]}...")
                    
                    # Handle interruption if generation is in progress
                    if self._current_task and not self._current_task.done():
                        # Use barge-in use case if available
                        if self.barge_in_uc:
                            from backend.domain.use_cases.handle_barge_in import BargeInCommand
                            
                            command: BargeInCommand = self.barge_in_uc.execute("user_spoke")
                            
                            if command.interrupt_audio:
                                logger.info(f"🛑 Barge-in: {command.reason}")
                                self._current_task.cancel()
                            
                            if command.clear_pipeline:
                                await self.push_frame(CancelFrame(), direction)
                        else:
                            # Fallback to direct cancellation
                            self._current_task.cancel()
                        
                    # Start new generation
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
            
            else:
                await self.push_frame(frame, direction)
        else:
            await self.push_frame(frame, direction)

    async def _handle_user_text(self, text: str):
        """Main LLM Loop: Update history -> Generate -> Execute Tools -> Repeat."""
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
                     await self.push_frame(TextFrame(text=sentence_buffer, role="assistant", is_final=True), FrameDirection.DOWNSTREAM)
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
