"""
Pydantic schemas for Charter Service
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List

# Vehicle schemas
class VehicleBase(BaseModel):
    """Base vehicle schema"""
    name: str
    capacity: int
    base_rate: float
    per_mile_rate: float

class VehicleResponse(VehicleBase):
    """Schema for vehicle response"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Stop schemas
class StopBase(BaseModel):
    """Base stop schema"""
    location: str
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    notes: Optional[str] = None
    # Phase 2 fields
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geocoded_address: Optional[str] = None
    stop_type: Optional[str] = "waypoint"  # pickup, dropoff, waypoint
    estimated_arrival: Optional[datetime] = None
    estimated_departure: Optional[datetime] = None

class StopCreate(StopBase):
    """Schema for creating a stop"""
    sequence: Optional[int] = None

class StopUpdate(BaseModel):
    """Schema for updating a stop"""
    location: Optional[str] = None
    sequence: Optional[int] = None
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    notes: Optional[str] = None

class StopResponse(StopBase):
    """Schema for stop response"""
    id: int
    charter_id: int
    sequence: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Charter schemas
class CharterBase(BaseModel):
    """Base charter schema"""
    client_id: int
    vehicle_id: int
    trip_date: date
    passengers: int
    trip_hours: float
    is_overnight: bool = False
    is_weekend: bool = False
    notes: Optional[str] = None
    vendor_notes: Optional[str] = None
    last_checkin_location: Optional[str] = None
    last_checkin_time: Optional[datetime] = None
    # Phase 2 Enhancement Fields
    trip_type: Optional[str] = None  # one-way, round-trip, multi-day
    requires_second_driver: bool = False
    vehicle_count: int = 1
    is_multi_vehicle: bool = False

class CharterCreate(CharterBase):
    """Schema for creating a charter"""
    vendor_id: Optional[int] = None
    status: Optional[str] = "quote"
    # Legacy pricing fields (kept for backwards compatibility)
    base_cost: float
    mileage_cost: float
    additional_fees: float = 0.0
    total_cost: float
    deposit_amount: Optional[float] = None
    # Vendor pricing (what we pay to vendor)
    vendor_base_cost: Optional[float] = None
    vendor_mileage_cost: Optional[float] = None
    vendor_additional_fees: Optional[float] = 0.0
    vendor_total_cost: Optional[float] = None
    # Client pricing (what we charge to client)
    client_base_charge: Optional[float] = None
    client_mileage_charge: Optional[float] = None
    client_additional_fees: Optional[float] = 0.0
    client_total_charge: Optional[float] = None
    profit_margin: Optional[float] = None
    stops: Optional[List[StopCreate]] = []

class CharterUpdate(BaseModel):
    """Schema for updating a charter"""
    vehicle_id: Optional[int] = None
    vendor_id: Optional[int] = None
    status: Optional[str] = None
    trip_date: Optional[date] = None
    passengers: Optional[int] = None
    trip_hours: Optional[float] = None
    is_overnight: Optional[bool] = None
    is_weekend: Optional[bool] = None
    # Legacy pricing
    base_cost: Optional[float] = None
    mileage_cost: Optional[float] = None
    additional_fees: Optional[float] = None
    total_cost: Optional[float] = None
    deposit_amount: Optional[float] = None
    # Vendor pricing
    vendor_base_cost: Optional[float] = None
    vendor_mileage_cost: Optional[float] = None
    vendor_additional_fees: Optional[float] = None
    vendor_total_cost: Optional[float] = None
    # Client pricing
    client_base_charge: Optional[float] = None
    client_mileage_charge: Optional[float] = None
    client_additional_fees: Optional[float] = None
    client_total_charge: Optional[float] = None
    profit_margin: Optional[float] = None
    notes: Optional[str] = None
    vendor_notes: Optional[str] = None
    last_checkin_location: Optional[str] = None
    last_checkin_time: Optional[datetime] = None
    # Phase 2 Enhancement Fields
    trip_type: Optional[str] = None
    requires_second_driver: Optional[bool] = None
    vehicle_count: Optional[int] = None
    recurrence_rule: Optional[str] = None
    approval_sent_date: Optional[datetime] = None
    approval_amount: Optional[float] = None
    approval_status: Optional[str] = None
    booking_status: Optional[str] = None
    booked_at: Optional[datetime] = None
    booking_cost: Optional[float] = None
    confirmation_status: Optional[str] = None
    confirmed_at: Optional[datetime] = None

class CharterResponse(CharterBase):
    """Schema for charter response"""
    id: int
    vendor_id: Optional[int]
    vendor_name: Optional[str] = None
    vendor_email: Optional[str] = None
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    driver_email: Optional[str] = None
    status: str
    # Legacy pricing
    base_cost: float
    mileage_cost: float
    additional_fees: float
    total_cost: float
    deposit_amount: Optional[float]
    # Vendor pricing
    vendor_base_cost: Optional[float] = None
    vendor_mileage_cost: Optional[float] = None
    vendor_additional_fees: Optional[float] = None
    vendor_total_cost: Optional[float] = None
    # Client pricing
    client_base_charge: Optional[float] = None
    client_mileage_charge: Optional[float] = None
    client_additional_fees: Optional[float] = None
    client_total_charge: Optional[float] = None
    profit_margin: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime]
    vehicle: VehicleResponse
    stops: List[StopResponse] = []
    # Phase 2.1: Multi-vehicle fields  
    is_multi_vehicle: bool = False
    total_vehicles: int = 1
    # Phase 2 Enhancement Fields
    parent_charter_id: Optional[int] = None
    quote_secure_token: Optional[str] = None
    revision_number: Optional[int] = None
    recurrence_rule: Optional[str] = None
    instance_number: Optional[int] = None
    series_total: Optional[int] = None
    is_series_master: Optional[bool] = None
    cloned_from_charter_id: Optional[int] = None
    approval_sent_date: Optional[datetime] = None
    approval_amount: Optional[float] = None
    approval_status: Optional[str] = None
    booking_status: Optional[str] = None
    booked_at: Optional[datetime] = None
    booking_cost: Optional[float] = None
    confirmation_status: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Payment schemas
class VendorPaymentBase(BaseModel):
    """Base vendor payment schema"""
    charter_id: int
    vendor_id: int
    amount: float
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_status: str = "pending"
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class VendorPaymentCreate(VendorPaymentBase):
    """Schema for creating a vendor payment"""
    created_by: Optional[int] = None

class VendorPaymentUpdate(BaseModel):
    """Schema for updating a vendor payment"""
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class VendorPaymentResponse(VendorPaymentBase):
    """Schema for vendor payment response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    class Config:
        from_attributes = True

class ClientPaymentBase(BaseModel):
    """Base client payment schema"""
    charter_id: int
    client_id: int
    amount: float
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_status: str = "pending"
    payment_type: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class ClientPaymentCreate(ClientPaymentBase):
    """Schema for creating a client payment"""
    created_by: Optional[int] = None

class ClientPaymentUpdate(BaseModel):
    """Schema for updating a client payment"""
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    payment_type: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class ClientPaymentResponse(ClientPaymentBase):
    """Schema for client payment response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    class Config:
        from_attributes = True

# Quote schemas
class QuoteRequest(BaseModel):
    """Schema for quote calculation request"""
    vehicle_id: int
    stops: List[str] = Field(..., min_items=2, description="List of locations (origin, destination, and optional waypoints)")
    trip_hours: float = Field(..., gt=0, description="Estimated trip duration in hours")
    passengers: int = Field(..., gt=0, description="Number of passengers")
    is_overnight: bool = False
    is_weekend: bool = False

class QuoteResponse(BaseModel):
    """Schema for quote calculation response"""
    vehicle_id: int
    vehicle_name: str
    distance_miles: float
    trip_hours: float
    passengers: int
    base_cost: float
    mileage_cost: float
    overnight_fee: float
    weekend_fee: float
    vendor_gratuity: float
    additional_fees: float
    subtotal: float
    tax: float
    total_cost: float
    deposit_amount: float
    deposit_percentage: float

class CheckInRequest(BaseModel):
    """Schema for charter check-in"""
    location: str
    checkin_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Phase 2.1: Multi-vehicle charter schemas
class CharterVehicleBase(BaseModel):
    """Base charter vehicle schema"""
    vehicle_type_id: int
    capacity: int
    cost: float
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    special_requirements: Optional[str] = None

class CharterVehicleCreate(CharterVehicleBase):
    """Schema for creating a charter vehicle"""
    vehicle_id: Optional[int] = None
    vendor_id: Optional[int] = None
    status: str = "pending"

class CharterVehicleUpdate(BaseModel):
    """Schema for updating a charter vehicle"""
    vehicle_id: Optional[int] = None
    vendor_id: Optional[int] = None
    capacity: Optional[int] = None
    cost: Optional[float] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    special_requirements: Optional[str] = None
    status: Optional[str] = None

class CharterVehicleResponse(CharterVehicleBase):
    """Schema for charter vehicle response"""
    id: int
    charter_id: int
    vehicle_id: Optional[int]
    vendor_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class MultiVehicleCharterCreate(BaseModel):
    """Schema for creating a multi-vehicle charter"""
    client_id: int
    trip_date: date
    passengers: int
    trip_hours: float
    pickup_location: str
    dropoff_location: str
    event_type: Optional[str] = None
    notes: Optional[str] = None
    vehicles: List[CharterVehicleCreate] = Field(..., min_items=2, description="At least 2 vehicles required")
    
    class Config:
        from_attributes = True

class MultiVehicleCharterResponse(BaseModel):
    """Schema for multi-vehicle charter creation response"""
    charter_id: int
    is_multi_vehicle: bool
    total_vehicles: int
    total_capacity: int
    total_cost: float
    vehicles: List[CharterVehicleResponse]
    
    class Config:
        from_attributes = True

# Phase 2.2: Charter Cloning & Templates
class SaveAsTemplateRequest(BaseModel):
    """Schema for saving charter as template"""
    template_name: str
    
class CloneCharterRequest(BaseModel):
    """Schema for cloning charter"""
    trip_date: date
    client_id: Optional[int] = None
    overrides: Optional[dict] = None

# Phase 2.3: Charter Series Management
class CharterSeriesCreate(BaseModel):
    """Schema for creating charter series"""
    series_name: str
    client_id: int
    description: Optional[str] = None
    recurrence_pattern: str  # daily, weekly, monthly
    recurrence_days: Optional[str] = None  # For weekly: 'mon,wed,fri'
    start_date: date
    end_date: Optional[date] = None
    template_charter_id: int
    generate_charters: bool = False

class CharterSeriesResponse(BaseModel):
    """Schema for charter series response"""
    id: int
    series_name: str
    client_id: int
    description: Optional[str]
    recurrence_pattern: str
    recurrence_days: Optional[str]
    start_date: date
    end_date: Optional[date]
    is_active: bool
    created_at: datetime
    charter_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# Phase 2.4: DOT Compliance Certifications
class DOTCertificationCreate(BaseModel):
    """Schema for creating DOT certification"""
    certification_type: str
    certification_number: str
    issue_date: date
    expiration_date: date
    document_id: Optional[int] = None
    notes: Optional[str] = None

class DOTCertificationResponse(BaseModel):
    """Schema for DOT certification response"""
    id: int
    vendor_id: int
    certification_type: str
    certification_number: str
    issue_date: date
    expiration_date: date
    status: str
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    days_until_expiration: Optional[int] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Phase 7: Charter Splitting Schemas
# ============================================================================

class CharterLegCreate(BaseModel):
    """Schema for a single leg in charter splitting"""
    trip_date: date
    passengers: int
    notes: Optional[str] = None


class CharterSplitRequest(BaseModel):
    """Schema for splitting a charter into multiple legs"""
    legs: List[CharterLegCreate] = Field(..., min_length=2, description="At least 2 legs required")


class CharterLegResponse(BaseModel):
    """Schema for a split charter leg response"""
    id: int
    sequence: int
    trip_date: str
    passengers: int
    status: str
    total_cost: float


class CharterSplitResponse(BaseModel):
    """Schema for charter split response"""
    parent_charter_id: int
    split_count: int
    split_charters: List[CharterLegResponse]


class CharterSplitListResponse(BaseModel):
    """Schema for listing split charters"""
    parent_charter_id: int
    is_split: bool
    split_count: int
    split_charters: List[CharterLegResponse]


# ============================================================================
# Task 8.4: Secure Charter Share Link Schemas
# ============================================================================

class CharterShareLinkCreate(BaseModel):
    """Create charter share link request"""
    expires_hours: int = Field(168, ge=1, le=720, description="Hours until expiration (max 30 days)")
    password: Optional[str] = Field(None, min_length=4, max_length=36, description="Optional password protection (max 36 chars)")


class CharterShareLinkResponse(BaseModel):
    """Charter share link response"""
    link_id: int
    token: str
    url: str  # Full shareable URL
    expires_at: datetime
    has_password: bool
    view_count: int
    
    class Config:
        from_attributes = True


class CharterShareLinkVerify(BaseModel):
    """Verify charter share link request"""
    token: str = Field(..., description="JWT token from link")
    password: Optional[str] = Field(None, description="Password if link is protected")

