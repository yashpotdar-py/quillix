"""System and health check routes."""

from fastapi import APIRouter

from ..core.service_manager import service_manager
from ..core.config import settings

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check():
    """Overall system health check."""
    service_health = await service_manager.health_check_all()

    overall_health = all(result.success for result in service_health.values())

    return {
        "status": "healthy" if overall_health else "unhealthy",
        "services": {
            name: {"healthy": result.success, "message": result.message}
            for name, result in service_health.items()
        },
    }


@router.get("/info")
async def get_system_info():
    """Get system information."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "services": service_manager.get_services_info(),
    }


@router.get("/services")
async def list_services():
    """List all registered services."""
    return {
        "services": service_manager.list_services(),
        "total": len(service_manager.list_services()),
    }
