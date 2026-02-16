from typing import Dict, Any, List

class RiskEngine:
    """
    Computes financial risk scores and generates executive summary.
    """

    def compute_risk_score(self, summary_data: Dict[str, Any]) -> float:
        """
        0-100 Score. Higher is worse.
        Weighted factors:
        - Waste % (30%)
        - Anomaly Count (20%)
        - Governance Violations (30%)
        - Forecast Trend (20%)
        """
        score = 0.0
        
        waste_pct = summary_data.get("waste_percentage", 0)
        score += min(waste_pct, 100) * 0.3

        anomalies = summary_data.get("anomaly_count", 0)
        score += min(anomalies * 5, 100) * 0.2 # 5 points per anomaly, max 20% impact

        violations = summary_data.get("governance_violations", 0)
        score += min(violations * 10, 100) * 0.3 # 10 points per violation, max 30% impact

        forecast_trend = summary_data.get("forecast_trend_percent", 0)
        if forecast_trend > 0:
            score += min(forecast_trend, 100) * 0.2

        return round(score, 2)

    def generate_executive_summary(self, 
                                   total_cost: float,
                                   optimization_potential: float,
                                   anomalies: List[Dict],
                                   violations: List[Dict],
                                   forecast: Dict,
                                   trends: Dict) -> Dict[str, Any]:
        
        waste_pct = (optimization_potential / total_cost * 100) if total_cost > 0 else 0
        anomaly_count = len(anomalies)
        violation_count = len(violations)
        
        summary = {
            "total_spend": round(total_cost, 2),
            "waste_percentage": round(waste_pct, 2),
            "optimization_potential": round(optimization_potential, 2),
            "anomaly_count": anomaly_count,
            "governance_violations": violation_count,
            "forecast_risk_level": "High" if trends.get("trend_percent", 0) > 20 else "Low",
            "forecast_trend_percent": trends.get("trend_percent", 0),
            "unallocated_cost_percentage": 0.0 # Placeholder
        }

        risk_score = self.compute_risk_score(summary)
        summary["risk_score"] = risk_score
        summary["exposure_category"] = "CRITICAL" if risk_score > 75 else "HIGH" if risk_score > 50 else "MODERATE" if risk_score > 25 else "LOW"

        return summary
