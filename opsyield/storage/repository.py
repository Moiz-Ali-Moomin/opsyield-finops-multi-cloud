from typing import List, Optional, Type, TypeVar, Any, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from .models import Base, Organization, User, CloudAccount, CostSnapshot, Anomaly, Recommendation

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository:
    """Base repository for generic CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        db_obj = await self.get_by_id(id)
        if db_obj:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            self.session.add(db_obj)
            await self.session.flush()
            await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: str) -> bool:
        db_obj = await self.get_by_id(id)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.flush()
            return True
        return False

class CostRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CostSnapshot)

    async def get_aggregated_costs(
        self, organization_id: str, days: int = 30, provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch aggregated daily costs over a period for an organization."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            func.date(self.model.timestamp).label("date"),
            func.sum(self.model.cost).label("total_cost")
        ).where(
            self.model.organization_id == organization_id,
            self.model.timestamp >= start_date
        )
        
        if provider:
            query = query.where(self.model.provider == provider)
            
        query = query.group_by(func.date(self.model.timestamp)).order_by(func.date(self.model.timestamp))
        
        result = await self.session.execute(query)
        rows = result.all()
        return [{"date": str(row.date), "amount": row.total_cost} for row in rows]

    async def get_cost_drivers(self, organization_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get top spending services."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            self.model.service,
            func.sum(self.model.cost).label("total_cost")
        ).where(
            self.model.organization_id == organization_id,
            self.model.timestamp >= start_date
        ).group_by(
            self.model.service
        ).order_by(
            desc("total_cost")
        ).limit(10)
        
        result = await self.session.execute(query)
        return [{"service": row.service, "cost": row.total_cost} for row in result.all()]

class CloudAccountRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CloudAccount)

    async def get_by_organization(self, organization_id: str) -> List[CloudAccount]:
        result = await self.session.execute(
            select(self.model).where(
                self.model.organization_id == organization_id,
                self.model.is_active == True
            )
        )
        return result.scalars().all()

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
        
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(self.model).where(self.model.email == email))
        return result.scalars().first()
