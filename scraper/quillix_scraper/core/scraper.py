"""Core scraper interface and base implementation."""

import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import logging

from ..models.trend import TrendCollection
from ..core.cache import CacheManager
from ..core.fetcher import ContentFetcher
from ..config import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or CacheManager()
        self.fetcher = ContentFetcher(self.cache_manager)
        self.source_name = self.__class__.__name__.replace(
            "Scraper", "").lower()

    @abstractmethod
    def parse_content(self, html_content: str, url: str) -> TrendCollection:
        """Parse HTML content and extract trends."""
        pass

    def scrape_trends(self, url: str, use_cache: bool = True, **kwargs) -> TrendCollection:
        """Scrape trends from the given URL."""
        logger.info(f"Starting scrape from {url}")
        start_time = time.time()

        try:
            # Fetch content
            html_content = self.fetcher.fetch(
                url, use_cache=use_cache, **kwargs)
            if not html_content:
                logger.error(f"Failed to fetch content from {url}")
                return TrendCollection(source=self.source_name)

            # Parse content
            trends = self.parse_content(html_content, url)
            trends.source = self.source_name

            duration = time.time() - start_time
            logger.info(
                f"Scrape completed: {trends.total_count} trends in {duration:.2f}s")

            return trends

        except Exception as e:
            logger.error(f"Scrape failed for {url}: {e}")
            return TrendCollection(source=self.source_name)

    def close(self):
        """Clean up resources."""
        self.fetcher.close()


class ScraperManager:
    """Manages multiple scraper implementations."""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or CacheManager()
        self._scrapers: Dict[str, BaseScraper] = {}

    def register_scraper(self, name: str, scraper: BaseScraper) -> None:
        """Register a scraper implementation."""
        self._scrapers[name] = scraper
        logger.info(f"Registered scraper: {name}")

    def get_scraper(self, name: str) -> Optional[BaseScraper]:
        """Get a registered scraper by name."""
        return self._scrapers.get(name)

    def list_scrapers(self) -> List[str]:
        """List all registered scrapers."""
        return list(self._scrapers.keys())

    def scrape(self, scraper_name: str, url: Optional[str] = None, **kwargs) -> TrendCollection:
        """Scrape trends using the specified scraper."""
        scraper = self.get_scraper(scraper_name)
        if not scraper:
            raise ValueError(f"Scraper '{scraper_name}' not found")

        target_url = url or config.default_scrape_url
        return scraper.scrape_trends(target_url, **kwargs)

    def scrape_all(self, url: Optional[str] = None, **kwargs) -> Dict[str, TrendCollection]:
        """Scrape trends using all registered scrapers."""
        target_url = url or config.default_scrape_url
        results = {}

        for name, scraper in self._scrapers.items():
            try:
                logger.info(f"Running scraper: {name}")
                results[name] = scraper.scrape_trends(target_url, **kwargs)
            except Exception as e:
                logger.error(f"Scraper {name} failed: {e}")
                results[name] = TrendCollection(source=name)

        return results
