"""
Cache Factory - Creates and configures cache instances.

Hexagonal Architecture: Infrastructure factory for cache dependency injection.
"""
import logging

from backend.domain.ports.cache_port import CachePort
from backend.infrastructure.adapters.cache import RedisCacheAdapter
from backend.infrastructure.cache import get_redis_client
from backend.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


async def create_cache(redis_url: str | None = None) -> CachePort:
    """
    Create and initialize cache instance.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        CachePort implementation (RedisCacheAdapter)
        
    Example:
        >>> cache = await create_cache()
        >>> await cache.set("key", "value", ttl=3600)
        >>> result = await cache.get("key")
    """
    # Get Redis client
    actual_url = redis_url or settings.REDIS_URL
    redis_client = get_redis_client(actual_url)
    
    # Establish connection
    await redis_client.connect()
    
    # Create adapter
    cache = RedisCacheAdapter(redis_client)
    
    logger.info("✅ Cache created and initialized")
    return cache
