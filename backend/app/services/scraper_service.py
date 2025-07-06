"""Scraper service integration with quillix-scraper package"""

from ..core.service import BaseService, ServiceResponse
import sys
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add the scraper directory to the path so we can import quillix_scraper
# scraper_path = Path(__file__).parent.parent.parent / "scraper"
# sys.path.insert(0, str(scraper_path))

try:
    from quillix_scraper import ScraperManager as QuillixScraperManager
    from quillix_scraper import TechCrunchScraper
    SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import quillix_scraper: {e}")
    SCRAPER_AVAILABLE = False


class ScraperService(BaseService):
    """Service for scraping trends using quillix-scraper"""

    def __init__(self):
        super().__init__("scraper")
        self.scraper_manager: Optional[QuillixScraperManager] = None
        self.available = SCRAPER_AVAILABLE

    async def initialize(self) -> bool:
        """Initialize the scraper service"""
        if not self.available:
            self.logger.error("quillix-scraper package not available")
            return False

        try:
            self.scraper_manager = QuillixScraperManager()
            # Register available scrapers
            self.scraper_manager.register_scraper(
                'techcrunch', TechCrunchScraper())

            self.logger.info("Scraper service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize scraper service: {e}")
            return False

    async def health_check(self) -> ServiceResponse:
        """Check scraper scraper service health"""
        if not self.available or not self.scraper_manager:
            return ServiceResponse(
                success=False,
                message="Scraper service not available"
            )

        return ServiceResponse(
            success=True,
            message="Scraper service is healthy",
            data={
                "available_scrapers": self.scraper_manager.list_scrapers()
            }
        )

    async def cleanup(self) -> None:
        """Cleanup scraper service resources"""
        pass

    async def scrape_trends(self, scraper_name: str = "techcrunch", url: Optional[str] = None) -> ServiceResponse:
        """Scrape trends using the specifide scraper"""
        if not self.scraper_manager:
            return ServiceResponse(
                success=False,
                message="Scraper service not initialized"
            )

        try:
            trends = self.scraper_manager.scrape(scraper_name, url)

            return ServiceResponse(
                success=True,
                message=f"Successfully scraped {trends.total_count} trends",
                data=trends.to_dict()
            )
        except Exception as e:
            self.logger.error(f"Error scraping trends {e}")
            return ServiceResponse(
                success=False,
                message="Failed to scrape trends",
                error=str(e)
            )

    def list_scrapers(self) -> List[str]:
        """List available scrapers"""
        if not self.scraper_manager:
            return []
        return self.scraper_manager.list_scrapers()
