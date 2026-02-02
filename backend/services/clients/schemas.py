"""
Pydantic schemas for Client Service
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Contact schemas
class ContactBase(BaseModel):
    """Base contact schema"""
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None

class ContactCreate(ContactBase):
    """Schema for creating a contact"""
    pass

class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None

class ContactResponse(ContactBase):
    """Schema for contact response"""
    id: int
    client_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Client schemas
class ClientBase(BaseModel):
    """Base client schema"""
    name: str
    type: str  # corporate, personal, government, nonprofit
    email: EmailStr
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    """Schema for creating a client"""
    credit_limit: float = 0.0

class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = None
    type: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    credit_limit: Optional[float] = None
    balance_owed: Optional[float] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class ClientResponse(ClientBase):
    """Schema for client response"""
    id: int
    credit_limit: float
    balance_owed: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    contacts: List[ContactResponse] = []
    
    class Config:
        from_attributes = True
