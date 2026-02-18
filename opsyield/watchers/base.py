from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..core.models import Resource, NormalizedCost

class BaseWatcher(ABC):
    @abstractmethod
    def watch(self, resources: List[Resource], costs: List[NormalizedCost]) -> List[Dict[str, Any]]:
        """
        Analyze resources and costs to find anomalies or issues.
        Returns a list of findings/alerts.
        """
        pass
