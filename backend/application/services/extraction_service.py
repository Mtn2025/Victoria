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
    ExtractionSchema,
    ExtractionResult,
    ExtractionError
)

logger = logging.getLogger(__name__)


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
        schema: Optional[ExtractionSchema] = None
    ):
        """
        Initialize extraction service.
        
        Args:
            llm_port: LLM implementation for extraction
            schema: Optional custom extraction schema (uses default if None)
        """
        self.llm_port = llm_port
        self.schema = schema or ExtractionSchema.default_schema()
    
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
                temperature=0.1,  # Deterministic
                max_tokens=800,
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
                f"intent={result.intent}, sentiment={result.sentiment}"
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
        Build system prompt with schema definition.
        
        Returns:
            System prompt string
        """
        schema_json = json.dumps(self.schema.fields, indent=2, ensure_ascii=False)
        
        return (
            "Eres un analista experto de llamadas telefónicas. "
            "Tu tarea es extraer información estructurada del diálogo "
            "que te proporcionaré, en formato JSON estricto.\n\n"
            "REGLAS IMPORTANTES:\n"
            "1. No inventes datos que no estén en el diálogo\n"
            "2. Si no hay información para un campo, usa null\n"
            "3. Sigue exactamente el schema proporcionado\n"
            "4. Retorna SOLO el JSON, sin texto adicional\n\n"
            f"SCHEMA ESPERADO:\n{schema_json}"
        )
    
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
            intent=data.get("intent", "irrelevante"),
            sentiment=data.get("sentiment", "neutral"),
            entities=data.get("extracted_entities", {}),
            next_action=data.get("next_action", "do_nothing"),
            raw_data=data
        )
