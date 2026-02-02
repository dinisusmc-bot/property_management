"""
Pydantic schemas for Auth Service
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str

class AdminPasswordChange(BaseModel):
    """Schema for admin changing user password"""
    new_password: str

class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_superuser: bool
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token schema"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data schema"""
    email: Optional[str] = None
