"""
Pydantic schemas for Pricing Service
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from decimal import Decimal

# Enums
class RuleTypeEnum(str, Enum):
    BASE_RATE = "base_rate"
    MILEAGE_RATE = "mileage_rate"
    TIME_MULTIPLIER = "time_multiplier"
    SEASONAL = "seasonal"
    CLIENT_SPECIFIC = "client_specific"
    VEHICLE_SPECIFIC = "vehicle_specific"

class RuleScopeEnum(str, Enum):
    GLOBAL = "global"
    CLIENT = "client"
    VEHICLE = "vehicle"
    ROUTE = "route"

# Pricing Rule Schemas
class PricingRuleBase(BaseModel):
    """Base pricing rule schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    rule_type: RuleTypeEnum
    scope: RuleScopeEnum = RuleScopeEnum.GLOBAL
    vehicle_id: Optional[int] = None
    client_id: Optional[int] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    applicable_days: Optional[str] = None  # JSON string
    is_overnight: bool = False
    is_weekend: bool = False
    is_holiday: bool = False
    base_rate: Optional[float] = None
    per_mile_rate: Optional[float] = None
    per_hour_rate: Optional[float] = None
    multiplier: float = 1.0
    min_charge: Optional[float] = None
    max_charge: Optional[float] = None
    priority: int = 0
    is_active: bool = True

class PricingRuleCreate(PricingRuleBase):
    """Schema for creating a pricing rule"""
    pass

class PricingRuleUpdate(BaseModel):
    """Schema for updating a pricing rule"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[RuleTypeEnum] = None
    scope: Optional[RuleScopeEnum] = None
    vehicle_id: Optional[int] = None
    client_id: Optional[int] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    applicable_days: Optional[str] = None
    is_overnight: Optional[bool] = None
    is_weekend: Optional[bool] = None
    is_holiday: Optional[bool] = None
    base_rate: Optional[float] = None
    per_mile_rate: Optional[float] = None
    per_hour_rate: Optional[float] = None
    multiplier: Optional[float] = None
    min_charge: Optional[float] = None
    max_charge: Optional[float] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class PricingRuleResponse(PricingRuleBase):
    """Schema for pricing rule response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    class Config:
        from_attributes = True

# Quote Request/Response Schemas
class QuoteRequest(BaseModel):
    """Schema for quote calculation request"""
    client_id: int
    vehicle_id: int
    trip_date: date
    passengers: int
    total_miles: float = Field(..., ge=0)
    trip_hours: float = Field(..., ge=0)
    is_overnight: bool = False
    is_weekend: bool = False
    is_holiday: bool = False
    additional_fees: float = 0.0
    notes: Optional[str] = None

class QuoteBreakdown(BaseModel):
    """Detailed quote breakdown"""
    base_cost: float
    mileage_cost: float
    time_based_cost: float
    weekend_multiplier: float
    overnight_multiplier: float
    holiday_multiplier: float
    seasonal_multiplier: float
    additional_fees: float
    fuel_surcharge: float
    subtotal: float
    total_cost: float
    rules_applied: List[int] = []
    calculation_notes: Optional[str] = None

class QuoteResponse(BaseModel):
    """Schema for quote calculation response"""
    calculation_id: Optional[int] = None
    breakdown: QuoteBreakdown
    expires_at: Optional[datetime] = None

# Quote Calculation History Schemas
class QuoteCalculationResponse(BaseModel):
    """Schema for quote calculation history"""
    id: int
    charter_id: Optional[int]
    client_id: int
    vehicle_id: int
    trip_date: date
    passengers: int
    total_miles: float
    trip_hours: float
    is_overnight: bool
    is_weekend: bool
    is_holiday: bool
    base_cost: float
    mileage_cost: float
    time_based_cost: float
    weekend_multiplier: float
    overnight_multiplier: float
    holiday_multiplier: float
    seasonal_multiplier: float
    additional_fees: float
    fuel_surcharge: float
    subtotal: float
    total_cost: float
    rules_applied: Optional[str]
    calculation_notes: Optional[str]
    expires_at: Optional[datetime]
    status: str
    created_at: datetime
    created_by: Optional[int]
    
    class Config:
        from_attributes = True

# Price History Schemas
class PriceHistoryResponse(BaseModel):
    """Schema for price history"""
    id: int
    rule_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    change_reason: Optional[str]
    changed_at: datetime
    changed_by: Optional[int]
    
    class Config:
        from_attributes = True


# Amenity Schemas
class AmenityBase(BaseModel):
    """Base amenity schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: Optional[str] = None
    is_active: bool = True


class AmenityCreate(AmenityBase):
    """Schema for creating an amenity"""
    pass


class AmenityUpdate(BaseModel):
    """Schema for updating an amenity"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class AmenityResponse(AmenityBase):
    """Schema for amenity response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Quote Amenity Schemas
class QuoteAmenityAdd(BaseModel):
    """Schema for adding amenity to quote"""
    amenity_id: int
    quantity: int = Field(default=1, ge=1)


class QuoteAmenityResponse(BaseModel):
    """Schema for quote amenity response"""
    id: int
    quote_id: int
    amenity_id: int
    quantity: int
    price: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# Promo Code Schemas
class PromoCodeBase(BaseModel):
    """Base promo code schema"""
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    discount_type: str = Field(..., pattern="^(percentage|fixed)$")
    discount_value: float = Field(..., gt=0)
    min_order_value: Optional[float] = Field(None, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    valid_from: date
    valid_until: date
    usage_limit: Optional[int] = Field(None, ge=0)
    is_active: bool = True


class PromoCodeCreate(PromoCodeBase):
    """Schema for creating a promo code"""
    pass


class PromoCodeResponse(PromoCodeBase):
    """Schema for promo code response"""
    id: int
    usage_count: int
    created_at: datetime
    created_by: Optional[int]
    
    class Config:
        from_attributes = True


class ApplyPromoCodeRequest(BaseModel):
    """Schema for applying promo code to quote"""
    promo_code: str = Field(..., min_length=1, max_length=50)
    quote_id: int = Field(..., gt=0)


# ============================================================================
# PHASE 4 TASK 4.3: Pricing Modifier Schemas
# ============================================================================

class PricingModifierBase(BaseModel):
    """Base pricing modifier schema"""
    modifier_name: str = Field(..., min_length=1, max_length=100)
    modifier_type: str = Field(..., min_length=1, max_length=50)  # seasonal, day_of_week, etc.
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    adjustment_type: str = Field(..., pattern="^(percentage|fixed_amount)$")
    adjustment_value: Decimal
    priority: int = Field(0, ge=0, le=100)
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class PricingModifierCreate(PricingModifierBase):
    """Schema for creating a pricing modifier"""
    created_by: int


class PricingModifierUpdate(BaseModel):
    """Schema for updating a pricing modifier"""
    modifier_name: Optional[str] = None
    modifier_type: Optional[str] = None
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    adjustment_type: Optional[str] = None
    adjustment_value: Optional[Decimal] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class PricingModifierResponse(PricingModifierBase):
    """Schema for pricing modifier response"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PricingModifierLogResponse(BaseModel):
    """Schema for pricing modifier log response"""
    id: int
    quote_id: Optional[int]
    charter_id: Optional[int]
    modifier_id: int
    base_price: Decimal
    adjusted_price: Decimal
    adjustment_amount: Decimal
    applied_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Geocoding Schemas - Task 8.2
# ============================================================================

class AddressComponents(BaseModel):
    """Address components from geocoding"""
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class GeocodeRequest(BaseModel):
    """Request to geocode an address"""
    address: str = Field(..., min_length=5, max_length=500, description="Address to geocode")
    use_cache: bool = Field(True, description="Whether to use cached results")


class GeocodeResponse(BaseModel):
    """Response from geocoding"""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    formatted_address: str = Field(..., description="Formatted address from TomTom")
    components: AddressComponents
    confidence: float = Field(..., ge=0, le=100, description="Confidence score (0-100, higher is better)")
    cached: bool = Field(..., description="Whether result came from cache")


class ReverseGeocodeRequest(BaseModel):
    """Request to reverse geocode coordinates"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class ReverseGeocodeResponse(BaseModel):
    """Response from reverse geocoding"""
    formatted_address: str
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class AutocompleteRequest(BaseModel):
    """Request for address autocomplete"""
    query: str = Field(..., min_length=2, max_length=200, description="Partial address to autocomplete")
    center_lat: Optional[float] = Field(None, ge=-90, le=90, description="Center latitude for biasing results")
    center_lon: Optional[float] = Field(None, ge=-180, le=180, description="Center longitude for biasing results")


class AutocompleteSuggestion(BaseModel):
    """Single address suggestion"""
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AutocompleteResponse(BaseModel):
    """Response from autocomplete"""
    suggestions: List[AutocompleteSuggestion]


class RouteRequest(BaseModel):
    """Request to calculate route"""
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lon: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lon: float = Field(..., ge=-180, le=180)


class RouteResponse(BaseModel):
    """Response from route calculation"""
    distance_miles: float = Field(..., description="Total distance in miles")
    duration_minutes: float = Field(..., description="Estimated travel time in minutes")
    traffic_delay_minutes: float = Field(..., description="Additional delay due to traffic")


# ============================================================================
# Task 8.3: Multi-Vehicle Pricing Schemas
# ============================================================================

class MultiVehiclePricingRequest(BaseModel):
    """Request for multi-vehicle pricing calculation"""
    total_passengers: int = Field(..., gt=0, description="Total passenger count")
    total_miles: float = Field(..., gt=0, description="Total miles for trip")
    vehicle_count: int = Field(..., gt=0, description="Number of vehicles needed")
    vehicle_type: str = Field(..., description="Vehicle type (e.g., '56_passenger', 'minibus')")
    estimated_hours: float = Field(..., gt=0, description="Estimated trip duration in hours")
    
    # Optional rate overrides
    base_rate_per_mile: Optional[float] = Field(None, gt=0, description="Override base rate per mile")
    base_rate_per_hour: Optional[float] = Field(None, gt=0, description="Override base rate per hour")


class VehicleBreakdown(BaseModel):
    """Breakdown for individual vehicle in multi-vehicle pricing"""
    vehicle_number: int = Field(..., description="Vehicle number (1, 2, 3, etc.)")
    passengers: int = Field(..., description="Passengers assigned to this vehicle")
    miles: float = Field(..., description="Miles this vehicle will travel")
    estimated_hours: float = Field(..., description="Hours this vehicle will be in service")
    mileage_cost: float = Field(..., description="Cost based on mileage")
    hourly_cost: float = Field(..., description="Cost based on hours")
    total_cost: float = Field(..., description="Total cost for this vehicle")


class MultiVehiclePricingResponse(BaseModel):
    """Response from multi-vehicle pricing calculation"""
    vehicle_count: int
    vehicle_type: str
    total_passengers: int
    passengers_per_vehicle: int = Field(..., description="Average passengers per vehicle")
    remaining_passengers: int = Field(..., description="Extra passengers distributed to first vehicles")
    total_miles: float
    estimated_hours: float
    
    # Rates used
    base_rate_per_mile: float
    base_rate_per_hour: float
    
    # Costs per vehicle
    mileage_cost_per_vehicle: float
    hourly_cost_per_vehicle: float
    base_cost_per_vehicle: float
    
    # Total costs
    total_base_cost: float
    
    # Individual vehicle breakdown
    vehicles: List[VehicleBreakdown]
    
    # Notes
    notes: str = Field(..., description="Additional pricing notes")
