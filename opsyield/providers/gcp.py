
from typing import List
from ..core.models import NormalizedCost, Resource
from .base import CloudProvider
import datetime

class GCPProvider(CloudProvider):
    async def get_costs(self, days: int = 30) -> List[NormalizedCost]:
        # TODO: Implement real BigQuery/Billing API calls
        return [
            NormalizedCost(
                amount=150.0,
                currency="USD",
                date=datetime.date.today(),
                service="Compute Engine",
                provider="gcp"
            ),
            NormalizedCost(
                amount=50.0,
                currency="USD",
                date=datetime.date.today(),
                service="Cloud Storage",
                provider="gcp"
            )
        ]

    async def get_infrastructure(self) -> List[Resource]:
        # TODO: Implement real Asset Inventory/Compute API calls
        return [
            Resource(
                id="vm-1",
                name="instance-1",
                type="compute_instance",
                provider="gcp",
                region="us-central1"
            )
        ]
