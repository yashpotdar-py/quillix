"""Discord webhook service implementation"""

import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ..core.service import BaseService, ServiceResponse
from ..core.config import settings


class DiscordMessage(BaseModel):
    """Discord message model."""
    content: str
    username: str = "Quillix Bot"
    avatar_url: Optional[str] = None


class DiscordEmbed(BaseModel):
    """Discord embed model."""
    title: str
    description: str
    color: int = 0x00ff00  # Green
    username: str = "Quillix Bot"
    avatar_url: Optional[str] = None
    url: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None


class DiscordService(BaseService):
    """Discord webhook service"""

    def __init__(self):
        super().__init__("discord")
        self.webhook_url = settings.discord_webhook_url
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> bool:
        """Initialize Discord service"""
        if not self.webhook_url:
            self.logger.error("Discord webhook URL not configured")
            return False

        self.client = httpx.AsyncClient(timeout=30.0)

        # Test the webhook
        try:
            test_response = await self._send_webhook(
                {
                    "content": "Quillix Discord Service initialized!",
                    "username": "Quillix Bot"
                }
            )
            return test_response.success
        except Exception as e:
            self.logger.error(f"Failed to initialize Discord service: {e}")
            return False

    async def health_check(self) -> ServiceResponse:
        """Check Discord service health"""
        if not self.client or not self.webhook_url:
            return ServiceResponse(
                success=False,
                message="Discord service not properly initialized"
            )

        try:
            # Simple ping test
            response = await self.client.get("https://discord.com/api/v10/gateway")
            if response.status_code == 200:
                return ServiceResponse(
                    success=True,
                    message="Discord service is healthy"
                )
            else:
                return ServiceResponse(
                    success=False,
                    message=f"Discord API returned status {response.status_code}"
                )

        except Exception as e:
            return ServiceResponse(
                success=False,
                message="Discord service health check failed",
                error=str(e)
            )

    async def cleanup(self) -> None:
        """Cleanup Discord service resources"""
        if self.client:
            await self.client.aclose()

    async def send_message(self, message: DiscordMessage) -> ServiceResponse:
        """Send a text message to Discord."""
        payload = {
            "content": message.content,
            "username": message.username
        }

        if message.avatar_url:
            payload["avatar_url"] = message.avatar_url

        return await self._send_webhook(payload)

    async def send_embed(self, embed: DiscordEmbed) -> ServiceResponse:
        """Send an embed message to Discord"""
        embed_data = {
            "title": embed.title,
            "description": embed.description,
            "color": embed.color
        }

        if embed.url:
            embed_data["url"] = embed.url

        if embed.fields:
            embed_data["fields"] = embed.fields

        payload = {
            "username": embed.username,
            "embeds": [embed_data]
        }

        if embed.avatar_url:
            payload["avatar_url"] = embed.avatar_url

        return await self._send_webhook(payload)

    async def send_trend_notification(self, trend_data: Dict[str, Any]) -> ServiceResponse:
        """Send a formatted trend notification"""
        embed = DiscordEmbed(
            title=f"🔥 New Trend: {trend_data.get('title', 'Unknown')}",
            description=trend_data.get(
                'summary', 'No summary available')[:2000],
            color=0xff6b35,  # Orange color
            url=trend_data.get('url'),
            fields=[
                {
                    "name": "Source",
                    "value": trend_data.get('source', 'Unknown'),
                    "inline": True
                },
                {
                    "name": "Tags",
                    "value": ", ".join(trend_data.get('tags', [])) or "None",
                    "inline": True
                }
            ]
        )

        return await self.send_embed(embed)

    async def _send_webhook(self, payload: Dict[str, Any]) -> ServiceResponse:
        """Send webhook payload to Discord"""
        if not self.client:
            return ServiceResponse(
                success=False,
                message="Discord client not initialized"
            )

        try:
            response = await self.client.post(self.webhook_url, json=payload)

            if response.status_code == 204:
                self.logger.info("Discord message sent successfully")

                return ServiceResponse(
                    success=True,
                    message="Message sent to Discord successfully"
                )

            else:
                error_msg = f"Discord API error: {response.status_code}"
                self.logger.error(f"{error_msg} - {response.text}")
                return ServiceResponse(
                    success=False,
                    message=error_msg,
                    error=response.text
                )

        except Exception as e:
            self.logger.error(f"Error sending Discord message: {e}")
            return ServiceResponse(
                success=False,
                message="Failed to send message to Discord",
                error=str(e)
            )
