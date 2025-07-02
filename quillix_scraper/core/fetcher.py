"""HTTP content fetcher with caching support."""

import requests
import time
import logging
from typing import Optional, Dict

from .cache import CacheManager
from ..config import config

logger = logging.getLogger(__name__)


class ContentFetcher:
    """Simple HTTP content fetcher with Redis caching."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache = cache_manager or CacheManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent
        })
    
    def fetch(self, url: str, use_cache: bool = True, **kwargs) -> Optional[str]:
        """Fetch content from URL with optional caching."""
        
        # Check cache first if enabled
        if use_cache:
            cached_content = self.cache.get(url, kwargs)
            if cached_content:
                logger.info(f"Using cached content for: {url}")
                return cached_content
        
        # Fetch fresh content
        logger.info(f"Fetching fresh content from: {url}")
        
        try:
            response = self.session.get(
                url, 
                timeout=config.request_timeout,
                **kwargs
            )
            response.raise_for_status()
            
            content = response.text
            
            # Cache the content if caching is enabled
            if use_cache:
                self.cache.set(url, content, kwargs)
            
            return content
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def close(self):
        """Close the requests session."""
        self.session.close()