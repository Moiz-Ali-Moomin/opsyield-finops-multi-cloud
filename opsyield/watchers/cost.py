from typing import List, Dict, Any
from collections import defaultdict
from .base import BaseWatcher
from ..core.models import Resource, NormalizedCost

class CostSpikeWatcher(BaseWatcher):
    def watch(self, resources: List[Resource], costs: List[NormalizedCost]) -> List[Dict[str, Any]]:
        findings = []
        # Group costs by service and date
        # Check if yesterday's cost > 1.5 * avg of previous 7 days
        
        daily_costs = defaultdict(lambda: defaultdict(float))
        for c in costs:
            d = c.timestamp.strftime("%Y-%m-%d")
            daily_costs[c.service][d] += c.cost
            
        sorted_dates = sorted(list(set(d for s in daily_costs.values() for d in s.keys())))
        if len(sorted_dates) < 2:
            return []

        latest_date = sorted_dates[-1]
        
        for service, dates in daily_costs.items():
            latest_cost = dates.get(latest_date, 0)
            if latest_cost < 10: # Ignore small costs
                 continue

            # Calculate avg of previous days
            prev_costs = [dates.get(d, 0) for d in sorted_dates[:-1]]
            if not prev_costs:
                continue
                
            avg_prev = sum(prev_costs) / len(prev_costs)
            
            if avg_prev > 0 and latest_cost > (avg_prev * 1.5):
                findings.append({
                    "type": "cost_spike",
                    "service": service,
                    "date": latest_date,
                    "cost": latest_cost,
                    "avg_previous": avg_prev,
                    "increase_pct": round(((latest_cost - avg_prev) / avg_prev) * 100, 1),
                    "severity": "high" if latest_cost > 100 else "medium"
                })

        return findings
