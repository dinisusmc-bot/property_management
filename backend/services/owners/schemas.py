"""
Pydantic schemas for Owners API
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


class OwnerBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None


class OwnerCreate(OwnerBase):
    tax_id: Optional[str] = Field(None, description="Encrypted EIN/SSN")


class OwnerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class OwnerResponse(OwnerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OwnerNoteBase(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)
    is_private: bool = True


class OwnerNoteCreate(OwnerNoteBase):
    pass


class OwnerNoteResponse(OwnerNoteBase):
    id: int
    owner_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
