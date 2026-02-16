
import logging
from typing import Dict, Any, List
from .models import AnalysisResult, NormalizedCost, Resource
from ..providers.factory import ProviderFactory
from ..analytics.engine import AnalyticsEngine
from ..governance.engine import PolicyEngine
from ..risk.engine import RiskEngine

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.provider_factory = ProviderFactory()
        self.analytics = AnalyticsEngine()
        self.governance = PolicyEngine()
        self.risk = RiskEngine()

    async def analyze(self, provider_name: str, days: int = 30, **kwargs) -> AnalysisResult:
        """
        Orchestrates the analysis workflow:
        1. Fetch cost and infra data from provider
        2. Analyze trends and anomalies
        3. Evaluate governance policies
        4. Assess risk
        5. Generate final report
        """
        logger.info(f"Starting analysis for {provider_name} over {days} days")
        
        provider = self.provider_factory.get_provider(provider_name)
        
        # 1. Fetch Data
        costs = await provider.get_costs(days=days, **kwargs)
        resources = await provider.get_infrastructure(**kwargs)
        
        # 2. Analytics
        trends = self.analytics.analyze_trends(costs)
        anomalies = self.analytics.detect_anomalies(costs)
        forecast = self.analytics.forecast_spend(costs)
        
        # 3. Governance
        policy_violations = self.governance.evaluate(resources, costs)
        
        # 4. Risk
        risk_score = self.risk.assess(resources, policy_violations)
        
        # 5. Construct Result
        result = AnalysisResult(
            meta={
                "provider": provider_name,
                "period": f"{days} days"
            },
            summary={
                "total_cost": sum(c.amount for c in costs),
                "resource_count": len(resources),
                "risk_score": risk_score
            },
            trends=trends,
            anomalies=anomalies,
            forecast=forecast,
            governance_issues=policy_violations,
            resources=resources
        )
        
        return result

    async def aggregate_analysis(self, providers: List[str], days: int = 30) -> Dict[str, Any]:
        results = {}
        for p in providers:
            try:
                results[p] = await self.analyze(p, days)
            except Exception as e:
                logger.error(f"Failed to analyze {p}: {e}")
                results[p] = {"error": str(e)}
        
        return self.analytics.aggregate_results(results)
