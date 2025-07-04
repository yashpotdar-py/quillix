"""Base Service interface for modular services"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ServiceResponse(BaseModel):
    """Standard response model for all services"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseService(ABC):
    """Abstract base class for all services"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"service.{name}")

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service. Return True if successfull."""
        pass

    @abstractmethod
    async def health_check(self) -> ServiceResponse:
        """Check if the service is healthy"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources when shutting down"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "status": "active"
        }
