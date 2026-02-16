
from typing import List
from ..core.models import NormalizedCost, Resource
from .base import CloudProvider
import datetime

class AzureProvider(CloudProvider):
    async def get_costs(self, days: int = 30) -> List[NormalizedCost]:
        # TODO: Implement real Cost Management API calls
        return [
            NormalizedCost(
                amount=100.0,
                currency="USD",
                date=datetime.date.today(),
                service="Virtual Machines",
                provider="azure"
            )
        ]

    async def get_infrastructure(self) -> List[Resource]:
        # TODO: Implement real Resource Graph/Management SDK calls
        return [
            Resource(
                id="/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                name="vm1",
                type="virtual_machine",
                provider="azure",
                region="eastus"
            )
        ]
