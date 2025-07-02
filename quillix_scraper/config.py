"""Configuration management for quillix-scraper."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Simple configuration class for the scraper."""
    
    def __init__(self):
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
        
        # Request configuration
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.user_agent = os.getenv("USER_AGENT", "quillix-scraper/0.1.0")
        
        # Default URLs
        self.default_scrape_url = os.getenv("DEFAULT_SCRAPE_URL", "https://techcrunch.com/")


# Global config instance
config = Config()