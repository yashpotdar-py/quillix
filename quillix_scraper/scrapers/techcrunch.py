"""TechCrunch scraper implementation."""

from typing import List, Optional
from bs4 import BeautifulSoup
import logging
import re

from ..core.scraper import BaseScraper
from ..models.trend import TrendData, TrendCollection

logger = logging.getLogger(__name__)


class TechCrunchScraper(BaseScraper):
    """Improved scraper for TechCrunch articles."""
    
    def __init__(self, cache_manager=None):
        super().__init__(cache_manager)
        self.source_name = "techcrunch"
    
    def parse_content(self, html_content: str, url: str) -> TrendCollection:
        """Parse TechCrunch HTML content and extract trends."""
        soup = BeautifulSoup(html_content, 'html.parser')
        collection = TrendCollection(source=self.source_name)
        
        # Try multiple approaches to find articles
        articles = []
        
        # Approach 1: Find links that look like articles
        article_links = self._find_article_links(soup)
        if article_links:
            logger.info(f"Found {len(article_links)} article links")
            for link in article_links[:15]:
                trend_data = self._create_trend_from_link(link, url)
                if trend_data:
                    collection.add_trend(trend_data)
        
        # Approach 2: Look for structured article containers
        if collection.total_count == 0:
            articles = self._find_articles(soup)
            logger.info(f"Found {len(articles)} article containers")
            
            for article in articles[:15]:
                try:
                    trend_data = self._extract_trend_from_article(article, url)
                    if trend_data:
                        collection.add_trend(trend_data)
                except Exception as e:
                    logger.debug(f"Failed to parse article: {e}")
                    continue
        
        logger.info(f"Successfully parsed {collection.total_count} trends")
        return collection
    
    def _find_article_links(self, soup: BeautifulSoup) -> List:
        """Find links that appear to be articles."""
        # Look for links with article-like URLs and meaningful text
        all_links = soup.find_all('a', href=True)
        article_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if this looks like an article link
            if self._is_article_link(href, text):
                article_links.append(link)
        
        # Remove duplicates based on href
        seen_hrefs = set()
        unique_links = []
        for link in article_links:
            href = link.get('href')
            if href not in seen_hrefs:
                seen_hrefs.add(href)
                unique_links.append(link)
        
        return unique_links
    
    def _is_article_link(self, href: str, text: str) -> bool:
        """Check if a link appears to be an article."""
        if not href or not text:
            return False
        
        # Check URL pattern (TechCrunch article URLs usually contain year)
        if not (('/2024/' in href or '/2025/' in href) or href.startswith('/2024/') or href.startswith('/2025/')):
            return False
        
        # Check text length and content
        if len(text) < 15 or len(text) > 200:
            return False
        
        # Skip if text looks like navigation or boilerplate
        skip_texts = ['read more', 'continue reading', 'techcrunch', 'subscribe', 'newsletter', 'follow us']
        if any(skip_text in text.lower() for skip_text in skip_texts):
            return False
        
        return True
    
    def _create_trend_from_link(self, link, base_url: str) -> Optional[TrendData]:
        """Create trend data from an article link."""
        title = link.get_text(strip=True)
        href = link.get('href', '')
        
        # Normalize URL
        if href.startswith('/'):
            article_url = f"https://techcrunch.com{href}"
        elif href.startswith('http'):
            article_url = href
        else:
            return None
        
        # Try to find summary from nearby elements
        summary = self._find_summary_near_link(link)
        
        # Extract tags from title
        tags = self._extract_basic_tags(title, summary)
        
        return TrendData(
            title=title,
            url=article_url,
            source=self.source_name,
            summary=summary,
            tags=tags
        )
    
    def _find_summary_near_link(self, link) -> str:
        """Try to find summary text near the article link."""
        # Look in parent containers for summary text
        parent = link.parent
        for _ in range(3):  # Go up 3 levels max
            if parent is None:
                break
            
            # Look for paragraph or summary elements
            summary_elem = parent.find(['p', 'div'], class_=lambda x: x and ('excerpt' in str(x).lower() or 'summary' in str(x).lower()))
            if summary_elem:
                summary = summary_elem.get_text(strip=True)
                if len(summary) > 20:
                    return summary[:300]
            
            parent = parent.parent
        
        return ""
    
    def _find_articles(self, soup: BeautifulSoup) -> List:
        """Find article elements in the HTML using various selectors."""
        selectors = [
            'article',
            '[data-module="ArticleLink"]',
            '[data-module="ClickGoal"]',
            '.post',
            '.story',
            '.card',
            'div[class*="post"]',
            'div[class*="story"]',
            'div[class*="article"]',
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                logger.debug(f"Found {len(articles)} articles using selector: {selector}")
                return articles
        
        return []
    
    def _extract_trend_from_article(self, article, base_url: str) -> Optional[TrendData]:
        """Extract trend data from a single article element."""
        
        # Extract title and URL
        title_element = self._find_title_element(article)
        if not title_element:
            return None
        
        title = title_element.get_text(strip=True)
        if not title or len(title) < 10:
            return None
        
        # Get article URL
        article_url = self._extract_url(title_element, base_url)
        if not article_url:
            return None
        
        # Extract summary
        summary = self._extract_summary(article)
        
        # Extract tags
        tags = self._extract_basic_tags(title, summary)
        
        return TrendData(
            title=title,
            url=article_url,
            source=self.source_name,
            summary=summary,
            tags=tags
        )
    
    def _find_title_element(self, article):
        """Find the title element in an article."""
        title_selectors = [
            'h1 a', 'h2 a', 'h3 a', 'h4 a',
            'a[data-module="ClickGoal"]',
            '.title a', '.headline a',
            'a[href*="/2024/"]', 'a[href*="/2025/"]'
        ]
        
        for selector in title_selectors:
            element = article.select_one(selector)
            if element and element.get_text(strip=True):
                return element
        
        return None
    
    def _extract_url(self, title_element, base_url: str) -> Optional[str]:
        """Extract and normalize article URL."""
        href = title_element.get('href', '')
        if not href:
            return None
        
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"https://techcrunch.com{href}"
        else:
            return None
    
    def _extract_summary(self, article) -> str:
        """Extract article summary/excerpt."""
        summary_selectors = [
            '.excerpt', '.summary', '.description',
            'p[class*="excerpt"]', 'div[class*="excerpt"]',
            'p', 'div'
        ]
        
        for selector in summary_selectors:
            elements = article.select(selector)
            for element in elements:
                summary = element.get_text(strip=True)
                if 20 < len(summary) < 500:  # Reasonable summary length
                    return summary[:300]
        
        return ""
    
    def _extract_basic_tags(self, title: str, summary: str) -> List[str]:
        """Extract basic tags from title and summary."""
        text = f"{title} {summary}".lower()
        
        # Enhanced keyword matching
        tech_keywords = {
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'llm'],
            'startup': ['startup', 'founded', 'launches', 'new company'],
            'funding': ['funding', 'raises', 'investment', 'series a', 'series b', 'round'],
            'crypto': ['crypto', 'bitcoin', 'blockchain', 'web3', 'nft'],
            'mobile': ['app', 'mobile', 'ios', 'android', 'iphone'],
            'saas': ['saas', 'software', 'platform', 'service'],
            'fintech': ['fintech', 'payments', 'banking', 'finance'],
            'security': ['security', 'breach', 'hack', 'cybersecurity'],
            'acquisition': ['acquired', 'acquisition', 'buys', 'merger'],
            'product': ['product', 'feature', 'update', 'release']
        }
        
        found_tags = []
        for tag, keywords in tech_keywords.items():
            if any(keyword in text for keyword in keywords):
                found_tags.append(tag)
        
        return found_tags[:5]
