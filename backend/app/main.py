"""Main FastAPI application with modular services."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.service_manager import service_manager
from .services.discord_service import DiscordService
from .services.discord_bot_service import DiscordBotService
from .services.scraper_service import ScraperService
from .routes import discord_routes, system_routes, scraper_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Quillix Backend...")

    # Register services
    service_manager.register_service(DiscordService())
    service_manager.register_service(DiscordBotService())
    service_manager.register_service(ScraperService())

    # Initialize all services
    init_results = await service_manager.initialize_all()

    failed_services = [name for name, success in init_results.items() if not success]
    if failed_services:
        logger.warning(f"⚠️  Failed to initialize services: {failed_services}")

    logger.info("✅ Quillix Backend startup complete")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Quillix Backend...")
    await service_manager.cleanup_all()
    logger.info("✅ Quillix Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A modular backend service for Quillix",
    version=settings.app_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(system_routes.router)
app.include_router(discord_routes.router)
app.include_router(scraper_routes.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "services": service_manager.list_services(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "discord": "/discord",
            "scraper": "/scraper"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
