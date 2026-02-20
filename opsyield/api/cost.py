from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..storage.database import get_db_session
from ..storage.repository import CostRepository, BaseRepository
from ..storage.models import CostSnapshot, Anomaly, Recommendation, Forecast
from ..auth.middleware import get_current_organization
from ..cache.redis import RedisCache

router = APIRouter(prefix="/api/cost", tags=["cost"])

@router.get("/summary")
async def get_cost_summary(
    days: int = 30,
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    cache_key = f"cost_summary_{org_id}_{days}"
    
    async def fetch_summary():
        repo = CostRepository(db)
        history = await repo.get_aggregated_costs(org_id, days=days)
        total_cost = sum(item["amount"] for item in history)
        
        drivers = await repo.get_cost_drivers(org_id, days=days)
        
        return {
            "total_cost": total_cost,
            "days": days,
            "cost_drivers": drivers,
            "currency": "USD" # Assuming USD for now
        }
        
    return await RedisCache.cache_wrapper(cache_key, fetch_summary, ttl=3600)

@router.get("/history")
async def get_cost_history(
    days: int = 30,
    provider: str = None,
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    cache_key = f"cost_history_{org_id}_{days}_{provider or 'all'}"
    
    async def fetch_history():
        repo = CostRepository(db)
        return await repo.get_aggregated_costs(org_id, days=days, provider=provider)
        
    return await RedisCache.cache_wrapper(cache_key, fetch_history, ttl=3600)

@router.get("/anomalies")
async def list_anomalies(
    status: str = "open",
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    repo = BaseRepository(db, Anomaly)
    stmt = select(Anomaly).where(Anomaly.organization_id == org_id, Anomaly.resolved == (status == "resolved")).order_by(Anomaly.detected_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/forecast")
async def get_forecasts(
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    repo = BaseRepository(db, Forecast)
    # Only get future forecasts
    stmt = select(Forecast).where(
        Forecast.organization_id == org_id,
        Forecast.forecast_date >= datetime.utcnow()
    ).order_by(Forecast.forecast_date.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/recommendations")
async def list_recommendations(
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Recommendation).where(
        Recommendation.organization_id == org_id,
        Recommendation.status == "open"
    ).order_by(Recommendation.potential_savings.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
