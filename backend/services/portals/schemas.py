"""
Pydantic Schemas for Portals Service

Defines request/response schemas for:
- User preferences
- Portal sessions
- Dashboard data structures
- Aggregated views from multiple services
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ==================== User Preferences ====================

class PortalUserPreferenceBase(BaseModel):
    email_notifications_enabled: bool = True
    sms_notifications_enabled: bool = False
    push_notifications_enabled: bool = True
    notification_frequency: str = "realtime"
    dashboard_layout: Optional[Dict[str, Any]] = None
    default_view: str = "dashboard"
    items_per_page: int = 20
    timezone: str = "America/Los_Angeles"
    date_format: str = "MM/DD/YYYY"
    currency: str = "USD"
    language: str = "en-US"
    theme: str = "light"


class PortalUserPreferenceCreate(PortalUserPreferenceBase):
    user_id: int
    user_type: str  # client, vendor, admin


class PortalUserPreferenceUpdate(BaseModel):
    email_notifications_enabled: Optional[bool] = None
    sms_notifications_enabled: Optional[bool] = None
    push_notifications_enabled: Optional[bool] = None
    notification_frequency: Optional[str] = None
    dashboard_layout: Optional[Dict[str, Any]] = None
    default_view: Optional[str] = None
    items_per_page: Optional[int] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None


class PortalUserPreferenceResponse(PortalUserPreferenceBase):
    id: int
    user_id: int
    user_type: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== Portal Sessions ====================

class PortalSessionCreate(BaseModel):
    user_id: int
    user_type: str
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime


class PortalSessionResponse(BaseModel):
    id: int
    user_id: int
    user_type: str
    session_token: str
    ip_address: Optional[str]
    login_at: datetime
    last_activity_at: datetime
    logout_at: Optional[datetime]
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# ==================== Activity Logs ====================

class PortalActivityLogCreate(BaseModel):
    user_id: int
    user_type: str
    session_id: Optional[int] = None
    activity_type: str
    activity_category: str
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None


class PortalActivityLogResponse(BaseModel):
    id: int
    user_id: int
    user_type: str
    activity_type: str
    activity_category: str
    description: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Client Portal Schemas ====================

class ClientCharterSummary(BaseModel):
    """Simplified charter info for client dashboard"""
    id: int
    charter_number: Optional[str]
    pickup_datetime: datetime
    dropoff_datetime: Optional[datetime]
    pickup_location: str
    destination: str
    passenger_count: int
    vehicle_type: Optional[str]
    status: str
    total_amount: Optional[Decimal]
    payment_status: Optional[str]
    has_unread_updates: bool = False


class ClientQuoteSummary(BaseModel):
    """Quote information for client review"""
    id: int
    charter_id: int
    quote_number: Optional[str]
    total_amount: Decimal
    valid_until: datetime
    status: str
    vehicle_type: Optional[str]
    vendor_name: Optional[str]
    created_at: datetime


class ClientDashboard(BaseModel):
    """Aggregated dashboard data for client portal"""
    user_id: int
    client_name: str
    
    # Statistics
    total_charters: int
    active_charters: int
    upcoming_charters: int
    completed_charters: int
    
    pending_quotes: int
    total_spent: Decimal
    
    # Recent activity
    recent_charters: List[ClientCharterSummary]
    pending_quotes_list: List[ClientQuoteSummary]
    
    # Notifications
    unread_notifications: int
    has_pending_actions: bool


class ClientPaymentHistory(BaseModel):
    """Payment history for client"""
    id: int
    charter_id: int
    charter_number: Optional[str]
    amount: Decimal
    payment_method: str
    payment_date: datetime
    status: str
    receipt_url: Optional[str]


# ==================== Vendor Portal Schemas ====================

class VendorBidOpportunity(BaseModel):
    """Charter available for bidding"""
    charter_id: int
    charter_number: Optional[str]
    pickup_datetime: datetime
    pickup_location: str
    destination: str
    distance_miles: Optional[Decimal]
    passenger_count: int
    vehicle_type: Optional[str]
    bid_deadline: Optional[datetime]
    current_bids_count: int
    client_rating: Optional[Decimal]


class VendorScheduledTrip(BaseModel):
    """Upcoming trip for vendor"""
    charter_id: int
    charter_number: Optional[str]
    pickup_datetime: datetime
    dropoff_datetime: Optional[datetime]
    pickup_location: str
    destination: str
    passenger_count: int
    vehicle_assigned: Optional[str]
    driver_assigned: Optional[str]
    special_requirements: Optional[List[str]]


class VendorDashboard(BaseModel):
    """Aggregated dashboard data for vendor portal"""
    vendor_id: int
    vendor_name: str
    
    # Statistics
    total_bids_submitted: int
    bids_won: int
    win_rate_percentage: Optional[Decimal]
    average_rating: Optional[Decimal]
    total_completed_trips: int
    
    # Financial
    total_earnings: Decimal
    pending_payments: Decimal
    
    # Current activity
    active_bids: int
    upcoming_trips: int
    bid_opportunities: List[VendorBidOpportunity]
    scheduled_trips: List[VendorScheduledTrip]
    
    # Compliance
    compliance_status: str  # compliant, missing_docs, expired_docs
    expiring_documents: int
    
    # Notifications
    unread_notifications: int


# ==================== Admin Dashboard Schemas ====================

class AdminSystemStats(BaseModel):
    """System-wide statistics"""
    total_users: int
    total_clients: int
    total_vendors: int
    active_charters: int
    total_revenue: Decimal
    pending_approvals: int


class AdminRecentActivity(BaseModel):
    """Recent system activity"""
    activity_type: str
    description: str
    user_id: int
    user_name: str
    created_at: datetime


class AdminDashboard(BaseModel):
    """Aggregated dashboard data for admin"""
    system_stats: AdminSystemStats
    recent_activity: List[AdminRecentActivity]
    
    # Today's metrics
    new_charters_today: int
    new_users_today: int
    revenue_today: Decimal
    
    # Pending items
    pending_vendor_approvals: int
    pending_charter_approvals: int
    pending_change_requests: int
    
    # Alerts
    system_alerts: List[Dict[str, Any]]


# ==================== Common Response Schemas ====================

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]  # service_name: status
