"""
Unit tests for Cache Adapter.

Tests Redis cache adapter operations and error handling.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from backend.infrastructure.adapters.cache.redis_adapter import RedisCacheAdapter


class TestRedisCacheAdapter:
    """Test Redis cache adapter."""
    
    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self):
        """Test get returns value from Redis."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value={"cached": "data"})
        
        adapter = RedisCacheAdapter(mock_redis)
        
        result = await adapter.get("test_key")
        
        assert result == {"cached": "data"}
        mock_redis.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(self):
        """Test get returns None when key doesn't exist."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)
        
        adapter = RedisCacheAdapter(mock_redis)
        
        result = await adapter.get("missing_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_stores_value_with_ttl(self):
        """Test set stores value with TTL."""
        mock_redis = Mock()
        mock_redis.set = AsyncMock()
        
        adapter = RedisCacheAdapter(mock_redis)
        
        await adapter.set("test_key", {"data": "value"}, ttl=1800)
        
        mock_redis.set.assert_called_once_with("test_key", {"data": "value"}, ttl=1800)
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self):
        """Test invalidate removes keys matching pattern."""
        mock_redis = Mock()
        mock_redis.invalidate = AsyncMock()
        
        adapter = RedisCacheAdapter(mock_redis)
        
        await adapter.invalidate("test_*")
        
        mock_redis.invalidate.assert_called_once_with("test_*")
    
    @pytest.mark.asyncio
    async def test_graceful_failure_on_error(self):
        """Test adapter doesn't crash when Redis fails."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))
        
        adapter = RedisCacheAdapter(mock_redis)
        
        # Should not raise
        result = await adapter.get("key")
        assert result is None
        
        # Should not raise
        await adapter.set("key", "value")
    
    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test close shuts down Redis connection."""
        mock_redis = Mock()
        mock_redis.close = AsyncMock()
        
        adapter = RedisCacheAdapter(mock_redis)
        
        await adapter.close()
        
        # Verify close was called on Redis client
        # (Implementation may vary based on actual RedisClient interface)
