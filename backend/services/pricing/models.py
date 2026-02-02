"""
Database models for Pricing Service
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, Enum as SQLEnum
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
