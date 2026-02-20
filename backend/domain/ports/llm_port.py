"""
LLM Port (Interface).
Part of the Domain Layer (Hexagonal Architecture).

Merged version combining best features from Legacy and Victoria systems.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
from dataclasses import dataclass, field

from backend.domain.entities.conversation import Conversation
from backend.domain.entities.agent import Agent


@dataclass
class LLMMessage:
    """Message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str


@dataclass
class LLMFunctionCall:
    """Function call request from LLM."""
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponseChunk:
    """
    Streaming response chunk from LLM.
    
    Can contain text, function call, or both.
    """
    text: str = ""
    is_final: bool = False
    function_call: Optional[LLMFunctionCall] = None

    @property
    def has_text(self) -> bool:
        """Check if chunk contains text."""
        return bool(self.text)

    @property
    def has_function_call(self) -> bool:
        """Check if chunk contains a function call."""
        return self.function_call is not None


@dataclass
class LLMRequest:
    """
    Request for LLM generation.
    
    Supports streaming, function calling, and advanced controls.
    """
    messages: List[LLMMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 600  # Increased from 500 (Legacy default)
    system_prompt: str = ""
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced LLM Controls
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class LLMPort(ABC):
    """
    Interface for Large Language Model providers.
    
    Adapters must implement this to connect with Groq, OpenAI, Claude, etc.
    """

    @abstractmethod
    async def generate_response(self, conversation: Conversation, agent: Agent) -> str:
        """
        Generate a single completion (simple/legacy method).
        
        Used by GenerateResponseUseCase for backward compatibility.
        
        Args:
            conversation: Current conversation context
            agent: Agent configuration
            
        Returns:
            Generated text response
            
        Raises:
            LLMException: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMResponseChunk]:
        """
        Stream structured response chunks.
        
        Supports function calling and granular control for voice applications.
        
        Args:
            request: Generation parameters
            
        Yields:
            LLMResponseChunk with text or function_call
            
        Raises:
            LLMException: If streaming fails
        """
        yield LLMResponseChunk(text="")  # Placeholder for type hint

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        Get list of available models from this provider.
        
        Useful for UI model selection and validation.
        
        Returns:
            List of model IDs
            
        Raises:
            LLMException: If model list retrieval fails
        """
        pass

    @abstractmethod
    def is_model_safe_for_voice(self, model: str) -> bool:
        """
        Check if a model is suitable for voice applications.
        
        Some models have high latency or are optimized for other use cases.
        
        Args:
            model: Model ID to check
            
        Returns:
            True if model is safe/recommended for voice
        """
        pass


class LLMException(Exception):
    """
    Base exception for LLM-related errors.
    
    Provides structured error information including retry hints.
    
    Attributes:
        message: Human-readable error message
        retryable: Whether the error might succeed if retried
        provider: Provider that generated the error (e.g., "groq", "openai")
        original_error: Original exception from the SDK (if any)
    """

    def __init__(
        self,
        message: str,
        retryable: bool = False,
        provider: str = "unknown",
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.retryable = retryable
        self.provider = provider
        self.original_error = original_error

    def __str__(self):
        retry_hint = "(retryable)" if self.retryable else "(not retryable)"
        return f"[{self.provider}] {super().__str__()} {retry_hint}"
