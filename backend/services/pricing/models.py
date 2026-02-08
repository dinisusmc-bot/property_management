"""
Database models for Pricing Service
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, Enum as SQLEnum, Numeric, ForeignKey, CheckConstraint, DECIMAL
from sqlalchemy.sql import func
from database import Base
from enum import Enum

# Enums
class RuleType(str, Enum):
    BASE_RATE = "base_rate"
    MILEAGE_RATE = "mileage_rate"
    TIME_MULTIPLIER = "time_multiplier"
    SEASONAL = "seasonal"
    CLIENT_SPECIFIC = "client_specific"
    VEHICLE_SPECIFIC = "vehicle_specific"

class RuleScope(str, Enum):
    GLOBAL = "global"
    CLIENT = "client"
    VEHICLE = "vehicle"
    ROUTE = "route"

class PricingRule(Base):
    """Pricing rule model - defines dynamic pricing rules"""
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(SQLEnum(RuleType), nullable=False, index=True)
    scope = Column(SQLEnum(RuleScope), default=RuleScope.GLOBAL, index=True)
    
    # Rule applicability
    vehicle_id = Column(Integer, nullable=True, index=True)  # Specific vehicle type
    client_id = Column(Integer, nullable=True, index=True)  # Specific client
    
    # Date range for rule
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    
    # Days of week (JSON array: [0=Monday, 6=Sunday])
    applicable_days = Column(Text, nullable=True)  # Store as JSON string
    
    # Time constraints
    is_overnight = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    
    # Pricing values
    base_rate = Column(Float, nullable=True)  # Fixed base rate
    per_mile_rate = Column(Float, nullable=True)  # Rate per mile
    per_hour_rate = Column(Float, nullable=True)  # Rate per hour
    multiplier = Column(Float, default=1.0)  # Multiplier to apply
    
    # Minimum/Maximum constraints
    min_charge = Column(Float, nullable=True)
    max_charge = Column(Float, nullable=True)
    
    # Rule priority (higher = applied first)
    priority = Column(Integer, default=0, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # User ID who created

    def __repr__(self):
        return f"<PricingRule {self.name} - {self.rule_type}>"


class QuoteCalculation(Base):
    """Quote calculation history - tracks all quote calculations"""
    __tablename__ = "quote_calculations"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, nullable=True, index=True)  # Reference to charter if converted
    client_id = Column(Integer, nullable=False, index=True)
    vehicle_id = Column(Integer, nullable=False)
    
    # Trip details
    trip_date = Column(Date, nullable=False)
    passengers = Column(Integer, nullable=False)
    total_miles = Column(Float, nullable=False)
    trip_hours = Column(Float, nullable=False)
    is_overnight = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    
    # Calculated pricing
    base_cost = Column(Float, nullable=False)
    mileage_cost = Column(Float, nullable=False)
    time_based_cost = Column(Float, default=0.0)
    
    # Applied multipliers
    weekend_multiplier = Column(Float, default=1.0)
    overnight_multiplier = Column(Float, default=1.0)
    holiday_multiplier = Column(Float, default=1.0)
    seasonal_multiplier = Column(Float, default=1.0)
    
    # Additional fees
    additional_fees = Column(Float, default=0.0)
    fuel_surcharge = Column(Float, default=0.0)
    
    # Total
    subtotal = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Rules applied (JSON array of rule IDs)
    rules_applied = Column(Text, nullable=True)
    
    # Calculation metadata
    calculation_notes = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Quote expiration
    
    # Status
    status = Column(String(50), default="draft")  # draft, sent, accepted, expired, declined
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<QuoteCalculation {self.id} - ${self.total_cost}>"


class PriceHistory(Base):
    """Price history - tracks price changes over time for analysis"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)  # Which rule changed
    
    # What changed
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Reason for change
    change_reason = Column(Text, nullable=True)
    
    # Audit
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<PriceHistory Rule {self.rule_id} - {self.field_name}>"


class Amenity(Base):
    """Amenity model - charter add-ons like WiFi, drinks, etc."""
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=True)  # entertainment, refreshments, comfort
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Amenity {self.name} - ${self.price}>"


class QuoteAmenity(Base):
    """Quote amenity junction table - amenities added to quotes"""
    __tablename__ = "quote_amenities"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, nullable=False, index=True)
    amenity_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)  # Price at time of quote (frozen)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<QuoteAmenity quote={self.quote_id} amenity={self.amenity_id}>"


class PromoCode(Base):
    """Promotional code model - discount codes for marketing campaigns"""
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = Column(Float, nullable=False)
    min_order_value = Column(Float, nullable=True)  # Minimum order to apply
    max_discount = Column(Float, nullable=True)  # Max discount for percentage codes
    valid_from = Column(Date, nullable=False, index=True)
    valid_until = Column(Date, nullable=False, index=True)
    usage_limit = Column(Integer, nullable=True)  # NULL = unlimited
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<PromoCode {self.code} - {self.discount_type}>"


# ============================================================================
# PHASE 4 TASK 4.3: Pricing Configuration System
# ============================================================================

class PricingModifier(Base):
    """
    Dynamic pricing modifiers for advanced pricing control - Phase 4 Task 4.3
    Allows managers to configure pricing adjustments based on various conditions
    """
    __tablename__ = "pricing_modifiers"
    __table_args__ = {'schema': 'pricing'}

    id = Column(Integer, primary_key=True, index=True)
    modifier_name = Column(String(100), nullable=False)
    modifier_type = Column(String(50), nullable=False, index=True)  # seasonal, day_of_week, time_of_day, distance, passenger_count, event_type, custom
    
    # Condition logic
    condition_field = Column(String(100), nullable=True)  # Field to evaluate
    condition_operator = Column(String(20), nullable=True)  # equals, greater_than, less_than, in, between, etc.
    condition_value = Column(String(255), nullable=True)  # Value to compare against
    
    # Adjustment
    adjustment_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    adjustment_value = Column(Numeric(10, 2), nullable=False)  # Can be positive or negative
    
    # Priority and activation
    priority = Column(Integer, default=0, index=True)  # Higher priority applied first
    is_active = Column(Boolean, default=True, index=True)
    
    # Date range (for seasonal modifiers)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PricingModifier {self.modifier_name} ({self.adjustment_type}: {self.adjustment_value})>"


class PricingModifierLog(Base):
    """
    Audit trail of applied pricing modifiers - Phase 4 Task 4.3
    Tracks when and how modifiers are applied to quotes/charters
    """
    __tablename__ = "pricing_modifier_log"
    __table_args__ = {'schema': 'pricing'}

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, nullable=True, index=True)
    charter_id = Column(Integer, nullable=True, index=True)
    modifier_id = Column(Integer, ForeignKey('pricing.pricing_modifiers.id'), nullable=False, index=True)
    
    base_price = Column(Numeric(10, 2), nullable=False)
    adjusted_price = Column(Numeric(10, 2), nullable=False)
    adjustment_amount = Column(Numeric(10, 2), nullable=False)
    
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<PricingModifierLog modifier={self.modifier_id} amount={self.adjustment_amount}>"


class GeocodingCache(Base):
    """Cache for geocoded addresses - Task 8.2"""
    __tablename__ = "geocoding_cache"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="valid_coordinates"
        ),
        {'schema': 'pricing'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Input address
    address_text = Column(Text, nullable=False)
    address_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Geocoded location
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    formatted_address = Column(Text)
    
    # Address components
    street_number = Column(String(50))
    street_name = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(50))
    
    # Metadata
    confidence_score = Column(DECIMAL(10, 4))  # TomTom returns values 0-100
    geocoding_provider = Column(String(50), default='tomtom')
    
    # Audit
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, server_default=func.now())
    use_count = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<GeocodingCache {self.city}, {self.state} ({self.latitude}, {self.longitude})>"
