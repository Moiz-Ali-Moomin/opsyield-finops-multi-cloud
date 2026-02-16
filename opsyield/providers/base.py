
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.models import NormalizedCost, Resource

class CloudProvider(ABC):
    @abstractmethod
    async def get_costs(self, days: int = 30) -> List[NormalizedCost]:
        """Fetch cost data normalized to a common format"""
        pass

    @abstractmethod
    async def get_infrastructure(self) -> List[Resource]:
        """Discover infrastructure resources"""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Check provider status (installed, authenticated)"""
        pass
