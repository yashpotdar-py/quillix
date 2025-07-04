"""Discord service API routes."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..core.service_manager import service_manager
from ..services.discord_service import DiscordMessage, DiscordEmbed

router = APIRouter(prefix="/discord", tags=["discord"])


@router.post("/send-message")
async def send_message(message: DiscordMessage):
    """Send a simple test message to Discord."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service is not available")

    result = await discord_service.send_message(message)

    if result.success:
        return {
            "status": "success",
            "message": result.message
        }
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.post("/send-embed")
async def send_embed(embed: DiscordEmbed):
    """Send an embed message to Discord."""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service is not available")

    result = await discord_service.send_embed(embed)

    if result.success:
        return {
            "status": "success",
            "message": result.message
        }
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)


@router.post("/send-trend")
async def send_trend(trend_data: Dict[str, Any]):
    """Send a formatted trend notification to Discord"""
    discord_service = service_manager.get_service("discord")
    if not discord_service:
        raise HTTPException(
            status_code=503, detail="Discord service not available")

    result = await discord_service.send_trend_notification(trend_data)

    if result.success:
        return {
            "status": "success",
            "message": result.message
        }
    else:
        raise HTTPException(
            status_code=400, detail=result.error or result.message)
