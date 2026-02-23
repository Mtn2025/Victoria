"""
Extraction Schema Value Objects.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExtractionSchema:
    """
    Schema definition for post-call conversation extraction.
    Defines the structure and expected fields for LLM extraction.
    """
    fields: dict[str, str]
    
    @staticmethod
    def default_schema() -> "ExtractionSchema":
        """
        Default extraction schema for call analysis.
        
        Returns:
            ExtractionSchema with standard fields
        """
        return ExtractionSchema(fields={
            "summary": "Resumen breve de la conversación (1-2 frases)",
            "intent": "Intención principal: agendar_cita | consulta | queja | irrelevante | buzon",
            "sentiment": "Sentimiento general: positive | neutral | negative",
            "extracted_entities": {
                "name": "Nombre del usuario (si se mencionó)",
                "phone": "Teléfono alternativo (si se mencionó)",
                "email": "Correo electrónico (si se mencionó)",
                "appointment_date": "Fecha de cita en formato ISO (si se agendó)"
            },
            "next_action": "Acción recomendada: follow_up | do_nothing"
        })


@dataclass
class ExtractionResult:
    """
    Result of post-call conversation extraction.
    Contains structured data extracted from conversation.
    """
    summary: str = ""
    is_success: bool = False
    sentiment_score: float = 0.0
    raw_data: dict = field(default_factory=dict)


class ExtractionError(Exception):
    """Raised when conversation extraction fails."""
    pass
