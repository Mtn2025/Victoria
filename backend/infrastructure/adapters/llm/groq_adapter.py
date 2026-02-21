"""
Groq LLM Adapter.
Part of the Infrastructure Layer (Hexagonal Architecture).
"""
import logging
import json
from typing import AsyncIterator, List, Optional

from groq import AsyncGroq, APIConnectionError, RateLimitError, APIError

from backend.domain.ports.llm_port import LLMPort, LLMRequest, LLMResponseChunk
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent
from backend.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class GroqLLMAdapter(LLMPort):
    """
    Adapter for the Groq API implementing the LLMPort interface.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("Groq API Key missing. Adapter may fail.")
        
        self.client = AsyncGroq(api_key=self.api_key)
        # Canonical default — must match the model saved by PATCH /agents/{uuid}
        self.default_model = "llama-3.3-70b-versatile"

    async def generate_response(self, conversation: Conversation, agent: Agent) -> str:
        """
        Generate a single completion.
        Reads model/temperature from agent.llm_config (SSoT: DB → Agent entity → here).
        """
        try:
            messages = self._build_messages(conversation, agent)
            llm_cfg  = getattr(agent, 'llm_config', {}) or {}

            completion = await self.client.chat.completions.create(
                # Read 'llm_model' (canonical since Rep D), fallback to legacy 'model'
                model=llm_cfg.get('llm_model') or llm_cfg.get('model', self.default_model),
                messages=messages,
                temperature=llm_cfg.get('temperature', 0.7),
                max_tokens=llm_cfg.get('max_tokens', 600),
                stream=False
            )

            return completion.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"[GroqLLM] Generation failed: {e}")
            raise

    async def generate_stream(self, request: "LLMRequest") -> AsyncIterator["LLMResponseChunk"]:
        """
        Stream structured response chunks.
        """
        try:
            # Prepare messages from request
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            
            # System prompt is usually in request or separate? 
            # LLMRequest has system_prompt field.
            if request.system_prompt:
                 messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            stream = await self.client.chat.completions.create(
                model=request.model or self.default_model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield LLMResponseChunk(text=content, is_final=False)
            
            # Yield final chunk? or just end.
            yield LLMResponseChunk(text="", is_final=True)

        except Exception as e:
            logger.error(f"[GroqLLM] Streaming failed: {e}")
            raise

    def _build_messages(self, conversation: Conversation, agent: Agent) -> List[dict]:
        """Convert Domain Conversation to Groq Message format."""
        messages = []
        
        # System Prompt
        if agent.system_prompt:
            messages.append({"role": "system", "content": agent.system_prompt})
            
        # Conversation History
        for turn in conversation.turns:
            messages.append({"role": turn.role, "content": turn.content})
            
        return messages

    async def get_available_models(self) -> List[str]:
        """
        Get list of available Groq models.
        """
        # Groq models as of current knowledge
        # TODO: Fetch dynamically from Groq API when available
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

    def is_model_safe_for_voice(self, model: str) -> bool:
        """
        Check if model is suitable for voice applications.
        
        Voice requires low latency and conversational quality.
        """
        # Fast models suitable for voice
        voice_safe_models = [
            "llama-3.3-70b-versatile",  # Good balance of speed and quality
            "llama-3.1-8b-instant",   # Faster but lower quality
            "mixtral-8x7b-32768",  # Good quality, acceptable latency
        ]
        return model in voice_safe_models
