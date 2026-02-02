"""
Pydantic schemas for Pricing Service
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

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
