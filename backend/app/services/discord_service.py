"""Discord webhook service implementation with multiple webhook support."""

from datetime import datetime
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum

from ..core.service import BaseService, ServiceResponse
from ..core.config import settings


class WebhookType(str, Enum):
    """Types of Discord webhooks."""
    DEFAULT = "default"
    TESTING = "testing"
    SCRAPING = "scraping"


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
    """Discord webhook service with multiple webhook support."""

    def __init__(self):
        super().__init__("discord")
        self.webhook_urls = {
            WebhookType.DEFAULT: settings.discord_default_webhook_url,
            WebhookType.TESTING: settings.discord_testing_webhook_url,
            WebhookType.SCRAPING: settings.discord_scraping_webhook_url,
        }
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> bool:
        """Initialize Discord service."""
        # Check if at least one webhook URL is configured
        available_webhooks = {k: v for k, v in self.webhook_urls.items() if v}

        if not available_webhooks:
            self.logger.error("No Discord webhook URLs configured")
            return False

        self.client = httpx.AsyncClient(timeout=30.0)

        # Test the testing webhook (or default if testing not available)
        test_webhook = (
            self.webhook_urls[WebhookType.TESTING] or
            self.webhook_urls[WebhookType.DEFAULT]
        )

        if test_webhook:
            try:
                test_response = await self._send_webhook(
                    {
                        "content": f"Quillix Discord Service initialized! - {datetime.now()}",
                        "username": "Quillix System"
                    },
                    webhook_url=test_webhook
                )

                self.logger.info(
                    f"Available webhooks: {list(available_webhooks.keys())}")
                return test_response.success
            except Exception as e:
                self.logger.error(f"Failed to initialize Discord service: {e}")
                return False

        return False

    async def health_check(self) -> ServiceResponse:
        """Check Discord service health."""
        if not self.client:
            return ServiceResponse(
                success=False,
                message="Discord service not properly initialized"
            )

        try:
            # Simple ping test
            response = await self.client.get("https://discord.com/api/v10/gateway")
            if response.status_code == 200:
                available_webhooks = [
                    k for k, v in self.webhook_urls.items() if v]
                return ServiceResponse(
                    success=True,
                    message="Discord service is healthy",
                    data={"available_webhooks": available_webhooks}
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
        """Cleanup Discord service resources."""
        if self.client:
            await self.client.aclose()

    def _get_webhook_url(self, webhook_type: WebhookType) -> Optional[str]:
        """Get webhook URL with fallback logic."""
        # Try requested webhook type first
        webhook_url = self.webhook_urls.get(webhook_type)
        if webhook_url:
            return webhook_url

        # Fallback to default
        default_url = self.webhook_urls.get(WebhookType.DEFAULT)
        if default_url:
            self.logger.warning(
                f"Webhook {webhook_type} not available, using default")
            return default_url

        # Last resort - any available webhook
        for url in self.webhook_urls.values():
            if url:
                self.logger.warning(
                    f"Using fallback webhook for {webhook_type}")
                return url

        return None

    async def send_message(
        self,
        message: DiscordMessage,
        webhook_type: WebhookType = WebhookType.DEFAULT
    ) -> ServiceResponse:
        """Send a text message to Discord using specified webhook type."""
        webhook_url = self._get_webhook_url(webhook_type)
        if not webhook_url:
            return ServiceResponse(
                success=False,
                message=f"No webhook URL available for type: {webhook_type}"
            )

        payload = {
            "content": message.content,
            "username": message.username
        }

        if message.avatar_url:
            payload["avatar_url"] = message.avatar_url

        return await self._send_webhook(payload, webhook_url)

    async def send_embed(
        self,
        embed: DiscordEmbed,
        webhook_type: WebhookType = WebhookType.DEFAULT
    ) -> ServiceResponse:
        """Send an embed message to Discord using specified webhook type."""
        webhook_url = self._get_webhook_url(webhook_type)
        if not webhook_url:
            return ServiceResponse(
                success=False,
                message=f"No webhook URL available for type: {webhook_type}"
            )

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

        return await self._send_webhook(payload, webhook_url)

    async def send_trend_notification(self, trend_data: Dict[str, Any]) -> ServiceResponse:
        """Send a formatted trend notification using scraping webhook."""
        embed = DiscordEmbed(
            title=f"New Trend: {trend_data.get('title', 'Unknown')}",
            description=trend_data.get(
                'summary', 'No summary available')[:2000],
            color=0xff6b35,  # Orange color
            url=trend_data.get('url'),
            username="Quillix Scraper",
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

        return await self.send_embed(embed, WebhookType.SCRAPING)

    async def send_system_notification(self, message: str) -> ServiceResponse:
        """Send a system notification using testing webhook."""
        discord_message = DiscordMessage(
            content=f"**System Notification**\n{message}",
            username="Quillix System"
        )
        return await self.send_message(discord_message, WebhookType.TESTING)

    async def send_health_check(self) -> ServiceResponse:
        """Send a health check message using testing webhook."""
        discord_message = DiscordMessage(
            content=f"Health check - All systems operational! - {datetime.now()}",
            username="Quillix Health"
        )
        return await self.send_message(discord_message, WebhookType.TESTING)

    async def _send_webhook(self, payload: Dict[str, Any], webhook_url: str) -> ServiceResponse:
        """Send webhook payload to Discord."""
        if not self.client:
            return ServiceResponse(
                success=False,
                message="Discord client not initialized"
            )

        try:
            response = await self.client.post(webhook_url, json=payload)

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
