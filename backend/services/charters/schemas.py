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
