from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str
    organization_id: str
    role: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    organization_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OrganizationCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    organization_id: str
    role: str

    class Config:
        from_attributes = True

class OrganizationResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True
