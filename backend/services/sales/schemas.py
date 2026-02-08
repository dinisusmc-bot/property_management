"""
Pydantic schemas for Sales Service
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime, time, date
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
    estimated_trip_date: Optional[Union[datetime, date, str]] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None

    @field_validator('estimated_trip_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        if isinstance(v, str):
            # Try parsing as date first (YYYY-MM-DD)
            try:
                parsed_date = datetime.strptime(v, '%Y-%m-%d')
                return parsed_date
            except ValueError:
                # Try parsing as datetime
                try:
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
                except ValueError:
                    return v  # Let pydantic handle the error
        return v

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
    estimated_trip_date: Optional[Union[datetime, date, str]] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    next_follow_up_date: Optional[Union[datetime, date, str]] = None
    priority: Optional[str] = None

    @field_validator('estimated_trip_date', 'next_follow_up_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
                except ValueError:
                    return v
        return v

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


# ==================== Phase 3: Sales & Lead Management Schemas ====================

# Follow-Up Schemas (Task 3.1)
class FollowUpTypeEnum(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    QUOTE = "quote"
    OTHER = "other"

class FollowUpOutcomeEnum(str, Enum):
    SUCCESSFUL = "successful"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    RESCHEDULED = "rescheduled"
    LOST = "lost"

class FollowUpCreate(BaseModel):
    """Schema for creating a follow-up task"""
    lead_id: int
    follow_up_type: FollowUpTypeEnum
    scheduled_date: datetime
    scheduled_time: Optional[time] = None
    notes: Optional[str] = None
    assigned_to: Optional[int] = None  # If not provided, assign to current user

class FollowUpUpdate(BaseModel):
    """Schema for updating a follow-up task"""
    follow_up_type: Optional[FollowUpTypeEnum] = None
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[time] = None
    notes: Optional[str] = None
    assigned_to: Optional[int] = None

class FollowUpComplete(BaseModel):
    """Schema for completing a follow-up task"""
    outcome: FollowUpOutcomeEnum
    notes: Optional[str] = None

class FollowUpResponse(BaseModel):
    """Schema for follow-up response"""
    id: int
    lead_id: int
    activity_id: Optional[int]
    follow_up_type: FollowUpTypeEnum
    scheduled_date: datetime
    scheduled_time: Optional[time]
    completed: bool
    completed_at: Optional[datetime]
    completed_by: Optional[int]
    outcome: Optional[FollowUpOutcomeEnum]
    notes: Optional[str]
    reminder_sent: bool
    assigned_to: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Lead Scoring Schemas (Task 3.2)
class ScoringRuleTypeEnum(str, Enum):
    ATTRIBUTE = "attribute"
    ACTIVITY = "activity"
    ENGAGEMENT = "engagement"

class LeadScoringRuleCreate(BaseModel):
    """Schema for creating a scoring rule"""
    rule_name: str = Field(..., min_length=1, max_length=100)
    rule_type: ScoringRuleTypeEnum
    description: Optional[str] = None
    attribute_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    points: int
    is_active: bool = True

class LeadScoringRuleUpdate(BaseModel):
    """Schema for updating a scoring rule"""
    rule_name: Optional[str] = None
    rule_type: Optional[ScoringRuleTypeEnum] = None
    description: Optional[str] = None
    attribute_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    points: Optional[int] = None
    is_active: Optional[bool] = None

class LeadScoringRuleResponse(BaseModel):
    """Schema for scoring rule response"""
    id: int
    rule_name: str
    rule_type: ScoringRuleTypeEnum
    description: Optional[str]
    attribute_field: Optional[str]
    condition_operator: Optional[str]
    condition_value: Optional[str]
    points: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class LeadScoreHistoryResponse(BaseModel):
    """Schema for score history response"""
    id: int
    lead_id: int
    old_score: int
    new_score: int
    reason: Optional[str]
    changed_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class LeadScoreCalculateRequest(BaseModel):
    """Request to recalculate lead score"""
    reason: Optional[str] = "Manual recalculation"

# Lead Transfer Schemas (Task 3.3)
class LeadTransferCreate(BaseModel):
    """Schema for transferring lead ownership"""
    to_agent_id: int
    reason: Optional[str] = None

class BulkLeadTransferCreate(BaseModel):
    """Schema for bulk lead transfer"""
    lead_ids: List[int]
    to_agent_id: int
    reason: Optional[str] = None

class LeadTransferResponse(BaseModel):
    """Schema for lead transfer response"""
    id: int
    lead_id: int
    from_user_id: int
    to_user_id: int
    transfer_reason: Optional[str]
    notes: Optional[str]
    transferred_by: int
    transferred_at: datetime

    class Config:
        from_attributes = True
