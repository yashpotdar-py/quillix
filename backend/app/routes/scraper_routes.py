"""Scraper service API routes with consolidated reporting."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List

from ..core.service_manager import service_manager
from ..services.discord_service import DiscordMessage, DiscordEmbed, WebhookType

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

    # Send consolidated report to Discord if requested
    if send_to_discord and result.data:
        discord_service = service_manager.get_service("discord")
        if discord_service:
            await _send_consolidated_report(discord_service, result.data)

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
    report_style: str = Query(
        default="detailed", description="Report style: 'summary', 'detailed', or 'compact'")
):
    """Scrape trends and send a consolidated report to Discord."""
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

    # Send consolidated report based on style
    await _send_consolidated_report(discord_service, result.data, report_style)

    return {
        "status": "success",
        "message": f"Sent consolidated {report_style} report to Discord",
        "scraped_count": result.data.get('total_count', 0),
        "report_style": report_style
    }


async def _send_consolidated_report(discord_service, scrape_data: Dict[str, Any], style: str = "detailed") -> None:
    """Send a consolidated trends report to Discord."""
    trends_data = scrape_data.get('trends', [])
    source = scrape_data.get('source', 'Unknown')
    total_count = scrape_data.get('total_count', 0)
    scraped_at = scrape_data.get('scraped_at', 'Unknown')

    if style == "summary":
        await _send_summary_report(discord_service, trends_data, source, total_count, scraped_at)
    elif style == "compact":
        await _send_compact_report(discord_service, trends_data, source, total_count, scraped_at)
    else:  # detailed
        await _send_detailed_report(discord_service, trends_data, source, total_count, scraped_at)


async def _send_summary_report(discord_service, trends: List, source: str, total_count: int, scraped_at: str) -> None:
    """Send a summary report with just titles and basic stats."""
    # Create title list
    trend_titles = []
    for i, trend in enumerate(trends[:10], 1):
        title = trend.get('title', 'Unknown')
        if len(title) > 80:
            title = title[:77] + "..."
        trend_titles.append(f"`{i:2d}.` {title}")

    # Create the embed
    embed = DiscordEmbed(
        title=f"📊 Tech Trends Summary - {source.title()}",
        description=f"Found **{total_count}** trending topics\n\n" +
        "\n".join(trend_titles),
        color=0x3498db,  # Blue
        username="Quillix Reporter",
        fields=[
            {
                "name": "📅 Scraped",
                "value": scraped_at[:19].replace('T', ' '),
                "inline": True
            },
            {
                "name": "📈 Total Trends",
                "value": str(total_count),
                "inline": True
            },
            {
                "name": "🔗 Source",
                "value": source.title(),
                "inline": True
            }
        ]
    )

    await discord_service.send_embed(embed, WebhookType.SCRAPING)


async def _send_compact_report(discord_service, trends: List, source: str, total_count: int, scraped_at: str) -> None:
    """Send a compact report with titles and tags."""
    # Build the trends list
    trends_text = []
    for i, trend in enumerate(trends, 1):
        title = trend.get('title', 'Unknown')
        if len(title) > 60:
            title = title[:57] + "..."

        tags = trend.get('tags', [])
        tags_text = f" `{', '.join(tags[:3])}`" if tags else ""

        trends_text.append(f"`{i}.` **{title}**{tags_text}")

    # Create the embed
    embed = DiscordEmbed(
        title=f"🚀 Tech Trends Report - {source.title()}",
        description=f"**{total_count}** trends discovered\n\n" +
        "\n\n".join(trends_text),
        color=0xe74c3c,  # Red
        username="Quillix Reporter",
        fields=[
            {
                "name": "⏰ Timestamp",
                "value": scraped_at[:19].replace('T', ' '),
                "inline": False
            }
        ]
    )

    await discord_service.send_embed(embed, WebhookType.SCRAPING)


async def _send_detailed_report(discord_service, trends: List, source: str, total_count: int, scraped_at: str) -> None:
    """Send a detailed report with summaries and links."""
    # Send header embed
    header_embed = DiscordEmbed(
        title=f"📋 Detailed Tech Trends Report",
        description=f"**{source.title()}** • {scraped_at[:19].replace('T', ' ')}\nAnalyzed **{total_count}** trending topics",
        color=0x2ecc71,  # Green
        username="Quillix Reporter"
    )
    await discord_service.send_embed(header_embed, WebhookType.SCRAPING)

    # Group trends by tags for better organization
    categorized_trends = _categorize_trends(trends[:15])

    # Send categorized trends
    for category, category_trends in categorized_trends.items():
        if not category_trends:
            continue

        category_text = []
        for trend in category_trends[:4]:  # Max 4 per category
            title = trend.get('title', 'Unknown')
            if len(title) > 70:
                title = title[:67] + "..."

            summary = trend.get('summary', '')
            if summary and len(summary) > 100:
                summary = summary[:97] + "..."

            url = trend.get('url', '')

            trend_text = f"**{title}**"
            if summary:
                trend_text += f"\n{summary}"
            if url:
                trend_text += f"\n🔗 [Read more]({url})"

            category_text.append(trend_text)

        # Create category embed
        category_embed = DiscordEmbed(
            title=f"{_get_category_emoji(category)} {category.title()} Trends",
            description="\n\n".join(category_text),
            color=0x9b59b6,  # Purple
            username="Quillix Reporter"
        )

        await discord_service.send_embed(category_embed, WebhookType.SCRAPING)

    # Send footer with remaining trends count
    if total_count > 15:
        footer_embed = DiscordEmbed(
            title="📌 Report Summary",
            description=f"Showing top 15 trends. **{total_count - 15}** more trends available.",
            color=0x95a5a6,  # Grey
            username="Quillix Reporter"
        )
        await discord_service.send_embed(footer_embed, WebhookType.SCRAPING)


def _categorize_trends(trends: List) -> Dict[str, List]:
    """Categorize trends by their tags."""
    categories = {
        "ai": [],
        "startup": [],
        "funding": [],
        "product": [],
        "other": []
    }

    for trend in trends:
        tags = trend.get('tags', [])
        categorized = False

        # Check for specific categories
        for tag in tags:
            if tag.lower() in ['ai', 'artificial intelligence', 'machine learning']:
                categories['ai'].append(trend)
                categorized = True
                break
            elif tag.lower() in ['startup', 'founded']:
                categories['startup'].append(trend)
                categorized = True
                break
            elif tag.lower() in ['funding', 'investment', 'series a', 'series b']:
                categories['funding'].append(trend)
                categorized = True
                break
            elif tag.lower() in ['product', 'feature', 'update', 'release']:
                categories['product'].append(trend)
                categorized = True
                break

        if not categorized:
            categories['other'].append(trend)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def _get_category_emoji(category: str) -> str:
    """Get emoji for category."""
    emojis = {
        'ai': '🤖',
        'startup': '🚀',
        'funding': '💰',
        'product': '📱',
        'other': '📰'
    }
    return emojis.get(category, '📰')


@router.post("/send-daily-digest")
async def send_daily_digest(
    scraper_name: str = Query(default="techcrunch",
                              description="Scraper to use"),
    url: Optional[str] = Query(default=None, description="URL to scrape")
):
    """Send a daily digest format report."""
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

    # Send daily digest
    await _send_daily_digest(discord_service, result.data)

    return {
        "status": "success",
        "message": "Daily digest sent to Discord",
        "scraped_count": result.data.get('total_count', 0)
    }


async def _send_daily_digest(discord_service, scrape_data: Dict[str, Any]) -> None:
    """Send a daily digest format report."""
    trends_data = scrape_data.get('trends', [])
    source = scrape_data.get('source', 'Unknown')
    total_count = scrape_data.get('total_count', 0)

    # Get trending tags
    all_tags = []
    for trend in trends_data:
        all_tags.extend(trend.get('tags', []))

    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Create digest embed
    digest_embed = DiscordEmbed(
        title="📰 Daily Tech Digest",
        description=f"Your daily roundup from **{source.title()}**",
        color=0xf39c12,  # Orange
        username="Quillix Daily",
        fields=[
            {
                "name": "📊 Headlines",
                "value": f"**{total_count}** trending stories today",
                "inline": True
            },
            {
                "name": "🔥 Hot Topics",
                "value": ", ".join([f"`{tag}`({count})" for tag, count in top_tags]) or "Various",
                "inline": True
            },
            {
                "name": "🕐 Generated",
                "value": scrape_data.get('scraped_at', 'Unknown')[:19].replace('T', ' '),
                "inline": True
            }
        ]
    )

    await discord_service.send_embed(digest_embed, WebhookType.SCRAPING)

    # Send top 5 stories
    top_stories = []
    for i, trend in enumerate(trends_data[:5], 1):
        title = trend.get('title', 'Unknown')
        if len(title) > 80:
            title = title[:77] + "..."

        url = trend.get('url', '')
        link_text = f" [→]({url})" if url else ""

        top_stories.append(f"`{i}.` **{title}**{link_text}")

    stories_embed = DiscordEmbed(
        title="🗞️ Top Stories",
        description="\n\n".join(top_stories),
        color=0x3498db,  # Blue
        username="Quillix Daily"
    )

    await discord_service.send_embed(stories_embed, WebhookType.SCRAPING)
