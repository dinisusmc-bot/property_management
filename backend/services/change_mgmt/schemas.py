"""
Pydantic schemas for change management service
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


# Enums matching models.py
class ChangeType(str, Enum):
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


class ChangeStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    CANCELLED = "cancelled"


class ChangePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ImpactLevel(str, Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    MAJOR = "major"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


# Change Case Schemas
class ChangeCaseBase(BaseModel):
    charter_id: int
    client_id: int
    vendor_id: Optional[int] = None
    change_type: ChangeType
    priority: ChangePriority = ChangePriority.MEDIUM
    title: str = Field(..., min_length=1, max_length=200)
    description: str
    reason: str
    impact_level: ImpactLevel = ImpactLevel.MINIMAL
    impact_assessment: Optional[str] = None
    affects_vendor: bool = False
    affects_pricing: bool = False
    affects_schedule: bool = False
    current_price: Optional[float] = None
    proposed_price: Optional[float] = None
    proposed_changes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class ChangeCaseCreate(ChangeCaseBase):
    requested_by: int
    requested_by_name: str


class ChangeCaseUpdate(BaseModel):
    priority: Optional[ChangePriority] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    reason: Optional[str] = None
    impact_level: Optional[ImpactLevel] = None
    impact_assessment: Optional[str] = None
    affects_vendor: Optional[bool] = None
    affects_pricing: Optional[bool] = None
    affects_schedule: Optional[bool] = None
    proposed_price: Optional[float] = None
    proposed_changes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class ChangeCaseResponse(ChangeCaseBase):
    id: int
    case_number: str
    status: ChangeStatus
    requested_by: int
    requested_by_name: str
    requested_at: datetime
    requires_approval: bool
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    rejected_by: Optional[int] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    implemented_by: Optional[int] = None
    implemented_at: Optional[datetime] = None
    implementation_notes: Optional[str] = None
    price_difference: Optional[float] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    related_change_cases: Optional[List[int]] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChangeCaseListResponse(BaseModel):
    items: List[ChangeCaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# State Transition Schemas
class ApproveChangeRequest(BaseModel):
    approved_by: int
    approved_by_name: str
    approval_notes: Optional[str] = None


class RejectChangeRequest(BaseModel):
    rejected_by: int
    rejected_by_name: str
    rejection_reason: str


class ImplementChangeRequest(BaseModel):
    implemented_by: int
    implemented_by_name: str
    implementation_notes: Optional[str] = None


class CancelChangeRequest(BaseModel):
    cancelled_by: int
    cancelled_by_name: str
    cancellation_reason: str


# Change History Schemas
class ChangeHistoryCreate(BaseModel):
    change_case_id: int
    action: str
    action_by: int
    action_by_name: str
    previous_status: Optional[ChangeStatus] = None
    new_status: Optional[ChangeStatus] = None
    notes: Optional[str] = None
    field_changes: Optional[Dict[str, Any]] = None
    system_generated: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ChangeHistoryResponse(BaseModel):
    id: int
    change_case_id: int
    action: str
    action_by: int
    action_by_name: str
    action_at: datetime
    previous_status: Optional[ChangeStatus] = None
    new_status: Optional[ChangeStatus] = None
    notes: Optional[str] = None
    field_changes: Optional[Dict[str, Any]] = None
    system_generated: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True


# Change Approval Schemas
class ChangeApprovalBase(BaseModel):
    approver_id: int
    approver_name: str
    approver_role: str
    approval_level: int = 1
    required: bool = True
    conditions: Optional[str] = None


class ChangeApprovalCreate(ChangeApprovalBase):
    change_case_id: int


class ChangeApprovalUpdate(BaseModel):
    status: ApprovalStatus
    decision: Optional[str] = None
    notes: Optional[str] = None


class ChangeApprovalResponse(ChangeApprovalBase):
    id: int
    change_case_id: int
    status: ApprovalStatus
    decision: Optional[str] = None
    notes: Optional[str] = None
    requested_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Change Notification Schemas
class ChangeNotificationCreate(BaseModel):
    change_case_id: int
    recipient_id: int
    recipient_email: EmailStr
    recipient_type: str
    notification_type: str
    notification_method: str = "email"
    subject: str
    message: str


class ChangeNotificationResponse(BaseModel):
    id: int
    change_case_id: int
    recipient_id: int
    recipient_email: str
    recipient_type: str
    notification_type: str
    notification_method: str
    subject: str
    message: str
    sent_at: Optional[datetime] = None
    delivered: bool
    delivered_at: Optional[datetime] = None
    opened: bool
    opened_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


# Dashboard and Analytics Schemas
class ChangeMetrics(BaseModel):
    total_changes: int
    pending_changes: int
    under_review_changes: int
    approved_changes: int
    rejected_changes: int
    implemented_changes: int
    cancelled_changes: int
    avg_approval_time_hours: Optional[float] = None
    avg_implementation_time_hours: Optional[float] = None


class ChangesByType(BaseModel):
    change_type: ChangeType
    count: int
    avg_price_impact: Optional[float] = None


class ChangesByPriority(BaseModel):
    priority: ChangePriority
    count: int
    avg_resolution_time_hours: Optional[float] = None


class ChangeDashboard(BaseModel):
    metrics: ChangeMetrics
    changes_by_type: List[ChangesByType]
    changes_by_priority: List[ChangesByPriority]
    pending_approvals: int
    overdue_changes: int


# Health Check Schema
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    timestamp: datetime
