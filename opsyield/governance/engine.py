from typing import List, Any
from ..core.models import Resource, NormalizedCost

class PolicyEngine:
    def evaluate(self, resources: List[Resource], costs: List[NormalizedCost]) -> List[Any]:
        return []
