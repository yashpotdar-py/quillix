"""Discord service API routes."""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any
from pydantic import BaseModel

from ..core.service_manager import service_manager
from ..services.discord_service import DiscordMessage, DiscordEmbed, WebhookType

router = APIRouter(prefix="/discord", tags=["Discord"])


class SystemNotificationRequest(BaseModel):
    """Request model for system notifications."""
    message: str


@router.post("/send-message")
async def send_message(
    message: DiscordMessage,
    webhook_type: WebhookType = Query(
        default=WebhookType.DEFAULT, description="Webhook type to use")
):
    """Send a simple text message to Discord using specified webhook type."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    result = await discord_service.send_message(message, webhook_type)

    if result.success:
        return {"status": "success", "message": result.message, "webhook_type": webhook_type}
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.post("/send-embed")
async def send_embed(
    embed: DiscordEmbed,
    webhook_type: WebhookType = Query(
        default=WebhookType.DEFAULT, description="Webhook type to use")
):
    """Send an embed message to Discord using specified webhook type."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    result = await discord_service.send_embed(embed, webhook_type)

    if result.success:
        return {"status": "success", "message": result.message, "webhook_type": webhook_type}
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.post("/send-trend")
async def send_trend(trend_data: Dict[str, Any]):
    """Send a formatted trend notification to Discord (uses scraping webhook)."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    result = await discord_service.send_trend_notification(trend_data)

    if result.success:
        return {"status": "success", "message": result.message, "webhook_type": "scraping"}
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.post("/send-system-notification")
async def send_system_notification(request: SystemNotificationRequest):
    """Send a system notification to Discord (uses testing webhook)."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    result = await discord_service.send_system_notification(request.message)

    if result.success:
        return {"status": "success", "message": result.message, "webhook_type": "testing"}
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.post("/health-check")
async def send_health_check():
    """Send a health check message to Discord (uses testing webhook)."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    result = await discord_service.send_health_check()

    if result.success:
        return {"status": "success", "message": result.message, "webhook_type": "testing"}
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.get("/webhooks")
async def list_webhooks():
    """List available webhook types and their status."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    webhook_status = {}
    for webhook_type in WebhookType:
        webhook_url = discord_service._get_webhook_url(webhook_type)
        webhook_status[webhook_type] = {
            "available": webhook_url is not None,
            "configured": discord_service.webhook_urls.get(webhook_type) is not None
        }

    return {
        "webhooks": webhook_status,
        "total_configured": sum(1 for url in discord_service.webhook_urls.values() if url)
    }
