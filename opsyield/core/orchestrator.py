
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
from ..analysis.idle_scoring import IdleScorer
from ..analysis.waste_detector import WasteDetector

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
        
        subscription_id = kwargs.get("subscription_id")
        project_id = kwargs.get("project_id")
        provider = self.provider_factory.get_provider(
            provider_name,
            subscription_id=subscription_id,
            project_id=project_id,
        )
        
        # 1. Fetch Data
        costs = await provider.get_costs(days=days)
        resources = await provider.get_infrastructure()

        # Optional: enrich resources with per-resource costs if provider supports it
        resource_cost_map: Dict[str, Dict[str, Any]] = {}
        if hasattr(provider, "get_resource_costs"):
            try:
                resource_cost_map = await provider.get_resource_costs(days=days)  # type: ignore[attr-defined]
            except Exception as e:
                logger.info(f"Resource-cost enrichment skipped: {e}")

        if resource_cost_map and resources:
            for r in resources:
                # Best-effort match by name or id
                key_candidates = [r.name, r.id]
                found = None
                for k in key_candidates:
                    if k and k in resource_cost_map:
                        found = resource_cost_map[k]
                        break
                if found:
                    r.cost_30d = found.get("cost_30d")
                    r.currency = found.get("currency")
                    # optionally override type for display
                    if not r.type and found.get("service"):
                        r.type = str(found.get("service"))
        
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
        # Enrichment: cost drivers (top services)
        service_totals: Dict[str, float] = defaultdict(float)
        currency = "USD"
        for c in costs:
            service_totals[c.service] += float(c.cost or 0)
            currency = c.currency or currency

        cost_drivers = [
            {"service": s, "cost": round(v, 4), "currency": currency}
            for s, v in sorted(service_totals.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ]

        # Enrichment: resource type counts + running count + idle/waste heuristics
        resource_types: Dict[str, int] = defaultdict(int)
        running_count = 0
        idle_scorer = IdleScorer()
        waste_detector = WasteDetector()
        idle_resources: List[Dict[str, Any]] = []

        now = datetime.utcnow()

        resource_dicts_for_waste: List[Dict[str, Any]] = []
        for r in resources:
            resource_types[r.type] += 1
            state = (r.state or "").lower()
            if "running" in state:
                running_count += 1

            days_running = 0
            if r.creation_date:
                try:
                    days_running = (now - r.creation_date.replace(tzinfo=None)).days
                except Exception:
                    days_running = 0

            # basic idle heuristics:
            # - no external IP (often internal-only workloads)
            # - long running
            # - very low 30d cost if available
                idle_score = idle_scorer.calculate_score({
                    "name": r.name,
                    "state": r.state,
                    "external_ip": r.external_ip,
                    "days_running": days_running,
                    "type": r.type,
                    "cost_30d": r.cost_30d
                }, cpu_avg=None)
                
                if r.cost_30d is not None:
                     # Boost score if burning significant money for no reason
                    if r.cost_30d > 50 and "dev" in (r.name or "").lower():
                        idle_score += 20

                r.idle_score = min(100, int(idle_score))

                if r.idle_score >= 50: # Lowered threshold to see more candidates
                    idle_resources.append({
                        "id": r.id,
                        "name": r.name,
                        "type": r.type,
                        "class_type": r.class_type,
                        "region": r.region,
                        "state": r.state,
                        "idle_score": r.idle_score,
                        "cost_30d": r.cost_30d,
                        "currency": r.currency,
                        "days_running": days_running,
                    })

            resource_dicts_for_waste.append({
                "name": r.name,
                "type": r.type,
                "state": r.state, 
                "external_ip": r.external_ip,
                "created_at": r.creation_date,
                "cost_30d": r.cost_30d 
            })

        waste_findings = waste_detector.detect(resource_dicts_for_waste) if resources else []

        # High-cost resources (if we have per-resource costs)
        high_cost_resources = []
        costy = [r for r in resources if r.cost_30d is not None]
        if costy:
            for r in sorted(costy, key=lambda x: float(x.cost_30d or 0), reverse=True)[:10]:
                high_cost_resources.append({
                    "id": r.id,
                    "name": r.name,
                    "type": r.type,
                    "class_type": r.class_type,
                    "region": r.region,
                    "state": r.state,
                    "cost_30d": r.cost_30d,
                    "currency": r.currency,
                })

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
            resources=resources,
            cost_drivers=cost_drivers,
            resource_types=dict(resource_types),
            running_count=running_count,
            high_cost_resources=high_cost_resources,
            idle_resources=idle_resources,
            waste_findings=waste_findings,
        )
        
        return result

    async def aggregate_analysis(self, providers: List[str], days: int = 30, subscription_id: str = None) -> Dict[str, Any]:
        """
        Aggregates analysis across multiple providers.
        """
        # Run analysis for each provider in parallel
        tasks = [self.analyze(p, days, subscription_id=subscription_id) for p in providers]
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
