"""
Cache Integration Wrapper for Use Cases.

Provides caching functionality for LLM and TTS use cases.
"""
import hashlib
import logging
from typing import Any, Optional

from backend.domain.ports.cache_port import CachePort

logger = logging.getLogger(__name__)


class CachedLLMWrapper:
    """
    Wrapper for LLM operations with caching.
    
    Caches LLM responses based on prompt hash to reduce API calls and improve latency.
    """
    
    def __init__(self, llm_port: Any, cache: Optional[CachePort] = None):
        """
        Initialize cached LLM wrapper.
        
        Args:
            llm_port: LLMPort implementation
            cache: Optional cache implementation (if None, no caching)
        """
        self.llm_port = llm_port
        self.cache = cache
        self._cache_ttl = 3600  # 1 hour default
    
    def _generate_cache_key(self, messages: list, model: str, temperature: float) -> str:
        """
        Generate cache key from request parameters.
        
        Args:
            messages: Conversation messages
            model: LLM model name
            temperature: Generation temperature
            
        Returns:
            Cache key string
        """
        # Create deterministic hash from parameters
        content = f"{model}:{temperature}:{str(messages)}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"llm_cache:{hash_digest}"
    
    async def generate_stream(self, request: Any):
        """
        Generate LLM response with caching.
        
        Note: Streaming responses are NOT cached (would require buffering).
        Only use cache for non-streaming or implement buffer strategy.
        """
        # For streaming, bypass cache
        async for chunk in self.llm_port.generate_stream(request):
            yield chunk
    
    async def generate(self, request: Any) -> str:
        """
        Generate LLM response with caching (non-streaming).
        
        Args:
            request: LLMRequest object
            
        Returns:
            Generated text response
        """
        if not self.cache:
            # No cache, direct generation
            return await self.llm_port.generate(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            request.messages,
            request.model,
            request.temperature
        )
        
        # Check cache
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.info(f"✅ Cache HIT: {cache_key}")
            return cached_response
        
        # Cache miss - generate
        logger.info(f"❌ Cache MISS: {cache_key}")
        response = await self.llm_port.generate(request)
        
        # Store in cache
        await self.cache.set(cache_key, response, ttl=self._cache_ttl)
        
        return response


class CachedTTSWrapper:
    """
    Wrapper for TTS operations with caching.
    
    Caches synthesized audio based on text+voice hash.
    """
    
    def __init__(self, tts_port: Any, cache: Optional[CachePort] = None):
        """
        Initialize cached TTS wrapper.
        
        Args:
            tts_port: TTSPort implementation
            cache: Optional cache implementation
        """
        self.tts_port = tts_port
        self.cache = cache
        self._cache_ttl = 86400  # 24 hours (audio rarely changes)
    
    def _generate_cache_key(self, text: str, voice_config: Any) -> str:
        """
        Generate cache key from TTS parameters.
        
        Args:
            text: Text to synthesize
            voice_config: Voice configuration
            
        Returns:
            Cache key string
        """
        voice_str = f"{voice_config.voice_name}:{voice_config.style}:{voice_config.speed}"
        content = f"{voice_str}:{text}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"tts_cache:{hash_digest}"
    
    async def synthesize(self, text: str, voice_config: Any) -> bytes:
        """
        Synthesize speech with caching.
        
        Args:
            text: Text to convert to speech
            voice_config: Voice configuration object
            
        Returns:
            Audio bytes
        """
        if not self.cache:
            # No cache, direct synthesis
            return await self.tts_port.synthesize(text, voice_config)
        
        # Generate cache key
        cache_key = self._generate_cache_key(text, voice_config)
        
        # Check cache
        cached_audio = await self.cache.get(cache_key)
        if cached_audio:
            logger.info(f"✅ TTS Cache HIT: {cache_key}")
            # Cache stores base64 or bytes, convert as needed
            return cached_audio
        
        # Cache miss - synthesize
        logger.info(f"❌ TTS Cache MISS: {cache_key}")
        audio = await self.tts_port.synthesize(text, voice_config)
        
        # Store in cache (audio as bytes or base64 string)
        await self.cache.set(cache_key, audio, ttl=self._cache_ttl)
        
        return audio


def create_cached_llm(llm_port: Any, cache: Optional[CachePort] = None) -> CachedLLMWrapper:
    """
    Create cached LLM wrapper.
    
    Args:
        llm_port: LLM port implementation
        cache: Optional cache port
        
    Returns:
        Cached LLM wrapper instance
    """
    wrapper = CachedLLMWrapper(llm_port, cache)
    if cache:
        logger.info("🚀 LLM caching enabled")
    return wrapper


def create_cached_tts(tts_port: Any, cache: Optional[CachePort] = None) -> CachedTTSWrapper:
    """
    Create cached TTS wrapper.
    
    Args:
        tts_port: TTS port implementation
        cache: Optional cache port
        
    Returns:
        Cached TTS wrapper instance
    """
    wrapper = CachedTTSWrapper(tts_port, cache)
    if cache:
        logger.info("🚀 TTS caching enabled")
    return wrapper
