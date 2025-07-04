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

    # Discord settings
    discord_webhook_url: Optional[str] = None

    # Redis settings
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment variables
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.redis_url = os.getenv("REDIS_URL")


settings = Settings()
