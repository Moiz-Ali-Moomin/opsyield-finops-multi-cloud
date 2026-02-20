import logging
import numpy as np
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..storage.models import CostSnapshot, Forecast
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class ForecastEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_forecast(self, organization_id: str, days_ahead: int = 30) -> List[Forecast]:
        """Generates simple moving-average cost forecasts for future dates."""
        start_date = datetime.utcnow() - timedelta(days=60) # use 60 days of history
        
        # Aggregate daily total cost for the org
        result = await self.session.execute(
            select(
                func.date(CostSnapshot.timestamp).label("date"),
                func.sum(CostSnapshot.cost).label("total")
            )
            .where(
                CostSnapshot.organization_id == organization_id,
                CostSnapshot.timestamp >= start_date
            )
            .group_by(func.date(CostSnapshot.timestamp))
            .order_by(func.date(CostSnapshot.timestamp))
        )
        
        daily_totals = [float(row.total) for row in result.all()]
        
        if not daily_totals:
            return []
            
        # Very simple moving average
        recent_average = np.mean(daily_totals[-14:]) if len(daily_totals) >= 14 else np.mean(daily_totals)
        std_dev = np.std(daily_totals[-14:]) if len(daily_totals) >= 14 else 0
        
        forecasts = []
        last_date = datetime.utcnow()
        
        for i in range(1, days_ahead + 1):
            target_date = last_date + timedelta(days=i)
            # Add some linear noise or simple projection here if desired
            predicted = recent_average
            
            f = Forecast(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                forecast_date=target_date,
                predicted_cost=float(predicted),
                lower_bound=float(max(0, predicted - std_dev)),
                upper_bound=float(predicted + std_dev)
            )
            self.session.add(f)
            forecasts.append(f)
            
        await self.session.commit()
        return forecasts
