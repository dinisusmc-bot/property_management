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


# ============================================================================
# Phase 7: SMS Preferences Model
# ============================================================================

class SMSPreference(Base):
    """SMS preferences and opt-out tracking"""
    __tablename__ = "sms_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    opted_out = Column(Boolean, default=False, index=True)
    opted_out_at = Column(DateTime)
    opt_out_reason = Column(String(255))
    preferences = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Phase 7: Email Tracking Model
# ============================================================================

class EmailTracking(Base):
    """Email open and click tracking"""
    __tablename__ = "email_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    email_log_id = Column(Integer)  # FK to email_logs table
    tracking_token = Column(String(255), unique=True, nullable=False, index=True)
    opened = Column(Boolean, default=False, index=True)
    opened_at = Column(DateTime)
    open_count = Column(Integer, default=0)
    clicked = Column(Boolean, default=False, index=True)
    clicked_at = Column(DateTime)
    click_count = Column(Integer, default=0)
    user_agent = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
