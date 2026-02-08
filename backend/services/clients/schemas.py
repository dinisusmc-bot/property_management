"""
Pydantic schemas for Client Service
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

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
    payment_terms: Optional[str] = "net_30"
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
    payment_terms: Optional[str] = None
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


# ============================================================================
# PHASE 4 TASK 4.2: Certificate of Insurance (COI) Tracking
# ============================================================================

class ClientInsuranceBase(BaseModel):
    """Base insurance schema"""
    policy_type: str  # general_liability, auto, workers_comp, umbrella, other
    insurance_company: str
    policy_number: str
    coverage_amount: Decimal
    effective_date: date
    expiration_date: date
    certificate_holder: Optional[str] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None


class ClientInsuranceCreate(ClientInsuranceBase):
    """Schema for creating insurance"""
    client_id: int


class ClientInsuranceUpdate(BaseModel):
    """Schema for updating insurance"""
    policy_type: Optional[str] = None
    insurance_company: Optional[str] = None
    policy_number: Optional[str] = None
    coverage_amount: Optional[Decimal] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_holder: Optional[str] = None
    document_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ClientInsuranceResponse(ClientInsuranceBase):
    """Schema for insurance response"""
    id: int
    client_id: int
    status: str
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InsuranceVerificationCreate(BaseModel):
    """Schema for creating insurance verification"""
    status: str  # approved, rejected, needs_update
    notes: Optional[str] = None


class InsuranceVerificationResponse(BaseModel):
    """Schema for verification response"""
    id: int
    insurance_id: int
    verified_by: int
    verification_date: datetime
    status: str
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
