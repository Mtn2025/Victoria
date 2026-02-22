"""
Pipeline Factory - Enhanced with Legacy patterns.
Part of the Application Layer (Hexagonal Architecture).

FASE 3B Enhancement: Added ProcessorChain, async lifecycle, convenience functions.
"""
import logging
from typing import Any, List, Optional

from backend.application.processors.frame_processor import FrameProcessor
from backend.application.processors.stt_processor import STTProcessor
from backend.application.processors.vad_processor import VADProcessor
from backend.application.processors.llm_processor import LLMProcessor
from backend.application.processors.tts_processor import TTSProcessor
from backend.domain.entities.conversation_state import ConversationFSM
from backend.domain.ports.stt_port import STTPort
from backend.domain.ports.tts_port import TTSPort
from backend.domain.ports.llm_port import LLMPort
from backend.domain.value_objects.audio_format import AudioFormat
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase
from backend.domain.use_cases.handle_barge_in import HandleBargeInUseCase

logger = logging.getLogger(__name__)


class ProcessorChain:
    """
    Container for processor chain with lifecycle management.
    
    FASE 3B: Encapsulates processor list with start/stop methods.
    """
    
    def __init__(self, processors: List[FrameProcessor]):
        """
        Initialize processor chain.
        
        Args:
            processors: List of linked processors
        """
        self.processors = processors
        logger.info(f"🏭 Pipeline assembled with {len(processors)} processors")
    
    async def start(self):
        """Start all processors that support async initialization."""
        for processor in self.processors:
            if hasattr(processor, 'start') and callable(processor.start):
                await processor.start()
        logger.info("✅ All processors started")
    
    async def stop(self):
        """Stop all processors in reverse order."""
        for processor in reversed(self.processors):
            if hasattr(processor, 'stop') and callable(processor.stop):
                await processor.stop()
        logger.info("✅ All processors stopped")
    
    def __len__(self):
        """Return number of processors."""
        return len(self.processors)


class PipelineFactory:
    """
    Factory for assembling voice processing pipelines.
    
    Enhanced (FASE 3B):
    - Returns ProcessorChain instead of raw list
    - Supports optional FSM and ControlChannel injection
    - Config-based feature enablement
    - Async-aware construction
    """

    @staticmethod
    async def create_pipeline(
        config: Any,
        stt_port: STTPort,
        llm_port: LLMPort,
        tts_port: TTSPort,
        detect_turn_end: DetectTurnEndUseCase,
        execute_tool: ExecuteToolUseCase,
        conversation_history: List[dict],
        control_channel: Optional[Any] = None,
        fsm: Optional[ConversationFSM] = None,
        on_interruption_callback: Optional[Callable] = None,
        stream_id: Optional[str] = None,
        output_callback = None,          # async def cb(audio_bytes: bytes) -> None
        transcript_callback = None,      # async def cb(role: str, text: str) -> None
    ) -> ProcessorChain:
        """
        Create and wire processors into a chain.
        
        Args:
            config: Agent configuration
            stt_port: Speech-to-Text provider
            llm_port: Large Language Model provider
            tts_port: Text-to-Speech provider
            detect_turn_end: Turn detection use case
            execute_tool: Tool execution use case
            conversation_history: Shared conversation history
            control_channel: Optional control signal channel (FASE 3A)
            fsm: Optional conversation FSM (FASE 3A)
            on_interruption_callback: Optional callback for orchestrator to handle barge-in
            stream_id: Optional trace ID for logging
            output_callback: Coroutine called with each synthesized audio chunk.
                Route TTS output → WebSocket/Telephony transport.
                Signature: async def cb(audio_bytes: bytes) -> None
            
        Returns:
            ProcessorChain with linked processors
        """
        logger.info(f"🏭 Building pipeline for stream: {stream_id or 'unknown'}")

        # --- Resolución de AudioFormat desde el tipo de cliente ---
        # El client_type del agente es la fuente de verdad. Ningún procesador
        # asume un formato propio (ver contrato en audio_format.py).
        client_type = getattr(config, 'client_type', None)
        if not client_type:
            logger.warning(
                "⚠️  client_type no encontrado en config. "
                "Usando 'browser' como fallback seguro (24kHz PCM). "
                "Verifica que el agente tiene client_type configurado."
            )
            client_type = 'browser'

        audio_format = AudioFormat.for_client(client_type)
        logger.info(
            f"📡 AudioFormat resuelto: client_type={client_type!r} → "
            f"sr={audio_format.sample_rate} bits={audio_format.bits_per_sample} "
            f"enc={audio_format.encoding}"
        )

        # 1. Instantiate Processors with explicit AudioFormat
        vad = VADProcessor(config, detect_turn_end)
        stt = STTProcessor(stt_port, audio_format=audio_format, config=config)

        # LLM with optional enhancements
        llm = LLMProcessor(
            llm_port=llm_port,
            config=config,
            conversation_history=conversation_history,
            execute_tool_use_case=execute_tool,
            on_interruption_callback=on_interruption_callback,  # FASE 2.6 integration decoupled
            transcript_callback=transcript_callback, # -> Simulator real-time panel
        )

        # TTS with output_callback — routes synthesized audio back to transport.
        # Without output_callback, audio is silently dropped (TTS is last in chain).
        tts = TTSProcessor(tts_port, config, output_callback=output_callback)
        if not output_callback:
            logger.warning(
                "⚠️ No output_callback provided to TTSProcessor. "
                "Synthesized audio will NOT be sent to the client. "
                "Pass output_callback to create_pipeline() from the WS endpoint."
            )

        # 2. Wiring (Linear Pipeline)
        # Flow: Input → VAD → STT → LLM → TTS → [output_callback → WebSocket]
        vad.link(stt)
        stt.link(llm)
        llm.link(tts)

        processors = [vad, stt, llm, tts]

        logger.info(
            f"✅ Pipeline configured: {len(processors)} processors "
            f"(Tools: {bool(execute_tool)}, Barge-in Callback: {bool(on_interruption_callback)}, "
            f"Output: {'callback' if output_callback else 'NONE ⚠️'})"
        )

        return ProcessorChain(processors)
    
    @staticmethod
    async def create_minimal_pipeline(
        llm_port: LLMPort,
        tts_port: TTSPort,
        config: Any,
        conversation_history: List[dict]
    ) -> ProcessorChain:
        """
        Create minimal pipeline (LLM + TTS only).
        
        Useful for:
        - Testing
        - Text-only interactions
        - Simplified scenarios
        
        Args:
            llm_port: LLM provider
            tts_port: TTS provider
            config: Agent configuration
            conversation_history: Shared history
            
        Returns:
            ProcessorChain with LLM and TTS only
        """
        logger.info("🏭 Building minimal pipeline (LLM + TTS)")
        
        llm = LLMProcessor(
            llm_port=llm_port,
            config=config,
            conversation_history=conversation_history
        )
        tts = TTSProcessor(tts_port, config)
        
        llm.link(tts)
        
        return ProcessorChain([llm, tts])


# Convenience function for standard configuration
async def create_standard_pipeline(
    config: Any,
    stt_port: STTPort,
    llm_port: LLMPort,
    tts_port: TTSPort,
    conversation_history: List[dict],
    tools: Optional[dict] = None,
    control_channel: Optional[Any] = None,
    fsm: Optional[ConversationFSM] = None,
    stream_id: Optional[str] = None
) -> ProcessorChain:
    """
    Create pipeline with standard configuration.
    
    Automatically creates use cases and wires everything together.
    
    Args:
        config: Agent configuration
        stt_port: STT provider
        llm_port: LLM provider
        tts_port: TTS provider
        conversation_history: Shared history
        tools: Optional tool registry
        control_channel: Optional control channel
        fsm: Optional FSM
        stream_id: Optional trace ID
        
    Returns:
        Configured ProcessorChain
    """
    # Create use cases
    detect_turn_end = DetectTurnEndUseCase()
    execute_tool = ExecuteToolUseCase(tools) if tools else ExecuteToolUseCase({})
    handle_barge_in = HandleBargeInUseCase()
    
    return await PipelineFactory.create_pipeline(
        config=config,
        stt_port=stt_port,
        llm_port=llm_port,
        tts_port=tts_port,
        detect_turn_end=detect_turn_end,
        execute_tool=execute_tool,
        conversation_history=conversation_history,
        control_channel=control_channel,
        fsm=fsm,
        handle_barge_in_uc=handle_barge_in,
        stream_id=stream_id
    )
