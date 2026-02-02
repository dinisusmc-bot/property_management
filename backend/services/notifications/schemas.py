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
