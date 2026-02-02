from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum as SQLEnum
from datetime import datetime
from database import Base
import enum

class NotificationType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient info
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    recipient_name = Column(String(255))
    
    # Notification details
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    template_name = Column(String(100), nullable=False)
    subject = Column(String(500))
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Content (JSON string with template variables)
    template_data = Column(Text)
    
    # Status tracking
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # External IDs (from SendGrid/Twilio)
    sendgrid_message_id = Column(String(255))
    twilio_message_sid = Column(String(255))
    
    # Related entity
    charter_id = Column(Integer)
    client_id = Column(Integer)
    payment_id = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    failed_at = Column(DateTime)
    next_retry_at = Column(DateTime)

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    
    # Email template
    email_subject = Column(String(500))
    email_body_html = Column(Text)
    email_body_text = Column(Text)
    
    # SMS template
    sms_body = Column(Text)
    
    # Metadata
    description = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
