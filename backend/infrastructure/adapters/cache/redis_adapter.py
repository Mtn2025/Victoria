"""
Redis Cache Adapter - Implementation of CachePort.

Hexagonal Architecture: Infrastructure adapter implements Domain port.
Provides caching for performance optimization (LLM responses, TTS audio, etc).
"""
import logging
from typing import Any

from backend.domain.ports.cache_port import CachePort

logger = logging.getLogger(__name__)


class RedisCacheAdapter(CachePort):
    """
    Redis cache adapter implementing CachePort.
    
    Features:
    - Lazy connection initialization
    - JSON serialization/deserialization
    - Graceful degradation (cache failures don't break app)
    - TTL-based expiration
    - Pattern-based invalidation
    
    Note: This is a wrapper adapter. Actual Redis client implementation
    should be injected or imported from backend.infrastructure.cache.redis_client
    
    Example usage:
        >>> cache = RedisCacheAdapter()
        >>> await cache.set("llm_cache:prompt_hash", response_data, ttl=3600)
        >>> cached = await cache.get("llm_cache:prompt_hash")
        >>> await cache.invalidate("llm_cache:*")
    """

    def __init__(self, redis_client=None):
        """
        Initialize Redis cache adapter.
        
        Args:
            redis_client: Optional RedisClient instance.
                         If None, will use default singleton client.
        """
        from backend.infrastructure.cache import get_redis_client
        
        # Use provided client or get singleton
        self._redis = redis_client or get_redis_client()
        
        # Initialize connection (lazy - will connect on first use)
        if hasattr(self._redis, '_connected') and not self._redis._connected:
            # Connection will be established on first operation
            logger.info("[RedisCacheAdapter] Initialized with lazy Redis connection")

    async def get(self, key: str) -> Any | None:
        """
        Retrieve value from cache.
        
        Returns None on cache miss or error (graceful degradation).
        """
        if not self._redis:
            return None
            
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.warning(f"[Redis Cache] Get failed for key '{key}': {e}")
            return None  # Graceful fallback - cache miss doesn't break app

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Store value in cache with TTL.
        
        Fails silently on error (graceful degradation).
        """
        if not self._redis:
            return
            
        try:
            await self._redis.set(key, value, ttl=ttl)
        except Exception as e:
            logger.warning(f"[Redis Cache] Set failed for key '{key}': {e}")
            # Don't raise - cache failures shouldn't break app

    async def invalidate(self, pattern: str):
        """
        Invalidate keys matching glob pattern.
        
        Fails silently on error (graceful degradation).
        """
        if not self._redis:
            return
            
        try:
            await self._redis.invalidate(pattern)
        except Exception as e:
            logger.warning(f"[Redis Cache] Invalidate failed for pattern '{pattern}': {e}")

    async def close(self):
        """
        Close Redis connection.
        
        Fails silently on error (graceful degradation).
        """
        if not self._redis:
            return
            
        try:
            await self._redis.close()
        except Exception as e:
            logger.warning(f"[Redis Cache] Close failed: {e}")
