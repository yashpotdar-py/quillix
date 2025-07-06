"""Scraper service API routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any

from ..core.service_manager import service_manager
from ..services.discord_service import DiscordMessage, DiscordEmbed

router = APIRouter(prefix="/scraper", tags=["Scraper"])


@router.get("/scrapers")
async def list_scrapers():
    """List all available scrapers."""
    scraper_service = service_manager.get_service("scraper")
    if not scraper_service:
        raise HTTPException(
            status_code=503, detail="Scraper service not available")

    scrapers = scraper_service.list_scrapers()
    return {"scrapers": scrapers, "total": len(scrapers)}


@router.post("/scrape")
async def scrape_trends(
    scraper_name: str = Query(default="techcrunch",
                              description="Scraper to use"),
    url: Optional[str] = Query(
        default=None, description="URL to scrape (optional)"),
    send_to_discord: bool = Query(
        default=False, description="Send results to Discord")
):
    """Scrape trends and optionally send to Discord."""
    scraper_service = service_manager.get_service("scraper")
    if not scraper_service:
        raise HTTPException(
            status_code=503, detail="Scraper service not available")

    # Scrape trends
    result = await scraper_service.scrape_trends(scraper_name, url)

    if not result.success:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)

    # Send to Discord if requested
    if send_to_discord and result.data:
        discord_service = service_manager.get_service("discord")
        if discord_service:
            trends_data = result.data.get('trends', [])

            # Create proper DiscordMessage object
            summary_message = f"🔍 **Scraping Results**\n"
            summary_message += f"Source: {result.data.get('source', 'Unknown')}\n"
            summary_message += f"Total trends found: {result.data.get('total_count', 0)}\n"
            summary_message += f"Scraped at: {result.data.get('scraped_at', 'Unknown')}"

            discord_message = DiscordMessage(
                content=summary_message,
                username="Quillix Scraper"
            )
            await discord_service.send_message(discord_message)

            # Send top 3 trends as embeds
            for i, trend in enumerate(trends_data[:3], 1):
                await discord_service.send_trend_notification(trend)

    return {
        "status": "success",
        "message": result.message,
        "data": result.data,
        "sent_to_discord": send_to_discord
    }


@router.post("/scrape-and-notify")
async def scrape_and_notify_all(
    scraper_name: str = Query(default="techcrunch",
                              description="Scraper to use"),
    url: Optional[str] = Query(default=None, description="URL to scrape"),
    max_trends: int = Query(
        default=5, description="Max trends to send to Discord")
):
    """Scrape trends and send all to Discord with formatting."""
    scraper_service = service_manager.get_service("scraper")
    discord_service = service_manager.get_service("discord")

    if not scraper_service:
        raise HTTPException(
            status_code=503, detail="Scraper service not available")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    # Scrape trends
    result = await scraper_service.scrape_trends(scraper_name, url)

    if not result.success:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)

    trends_data = result.data.get('trends', [])

    # Create proper DiscordEmbed object
    summary_embed = DiscordEmbed(
        title="🔍 New Scraping Results",
        description=f"Found **{len(trends_data)}** trending topics from **{result.data.get('source', 'Unknown')}**",
        color=0x00ff00,
        fields=[
            {
                "name": "Source",
                "value": result.data.get('source', 'Unknown'),
                "inline": True
            },
            {
                "name": "Total Trends",
                "value": str(len(trends_data)),
                "inline": True
            },
            {
                "name": "Scraped At",
                "value": result.data.get('scraped_at', 'Unknown')[:19].replace('T', ' '),
                "inline": True
            }
        ]
    )

    await discord_service.send_embed(summary_embed)

    # Send individual trends
    sent_count = 0
    for trend in trends_data[:max_trends]:
        discord_result = await discord_service.send_trend_notification(trend)
        if discord_result.success:
            sent_count += 1

    return {
        "status": "success",
        "message": f"Scraped {len(trends_data)} trends, sent {sent_count} to Discord",
        "data": result.data,
        "scraped_count": len(trends_data),
        "sent_to_discord": sent_count
    }


# Helper functions for bot commands
async def _send_consolidated_report(discord_service, scrape_data: Dict[str, Any], style: str = "detailed"):
    """Send a consolidated scraping report."""
    trends_data = scrape_data.get('trends', [])
    
    if style == "summary":
        # Send summary embed
        summary_embed = DiscordEmbed(
            title="📊 Scraping Summary",
            description=f"Found **{len(trends_data)}** trends from **{scrape_data.get('source', 'Unknown')}**",
            color=0x3498db,
            fields=[
                {
                    "name": "Total Trends",
                    "value": str(len(trends_data)),
                    "inline": True
                },
                {
                    "name": "Source",
                    "value": scrape_data.get('source', 'Unknown'),
                    "inline": True
                }
            ]
        )
        await discord_service.send_embed(summary_embed)
        
        # Send top 3 trends
        for trend in trends_data[:3]:
            await discord_service.send_trend_notification(trend)
    
    else:  # detailed
        # Send detailed report with more trends
        summary_embed = DiscordEmbed(
            title="🔍 Detailed Scraping Report",
            description=f"Comprehensive analysis of **{len(trends_data)}** trends from **{scrape_data.get('source', 'Unknown')}**",
            color=0x2ecc71,
            fields=[
                {
                    "name": "Total Trends",
                    "value": str(len(trends_data)),
                    "inline": True
                },
                {
                    "name": "Source",
                    "value": scrape_data.get('source', 'Unknown'),
                    "inline": True
                },
                {
                    "name": "Scraped At",
                    "value": scrape_data.get('scraped_at', 'Unknown')[:19].replace('T', ' '),
                    "inline": True
                }
            ]
        )
        await discord_service.send_embed(summary_embed)
        
        # Send top 5 trends for detailed report
        for trend in trends_data[:5]:
            await discord_service.send_trend_notification(trend)


async def _send_daily_digest(discord_service, scrape_data: Dict[str, Any]):
    """Send a daily digest report."""
    trends_data = scrape_data.get('trends', [])
    
    # Create digest embed
    digest_embed = DiscordEmbed(
        title="📰 Daily Tech Trends Digest",
        description=f"Today's top trending topics in tech from **{scrape_data.get('source', 'Unknown')}**",
        color=0xe74c3c,
        fields=[
            {
                "name": "📊 Statistics",
                "value": f"• **{len(trends_data)}** total trends\n• **{len([t for t in trends_data if t.get('tags')])}** tagged trends\n• Source: {scrape_data.get('source', 'Unknown')}",
                "inline": False
            }
        ]
    )
    await discord_service.send_embed(digest_embed)
    
    # Send top trending items
    for i, trend in enumerate(trends_data[:3], 1):
        digest_trend = {
            **trend,
            'title': f"#{i} {trend.get('title', 'Untitled')}"
        }
        await discord_service.send_trend_notification(digest_trend)
