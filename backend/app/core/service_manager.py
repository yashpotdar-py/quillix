"""Service manager for handling multiple services"""

from typing import Dict, List, Optional
import logging

from .service import BaseService, ServiceResponse

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages all registered services"""

    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._initialized = False

    def register_service(self, service: BaseService) -> None:
        """Register all registered services"""

        self._services[service.name] = service
        logger.info(f"Registred service: {service.name}")

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a service by name"""
        return self._services.get(name)

    def list_services(self) -> List[str]:
        """List all registered services names."""
        return list(self._services.keys())

    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all services."""
        results = {}

        for name, service in self._services.items():
            try:
                logger.info(f"Initializing service: {name}")
                success = await service.initialize()
                results[name] = success

                if success:
                    logger.info(f"Service {name} initialized successfully")
                else:
                    logger.error(f"Service {name} failed to initialize")

            except Exception as e:
                logger.error(f"Error initializing service {name}: {e}")
                results[name] = False

        self._initialized = True
        return results

    async def health_check_all(self) -> Dict[str, ServiceResponse]:
        """Run health checks on all services."""
        results = {}

        for name, service in self._services.items():
            try:
                results[name] = await service.health_check()
            except Exception as e:
                results[name] = ServiceResponse(
                    success=False,
                    message=f"Health check failed: {str(e)}",
                    error=str(e)
                )
        return results

    async def cleanup_all(self) -> None:
        """Cleanup all services."""
        for name, service in self._services.items():
            try:
                logger.info(f"Cleaning up service: {name}")
                await service.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up service {name}: {e}")

    def get_services_info(self) -> Dict[str, Dict]:
        """Get information about all services."""
        return {
            name: service.get_info() for name, service in self._services.items()
        }


# Global service manager instance
service_manager = ServiceManager()
