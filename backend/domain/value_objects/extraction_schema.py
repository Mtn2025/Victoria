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
    summary: str
    intent: str
    sentiment: str
    entities: dict[str, Any] = field(default_factory=dict)
    next_action: str = "do_nothing"
    raw_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate extracted data."""
        valid_intents = {"agendar_cita", "consulta", "queja", "irrelevante", "buzon"}
        if self.intent not in valid_intents:
            # Default to irrelevante if invalid
            object.__setattr__(self, 'intent', 'irrelevante')
        
        valid_sentiments = {"positive", "neutral", "negative"}
        if self.sentiment not in valid_sentiments:
            object.__setattr__(self, 'sentiment', 'neutral')
        
        valid_actions = {"follow_up", "do_nothing"}
        if self.next_action not in valid_actions:
            object.__setattr__(self, 'next_action', 'do_nothing')


class ExtractionError(Exception):
    """Raised when conversation extraction fails."""
    pass
