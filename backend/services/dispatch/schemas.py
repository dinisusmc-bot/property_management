"""
Pydantic schemas for Dispatch Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Dispatch Schemas
# ============================================================================

class DispatchBase(BaseModel):
    """Base schema for dispatch"""
    charter_id: int
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    dispatch_time: Optional[datetime] = None
    notes: Optional[str] = None


class DispatchCreate(DispatchBase):
    """Schema for creating a new dispatch"""
    pass


class DispatchUpdate(BaseModel):
    """Schema for updating a dispatch"""
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    status: Optional[str] = None
    pickup_time: Optional[datetime] = None
    dropoff_time: Optional[datetime] = None
    notes: Optional[str] = None


class DispatchResponse(DispatchBase):
    """Schema for dispatch response"""
    id: int
    status: str
    pickup_time: Optional[datetime]
    dropoff_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Location Schemas
# ============================================================================

class LocationUpdate(BaseModel):
    """Schema for updating GPS location"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, le=360)
    altitude: Optional[float] = None
    accuracy: Optional[float] = Field(None, ge=0)


class LocationResponse(LocationUpdate):
    """Schema for location response"""
    id: int
    dispatch_id: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Event Schemas
# ============================================================================

class DispatchEventCreate(BaseModel):
    """Schema for creating a dispatch event"""
    event_type: str = Field(..., description="Event type: assigned, dispatched, departed, arrived, delayed, breakdown, completed, cancelled")
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class DispatchEventResponse(DispatchEventCreate):
    """Schema for dispatch event response"""
    id: int
    dispatch_id: int
    occurred_at: datetime
    recorded_by: Optional[int]
    
    class Config:
        from_attributes = True


# ============================================================================
# Recovery Schemas
# ============================================================================

class RecoveryCreate(BaseModel):
    """Schema for creating a recovery/breakdown report"""
    dispatch_id: int
    issue_type: str = Field(..., description="Issue type: breakdown, accident, emergency")
    severity: str = Field(default="medium", description="Severity: low, medium, high, critical")
    description: str
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None


class RecoveryUpdate(BaseModel):
    """Schema for updating a recovery"""
    status: Optional[str] = Field(None, description="Status: reported, acknowledged, en_route, resolved, cancelled")
    resolution_notes: Optional[str] = None
    replacement_vehicle_id: Optional[int] = None
    replacement_driver_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class RecoveryResponse(BaseModel):
    """Schema for recovery response"""
    id: int
    dispatch_id: int
    issue_type: str
    severity: str
    description: str
    status: str
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]
    resolution_notes: Optional[str]
    replacement_vehicle_id: Optional[int]
    replacement_driver_id: Optional[int]
    reported_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    reported_by: Optional[int]
    assigned_to: Optional[int]
    # Phase 7 fields
    recovery_priority: Optional[str] = "normal"
    estimated_recovery_time: Optional[datetime] = None
    recovery_attempts: Optional[int] = 0
    last_contact_at: Optional[datetime] = None
    last_contact_method: Optional[str] = None
    escalated: Optional[bool] = False
    escalated_to: Optional[int] = None
    escalated_at: Optional[datetime] = None
    recovery_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Phase 7: Enhanced Recovery Workflow Schemas
# ============================================================================

class ContactAttemptRequest(BaseModel):
    """Schema for logging a contact attempt"""
    contact_method: str = Field(..., description="Contact method: phone, sms, email")
    notes: Optional[str] = None


class ContactAttemptResponse(BaseModel):
    """Schema for contact attempt response"""
    recovery_id: int
    attempts: int
    priority: str
    last_contact: str


class EscalateRecoveryRequest(BaseModel):
    """Schema for escalating a recovery"""
    escalate_to_user_id: int
    reason: str


class EscalateRecoveryResponse(BaseModel):
    """Schema for escalation response"""
    recovery_id: int
    escalated: bool
    escalated_to: int
    priority: str


class RecoveryDashboardItem(BaseModel):
    """Schema for dashboard recovery item"""
    recovery_id: int
    charter_id: Optional[int]
    driver_id: Optional[int]
    reason: str
    priority: str
    attempts: int
    last_contact: Optional[str]
    escalated: bool
    created_at: str


class RecoveryDashboard(BaseModel):
    """Schema for recovery dashboard"""
    summary: dict
    recoveries: dict  # {priority: [items]}


# ============================================================================
# Board/Summary Schemas
# ============================================================================

class DispatchBoardItem(BaseModel):
    """Schema for dispatch board item"""
    id: int
    charter_id: int
    driver_id: Optional[int]
    vehicle_id: Optional[int]
    status: str
    dispatch_time: Optional[datetime]
    last_location: Optional[LocationResponse]
    recent_events: List[DispatchEventResponse]


class DispatchBoard(BaseModel):
    """Schema for dispatch board"""
    active_dispatches: int
    pending_count: int
    assigned_count: int
    en_route_count: int
    in_service_count: int
    dispatches: List[DispatchBoardItem]
