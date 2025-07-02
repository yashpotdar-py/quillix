"""Command-line interface for quillix-scraper."""

import json
import logging
from typing import Optional
import click

from .core.scraper import ScraperManager
from .scrapers.techcrunch import TechCrunchScraper
from .config import config

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Less verbose by default
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose: bool):
    """Quillix Scraper CLI - A modular web scraper for tech trends."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('quillix_scraper').setLevel(logging.DEBUG)


@cli.command()
@click.option('--url', '-u', help='URL to scrape (defaults to TechCrunch)')
@click.option('--scraper', '-s', default='techcrunch', help='Scraper to use')
@click.option('--output', '-o', type=click.Path(), help='Output file for results (JSON)')
@click.option('--format', 'output_format', default='summary', 
              type=click.Choice(['json', 'summary', 'titles']),
              help='Output format')
@click.option('--no-cache', is_flag=True, help='Skip cache and fetch fresh content')
def scrape(url: Optional[str], scraper: str, output: Optional[str], 
           output_format: str, no_cache: bool):
    """Scrape trends using the specified scraper."""
    
    # Initialize scraper manager
    manager = ScraperManager()
    
    # Register available scrapers
    manager.register_scraper('techcrunch', TechCrunchScraper())
    
    # Add more scrapers here as we build them
    # manager.register_scraper('hackernews', HackerNewsScraper())
    
    try:
        result = manager.scrape(scraper, url, use_cache=not no_cache)
        
        if output_format == 'json':
            output_data = result.to_dict()
            if output:
                with open(output, 'w') as f:
                    json.dump(output_data, f, indent=2, default=str)
                click.echo(f"✅ Results saved to {output}")
            else:
                click.echo(json.dumps(output_data, indent=2, default=str))
        
        elif output_format == 'titles':
            click.echo(f"\n📋 {result.total_count} Trends from {result.source}:")
            click.echo("=" * 60)
            for i, trend in enumerate(result.trends, 1):
                click.echo(f"{i:2d}. {trend.title}")
        
        else:  # summary format
            click.echo(f"\n📊 Scrape Results")
            click.echo("=" * 50)
            click.echo(f"Source: {result.source}")
            click.echo(f"Total trends: {result.total_count}")
            click.echo(f"Scraped at: {result.scraped_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if result.trends:
                click.echo(f"\n🔥 Top Trends:")
                for i, trend in enumerate(result.trends[:10], 1):
                    click.echo(f"\n{i:2d}. {trend.title}")
                    click.echo(f"    🔗 {trend.url}")
                    if trend.tags:
                        click.echo(f"    🏷️  {', '.join(trend.tags)}")
                    if trend.summary and len(trend.summary) > 20:
                        summary = trend.summary[:150] + "..." if len(trend.summary) > 150 else trend.summary
                        click.echo(f"    📝 {summary}")
            else:
                click.echo("❌ No trends found")
        
        # Save to file if requested
        if output and output_format != 'json':
            with open(output, 'w') as f:
                if output_format == 'titles':
                    for trend in result.trends:
                        f.write(f"{trend.title}\n")
                else:
                    f.write(f"Scrape Results - {result.source}\n")
                    f.write(f"Total: {result.total_count} trends\n")
                    f.write(f"Date: {result.scraped_at}\n\n")
                    for i, trend in enumerate(result.trends, 1):
                        f.write(f"{i}. {trend.title}\n")
                        f.write(f"   URL: {trend.url}\n")
                        if trend.tags:
                            f.write(f"   Tags: {', '.join(trend.tags)}\n")
                        f.write("\n")
            click.echo(f"📄 Results also saved to {output}")
            
    except Exception as e:
        click.echo(f"❌ Scraping failed: {e}", err=True)
        if click.get_current_context().params.get('verbose'):
            import traceback
            traceback.print_exc()
        raise click.Abort()


@cli.command()
def list_scrapers():
    """List all available scrapers."""
    manager = ScraperManager()
    manager.register_scraper('techcrunch', TechCrunchScraper())
    
    scrapers = manager.list_scrapers()
    
    click.echo("📋 Available Scrapers:")
    click.echo("=" * 30)
    for scraper_name in scrapers:
        click.echo(f"  • {scraper_name}")
    
    click.echo(f"\nUsage: quillix-scraper scrape --scraper <name>")


@cli.group()
def cache():
    """Cache management commands."""
    pass


@cache.command()
def clear():
    """Clear all cached data."""
    from .core.cache import CacheManager
    
    cache_manager = CacheManager()
    try:
        cleared = cache_manager.clear_all()
        click.echo(f"✅ Cleared {cleared} cache entries")
    except Exception as e:
        click.echo(f"❌ Failed to clear cache: {e}", err=True)


@cache.command()
def stats():
    """Show cache statistics."""
    from .core.cache import CacheManager
    
    cache_manager = CacheManager()
    try:
        if cache_manager.test_connection():
            info = cache_manager.client.info()
            total_keys = cache_manager.client.dbsize()
            quillix_keys = len(cache_manager.client.keys("quillix:scraper:*"))
            
            click.echo("📊 Redis Cache Stats:")
            click.echo("=" * 30)
            click.echo(f"Status: ✅ Connected")
            click.echo(f"Total keys in DB: {total_keys}")
            click.echo(f"Quillix cache keys: {quillix_keys}")
            click.echo(f"Used memory: {info.get('used_memory_human', 'N/A')}")
            click.echo(f"Connected clients: {info.get('connected_clients', 'N/A')}")
        else:
            click.echo("❌ Redis connection failed")
    except Exception as e:
        click.echo(f"❌ Failed to get cache stats: {e}", err=True)


if __name__ == '__main__':
    cli()