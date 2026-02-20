"""
Unit tests for HandleBargeInUseCase.

Tests barge-in decision logic for different interruption scenarios.
"""
import pytest

from backend.domain.use_cases.handle_barge_in import HandleBargeInUseCase, BargeInCommand


class TestHandleBargeInUseCase:
    """Test barge-in use case decision logic."""
    
    def test_vad_detected_full_interruption(self):
        """Test VAD detection triggers full interruption."""
        use_case = HandleBargeInUseCase()
        
        command = use_case.execute("vad_detected")
        
        assert isinstance(command, BargeInCommand)
        assert command.clear_pipeline is True
        assert command.interrupt_audio is True
        assert command.reason == "vad_detected"
    
    def test_user_spoke_full_interruption(self):
        """Test user speech triggers full interruption."""
        use_case = HandleBargeInUseCase()
        
        command = use_case.execute("user_spoke")
        
        assert command.clear_pipeline is True
        assert command.interrupt_audio is True
        assert command.reason == "user_spoke"
    
    def test_user_input_full_interruption(self):
        """Test any user input reason triggers full interruption."""
        use_case = HandleBargeInUseCase()
        
        command = use_case.execute("user_input_detected")
        
        assert command.clear_pipeline is True
        assert command.interrupt_audio is True
    
    def test_other_reason_conservative_interruption(self):
        """Test non-user reasons trigger conservative interruption."""
        use_case = HandleBargeInUseCase()
        
        command = use_case.execute("silence_timeout")
        
        assert command.clear_pipeline is False  # Don't clear pipeline
        assert command.interrupt_audio is True  # But do stop audio
        assert command.reason == "silence_timeout"
    
    def test_error_reason_conservative_interruption(self):
        """Test error reasons don't clear pipeline."""
        use_case = HandleBargeInUseCase()
        
        command = use_case.execute("error: connection lost")
        
        assert command.clear_pipeline is False
        assert command.interrupt_audio is True
    
    def test_case_insensitive_matching(self):
        """Test reason matching is case-insensitive."""
        use_case = HandleBargeInUseCase()
        
        # Uppercase VAD
        command1 = use_case.execute("VAD_DETECTED")
        assert command1.clear_pipeline is True
        
        # Mixed case user
        command2 = use_case.execute("User_Spoke")
        assert command2.clear_pipeline is True
