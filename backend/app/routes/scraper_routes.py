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
        "scraped_count": len(trends_data),
        "sent_to_discord": sent_count
    }
