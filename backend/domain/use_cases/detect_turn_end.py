"""
Detect Turn End Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
# from backend.domain.entities.agent import Agent

class DetectTurnEndUseCase:
    """
    Determines if the user has finished speaking based on silence duration
    and agent configuration.
    """

    def execute(self, silence_duration_ms: int, threshold_ms: int) -> bool:
        """
        Check if the turn has ended.
        
        Args:
            silence_duration_ms: Detected duration of silence in milliseconds.
            threshold_ms: Silence threshold in milliseconds.
            
        Returns:
            True if turn end condition is met, False otherwise.
        """
        if silence_duration_ms < 0:
            raise ValueError("Silence duration cannot be negative")
        
        if threshold_ms < 0:
             raise ValueError("Threshold cannot be negative")

        return silence_duration_ms >= threshold_ms
