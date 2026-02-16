from typing import List, Dict, Any
from datetime import datetime
import statistics
from collections import defaultdict
from ..core.models import NormalizedCost

class AnalyticsEngine:
    """
    Performs statistical analysis on cost data to detect trends, anomalies, and forecast spend.
    """

    def analyze(self, costs: List[NormalizedCost]) -> Dict[str, Any]:
        if not costs:
            return {}

        return {
            "trends": self.calculate_trends(costs),
            "anomalies": self.detect_anomalies(costs),
            "forecast": self.forecast_spend(costs),
            "spend_by_dimension": self.aggregate_spend(costs)
        }

    def aggregate_spend(self, costs: List[NormalizedCost]) -> Dict[str, Dict[str, float]]:
        by_service = defaultdict(float)
        by_team = defaultdict(float)
        by_bu = defaultdict(float)
        by_env = defaultdict(float)

        for c in costs:
            by_service[c.service] += c.cost
            by_team[c.team or "Unassigned"] += c.cost
            by_bu[c.business_unit or "Unassigned"] += c.cost
            by_env[c.environment or "Unknown"] += c.cost

        return {
            "service": dict(by_service),
            "team": dict(by_team),
            "business_unit": dict(by_bu),
            "environment": dict(by_env)
        }

    def detect_anomalies(self, costs: List[NormalizedCost], threshold_z: float = 2.0) -> List[Dict]:
        """
        Detects cost spikes using Z-Score at the daily level per service.
        """
        # Group by Date and Service
        daily_service_cost = defaultdict(lambda: defaultdict(float))
        dates = set()
        for c in costs:
            date_str = c.timestamp.strftime("%Y-%m-%d")
            daily_service_cost[c.service][date_str] += c.cost
            dates.add(date_str)
        
        sorted_dates = sorted(list(dates))
        anomalies = []

        for service, date_map in daily_service_cost.items():
            cost_series = [date_map.get(d, 0.0) for d in sorted_dates]
            
            if len(cost_series) < 3:
                continue

            mean = statistics.mean(cost_series)
            try:
                stdev = statistics.stdev(cost_series)
            except statistics.StatisticsError:
                continue

            if stdev == 0:
                continue

            # Check the last few days for anomalies
            for i, cost in enumerate(cost_series):
                z_score = (cost - mean) / stdev
                if z_score > threshold_z:
                    anomalies.append({
                        "id": f"anomaly-{service}-{sorted_dates[i]}",
                        "date": sorted_dates[i],
                        "service": service,
                        "cost": cost,
                        "mean": mean,
                        "z_score": round(z_score, 2),
                        "severity": "high" if z_score > 3 else "medium"
                    })
        
        return anomalies

    def calculate_trends(self, costs: List[NormalizedCost]) -> Dict[str, Any]:
        """
        Simple trend analysis (Linear Regression slope or just % change).
        """
        total_cost = sum(c.cost for c in costs)
        if not costs:
            return {"trend_pct": 0.0}

        # Compare first half vs second half of the period roughly
        sorted_costs = sorted(costs, key=lambda x: x.timestamp)
        mid_point = len(sorted_costs) // 2
        
        first_half = sorted_costs[:mid_point]
        second_half = sorted_costs[mid_point:]
        
        sum_1 = sum(c.cost for c in first_half)
        sum_2 = sum(c.cost for c in second_half)
        
        if sum_1 == 0:
            trend = 100.0 if sum_2 > 0 else 0.0
        else:
            trend = ((sum_2 - sum_1) / sum_1) * 100
            
        return {
            "period_total": total_cost,
            "trend_percent": round(trend, 2),
            "direction": "up" if trend > 0 else "down"
        }

    def forecast_spend(self, costs: List[NormalizedCost]) -> Dict[str, float]:
        """
        Naive forecast: Average daily spend * 30 days.
        """
        if not costs:
            return {"predicted_monthly_cost": 0.0}

        days = (max(c.timestamp for c in costs) - min(c.timestamp for c in costs)).days + 1
        total = sum(c.cost for c in costs)
        daily_avg = total / max(days, 1)

        return {
            "daily_average": round(daily_avg, 2),
            "predicted_next_30_days": round(daily_avg * 30, 2)
        }
