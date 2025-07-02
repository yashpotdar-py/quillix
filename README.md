# Quillix Scraper

A modular and extensible Python package for scraping tech trends and news from various sources.

## Features

- 🕷️ **Modular Architecture**: Easy to extend with new scrapers
- ⚡ **Redis Caching**: Intelligent caching to avoid redundant requests
- 🔧 **CLI Interface**: Simple command-line interface
- 📊 **Structured Data**: Clean, serializable trend data models
- 🐍 **Modern Python**: Built with Python 3.8+ and modern tooling

## Quick Start

### Installation

```bash
# Install the package
pip install quillix-scraper

# Or install with development dependencies
pip install quillix-scraper[dev]

# Or install with async support
pip install quillix-scraper[async]
```

### Basic Usage

```python
from quillix_scraper import ScraperManager, TechCrunchScraper

# Initialize scraper
manager = ScraperManager()
manager.register_scraper('techcrunch', TechCrunchScraper())

# Scrape trends
trends = manager.scrape('techcrunch')
print(f"Found {trends.total_count} trends")

for trend in trends.trends[:5]:
    print(f"- {trend.title}")
    print(f"  Tags: {', '.join(trend.tags)}")
```

### CLI Usage

```bash
# List available scrapers
quillix-scraper list-scrapers

# Scrape with default settings
quillix-scraper scrape

# Scrape with custom format
quillix-scraper scrape --format json --output trends.json

# Clear cache
quillix-scraper cache clear

# View cache stats
quillix-scraper cache stats
```

## Configuration

Set environment variables or use a `.env.local` file:

```bash
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
REQUEST_TIMEOUT=30
USER_AGENT=quillix-scraper/0.1.0
```

## Development

```bash
# Clone the repository
git clone https://github.com/quillix/quillix-scraper.git
cd quillix-scraper

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black quillix_scraper/
isort quillix_scraper/

# Type checking
mypy quillix_scraper/
```

## Architecture

The package is built with modularity in mind:

- **Core Components**: Base scraper interface, cache manager, content fetcher
- **Models**: Structured data models for trends and collections
- **Scrapers**: Source-specific implementations (TechCrunch, etc.)
- **CLI**: Command-line interface for easy usage

## Adding New Scrapers

```python
from quillix_scraper import BaseScraper, TrendCollection

class CustomScraper(BaseScraper):
    def parse_content(self, html_content: str, url: str) -> TrendCollection:
        # Implement your parsing logic
        collection = TrendCollection(source="custom")
        # ... parse and add trends
        return collection
```

## License

MIT License - see LICENSE file for details.