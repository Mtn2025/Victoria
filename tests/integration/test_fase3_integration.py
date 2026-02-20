"""
Integration tests for FASE 3 components.

Tests FSM + ControlChannel + CallOrchestrator integration.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from backend.domain.entities.conversation_state import ConversationState
from backend.application.services.control_channel import ControlSignal
from backend.application.services.call_orchestrator import CallOrchestrator
from backend.domain.use_cases.start_call import StartCallUseCase
from backend.domain.use_cases.process_audio import ProcessAudioUseCase
from backend.domain.use_cases.generate_response import GenerateResponseUseCase
from backend.domain.use_cases.end_call import EndCallUseCase


class TestFASE3Integration:
    """Test FASE 3 components working together."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_lifecycle_with_fsm(self):
        """Test orchestrator lifecycle with FSM state transitions."""
        # Mock use cases
        start_call_uc = AsyncMock(spec=StartCallUseCase)
        process_audio_uc = AsyncMock(spec=ProcessAudioUseCase)
        generate_response_uc = AsyncMock(spec=GenerateResponseUseCase)
        end_call_uc = AsyncMock(spec=EndCallUseCase)
        
        # Mock call with agent
        mock_call = Mock()
        mock_agent = Mock()
        mock_agent.first_message = None
        mock_call.agent = mock_agent
        start_call_uc.execute = AsyncMock(return_value=mock_call)
        
        # Create orchestrator with short timeouts
        orchestrator = CallOrchestrator(
            start_call_uc=start_call_uc,
            process_audio_uc=process_audio_uc,
            generate_response_uc=generate_response_uc,
            end_call_uc=end_call_uc,
            max_duration=10,
            idle_timeout=2
        )
        
        # Test: Start session
        await orchestrator.start_session(
            agent_id="test-agent",
            stream_id="test-stream"
        )
        
        # Verify FSM state
        assert orchestrator.fsm.state == ConversationState.LISTENING
        
        # Verify control channel active
        assert orchestrator.control_channel.is_active
        
        # Verify background tasks running
        assert orchestrator._control_task is not None
        assert orchestrator._monitor_task is not None
        
        # Test: Stop session
        await orchestrator.end_session("test_complete")
        
        # Verify cleanup
        assert not orchestrator.active
        assert orchestrator.fsm.state == ConversationState.IDLE
        assert not orchestrator.control_channel.is_active
    
    @pytest.mark.asyncio
    async def test_orchestrator_handles_interruption(self):
        """Test orchestrator handles interruption via FSM."""
        # Setup
        start_call_uc = AsyncMock()
        process_audio_uc = AsyncMock()
        generate_response_uc = AsyncMock()
        end_call_uc = AsyncMock()
        
        mock_call = Mock()
        mock_agent = Mock()
        mock_agent.first_message = None
        mock_call.agent = mock_agent
        start_call_uc.execute = AsyncMock(return_value=mock_call)
        
        orchestrator = CallOrchestrator(
            start_call_uc=start_call_uc,
            process_audio_uc=process_audio_uc,
            generate_response_uc=generate_response_uc,
            end_call_uc=end_call_uc
        )
        
        await orchestrator.start_session("agent", "stream")
        
        # Transition to SPEAKING
        await orchestrator.fsm.transition(ConversationState.SPEAKING, "tts_started")
        
        # Test: Interrupt
        await orchestrator.handle_interruption(text="user spoke")
        
        # Verify state transitioned back to LISTENING
        assert orchestrator.fsm.state == ConversationState.LISTENING
        
        # Verify interaction time updated
        assert orchestrator.last_interaction_time > orchestrator.start_time
        
        await orchestrator.end_session()
    
    @pytest.mark.asyncio
    async def test_control_channel_sends_signals_to_loop(self):
        """Test control channel signals reach control loop."""
        # Setup
        start_call_uc = AsyncMock()
        process_audio_uc = AsyncMock()
        generate_response_uc = AsyncMock()
        end_call_uc = AsyncMock()
        
        mock_call = Mock()
        mock_agent = Mock()
        mock_agent.first_message = None
        mock_call.agent = mock_agent
        start_call_uc.execute = AsyncMock(return_value=mock_call)
        
        orchestrator = CallOrchestrator(
            start_call_uc=start_call_uc,
            process_audio_uc=process_audio_uc,
            generate_response_uc=generate_response_uc,
            end_call_uc=end_call_uc
        )
        
        await orchestrator.start_session("agent", "stream")
        
        # Send interrupt signal
        await orchestrator.control_channel.send_signal(
            ControlSignal.INTERRUPT,
            metadata={'text': 'test'}
        )
        
        # Give control loop time to process
        await asyncio.sleep(0.1)
        
        # Signal should be consumed (queue empty)
        assert orchestrator.control_channel.pending_count == 0
        
        await orchestrator.end_session()
    
    @pytest.mark.asyncio
    async def test_idle_monitor_triggers_emergency_stop(self):
        """Test idle monitor triggers emergency stop on timeout."""
        start_call_uc = AsyncMock()
        process_audio_uc = AsyncMock()
        generate_response_uc = AsyncMock()
        end_call_uc = AsyncMock()
        
        mock_call = Mock()
        mock_agent = Mock()
        mock_agent.first_message = None
        mock_call.agent = mock_agent
        start_call_uc.execute = AsyncMock(return_value=mock_call)
        
        # Very short idle timeout for testing
        orchestrator = CallOrchestrator(
            start_call_uc=start_call_uc,
            process_audio_uc=process_audio_uc,
            generate_response_uc=generate_response_uc,
            end_call_uc=end_call_uc,
            max_duration=100,
            idle_timeout=1  # 1 second
        )
        
        await orchestrator.start_session("agent", "stream")
        
        # Wait for idle timeout
        await asyncio.sleep(2)
        
        # Verify orchestrator stopped automatically
        assert not orchestrator.active
        
        # Cleanup
        await orchestrator.end_session()
