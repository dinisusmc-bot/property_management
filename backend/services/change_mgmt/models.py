"""
Database Models for Change Management Service

Stores change cases, workflow history, approvals, and audit trails.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey, Index, Numeric, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from database import Base


class ChangeType(str, enum.Enum):
    """Types of changes that can be requested"""
    ITINERARY_MODIFICATION = "itinerary_modification"
    PASSENGER_COUNT_CHANGE = "passenger_count_change"
    VEHICLE_CHANGE = "vehicle_change"
    DATE_TIME_CHANGE = "date_time_change"
    PICKUP_LOCATION_CHANGE = "pickup_location_change"
    DESTINATION_CHANGE = "destination_change"
    AMENITY_ADDITION = "amenity_addition"
    AMENITY_REMOVAL = "amenity_removal"
    CANCELLATION = "cancellation"
    PRICING_ADJUSTMENT = "pricing_adjustment"
    OTHER = "other"


class ChangeStatus(str, enum.Enum):
    """Workflow states for change cases"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    CANCELLED = "cancelled"


class ChangePriority(str, enum.Enum):
    """Priority levels for changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ImpactLevel(str, enum.Enum):
    """Impact assessment levels"""
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    MAJOR = "major"


class ChangeCase(Base):
    """
    Main change case tracking.
    Represents a requested change to a charter with workflow management.
    """
    __tablename__ = "change_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)  # e.g., CHG-2026-0001
    
    # Related entities
    charter_id = Column(Integer, nullable=False, index=True)
    client_id = Column(Integer, nullable=True)
    vendor_id = Column(Integer, nullable=True)
    
    # Change details
    change_type = Column(SQLEnum(ChangeType), nullable=False, index=True)
    priority = Column(SQLEnum(ChangePriority), default=ChangePriority.MEDIUM, index=True)
    status = Column(SQLEnum(ChangeStatus), default=ChangeStatus.PENDING, nullable=False, index=True)
    
    # Request information
    requested_by = Column(Integer, nullable=False)  # User ID
    requested_by_name = Column(String(200), nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Change description
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)  # Why is this change needed?
    
    # Impact assessment
    impact_level = Column(SQLEnum(ImpactLevel), nullable=True)
    impact_assessment = Column(Text, nullable=True)  # Detailed impact description
    affects_vendor = Column(Boolean, default=False)
    affects_pricing = Column(Boolean, default=False)
    affects_schedule = Column(Boolean, default=False)
    
    # Financial impact
    current_price = Column(Numeric(10, 2), nullable=True)
    proposed_price = Column(Numeric(10, 2), nullable=True)
    price_difference = Column(Numeric(10, 2), nullable=True)
    
    # Proposed changes (JSON with before/after values)
    proposed_changes = Column(JSON, nullable=True)  # {"field": {"old": "value", "new": "value"}}
    
    # Approval workflow
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(Integer, nullable=True)  # User ID
    approved_by_name = Column(String(200), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    rejected_by = Column(Integer, nullable=True)  # User ID
    rejected_by_name = Column(String(200), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Implementation
    implemented_by = Column(Integer, nullable=True)  # User ID
    implemented_by_name = Column(String(200), nullable=True)
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    implementation_notes = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # ["urgent", "pricing", etc.]
    attachments = Column(JSON, nullable=True)  # List of document references
    related_change_cases = Column(JSON, nullable=True)  # List of related case IDs
    
    # Tracking
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChangeHistory(Base):
    """
    Audit trail for change cases.
    Records every action and state transition.
    """
    __tablename__ = "change_history"
    
    id = Column(Integer, primary_key=True, index=True)
    change_case_id = Column(Integer, ForeignKey("change_cases.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # created, updated, approved, rejected, etc.
    action_by = Column(Integer, nullable=False)  # User ID
    action_by_name = Column(String(200), nullable=True)
    action_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # State transition
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    
    # Details
    notes = Column(Text, nullable=True)
    field_changes = Column(JSON, nullable=True)  # What fields were modified
    system_generated = Column(Boolean, default=False)  # Auto vs manual action
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChangeApproval(Base):
    """
    Multi-level approval tracking.
    Supports multiple approvers for complex changes.
    """
    __tablename__ = "change_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    change_case_id = Column(Integer, ForeignKey("change_cases.id"), nullable=False, index=True)
    
    # Approver
    approver_id = Column(Integer, nullable=False, index=True)
    approver_name = Column(String(200), nullable=True)
    approver_role = Column(String(50), nullable=True)  # manager, admin, finance, etc.
    
    # Approval details
    approval_level = Column(Integer, default=1)  # For multi-level approvals
    required = Column(Boolean, default=True)  # Is this approval required?
    
    # Status
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected
    decision = Column(String(50), nullable=True)  # approve, reject, request_changes
    notes = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)  # Any conditions for approval
    
    # Timestamps
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ChangeNotification(Base):
    """
    Track notifications sent for change cases.
    """
    __tablename__ = "change_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    change_case_id = Column(Integer, ForeignKey("change_cases.id"), nullable=False, index=True)
    
    # Recipient
    recipient_id = Column(Integer, nullable=False)
    recipient_email = Column(String(255), nullable=True)
    recipient_type = Column(String(50), nullable=True)  # client, vendor, admin, approver
    
    # Notification details
    notification_type = Column(String(100), nullable=False)  # change_requested, approved, rejected, etc.
    notification_method = Column(String(50), nullable=False)  # email, sms, push
    
    # Content
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    
    # Delivery
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Indexes for performance
Index('idx_change_case_charter_status', ChangeCase.charter_id, ChangeCase.status)
Index('idx_change_case_requested_date', ChangeCase.requested_at.desc())
Index('idx_change_case_priority_status', ChangeCase.priority, ChangeCase.status)
Index('idx_change_history_case_date', ChangeHistory.change_case_id, ChangeHistory.action_at.desc())
Index('idx_change_approval_case_status', ChangeApproval.change_case_id, ChangeApproval.status)
