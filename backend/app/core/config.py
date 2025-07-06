"""Configuration management for the backend"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application Settings"""

    # App settings
    app_name: str = "Quillix Backend"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Discord webhook settings - Multiple webhook URLs
    discord_default_webhook_url: Optional[str] = None
    discord_testing_webhook_url: Optional[str] = None
    discord_scraping_webhook_url: Optional[str] = None

    # Discord bot settings
    discord_bot_token: Optional[str] = None
    discord_command_channel: str = "bot-commands"
    discord_guild_id: Optional[int] = None  # Optional: restrict to specific server

    # Redis settings
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment variables
        self.discord_default_webhook_url = os.getenv("DISCORD_DEFAULT_WEBHOOK_URL")
        self.discord_testing_webhook_url = os.getenv("DISCORD_TESTING_WEBHOOK_URL")
        self.discord_scraping_webhook_url = os.getenv("DISCORD_SCRAPING_WEBHOOK_URL")
        self.discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.discord_command_channel = os.getenv("DISCORD_COMMAND_CHANNEL", "bot-commands")
        if os.getenv("DISCORD_GUILD_ID"):
            self.discord_guild_id = int(os.getenv("DISCORD_GUILD_ID"))
        self.redis_url = os.getenv("REDIS_URL")

    @property
    def discord_webhook_url(self) -> Optional[str]:
        """Fallback property for backward compatibility"""
        return self.discord_default_webhook_url


settings = Settings()
