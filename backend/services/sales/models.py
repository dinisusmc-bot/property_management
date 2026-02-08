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
    __table_args__ = {'schema': 'sales'}

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
    
    # Phase 3 fields
    last_follow_up_date = Column(DateTime(timezone=True), nullable=True)
    score_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="lead", cascade="all, delete-orphan")
    score_history = relationship("LeadScoreHistory", back_populates="lead", cascade="all, delete-orphan")
    transfers = relationship("LeadTransfer", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.id}: {self.first_name} {self.last_name} - {self.status}>"


class LeadActivity(Base):
    """Lead activity log - tracks all interactions with a lead"""
    __tablename__ = "lead_activities"
    __table_args__ = {'schema': 'sales'}

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("sales.leads.id"), nullable=False, index=True)
    
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
    __table_args__ = {'schema': 'sales'}

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
    __table_args__ = {'schema': 'sales'}

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


# ==================== Phase 3: Sales & Lead Management ====================

class FollowUpType(str, enum.Enum):
    """Follow-up type enumeration"""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    QUOTE = "quote"
    OTHER = "other"


class FollowUpOutcome(str, enum.Enum):
    """Follow-up outcome enumeration"""
    SUCCESSFUL = "successful"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    RESCHEDULED = "rescheduled"
    LOST = "lost"


class FollowUp(Base):
    """Follow-up tasks for leads - Task 3.1"""
    __tablename__ = "follow_ups"
    __table_args__ = {'schema': 'sales'}

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("sales.leads.id"), nullable=False, index=True)
    activity_id = Column(Integer, ForeignKey("sales.lead_activities.id"), nullable=True)
    
    # Task details
    follow_up_type = Column(Enum(FollowUpType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    scheduled_date = Column(DateTime(timezone=False), nullable=False)  # DATE in SQL
    scheduled_time = Column(DateTime(timezone=False), nullable=True)   # TIME in SQL
    
    # Completion tracking
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(Integer, nullable=True)  # FK to auth service
    outcome = Column(Enum(FollowUpOutcome, values_callable=lambda x: [e.value for e in x]), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Reminders
    reminder_sent = Column(Boolean, default=False)
    
    # Assignment
    assigned_to = Column(Integer, nullable=False, index=True)  # FK to auth service
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="follow_ups")

    def __repr__(self):
        return f"<FollowUp {self.id}: {self.follow_up_type} for Lead {self.lead_id}>"


class ScoringRuleType(str, enum.Enum):
    """Lead scoring rule type"""
    ATTRIBUTE = "attribute"
    ACTIVITY = "activity"
    ENGAGEMENT = "engagement"


class LeadScoringRule(Base):
    """Configurable lead scoring rules - Task 3.2"""
    __tablename__ = "lead_scoring_rules"
    __table_args__ = {'schema': 'sales'}

    id = Column(Integer, primary_key=True, index=True)
    
    # Rule definition
    rule_name = Column(String(100), nullable=False, unique=True)
    rule_type = Column(Enum(ScoringRuleType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scoring logic
    attribute_field = Column(String(50), nullable=True)  # e.g., "estimated_passengers"
    condition_operator = Column(String(20), nullable=True)  # e.g., ">", ">=", "=="
    condition_value = Column(String(100), nullable=True)  # e.g., "50"
    points = Column(Integer, nullable=False)  # Points to add/subtract
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<LeadScoringRule {self.id}: {self.rule_name} ({self.points} pts)>"


class LeadScoreHistory(Base):
    """Audit trail of lead score changes - Task 3.2"""
    __tablename__ = "lead_score_history"
    __table_args__ = {'schema': 'sales'}

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("sales.leads.id"), nullable=False, index=True)
    
    # Score tracking
    old_score = Column(Integer, nullable=False)
    new_score = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)  # What triggered the change
    
    # Who made the change
    changed_by = Column(Integer, nullable=True)  # FK to auth service, NULL for automatic
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="score_history")

    def __repr__(self):
        return f"<LeadScoreHistory {self.id}: Lead {self.lead_id} {self.old_score} → {self.new_score}>"


class LeadTransfer(Base):
    """Lead ownership transfer history - Task 3.3"""
    __tablename__ = "lead_transfers"
    __table_args__ = {'schema': 'sales'}

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("sales.leads.id"), nullable=False, index=True)
    
    # Transfer details - match actual DB schema
    from_user_id = Column(Integer, nullable=False, index=True)  # FK to auth service
    to_user_id = Column(Integer, nullable=False, index=True)    # FK to auth service
    transfer_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Who initiated the transfer
    transferred_by = Column(Integer, nullable=False)  # FK to auth service
    
    # Timestamp - match actual DB schema
    transferred_at = Column(DateTime(timezone=False), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="transfers")

    def __repr__(self):
        return f"<LeadTransfer {self.id}: Lead {self.lead_id} from {self.from_user_id} to {self.to_user_id}>"
