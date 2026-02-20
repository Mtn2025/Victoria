"""
Port (Interface) for distributed cache.

Hexagonal Architecture: Domain defines contract, adapters implement.
Abstracts Redis or other cache systems for the domain.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class CachePort(ABC):
    """
    Port for distributed cache system.
    
    Implementations: RedisCacheAdapter, MemoryCacheAdapter (for tests)
    
    Use cases:
    - Cache LLM responses (reduce latency + cost)
    - Cache TTS synthesized audio (avoid re-synthesis)
    - Cache session state (distributed sessions)
    - Cache voice metadata (reduce DB queries)
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized value or None if not exists
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        pass

    @abstractmethod
    async def invalidate(self, pattern: str) -> None:
        """
        Invalidate keys matching glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., "voices_*", "llm_cache:*")
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close cache connection."""
        pass
