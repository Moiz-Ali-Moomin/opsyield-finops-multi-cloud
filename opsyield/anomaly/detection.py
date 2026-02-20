import logging
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..storage.models import CostSnapshot, Anomaly
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_detection(self, organization_id: str, days_lookback: int = 14) -> List[Anomaly]:
        """Runs anomaly detection for the entire org based on historical z-scores."""
        start_date = datetime.utcnow() - timedelta(days=days_lookback)
        
        # Group costs by service and date
        result = await self.session.execute(
            select(CostSnapshot.service, CostSnapshot.timestamp, CostSnapshot.cost)
            .where(
                CostSnapshot.organization_id == organization_id,
                CostSnapshot.timestamp >= start_date
            )
            .order_by(CostSnapshot.timestamp)
        )
        data = result.all()
        
        service_history: Dict[str, List[float]] = {}
        for row in data:
            if row.service not in service_history:
                service_history[row.service] = []
            service_history[row.service].append(row.cost)

        new_anomalies = []
        
        for service, costs in service_history.items():
            if len(costs) < 7:
                continue # Need at least 7 data points
                
            historical = costs[:-1]
            latest = costs[-1]
            
            mean = np.mean(historical)
            std = np.std(historical)
            
            if std == 0:
                continue
                
            z_score = (latest - mean) / std
            
            if z_score > 3.0: # 3 standard deviations
                deviation_percent = ((latest - mean) / mean) * 100 if mean > 0 else 100.0
                severity = "critical" if z_score > 5.0 else "high" if z_score > 4.0 else "medium"
                
                anomaly = Anomaly(
                    id=str(uuid.uuid4()),
                    organization_id=organization_id,
                    provider="unknown", # Might need to group by provider too
                    service=service,
                    expected_cost=float(mean),
                    actual_cost=float(latest),
                    deviation_percent=float(deviation_percent),
                    severity=severity,
                    description=f"Cost spike detected in {service}: {latest:.2f} vs expected {mean:.2f}"
                )
                
                self.session.add(anomaly)
                new_anomalies.append(anomaly)
                logger.warning(anomaly.description)
                
        if new_anomalies:
            await self.session.commit()
            
        return new_anomalies
