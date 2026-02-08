from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from models import NotificationType, NotificationStatus, NotificationPriority

class NotificationCreate(BaseModel):
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    notification_type: NotificationType
    template_name: str
    template_data: Dict[str, Any] = {}
    priority: NotificationPriority = NotificationPriority.MEDIUM
    charter_id: Optional[int] = None
    client_id: Optional[int] = None
    payment_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    recipient_email: Optional[str]
    recipient_phone: Optional[str]
    notification_type: NotificationType
    template_name: str
    status: NotificationStatus
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TemplateCreate(BaseModel):
    name: str
    notification_type: NotificationType
    email_subject: Optional[str] = None
    email_body_html: Optional[str] = None
    email_body_text: Optional[str] = None
    sms_body: Optional[str] = None
    description: Optional[str] = None

class TemplateResponse(BaseModel):
    id: int
    name: str
    notification_type: NotificationType
    email_subject: Optional[str]
    sms_body: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Phase 7: SMS Preferences Schemas
# ============================================================================

class SMSOptOutRequest(BaseModel):
    phone_number: str
    reason: Optional[str] = "User request"


class SMSOptInRequest(BaseModel):
    phone_number: str


class SMSOptOutResponse(BaseModel):
    phone_number: str
    opted_out: bool
    message: str


class SMSOptStatusResponse(BaseModel):
    phone_number: str
    opted_out: bool
    opted_out_at: Optional[str] = None
    reason: Optional[str] = None


# ============================================================================
# Phase 7: Email Tracking Schemas
# ============================================================================

class EmailTrackingStats(BaseModel):
    """Schema for email tracking statistics"""
    total_emails: int
    opened: int
    clicked: int
    open_rate: float
    click_rate: float


class EmailTrackingResponse(BaseModel):
    """Schema for email tracking response"""
    tracking_token: str
    opened: bool
    opened_at: Optional[str] = None
    open_count: int
    clicked: bool
    clicked_at: Optional[str] = None
    click_count: int
