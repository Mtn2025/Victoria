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
        self.default_model = settings.GROQ_MODEL or "llama3-70b-8192"

    async def generate_response(self, conversation: Conversation, agent: Agent) -> str:
        """
        Generate a single completion.
        """
        try:
            messages = self._build_messages(conversation, agent)
            
            completion = await self.client.chat.completions.create(
                model=self.default_model, # Could override from agent.llm_config
                messages=messages,
                temperature=0.7,
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
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
        ]

    def is_model_safe_for_voice(self, model: str) -> bool:
        """
        Check if model is suitable for voice applications.
        
        Voice requires low latency and conversational quality.
        """
        # Fast models suitable for voice
        voice_safe_models = [
            "llama3-70b-8192",  # Good balance of speed and quality
            "llama3-8b-8192",   # Faster but lower quality
            "mixtral-8x7b-32768",  # Good quality, acceptable latency
        ]
        return model in voice_safe_models
