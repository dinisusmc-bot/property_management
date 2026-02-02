"""
Pydantic schemas for Sales Service
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class LeadStatusEnum(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    DEAD = "dead"

class LeadSourceEnum(str, Enum):
    WEB = "web"
    PHONE = "phone"
    EMAIL = "email"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    PARTNER = "partner"

class ActivityTypeEnum(str, Enum):
    CALL = "call"
    EMAIL = "email"
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    MEETING = "meeting"

# Lead Schemas
class LeadBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    company_name: Optional[str] = None
    source: LeadSourceEnum = LeadSourceEnum.WEB
    trip_details: Optional[str] = None
    estimated_passengers: Optional[int] = None
    estimated_trip_date: Optional[datetime] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None

class LeadCreate(LeadBase):
    """Schema for creating a new lead"""
    pass

class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    status: Optional[LeadStatusEnum] = None
    trip_details: Optional[str] = None
    estimated_passengers: Optional[int] = None
    estimated_trip_date: Optional[datetime] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None
    priority: Optional[str] = None

class LeadResponse(LeadBase):
    """Schema for lead response"""
    id: int
    status: LeadStatusEnum
    assigned_agent_id: Optional[int]
    assigned_at: Optional[datetime]
    converted_to_client_id: Optional[int]
    converted_to_charter_id: Optional[int]
    converted_at: Optional[datetime]
    score: int
    priority: str
    next_follow_up_date: Optional[datetime]
    follow_up_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Lead Activity Schemas
class LeadActivityBase(BaseModel):
    activity_type: ActivityTypeEnum
    subject: Optional[str] = None
    details: str = Field(..., min_length=1)
    duration_minutes: Optional[int] = None

class LeadActivityCreate(LeadActivityBase):
    """Schema for creating a lead activity"""
    pass

class LeadActivityResponse(LeadActivityBase):
    """Schema for lead activity response"""
    id: int
    lead_id: int
    performed_by: int
    created_at: datetime

    class Config:
        from_attributes = True

# Assignment Rule Schemas
class AssignmentRuleBase(BaseModel):
    agent_id: int
    agent_name: str
    is_active: bool = True
    weight: int = 1
    max_leads_per_day: int = 10

class AssignmentRuleCreate(AssignmentRuleBase):
    """Schema for creating an assignment rule"""
    pass

class AssignmentRuleUpdate(BaseModel):
    """Schema for updating an assignment rule"""
    is_active: Optional[bool] = None
    weight: Optional[int] = None
    max_leads_per_day: Optional[int] = None

class AssignmentRuleResponse(AssignmentRuleBase):
    """Schema for assignment rule response"""
    id: int
    total_leads_assigned: int
    last_assigned_at: Optional[datetime]
    leads_assigned_today: int
    last_reset_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Conversion Schema
class LeadConversionRequest(BaseModel):
    """Schema for lead to charter conversion"""
    create_client: bool = True
    create_charter: bool = True

class LeadConversionResponse(BaseModel):
    """Schema for conversion response"""
    success: bool
    lead_id: int
    client_id: Optional[int] = None
    charter_id: Optional[int] = None
    message: str

# Email Preference Schemas
class EmailPreferenceUpdate(BaseModel):
    """Schema for updating email preferences"""
    automated_emails_enabled: Optional[bool] = None
    marketing_emails_enabled: Optional[bool] = None
    reminder_emails_enabled: Optional[bool] = None
    quote_emails_enabled: Optional[bool] = None

class EmailPreferenceResponse(BaseModel):
    """Schema for email preference response"""
    id: int
    client_id: int
    automated_emails_enabled: bool
    marketing_emails_enabled: bool
    reminder_emails_enabled: bool
    quote_emails_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
