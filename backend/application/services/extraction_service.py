"""
Extraction Service.
Part of the Application Layer (Hexagonal Architecture).

Post-call conversation analysis and structured data extraction.
"""
import logging
import json
from typing import Optional

from backend.domain.entities.conversation import Conversation
from backend.domain.ports.llm_port import LLMPort
from backend.domain.ports.llm_port import LLMRequest, LLMMessage
from backend.domain.value_objects.extraction_schema import (
    ExtractionResult,
    ExtractionError
)
from backend.domain.ports.config_repository_port import ConfigDTO

logger = logging.getLogger(__name__)

# Maximum tokens for extraction prompt responses.
# Kept small (< 1k) since output is structured JSON, not conversational.
# TECHNICAL CONSTANT: changing this affects JSON completeness vs. cost tradeoff.
MAX_EXTRACTION_TOKENS: int = 800


class ExtractionService:
    """
    Service for extracting structured data from conversation history.
    
    Uses LLM to analyze completed conversations and extract:
    - Summary
    - Intent classification
    - Sentiment analysis
    - Named entities (name, phone, email, dates)
    - Recommended next action
    
    Example:
        >>> service = ExtractionService(llm_port=groq_adapter)
        >>> result = await service.extract_from_conversation(conversation)
        >>> print(result.intent)  # "consulta"
    """
    
    def __init__(
        self,
        llm_port: LLMPort,
        config: Optional[ConfigDTO] = None
    ):
        """
        Initialize extraction service.
        
        Args:
            llm_port: LLM implementation for extraction
            config: Agent dynamic configuration
        """
        self.llm_port = llm_port
        self.config = config
    
    async def extract_from_conversation(
        self,
        conversation: Conversation,
        call_id: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data from conversation.
        
        Args:
            conversation: Domain Conversation entity
            call_id: Optional call ID for logging
            
        Returns:
            ExtractionResult with extracted fields
            
        Raises:
            ValueError: If conversation is empty
            ExtractionError: If LLM extraction fails
        """
        # Input validation
        if not conversation.turns:
            raise ValueError("Cannot extract from empty conversation")
        
        logger.info(
            f"🔍 [EXTRACTION] Analyzing {len(conversation.turns)} turns "
            f"for call {call_id or 'unknown'}"
        )
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._format_conversation(conversation)
        
        # Call LLM (non-streaming, JSON mode)
        try:
            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_prompt)
                ],
                temperature=0.1,  # INTENTIONAL: deterministic for structured JSON extraction
                max_tokens=MAX_EXTRACTION_TOKENS,
                model=None,  # Use default model
            )
            
            # Generate response (Streaming accumulator)
            full_content = ""
            async for chunk in self.llm_port.generate_stream(request):
                if chunk.has_text:
                    full_content += chunk.text
            
            # Parse JSON
            extracted_data = json.loads(full_content)
            
            # Map to value object
            result = self._map_to_result(extracted_data)
            
            logger.info(
                f"✅ [EXTRACTION] Success for call {call_id}: "
                f"is_success={result.is_success}, sentiment={result.sentiment_score}"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [EXTRACTION] Invalid JSON response: {e}")
            raise ExtractionError(f"Failed to parse extraction JSON: {e}") from e
            
        except Exception as e:
            logger.error(f"❌ [EXTRACTION] Failed for call {call_id}: {e}")
            raise ExtractionError(f"Extraction failed: {e}") from e
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt with dynamic config values from the agent.
        """
        base_prompt = "Eres un analista experto de llamadas telefónicas. Tu tarea es extraer información estructurada del diálogo que te proporcionaré, en formato JSON estricto.\n\n"
        
        # User defined Analysis Prompt
        if self.config and self.config.analysis_prompt:
            base_prompt += f"INSTRUCCIONES PRINCIPALES:\n{self.config.analysis_prompt}\n\n"
            
        # Success Rubric
        if self.config and self.config.success_rubric:
            base_prompt += f"CRITERIO DE ÉXITO DE LA LLAMADA (Evaluador):\nEvalúa si la llamada fue un éxito basado en lo siguiente y retorna un booleano en 'is_success':\n{self.config.success_rubric}\n\n"
            
        # PII Redaction
        if self.config and getattr(self.config, 'pii_redaction_enabled', False):
            base_prompt += "CENSURA PII ACTIVADA: Debes censurar cualquier dato sensible (tarjetas de crédito, SSN, contraseñas) reemplazándolos por asteriscos **** en el JSON final.\n\n"

        # Construct Schema Expected
        schema_format = {}
        
        # Parse User Schema if present
        if self.config and getattr(self.config, 'extraction_schema', None):
            user_schema = self.config.extraction_schema
            if isinstance(user_schema, str):
                try:
                    schema_format = json.loads(user_schema)
                except json.JSONDecodeError:
                    pass
            elif isinstance(user_schema, dict):
                schema_format = user_schema
                
        # If no user schema, use default
        if not schema_format:
            schema_format = {
                "summary": "Resumen breve de la conversación (1-2 frases)",
                "intent": "Intención principal: agendar_cita | consulta | queja | irrelevante | buzon",
                "extracted_entities": {
                    "name": "Nombre del usuario (si se mencionó)",
                    "phone": "Teléfono alternativo (si se mencionó)"
                }
            }

        # Ensure core fields are present for Victoria metrics
        schema_format["summary"] = schema_format.get("summary", "Resumen ejecutivo de la llamada")
        schema_format["is_success"] = "Booleano si cumplió el criterio de éxito"
        if self.config and getattr(self.config, 'sentiment_analysis', False):
            schema_format["sentiment_score"] = "Número float entre -1.0 y 1.0 (Muy negativo a Muy Positivo)"
        
        schema_json = json.dumps(schema_format, indent=2, ensure_ascii=False)
        
        base_prompt += (
            "REGLAS IMPORTANTES:\n"
            "1. No inventes datos que no estén en el diálogo\n"
            "2. Si no hay información para un campo, usa null\n"
            "3. Sigue exactamente la estructura del schema JSON proporcionado\n"
            "4. Retorna SOLO el JSON válido, sin delimitadores como ```json ni texto adicional\n\n"
            f"SCHEMA JSON ESPERADO:\n{schema_json}"
        )
        return base_prompt
    
    def _format_conversation(self, conversation: Conversation) -> str:
        """
        Format conversation turns as text for LLM.
        
        Args:
            conversation: Conversation entity
            
        Returns:
            Formatted dialogue string
        """
        lines = []
        for turn in conversation.turns:
            role_label = "USUARIO" if turn.role == "user" else "ASISTENTE"
            lines.append(f"{role_label}: {turn.content}")
        
        dialogue = "\n".join(lines)
        return f"DIÁLOGO A ANALIZAR:\n\n{dialogue}"
    
    def _map_to_result(self, data: dict) -> ExtractionResult:
        """
        Map raw JSON data to ExtractionResult value object.
        
        Args:
            data: Raw extraction data from LLM
            
        Returns:
            ExtractionResult with validated fields
        """
        return ExtractionResult(
            summary=data.get("summary", ""),
            is_success=data.get("is_success", False),
            sentiment_score=float(data.get("sentiment_score", 0.0)),
            raw_data=data
        )
