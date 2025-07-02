"""
Quillix Scraper - A modular web scraping package for tech trends.
"""

from .models.trend import TrendData, TrendCollection
from .core.cache import CacheManager
from .core.fetcher import ContentFetcher
from .config import config

__version__ = "0.1.0"
__all__ = [
    "TrendData", 
    "TrendCollection", 
    "CacheManager",
    "ContentFetcher",
    "config"
]