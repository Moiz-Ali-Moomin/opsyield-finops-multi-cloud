from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .service import AuthService
from .models import TokenData

# OAuth2 scheme for Swagger UI and token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Middleware dependency to extract and validate the JWT token.
    Raises HTTPException if the token is invalid or missing.
    """
    token_data = AuthService.decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

async def get_current_organization(token_data: TokenData = Depends(get_current_user_token)) -> str:
    """
    Middleware dependency to return the organization_id from the valid token.
    Used to scope all database queries automatically.
    """
    return token_data.organization_id

async def require_admin(token_data: TokenData = Depends(get_current_user_token)):
    """
    Middleware dependency to ensure the user is an admin for their organization.
    """
    if token_data.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return token_data
