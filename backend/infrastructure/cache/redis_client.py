"""
Redis Client - Async Redis connection wrapper.

Hexagonal Architecture: Infrastructure implementation for cache operations.
Wraps redis-py async client with JSON serialization and connection management.
"""
import json
import logging
from typing import Any

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client with JSON serialization.
    
    Features:
    - Lazy connection initialization
    - JSON serialization/deserialization
    - TTL-based expiration
    - Pattern-based key invalidation
    - Graceful error handling
    
    Usage:
        >>> client = RedisClient(url="redis://localhost:6379/0")
        >>> await client.connect()
        >>> await client.set("key", {"data": "value"}, ttl=3600)
        >>> result = await client.get("key")
        >>> await client.close()
    """
    
    def __init__(self, url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis client.
        
        Args:
            url: Redis connection URL (default: localhost:6379/0)
        """
        if not REDIS_AVAILABLE:
            logger.warning(
                "⚠️ redis-py not installed. Install with: pip install redis"
            )
        
        self.url = url
        self._client: redis.Redis | None = None
        self._connected = False
    
    async def connect(self):
        """Establish Redis connection."""
        if not REDIS_AVAILABLE:
            logger.error("❌ Cannot connect: redis-py not installed")
            return
        
        if self._connected:
            return
        
        try:
            self._client = await redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"✅ Connected to Redis: {self.url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self._client = None
    
    async def get(self, key: str) -> Any | None:
        """
        Retrieve and deserialize value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized value or None if not exists
        """
        if not self._connected or not self._client:
            return None
        
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            
            # Deserialize JSON
            return json.loads(value)
        except json.JSONDecodeError:
            # Return raw string if not JSON
            return value
        except Exception as e:
            logger.warning(f"⚠️ Redis GET failed for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Serialize and store value in Redis with TTL.
        
        Args:
            key: Cache key
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds
        """
        if not self._connected or not self._client:
            return
        
        try:
            # Serialize to JSON
            serialized = json.dumps(value)
            
            # Store with TTL
            await self._client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"⚠️ Redis SET failed for key '{key}': {e}")
    
    async def invalidate(self, pattern: str):
        """
        Delete keys matching glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., "voices_*", "llm_cache:*")
        """
        if not self._connected or not self._client:
            return
        
        try:
            # Scan for matching keys
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete in batch
            if keys:
                await self._client.delete(*keys)
                logger.info(f"🗑️ Invalidated {len(keys)} keys matching '{pattern}'")
        except Exception as e:
            logger.warning(f"⚠️ Redis INVALIDATE failed for pattern '{pattern}': {e}")
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            try:
                await self._client.close()
                self._connected = False
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing Redis: {e}")


# Singleton instance for application-wide use
_redis_client: RedisClient | None = None


def get_redis_client(url: str = "redis://localhost:6379/0") -> RedisClient:
    """
    Get singleton Redis client instance.
    
    Args:
        url: Redis URL (only used on first call)
        
    Returns:
        RedisClient instance
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient(url)
    
    return _redis_client
