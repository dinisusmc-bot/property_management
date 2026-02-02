"""
Database models for Sales Service
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class LeadStatus(str, enum.Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    DEAD = "dead"

class LeadSource(str, enum.Enum):
    """Lead source enumeration"""
    WEB = "web"
    PHONE = "phone"
    EMAIL = "email"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    PARTNER = "partner"

class ActivityType(str, enum.Enum):
    """Activity type enumeration"""
    CALL = "call"
    EMAIL = "email"
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    MEETING = "meeting"

class Lead(Base):
    """Lead model - represents potential business before charter creation"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Lead identification
    source = Column(Enum(LeadSource), nullable=False, default=LeadSource.WEB)
    status = Column(Enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True)
    
    # Contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    company_name = Column(String(255), nullable=True)
    
    # Trip details (rough information)
    trip_details = Column(Text, nullable=True)  # JSON string
    estimated_passengers = Column(Integer, nullable=True)
    estimated_trip_date = Column(DateTime(timezone=True), nullable=True)
    pickup_location = Column(String(500), nullable=True)
    dropoff_location = Column(String(500), nullable=True)
    
    # Assignment
    assigned_agent_id = Column(Integer, nullable=True, index=True)  # FK to auth service
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Conversion tracking
    converted_to_client_id = Column(Integer, nullable=True)  # FK to client service
    converted_to_charter_id = Column(Integer, nullable=True)  # FK to charter service
    converted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scoring (for future use)
    score = Column(Integer, default=0)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Follow-up tracking
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.id}: {self.first_name} {self.last_name} - {self.status}>"


class LeadActivity(Base):
    """Lead activity log - tracks all interactions with a lead"""
    __tablename__ = "lead_activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False)
    subject = Column(String(255), nullable=True)
    details = Column(Text, nullable=False)
    
    # Who performed the activity
    performed_by = Column(Integer, nullable=False)  # FK to auth service user_id
    
    # Metadata
    duration_minutes = Column(Integer, nullable=True)  # For calls/meetings
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")

    def __repr__(self):
        return f"<LeadActivity {self.id}: {self.activity_type} on Lead {self.lead_id}>"


class AssignmentRule(Base):
    """Assignment rule for round-robin lead distribution"""
    __tablename__ = "assignment_rules"

    id = Column(Integer, primary_key=True, index=True)
    
    # Agent identification
    agent_id = Column(Integer, nullable=False, unique=True, index=True)  # FK to auth service
    agent_name = Column(String(255), nullable=False)  # Cached for performance
    
    # Rule configuration
    is_active = Column(Boolean, default=True, index=True)
    weight = Column(Integer, default=1)  # For weighted distribution (1 = normal)
    max_leads_per_day = Column(Integer, default=10)
    
    # Tracking
    total_leads_assigned = Column(Integer, default=0)
    last_assigned_at = Column(DateTime(timezone=True), nullable=True, index=True)
    leads_assigned_today = Column(Integer, default=0)
    last_reset_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AssignmentRule agent={self.agent_id} active={self.is_active}>"


class EmailPreference(Base):
    """Email preferences for clients - controls automated emails"""
    __tablename__ = "email_preferences"

    id = Column(Integer, primary_key=True, index=True)
    
    # Client identification
    client_id = Column(Integer, nullable=False, unique=True, index=True)  # FK to client service
    
    # Preferences
    automated_emails_enabled = Column(Boolean, default=True)
    marketing_emails_enabled = Column(Boolean, default=True)
    reminder_emails_enabled = Column(Boolean, default=True)
    quote_emails_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EmailPreference client={self.client_id}>"
