"""Redis-based caching mechanism for the scraper."""

import json
import hashlib
from typing import Optional, Any, Dict
import redis
import logging

from ..config import config

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager for scraping results."""
    
    def __init__(self, redis_url: Optional[str] = None, ttl: Optional[int] = None):
        self.redis_url = redis_url or config.redis_url
        self.ttl = ttl or config.cache_ttl
        self._client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client connection."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    def _generate_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key for the given URL and parameters."""
        cache_data = {"url": url}
        if params:
            cache_data.update(params)
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"quillix:scraper:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def get(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """Get cached content."""
        try:
            cache_key = self._generate_cache_key(url, params)
            cached_data = self.client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for: {url}")
                return cached_data
            
            logger.debug(f"Cache miss for: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    def set(self, url: str, content: str, params: Optional[Dict] = None, ttl: Optional[int] = None) -> bool:
        """Set cached content."""
        try:
            cache_key = self._generate_cache_key(url, params)
            cache_ttl = ttl or self.ttl
            
            result = self.client.setex(cache_key, cache_ttl, content)
            logger.debug(f"Cached content for: {url} (TTL: {cache_ttl}s)")
            return result
            
        except Exception as e:
            logger.error(f"Error setting cached data: {e}")
            return False
    
    def clear_all(self, pattern: str = "quillix:scraper:*") -> int:
        """Clear all cached data matching the pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def test_connection(self) -> bool:
        """Test Redis connection."""
        try:
            self.client.ping()
            logger.info("Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
