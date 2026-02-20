import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..storage.repository import CostRepository, BaseRepository
from ..storage.models import Anomaly, Recommendation, Forecast
from ..anomaly.detection import AnomalyDetector
from ..forecasting.forecast import ForecastEngine
from ..recommendations.engine import RecommendationEngine

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, session: AsyncSession, organization_id: str):
        self.session = session
        self.organization_id = organization_id

    async def run_analytics_engines(self) -> Dict[str, Any]:
        """
        Runs all backend intelligence engines on schedule (usually called by collector).
        """
        logger.info(f"Running intelligence engines for org {self.organization_id}")
        
        # 1. Anomaly Detection
        detector = AnomalyDetector(self.session)
        new_anomalies = await detector.run_detection(self.organization_id)
        
        # 2. Forecast Generation
        forecaster = ForecastEngine(self.session)
        new_forecasts = await forecaster.generate_forecast(self.organization_id)
        
        # 3. Recommendations
        rec_engine = RecommendationEngine(self.session)
        new_recs = await rec_engine.evaluate_resources(self.organization_id)
        
        return {
            "anomalies_detected": len(new_anomalies),
            "forecasts_generated": len(new_forecasts),
            "recommendations_found": len(new_recs),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Aggregates all data necessary for the unified dashboard from the DB.
        Replaces the old real-time aggregator.
        """
        cost_repo = CostRepository(self.session)
        
        # Costs
        daily_trends = await cost_repo.get_aggregated_costs(self.organization_id, days=days)
        cost_drivers = await cost_repo.get_cost_drivers(self.organization_id, days=days)
        total_cost = sum(d["amount"] for d in daily_trends)
        
        # Analytics Entities
        anomaly_repo = BaseRepository(self.session, Anomaly)
        rec_repo = BaseRepository(self.session, Recommendation)
        fast_repo = BaseRepository(self.session, Forecast)
        
        anomalies = await anomaly_repo.get_all(limit=10) # Simplified
        recommendations = await rec_repo.get_all(limit=10)
        
        # Simple risk score heuristic based on anomalies and optimizations
        risk_score = min(100, len(anomalies) * 5 + len(recommendations) * 2)

        return {
            "meta": {
                "period": f"{days} days",
                "generated_at": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_cost": total_cost,
                "risk_score": risk_score,
                "currency": "USD"
            },
            "executive_summary": {
                "total_spend": total_cost,
                "risk_score": risk_score,
                "anomaly_count": len(anomalies),
                "active_recommendations": len(recommendations)
            },
            "daily_trends": daily_trends,
            "cost_drivers": cost_drivers,
            "anomalies": anomalies,
            "recommendations": recommendations
        }
