"""
Pydantic schemas for Vendor Service
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


# Enums (matching models.py)
class VendorStatusEnum(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    REJECTED = "rejected"
    BANNED = "banned"


class VendorTypeEnum(str, Enum):
    OWNER_OPERATOR = "owner_operator"
    FLEET_OPERATOR = "fleet_operator"
    BROKER = "broker"


class BidStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class ComplianceStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ============================================================================
# Vendor Schemas
# ============================================================================

class VendorBase(BaseModel):
    """Base schema for vendor"""
    business_name: str = Field(..., min_length=1, max_length=200)
    legal_name: str = Field(..., min_length=1, max_length=200)
    vendor_type: VendorTypeEnum
    tax_id: Optional[str] = Field(None, max_length=50)
    
    primary_contact_name: str = Field(..., min_length=1, max_length=100)
    primary_email: EmailStr
    primary_phone: str = Field(..., min_length=10, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., min_length=5, max_length=20)
    country: str = Field(default="USA", max_length=50)
    
    total_vehicles: int = Field(default=0, ge=0)
    vehicle_types: Optional[Dict[str, int]] = None
    max_passenger_capacity: Optional[int] = Field(None, ge=1)
    
    service_radius_miles: Optional[int] = Field(None, ge=0)
    service_states: Optional[List[str]] = None
    
    bank_name: Optional[str] = Field(None, max_length=100)
    payment_terms: Optional[str] = Field(None, max_length=50)
    insurance_provider: Optional[str] = Field(None, max_length=100)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_expiration: Optional[date] = None
    
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class VendorCreate(VendorBase):
    """Schema for creating a new vendor"""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating a vendor"""
    business_name: Optional[str] = Field(None, min_length=1, max_length=200)
    legal_name: Optional[str] = Field(None, min_length=1, max_length=200)
    vendor_type: Optional[VendorTypeEnum] = None
    tax_id: Optional[str] = None
    
    primary_contact_name: Optional[str] = None
    primary_email: Optional[EmailStr] = None
    primary_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    website: Optional[str] = None
    
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    
    total_vehicles: Optional[int] = Field(None, ge=0)
    vehicle_types: Optional[Dict[str, int]] = None
    max_passenger_capacity: Optional[int] = None
    
    service_radius_miles: Optional[int] = None
    service_states: Optional[List[str]] = None
    
    bank_name: Optional[str] = None
    payment_terms: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_expiration: Optional[date] = None
    
    status: Optional[VendorStatusEnum] = None
    is_preferred: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class VendorResponse(VendorBase):
    """Schema for vendor response"""
    id: int
    status: VendorStatusEnum
    is_verified: bool
    is_preferred: bool
    verification_date: Optional[datetime]
    
    average_rating: Optional[float]
    total_ratings: int
    completed_trips: int
    cancelled_trips: int
    on_time_percentage: Optional[float]
    
    total_bids_submitted: int
    bids_won: int
    bids_lost: int
    win_rate_percentage: Optional[float]
    
    created_at: datetime
    updated_at: Optional[datetime]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Bid Schemas
# ============================================================================

class BidBase(BaseModel):
    """Base schema for bid"""
    vendor_id: int
    charter_id: int
    quoted_price: float = Field(..., gt=0)
    vehicle_id: Optional[int] = None
    vehicle_type: str = Field(..., min_length=1, max_length=50)
    passenger_capacity: int = Field(..., ge=1)
    driver_name: Optional[str] = Field(None, max_length=100)
    
    base_price: Optional[float] = Field(None, ge=0)
    mileage_charge: Optional[float] = Field(None, ge=0)
    driver_charge: Optional[float] = Field(None, ge=0)
    fuel_surcharge: Optional[float] = Field(None, ge=0)
    additional_fees: Optional[float] = Field(None, ge=0)
    
    valid_until: datetime
    estimated_arrival_time: Optional[datetime] = None
    estimated_departure_time: Optional[datetime] = None
    payment_terms: Optional[str] = Field(None, max_length=50)
    cancellation_policy: Optional[str] = None
    
    amenities: Optional[List[str]] = None
    is_ada_compliant: bool = False
    has_luggage_space: bool = True
    
    notes: Optional[str] = None


class BidCreate(BidBase):
    """Schema for creating a new bid"""
    pass


class BidUpdate(BaseModel):
    """Schema for updating a bid"""
    quoted_price: Optional[float] = Field(None, gt=0)
    vehicle_id: Optional[int] = None
    vehicle_type: Optional[str] = None
    passenger_capacity: Optional[int] = Field(None, ge=1)
    driver_name: Optional[str] = None
    
    base_price: Optional[float] = None
    mileage_charge: Optional[float] = None
    driver_charge: Optional[float] = None
    fuel_surcharge: Optional[float] = None
    additional_fees: Optional[float] = None
    
    valid_until: Optional[datetime] = None
    estimated_arrival_time: Optional[datetime] = None
    estimated_departure_time: Optional[datetime] = None
    payment_terms: Optional[str] = None
    cancellation_policy: Optional[str] = None
    
    amenities: Optional[List[str]] = None
    is_ada_compliant: Optional[bool] = None
    has_luggage_space: Optional[bool] = None
    
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    status: Optional[BidStatusEnum] = None


class BidResponse(BidBase):
    """Schema for bid response"""
    id: int
    status: BidStatusEnum
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    decided_at: Optional[datetime]
    decision_reason: Optional[str]
    
    rank: Optional[int]
    is_lowest_bid: bool
    price_difference_from_lowest: Optional[float]
    
    internal_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BidSubmitRequest(BaseModel):
    """Schema for submitting a bid"""
    bid_id: int


class BidDecisionRequest(BaseModel):
    """Schema for accepting/rejecting a bid"""
    decision: str = Field(..., pattern="^(accept|reject)$")
    reason: Optional[str] = None


# ============================================================================
# Rating Schemas
# ============================================================================

class VendorRatingBase(BaseModel):
    """Base schema for vendor rating"""
    vendor_id: int
    charter_id: int
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    vehicle_condition_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    driver_professionalism_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    on_time_performance_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    communication_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    value_for_money_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    
    review_title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None
    
    had_issues: bool = False
    issue_description: Optional[str] = None
    
    would_recommend: Optional[bool] = None
    would_use_again: Optional[bool] = None


class VendorRatingCreate(VendorRatingBase):
    """Schema for creating a vendor rating"""
    pass


class VendorRatingResponse(VendorRatingBase):
    """Schema for vendor rating response"""
    id: int
    rated_by: int
    is_verified: bool
    is_public: bool
    is_flagged: bool
    
    vendor_response: Optional[str]
    vendor_responded_at: Optional[datetime]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class VendorResponseRequest(BaseModel):
    """Schema for vendor responding to a rating"""
    response: str = Field(..., min_length=1, max_length=1000)


# ============================================================================
# Compliance Schemas
# ============================================================================

class VendorComplianceBase(BaseModel):
    """Base schema for compliance document"""
    vendor_id: int
    document_type: str = Field(..., min_length=1, max_length=100)
    document_name: str = Field(..., min_length=1, max_length=200)
    document_number: Optional[str] = Field(None, max_length=100)
    
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    
    file_path: Optional[str] = None
    file_url: Optional[str] = None


class VendorComplianceCreate(VendorComplianceBase):
    """Schema for creating a compliance document"""
    pass


class VendorComplianceUpdate(BaseModel):
    """Schema for updating a compliance document"""
    document_name: Optional[str] = None
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[ComplianceStatusEnum] = None
    review_notes: Optional[str] = None


class VendorComplianceResponse(VendorComplianceBase):
    """Schema for compliance document response"""
    id: int
    status: ComplianceStatusEnum
    file_size_bytes: Optional[int]
    file_type: Optional[str]
    
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    
    reminder_sent: bool
    reminder_sent_at: Optional[datetime]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Bid Request Schemas
# ============================================================================

class BidRequestBase(BaseModel):
    """Base schema for bid request"""
    charter_id: int
    vendor_id: int
    message: Optional[str] = None
    deadline: datetime


class BidRequestCreate(BidRequestBase):
    """Schema for creating a bid request"""
    pass


class BidRequestResponse(BidRequestBase):
    """Schema for bid request response"""
    id: int
    requested_by: int
    viewed_at: Optional[datetime]
    responded_at: Optional[datetime]
    response_message: Optional[str]
    declined_reason: Optional[str]
    
    is_accepted: Optional[bool]
    bid_id: Optional[int]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BidRequestResponseRequest(BaseModel):
    """Schema for vendor responding to a bid request"""
    accept: bool
    response_message: Optional[str] = None
    declined_reason: Optional[str] = None


# ============================================================================
# Statistics & Reports
# ============================================================================

class VendorStatistics(BaseModel):
    """Vendor performance statistics"""
    vendor_id: int
    business_name: str
    average_rating: Optional[float]
    total_ratings: int
    completed_trips: int
    cancelled_trips: int
    on_time_percentage: Optional[float]
    total_bids_submitted: int
    bids_won: int
    win_rate_percentage: Optional[float]
    is_preferred: bool


class BidComparison(BaseModel):
    """Compare bids for a charter"""
    charter_id: int
    total_bids: int
    lowest_bid: Optional[float]
    highest_bid: Optional[float]
    average_bid: Optional[float]
    bids: List[BidResponse]

# ============================================================================
# Vendor Document Schemas (COI Tracking)
# ============================================================================

class VendorDocumentBase(BaseModel):
    """Base schema for vendor document"""
    document_type: str = Field(..., description="Type: 'coi', 'license', 'dot_authority'")
    document_id: Optional[int] = Field(None, description="Link to document service")
    issue_date: Optional[date] = None
    expiry_date: date
    notes: Optional[str] = None


class VendorDocumentCreate(VendorDocumentBase):
    """Schema for creating a vendor document"""
    pass


class VendorDocumentResponse(VendorDocumentBase):
    """Schema for vendor document response"""
    id: int
    vendor_id: int
    status: str
    days_until_expiry: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Vendor Performance Schemas
# ============================================================================

class PerformanceMetricCreate(BaseModel):
    """Schema for creating a performance metric"""
    charter_id: Optional[int] = None
    metric_type: str = Field(..., description="Type: 'on_time', 'cancellation', 'rating'")
    value: Decimal = Field(..., description="1/0 for boolean metrics, 1-5 for ratings")
    notes: Optional[str] = None


class PerformanceMetricResponse(BaseModel):
    """Schema for performance metric response"""
    id: int
    vendor_id: int
    charter_id: Optional[int]
    metric_type: str
    value: Decimal
    notes: Optional[str]
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class VendorPerformanceSummary(BaseModel):
    """Schema for vendor performance summary"""
    vendor_id: int
    total_trips: int
    on_time_percentage: Optional[Decimal]
    cancellation_count: int
    average_rating: Optional[Decimal]
    last_updated: datetime