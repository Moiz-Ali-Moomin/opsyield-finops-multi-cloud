from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
import json
from ..storage.database import get_db_session
from ..storage.repository import CloudAccountRepository
from ..auth.middleware import get_current_organization, require_admin
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/cloud", tags=["cloud-accounts"])

class AccountAdd(BaseModel):
    provider: str # aws, gcp, azure
    account_id: str
    name: Optional[str] = None
    credentials: dict # Dict format of JSON securely stored

class AccountResponse(BaseModel):
    id: str
    provider: str
    account_id: str
    name: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

@router.post("/accounts/add", response_model=AccountResponse, dependencies=[Depends(require_admin)])
async def add_cloud_account(
    account: AccountAdd, 
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    repo = CloudAccountRepository(db)
    
    # Store credentials securely (could encrypt here)
    creds_json = json.dumps(account.credentials)
    
    new_account = {
        "organization_id": org_id,
        "provider": account.provider.lower(),
        "account_id": account.account_id,
        "name": account.name,
        "credentials_json": creds_json,
        "is_active": True
    }
    
    saved_account = await repo.create(new_account)
    return saved_account

@router.get("/accounts", response_model=List[AccountResponse])
async def list_cloud_accounts(
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    repo = CloudAccountRepository(db)
    accounts = await repo.get_by_organization(org_id)
    return accounts

@router.delete("/accounts/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_cloud_account(
    id: str,
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db_session)
):
    repo = CloudAccountRepository(db)
    # Check ownership
    account = await repo.get_by_id(id)
    if not account or account.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Account not found")
        
    await repo.delete(id)
    return None
