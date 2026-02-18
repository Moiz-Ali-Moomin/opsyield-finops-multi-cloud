
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
        self.risk = RiskEngine()
        self.optimization = OptimizationEngine()
        
        from ..watchers.idle import IdleWatcher
        from ..watchers.cost import CostSpikeWatcher
        from ..watchers.security import SecurityWatcher
        
        self.watchers = [
            IdleWatcher(),
            CostSpikeWatcher(),
            SecurityWatcher()
        ]

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
        
        # 1.5 Fetch Utilization Metrics
        try:
            resources = await provider.get_utilization_metrics(resources, period_days=7)
        except Exception as e:
            logger.warning(f"Failed to fetch metrics: {e}")

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
        
        for r in resources:
            resource_types[r.type] += 1
            state = (r.state or "").lower()
            if "running" in state:
                running_count += 1

        # 6. Run Watchers
        watcher_findings = []
        for w in self.watchers:
             try:
                 findings = w.watch(resources, costs)
                 watcher_findings.extend(findings)
             except Exception as e:
                 logger.error(f"Watcher {type(w).__name__} failed: {e}")
        
        # Integrate Watcher findings into result
        # We can put them in anomalies or executive summary
        waste_findings = [f for f in watcher_findings if f["type"] == "idle_resource"]
        security_findings = [f for f in watcher_findings if f["type"] == "security_risk"]
        cost_findings = [f for f in watcher_findings if f["type"] == "cost_spike"]
        
        # Backward compatibility for idle_resources list in AnalysisResult
        idle_resources = []
        for f in waste_findings:
             idle_resources.append({
                 "id": f.get("resource_id", "unknown"),
                 "name": f.get("name", "unknown"),
                 "type": "unknown", # Watcher might not preserve all details in finding, need to lookup?
                 # Actually, let's just pass what we have. The UI likely expects specific fields.
                 # Watcher findings: resource_id, name, score, reasons, cost_30d
                 "idle_score": f.get("score"),
                 "cost_30d": f.get("cost_30d"),
                 "reasons": f.get("reasons"),
                 "currency": "USD" # Default
             })
             # To get more details (type, region), we could look up in `resources` list
             # but this is O(N*M). For now, let's keep it simple or do a lookup map.
        
        # Optimization: Build resource map for fast lookup
        r_map = {r.id: r for r in resources}
        for ir in idle_resources:
            r = r_map.get(ir["id"])
            if r:
                ir["type"] = r.type
                ir["region"] = r.region
                ir["state"] = r.state
                ir["currency"] = r.currency

        # Merge with analytics results for backward compatibility
        all_anomalies = analytics_results.get("anomalies", []) + cost_findings

        # Logic for high cost resources...

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

        # Merged Results
        # Integrate Intelligence Engines
        from ..intelligence.engines import ComparisonEngine, ForecastEngine
        
        comparison_engine = ComparisonEngine()
        forecast_engine = ForecastEngine()
        
        comparison = comparison_engine.compare_providers(valid_results)
        forecast = forecast_engine.forecast_spend(agg_daily_trends, days_ahead=days)

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
                "comparison": comparison,
                "anomaly_count": len(all_anomalies),
                "governance_violations": len(all_violations)
            },
            trends={
                "period_total": total_cost, 
                "trend_percent": 0.0,
                "forecast": forecast
            }, 
            daily_trends=agg_daily_trends,
            anomalies=all_anomalies,
            forecast=forecast,
            governance_issues=all_violations,
            optimizations=all_optimizations,
            resources=all_resources
        )
