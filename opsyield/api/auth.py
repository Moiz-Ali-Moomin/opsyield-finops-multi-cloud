from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..storage.database import get_db_session
from ..storage.repository import UserRepository, BaseRepository
from ..storage.models import Organization, User
from ..auth.models import UserLogin, UserCreate, Token, UserResponse
from ..auth.service import AuthService
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db_session)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(user_data.email)
    
    if not user or not AuthService.verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = AuthService.create_access_token(
        data={"sub": user.id, "org": user.organization_id, "role": user.role},
        expires_delta=timedelta(minutes=1440)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    user_repo = UserRepository(db)
    
    # Check if user exists
    if await user_repo.get_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Verify organization exists
    org_repo = BaseRepository(db, Organization)
    if not await org_repo.get_by_id(user_data.organization_id):
        raise HTTPException(status_code=400, detail="Organization not found")

    hashed_password = AuthService.get_password_hash(user_data.password)
    
    user_obj = {
        "email": user_data.email,
        "password_hash": hashed_password,
        "organization_id": user_data.organization_id,
        "role": "admin" # First user typically admin, could make configurable
    }
    
    new_user = await user_repo.create(user_obj)
    return new_user
