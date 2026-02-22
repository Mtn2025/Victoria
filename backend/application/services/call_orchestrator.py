"""
Call Orchestrator Service.
Part of the Application Layer (Hexagonal Architecture).

Coordinating the flow of a voice call by executing Domain Use Cases.
Enhanced with FSM, ControlChannel, and lifecycle management (FASE 3).
"""
import asyncio
import contextlib
import logging
import time
from typing import Any, Optional, AsyncGenerator

from backend.domain.entities.call import Call
from backend.domain.entities.conversation_state import ConversationFSM, ConversationState
from backend.domain.use_cases.start_call import StartCallUseCase
from backend.domain.use_cases.process_audio import ProcessAudioUseCase
from backend.domain.use_cases.generate_response import GenerateResponseUseCase
from backend.domain.use_cases.end_call import EndCallUseCase
from backend.domain.use_cases.synthesize_text import SynthesizeTextUseCase
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.domain.use_cases.handle_barge_in import HandleBargeInUseCase
from backend.domain.value_objects.audio_format import AudioFormat
from backend.domain.value_objects.voice_config import VoiceConfig
from backend.domain.ports.config_repository_port import ConfigDTO
from backend.domain.ports.stt_port import STTPort
from backend.domain.ports.llm_port import LLMPort
from backend.domain.ports.tts_port import TTSPort
from backend.application.services.control_channel import (
    ControlChannel,
    ControlSignal,
    send_interrupt,
    send_emergency_stop
)
from backend.application.factories.pipeline_factory import PipelineFactory, ProcessorChain
from backend.application.processors.frames import AudioFrame, FrameDirection

logger = logging.getLogger(__name__)


def _agent_to_config_dto(agent) -> ConfigDTO:
    """
    Bridge function: converts Agent entity → ConfigDTO at the pipeline boundary.

    SSoT contract:
      DB → agent_repository._model_to_agent() → Agent entity
          → HERE → ConfigDTO → pipeline processors

    All pipeline processors receive a flat ConfigDTO and NEVER inspect
    the Agent entity directly. This is the single conversion point.
    """
    llm  = agent.llm_config or {}
    vc   = agent.voice_config  # VoiceConfig value object — guaranteed by Agent.__post_init__
    meta = getattr(agent, 'metadata', {}) or {}

    return ConfigDTO(
        # --- LLM (from agent.llm_config JSON — keys are 'llm_provider'/'llm_model' since Rep D fix) ---
        llm_provider = llm.get('llm_provider') or llm.get('provider', 'groq'),   # canonical first, legacy fallback
        llm_model    = llm.get('llm_model')    or llm.get('model',    'llama-3.3-70b-versatile'),
        temperature  = float(llm.get('temperature', 0.7)),
        max_tokens   = int(llm.get('max_tokens',   600)),
        system_prompt      = agent.system_prompt  or '',
        first_message      = agent.first_message  or '',
        first_message_mode = llm.get('first_message_mode', 'text'),

        # --- TTS (from agent.voice_config VoiceConfig VO, DB → here) ---
        tts_provider        = vc.provider         or 'azure',
        voice_name          = vc.name,            # ← actual voice from DB
        voice_style         = vc.style            or 'default',
        voice_style_degree  = float(vc.style_degree),
        voice_speed         = float(vc.speed),
        voice_pitch         = int(vc.pitch),
        voice_volume        = int(vc.volume),
        voice_language      = llm.get('voice_language', 'es-MX'),

        # --- STT ---
        stt_provider        = meta.get('stt_config', {}).get('sttProvider', 'azure'),  # canonical front key
        stt_language        = meta.get('stt_config', {}).get('sttLang', 'es-MX'),
        silence_timeout_ms  = agent.silence_timeout_ms,

        # --- Runtime ---
        client_type = llm.get('client_type', 'browser'),
    )


class CallOrchestrator:
    """
    Orchestrates the lifecycle of a voice call.
    Acts as the facade for the Interface layer to interact with the Core Domain.

    FASE 3 Complete: FSM, ControlChannel, PipelineFactory, SynthesizeText
    """

    def __init__(
        self,
        start_call_uc: StartCallUseCase,
        process_audio_uc: ProcessAudioUseCase,
        generate_response_uc: GenerateResponseUseCase,
        end_call_uc: EndCallUseCase,
        synthesize_text_uc: Optional[SynthesizeTextUseCase] = None,
        # Ports (COMPLETION: needed for pipeline)
        stt_port: Optional[STTPort] = None,
        llm_port: Optional[LLMPort] = None,
        tts_port: Optional[TTSPort] = None,
        # Repositories
        config_repository: Optional[Any] = None,
        transcript_repository: Optional[Any] = None,
        # Tools and history
        tools: Optional[dict] = None,
        # Timeouts
        max_duration: int = 600,
        idle_timeout: int = 30
    ):
        # Use cases
        self.start_call_uc = start_call_uc
        self.process_audio_uc = process_audio_uc
        self.generate_response_uc = generate_response_uc
        self.end_call_uc = end_call_uc
        self.synthesize_text_uc = synthesize_text_uc
        
        # Ports (COMPLETION)
        self.stt_port = stt_port
        self.llm_port = llm_port
        self.tts_port = tts_port
        
        # Repositories
        self.config_repo = config_repository
        self.transcript_repo = transcript_repository
        
        # Tools and conversation history
        self.tools = tools or {}
        self.conversation_history: list = []
        
        # Call state
        self.current_call: Optional[Call] = None
        
        # FASE 3A: FSM for conversation state management
        self.fsm = ConversationFSM()
        
        # FASE 3A: Control channel for signal management
        self.control_channel = ControlChannel()
        self._control_task: Optional[asyncio.Task] = None
        
        # FASE 3B: Pipeline
        self.pipeline: Optional[ProcessorChain] = None

        # Transcript callback — async def cb(role: str, text: str) -> None
        # Set by audio_stream.py to send real-time transcripts to the WebSocket.
        # Used by LLMProcessor (assistant turns) and STTProcessor (user turns).
        self._transcript_callback = None
        
        # FASE 3A: Lifecycle management
        self.start_time = time.time()
        self.last_interaction_time = time.time()
        self.max_duration = max_duration
        self.idle_timeout = idle_timeout
        self._monitor_task: Optional[asyncio.Task] = None
        self.active = False
        
        logger.info("🎯 CallOrchestrator initialized (FASE 3 complete)")

    async def start_session(
        self, 
        agent_id: str, 
        stream_id: str, 
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        audio_output_callback = None,    # async def cb(audio_bytes: bytes) -> None
        transcript_callback = None,      # async def cb(role: str, text: str) -> None
    ) -> Optional[bytes]:
        """
        Start the call session with enhanced lifecycle management.
        
        Args:
            audio_output_callback: Coroutine called for each TTS audio chunk produced
                by the pipeline. Routes audio bytes to the WebSocket client.
            transcript_callback: Coroutine called for each STT/LLM text turn produced
                by the pipeline. Routes transcript events to the WebSocket client so
                the Simulator panel can show real-time transcriptions.
                Signature: async def cb(role: str, text: str) -> None
        """
        logger.info(f"🚀 Starting session: {stream_id} for agent: {agent_id}")
        self.active = True
        self.start_time = time.time()
        self.last_interaction_time = time.time()
        
        try:
            # STEP 1: Start call via use case
            self.current_call = await self.start_call_uc.execute(
                agent_id=agent_id,
                call_id_value=stream_id,
                from_number=from_number,
                to_number=to_number
            )
            logger.info("✅ Call initialized")
            
            # Capture agent reference immediately for Pipeline and Greeting
            agent = self.current_call.agent
            
            # STEP 2: FSM transition to LISTENING
            await self.fsm.transition(ConversationState.LISTENING, "session_started")
            
            # STEP 3: Build pipeline (if ports available)
            if self.stt_port and self.llm_port and self.tts_port:
                logger.info("🏭 Building pipeline...")
                
                # Create use cases for pipeline
                detect_turn_end_uc = DetectTurnEndUseCase()
                execute_tool_uc = ExecuteToolUseCase(self.tools)
                self.handle_barge_in_uc = HandleBargeInUseCase()
                
                # Build pipeline via factory.
                # Convert Agent entity → ConfigDTO (flat) so every processor
                # reads from ConfigDTO attributes. See _agent_to_config_dto().
                self.pipeline = await PipelineFactory.create_pipeline(
                    config=_agent_to_config_dto(agent),
                    stt_port=self.stt_port,
                    llm_port=self.llm_port,
                    tts_port=self.tts_port,
                    detect_turn_end=detect_turn_end_uc,
                    execute_tool=execute_tool_uc,
                    conversation_history=self.conversation_history,
                    control_channel=self.control_channel,
                    fsm=self.fsm,
                    on_interruption_callback=self.handle_interruption,
                    stream_id=stream_id,
                    output_callback=audio_output_callback,       # TTS → WebSocket return path
                    transcript_callback=transcript_callback,     # STT/LLM → simulator panel
                )
                logger.info("✅ Pipeline built")
                
                # STEP 4: Start pipeline processors
                await self.pipeline.start()
                logger.info("✅ Pipeline started")
            else:
                logger.warning("⚠️ Ports not available, skipping pipeline creation")
            
            # STEP 5: Start control loop
            self._control_task = asyncio.create_task(self._control_loop())
            logger.info("✅ Control loop started")

            logger.info("🚀 All subsystems running")
            
            # STEP 7: Send initial greeting (FASE 3B)
            greeting_audio = None
            if agent.first_message and self.synthesize_text_uc and self.tts_port:
                logger.info(f"👋 Greeting: {agent.first_message[:50]}...")
                try:
                    # Use the agent's existing voice_config (already a VoiceConfig VO)
                    # agent.voice_config is always set — the repo guarantees it.
                    voice_config = agent.voice_config
                    
                    # Synthesize greeting (direct TTS, no LLM overhead)
                    greeting_audio = await self.synthesize_text_uc.execute(
                        text=agent.first_message,
                        voice_config=voice_config,
                        trace_id=stream_id
                    )
                    logger.info(f"✅ Greeting synthesized ({len(greeting_audio)} bytes)")
                except Exception as e:
                    logger.warning(f"⚠️ Greeting synthesis failed: {e}")

            # STEP 6 (moved after greeting): Start idle monitor so the countdown
            # only begins once the session is fully ready for user input.
            # Resetting last_interaction_time here covers the greeting synthesis time.
            self.last_interaction_time = time.time()
            self._monitor_task = asyncio.create_task(self._monitor_idle())
            logger.info("✅ Monitor task started (post-greeting)")

            # Return greeting audio (caller sends to transport)
            return greeting_audio

        except Exception as e:
            logger.error(f"❌ Session start failed: {e}")
            await self.stop()
            raise

    async def process_audio_input(self, audio_chunk: bytes) -> AsyncGenerator[bytes, None]:
        """
        Process incoming audio chunk.
        
        Behavior:
        1. Forward to VAD (not impl yet, assumed Platform trigger or simple buffering).
        2. If turn ends, STT -> LLM -> TTS.
        3. Yield audio response chunks.
        """
        if not self.current_call:
            logger.error("Call not initialized")
            return

        # SIMPLIFIED LOGIC FOR PHASE 7 (Service Verification):
        # We assume `ProcessAudioUseCase` handles the chunk (e.g. one-shot or accumulating).
        # In reality, we need VAD + Buffer.
        # For now, we will assume the Interface layer calls this when it has a "speech utterance".
        # Or we treat this as "one request = one turn" for verification.
        
        text_input = await self.process_audio_uc.execute(audio_chunk, self.current_call)
        
        if text_input:
            logger.info(f"User said: {text_input}")
            
            # Save user transcript if repository available
            if self.transcript_repo and self.current_call:
                # Note: Need call DB ID, not domain CallID
                # This assumes Call entity has db_id attribute or similar
                call_db_id = getattr(self.current_call, 'db_id', None)
                if call_db_id:
                    await self.transcript_repo.save(
                        call_id=call_db_id,
                        role="user",
                        content=text_input
                    )
            
            # Generate Response
            response_text = ""
            async for audio_chunk in self.generate_response_uc.execute(text_input, self.current_call):
                # Accumulate response text for transcript
                # This requires response text to be available, might need refactoring
                yield audio_chunk
            
            # Save assistant transcript if repository available
            # TODO: Capture assistant text from generate_response output
            # For now, this is a placeholder showing the integration point

    async def push_audio_frame(
        self,
        raw_audio: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
    ) -> None:
        """
        Inject raw PCM audio bytes into the pipeline as an AudioFrame.

        This is the correct path for browser audio: instead of calling
        process_audio_uc directly (which bypasses the pipeline), we create
        an AudioFrame and push it into the first pipeline processor (VAD).
        The pipeline then handles: VAD → STT → LLM → TTS.

        Args:
            raw_audio:   Raw PCM16 bytes (already decoded from base64 by the caller).
            sample_rate: Audio sample rate in Hz (24000 for browser).
            channels:    Number of channels (1 = mono).
        """
        if not self.pipeline or not self.pipeline.processors:
            logger.warning("push_audio_frame: pipeline not ready, dropping frame")
            return

        # Reset idle timer — receiving audio counts as user interaction
        self.last_interaction_time = time.time()

        # [PIPE-1] Confirm audio arrived at orchestrator and is entering the pipeline
        logger.debug(
            f"[PIPE-1/ORCH] {len(raw_audio)}B sr={sample_rate} ch={channels} "
            f"→ pushing to VAD"
        )

        frame = AudioFrame(
            data=raw_audio,
            sample_rate=sample_rate,
            channels=channels,
        )

        # The first processor in the chain is always VAD
        first_processor = self.pipeline.processors[0]
        try:
            await first_processor.process_frame(frame, FrameDirection.DOWNSTREAM)
        except Exception as e:
            logger.error(f"push_audio_frame: error pushing frame: {e}", exc_info=True)


    async def end_session(self, reason: str = "completed") -> None:
        """
        End the call session with graceful cleanup.

        FASE 3 enhancements:
        - Stop all background tasks
        - Clean FSM state
        - Close control channel

        Post-call extraction:
        If a conversation accumulated turns, ExtractionService is called to
        analyze the full transcript via LLM and save the result in
        call.metadata['extracted_data'] before persisting the final call state.
        """
        logger.info(f"🛑 Ending session: {reason}")
        await self.stop()
        
        if self.current_call:
            # --- Post-call extraction ---
            # Run only if the conversation has actual turns (user/assistant exchanges)
            if self.current_call.conversation.turns and self.llm_port:
                try:
                    from backend.application.services.extraction_service import ExtractionService
                    extraction = ExtractionService(llm_port=self.llm_port)
                    result = await extraction.extract_from_conversation(
                        self.current_call.conversation,
                        call_id=self.current_call.id.value
                    )
                    # Persist in call.metadata so call_repository.save() stores it
                    self.current_call.update_metadata("extracted_data", result.raw_data)
                    logger.info("✅ Post-call extraction saved to call metadata")
                except Exception as e:
                    # Non-fatal: log and continue — call record still saved
                    logger.warning(f"⚠️ Post-call extraction failed (non-fatal): {e}")

            await self.end_call_uc.execute(self.current_call, reason)
            self.current_call = None
            logger.info("✅ Session ended")
    
    async def stop(self) -> None:
        """
        Stop orchestrator and cleanup resources.
        
        FASE 3: Comprehensive cleanup of background tasks and state.
        """
        logger.info("Stopping orchestrator...")
        self.active = False
        
        # Stop pipeline processors (FASE 3B)
        if self.pipeline:
            await self.pipeline.stop()
            logger.info("✅ Pipeline stopped")
        
        # Cancel monitor task
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
        
        # Cancel control loop
        if self._control_task:
            self._control_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._control_task
        
        # Close control channel
        self.control_channel.close()
        
        # Reset FSM
        self.fsm.reset()
        
        logger.info("✅ Orchestrator stopped")
    
    async def handle_interruption(self, text: str = "") -> None:
        """
        Handle user interruption (barge-in).
        Called by downstream processors when user speech is detected.
        """
        # 1. Evaluate Domain Logic (if applicable)
        if hasattr(self, 'handle_barge_in_uc') and self.handle_barge_in_uc:
            try:
                command = self.handle_barge_in_uc.execute("user_spoke")
                if not command.interrupt_audio:
                    return
            except Exception as e:
                logger.error(f"Barge-In use case error: {e}")
                
        # 2. Only interrupt if FSM allows it
        if not await self.fsm.can_interrupt():
            logger.debug(
                f"🛑 Interruption ignored - state={self.fsm.state.value} "
                f"(text: {text[:30] if text else 'VAD'})"
            )
            return
        
        logger.info(f"🛑 Orchestrator executing Barge-in override: {text[:50] if text else 'VAD'}")
        
        # 3. INTERRUPT PIPELINE (PUSH CANCEL FRAME)
        if hasattr(self, 'pipeline') and self.pipeline and self.pipeline.processors:
            from backend.application.processors.frames import CancelFrame, FrameDirection
            try:
                logger.info("🛑 Pushing CancelFrame to pipeline")
                await self.pipeline.processors[0].process_frame(CancelFrame(), FrameDirection.DOWNSTREAM)
            except Exception as e:
                logger.error(f"Failed to push CancelFrame: {e}")

        # 4. CLEAR FRONTEND BUFFER
        if hasattr(self, '_transcript_callback') and self._transcript_callback:
            try:
                await self._transcript_callback("clear", f"barge-in-orchestrator")
                logger.debug("✅ Clear signal sent to frontend through Orchestrator")
            except Exception as e:
                logger.error(f"Failed to send clear signal: {e}")

        # 5. FSM Transition: SPEAKING/PROCESSING → INTERRUPTED
        await self.fsm.transition(
            ConversationState.INTERRUPTED,
            f"user_spoke: {text[:30]}" if text else "vad_detected"
        )
        
        # 6. Send interrupt signal to control channel
        await send_interrupt(
            self.control_channel,
            reason="user_spoke" if text else "vad_detected",
            text=text
        )
        
        # 7. Transition: INTERRUPTED → LISTENING
        await self.fsm.transition(ConversationState.LISTENING, "ready_for_input")
        
        # Update interaction time
        self.last_interaction_time = time.time()
    
    # -------------------------------------------------------------------------
    # BACKGROUND TASKS (FASE 3)
    # -------------------------------------------------------------------------
    
    async def _control_loop(self) -> None:
        """
        Background loop for processing control signals.
        Runs independently from main flow to ensure immediate response.
        """
        logger.info("Control loop started")
        
        while self.active:
            try:
                # Wait for control signal (non-blocking)
                msg = await self.control_channel.wait_for_signal(timeout=1.0)
                
                if not msg:
                    continue
                
                # Handle control signals
                if msg.signal == ControlSignal.INTERRUPT:
                    text = msg.metadata.get('text', '')
                    # Interrupt signal already handled, just log
                    logger.debug(f"Control: INTERRUPT processed ({text[:30] if text else 'VAD'})")
                
                elif msg.signal == ControlSignal.CANCEL:
                    logger.info("Control: CANCEL signal received")
                    # TODO: Clear processor queues when processors exist
                
                elif msg.signal == ControlSignal.EMERGENCY_STOP:
                    reason = msg.metadata.get('reason', 'unknown')
                    logger.warning(f"Control: EMERGENCY_STOP - {reason}")
                    await self.stop()
                    break
                
                elif msg.signal == ControlSignal.CLEAR_PIPELINE:
                    logger.debug("Control: CLEAR_PIPELINE")
                    # TODO: Implement when processors exist
            
            except Exception as e:
                logger.error(f"Control loop error: {e}", exc_info=True)
        
        logger.info("Control loop stopped")
    
    async def _monitor_idle(self) -> None:
        """
        Monitor for idle timeout and max duration.
        
        FASE 3: Resource management and automatic cleanup.
        """
        logger.info("👁️ Starting idle monitor")
        
        while self.active:
            try:
                await asyncio.sleep(1.0)
                now = time.time()
                
                # Max duration check
                if now - self.start_time > self.max_duration:
                    logger.info(f"⏱️ Max duration reached ({self.max_duration}s)")
                    await send_emergency_stop(
                        self.control_channel,
                        reason="max_duration_exceeded"
                    )
                    break
                
                # Idle timeout check
                if now - self.last_interaction_time > self.idle_timeout:
                    logger.info(f"😴 Idle timeout reached ({self.idle_timeout}s)")
                    await send_emergency_stop(
                        self.control_channel,
                        reason="idle_timeout"
                    )
                    break
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
        
        logger.info("Monitor stopped")
