
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict
from .models import AnalysisResult, NormalizedCost, Resource
from ..providers.factory import ProviderFactory
from ..analytics.engine import AnalyticsEngine
from ..governance.engine import PolicyEngine
from ..risk.engine import RiskEngine
from ..optimization.engine import OptimizationEngine

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.provider_factory = ProviderFactory()
        self.analytics = AnalyticsEngine()
        self.governance = PolicyEngine()
        self.risk = RiskEngine()
        self.optimization = OptimizationEngine()

    async def analyze(self, provider_name: str, days: int = 30, **kwargs) -> AnalysisResult:
        """
        Orchestrates the analysis workflow:
        1. Fetch cost and infra data from provider
        2. Optimization analysis
        3. Analyze trends and anomalies
        4. Evaluate governance policies
        5. Assess risk
        6. Generate final report
        """
        # logger.info(f"Starting analysis for {provider_name} over {days} days")
        
        provider = self.provider_factory.get_provider(provider_name)
        
        # 1. Fetch Data
        costs = await provider.get_costs(days=days)
        resources = await provider.get_infrastructure()
        
        # 2. Optimization
        optimizations = self.optimization.analyze(costs)
        opt_potential = sum(o.get("potential_savings", 0) for o in optimizations)

        # 3. Analytics
        analytics_results = self.analytics.analyze(costs)
        
        # 4. Governance
        policy_violations = self.governance.evaluate(costs)
        
        # 5. Risk
        total_cost = sum(c.cost for c in costs)
        exec_summary = self.risk.generate_executive_summary(
            total_cost=total_cost,
            optimization_potential=opt_potential,
            anomalies=analytics_results.get("anomalies", []),
            violations=policy_violations,
            forecast=analytics_results.get("forecast", {}),
            trends=analytics_results.get("trends", {})
        )

        # 5.5 Calculate Daily Trends for Frontend
        daily_map = defaultdict(float)
        for c in costs:
            d = c.timestamp.strftime("%Y-%m-%d")
            daily_map[d] += c.cost
        
        daily_trends = [{"date": d, "amount": v} for d, v in daily_map.items()]
        daily_trends.sort(key=lambda x: x["date"])
        
        # 6. Construct Result
        result = AnalysisResult(
            meta={
                "provider": provider_name,
                "project_id": kwargs.get("project_id", "unknown"),
                "period": f"{days} days",
                "generated_at": datetime.now().isoformat()
            },
            summary={
                "total_cost": total_cost,
                "resource_count": len(resources),
                "risk_score": exec_summary.get("risk_score", 0),
                "currency": costs[0].currency if costs else "USD"
            },
            executive_summary=exec_summary,
            trends=analytics_results.get("trends", {}),
            daily_trends=daily_trends,
            anomalies=analytics_results.get("anomalies", []),
            forecast=analytics_results.get("forecast", {}),
            governance_issues=policy_violations,
            optimizations=optimizations,
            resources=resources
        )
        
        return result

    async def aggregate_analysis(self, providers: List[str], days: int = 30) -> Dict[str, Any]:
        """
        Aggregates analysis across multiple providers.
        """
        # Run analysis for each provider in parallel
        tasks = [self.analyze(p, days) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        total_cost = 0
        all_optimizations = []
        all_anomalies = []
        all_violations = []
        all_resources = []
        
        valid_results = []
        
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Failed to analyze {providers[i]}: {res}")
                continue
            
            valid_results.append(res)
            total_cost += res.summary.get("total_cost", 0)
            all_optimizations.extend(res.optimizations)
            all_anomalies.extend(res.anomalies)
            all_violations.extend(res.governance_issues)
            all_resources.extend(res.resources)

        # Create aggregate summary
        # simplified risk aggregation (average of scores)
        avg_risk = sum(r.summary.get("risk_score", 0) for r in valid_results) / len(valid_results) if valid_results else 0
        
        # Aggregate daily trends
        agg_daily_map = defaultdict(float)
        for res in valid_results:
            for item in res.daily_trends:
                agg_daily_map[item["date"]] += item["amount"]
        
        agg_daily_trends = [{"date": d, "amount": v} for d, v in agg_daily_map.items()]
        agg_daily_trends.sort(key=lambda x: x["date"])

        return AnalysisResult(
            meta={
                "provider": "aggregate",
                "period": f"{days} days",
                "generated_at": datetime.now().isoformat()
            },
            summary={
                "total_cost": total_cost,
                "resource_count": len(all_resources),
                "risk_score": avg_risk,
                "currency": "USD"
            },
            executive_summary={
                "total_spend": total_cost,
                "risk_score": avg_risk,
                # Simple aggregation for other fields
                "anomaly_count": len(all_anomalies),
                "governance_violations": len(all_violations)
            },
            trends={"period_total": total_cost, "trend_percent": 0.0}, # Dummy summary
            daily_trends=agg_daily_trends,
            anomalies=all_anomalies,
            forecast={},
            governance_issues=all_violations,
            optimizations=all_optimizations,
            resources=all_resources
        )
