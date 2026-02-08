"""
Pricing Service - FastAPI application
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging

import config
from database import get_db, engine
from models import PricingRule, QuoteCalculation, PriceHistory, Amenity, QuoteAmenity, PromoCode, PricingModifier, PricingModifierLog, GeocodingCache
from schemas import (
    PricingRuleCreate, PricingRuleUpdate, PricingRuleResponse,
    QuoteRequest, QuoteResponse,
    QuoteCalculationResponse, PriceHistoryResponse,
    RuleTypeEnum, RuleScopeEnum,
    AmenityCreate, AmenityUpdate, AmenityResponse,
    QuoteAmenityAdd, QuoteAmenityResponse,
    PromoCodeCreate, PromoCodeResponse, ApplyPromoCodeRequest,
    PricingModifierCreate, PricingModifierUpdate, PricingModifierResponse, PricingModifierLogResponse,
    GeocodeRequest, GeocodeResponse, ReverseGeocodeRequest, ReverseGeocodeResponse,
    AutocompleteRequest, AutocompleteResponse, RouteRequest, RouteResponse, AutocompleteSuggestion,
    MultiVehiclePricingRequest, MultiVehiclePricingResponse, VehicleBreakdown
)
import schemas
from business_logic import PricingEngine
from tomtom_client import TomTomClient
import dot_compliance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pricing Service", version="1.0.0")


# Startup: Create schema if it doesn't exist
@app.on_event("startup")
async def startup_event():
    """Create pricing schema and tables on startup"""
    logger.info("Starting Pricing Service...")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {config.SCHEMA_NAME}"))
        conn.commit()
    
    # Create tables
    from models import Base
    Base.metadata.create_all(bind=engine)
    logger.info(f"Schema '{config.SCHEMA_NAME}' and tables created successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pricing-service",
        "version": "1.0.0"
    }


# ============================================================================
# Pricing Rules Endpoints
# ============================================================================

@app.post("/pricing-rules", response_model=PricingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    rule: PricingRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new pricing rule"""
    logger.info(f"Creating pricing rule: {rule.name}")
    
    db_rule = PricingRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    logger.info(f"Pricing rule created with ID: {db_rule.id}")
    return db_rule


@app.get("/pricing-rules", response_model=List[PricingRuleResponse])
async def get_pricing_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    rule_type: Optional[RuleTypeEnum] = None,
    scope: Optional[RuleScopeEnum] = None,
    is_active: Optional[bool] = None,
    client_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all pricing rules with optional filters"""
    query = db.query(PricingRule)
    
    if rule_type:
        query = query.filter(PricingRule.rule_type == rule_type.value)
    
    if scope:
        query = query.filter(PricingRule.scope == scope.value)
    
    if is_active is not None:
        query = query.filter(PricingRule.is_active == is_active)
    
    if client_id:
        query = query.filter(PricingRule.client_id == client_id)
    
    if vehicle_id:
        query = query.filter(PricingRule.vehicle_id == vehicle_id)
    
    rules = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(rules)} pricing rules")
    return rules


@app.get("/pricing-rules/{rule_id}", response_model=PricingRuleResponse)
async def get_pricing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific pricing rule by ID"""
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    
    if not rule:
        logger.warning(f"Pricing rule {rule_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with ID {rule_id} not found"
        )
    
    return rule


@app.put("/pricing-rules/{rule_id}", response_model=PricingRuleResponse)
async def update_pricing_rule(
    rule_id: int,
    rule_update: PricingRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing pricing rule"""
    logger.info(f"Updating pricing rule {rule_id}")
    
    db_rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not db_rule:
        logger.warning(f"Pricing rule {rule_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with ID {rule_id} not found"
        )
    
    # Track changes for history
    changes = []
    update_data = rule_update.model_dump(exclude_unset=True)
    
    for field, new_value in update_data.items():
        old_value = getattr(db_rule, field)
        if old_value != new_value:
            changes.append({
                "field": field,
                "old_value": str(old_value) if old_value else None,
                "new_value": str(new_value) if new_value else None
            })
            setattr(db_rule, field, new_value)
    
    # Save price history
    for change in changes:
        history = PriceHistory(
            rule_id=rule_id,
            field_name=change["field"],
            old_value=change["old_value"],
            new_value=change["new_value"],
            change_reason=f"Rule updated via API"
        )
        db.add(history)
    
    db.commit()
    db.refresh(db_rule)
    
    logger.info(f"Pricing rule {rule_id} updated with {len(changes)} changes")
    return db_rule


@app.delete("/pricing-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pricing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Delete a pricing rule (soft delete by setting is_active=False)"""
    logger.info(f"Deleting pricing rule {rule_id}")
    
    db_rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not db_rule:
        logger.warning(f"Pricing rule {rule_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with ID {rule_id} not found"
        )
    
    # Soft delete
    db_rule.is_active = False
    
    # Add to history
    history = PriceHistory(
        rule_id=rule_id,
        field_name="is_active",
        old_value="True",
        new_value="False",
        change_reason="Rule deleted via API"
    )
    db.add(history)
    
    db.commit()
    logger.info(f"Pricing rule {rule_id} deactivated")
    return None


# ============================================================================
# Quote Calculation Endpoints
# ============================================================================

@app.post("/calculate-quote", response_model=QuoteResponse, status_code=status.HTTP_200_OK)
async def calculate_quote(
    request: QuoteRequest,
    save_calculation: bool = Query(True, description="Whether to save the calculation to database"),
    db: Session = Depends(get_db)
):
    """
    Calculate quote based on trip parameters and pricing rules
    
    This endpoint:
    1. Finds all applicable pricing rules
    2. Applies rules in priority order
    3. Calculates base costs, mileage, time-based costs
    4. Applies multipliers (weekend, overnight, holiday, seasonal)
    5. Enforces min/max constraints
    6. Returns detailed breakdown
    7. Optionally saves calculation for audit trail
    """
    logger.info(f"Calculating quote for client {request.client_id}")
    
    engine = PricingEngine(db)
    result = engine.calculate_quote(request)
    
    breakdown = result["breakdown"]
    rules_applied_ids = result["rules_applied_ids"]
    
    # Optionally save to database
    calculation_id = None
    if save_calculation:
        calculation = engine.save_quote_calculation(
            request=request,
            breakdown=breakdown,
            rules_applied_ids=rules_applied_ids
        )
        calculation_id = calculation.id
    
    response = QuoteResponse(
        calculation_id=calculation_id,
        breakdown=breakdown,
        expires_at=None if not save_calculation else (calculation.expires_at if save_calculation else None)
    )
    
    logger.info(f"Quote calculated: ${breakdown.total_cost:.2f} (saved: {save_calculation})")
    return response


@app.get("/quotes", response_model=List[QuoteCalculationResponse])
async def get_quote_calculations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    client_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Get quote calculation history with optional filters"""
    query = db.query(QuoteCalculation)
    
    if client_id:
        query = query.filter(QuoteCalculation.client_id == client_id)
    
    if charter_id:
        query = query.filter(QuoteCalculation.charter_id == charter_id)
    
    if status_filter:
        query = query.filter(QuoteCalculation.status == status_filter)
    
    # Order by most recent first
    query = query.order_by(QuoteCalculation.created_at.desc())
    
    calculations = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(calculations)} quote calculations")
    return calculations


@app.get("/quotes/{calculation_id}", response_model=QuoteCalculationResponse)
async def get_quote_calculation(
    calculation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific quote calculation by ID"""
    calculation = db.query(QuoteCalculation).filter(
        QuoteCalculation.id == calculation_id
    ).first()
    
    if not calculation:
        logger.warning(f"Quote calculation {calculation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote calculation with ID {calculation_id} not found"
        )
    
    return calculation


@app.patch("/quotes/{calculation_id}/status")
async def update_quote_status(
    calculation_id: int,
    new_status: str,
    db: Session = Depends(get_db)
):
    """Update the status of a quote calculation (e.g., draft -> accepted)"""
    logger.info(f"Updating quote {calculation_id} status to {new_status}")
    
    calculation = db.query(QuoteCalculation).filter(
        QuoteCalculation.id == calculation_id
    ).first()
    
    if not calculation:
        logger.warning(f"Quote calculation {calculation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote calculation with ID {calculation_id} not found"
        )
    
    calculation.status = new_status
    db.commit()
    db.refresh(calculation)
    
    logger.info(f"Quote {calculation_id} status updated to {new_status}")
    return {"message": "Status updated", "calculation_id": calculation_id, "new_status": new_status}


# ============================================================================
# Price History Endpoints
# ============================================================================

@app.get("/pricing-rules/{rule_id}/history", response_model=List[PriceHistoryResponse])
async def get_rule_history(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Get change history for a specific pricing rule"""
    # First check if rule exists
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        logger.warning(f"Pricing rule {rule_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with ID {rule_id} not found"
        )
    
    history = db.query(PriceHistory).filter(
        PriceHistory.rule_id == rule_id
    ).order_by(PriceHistory.changed_at.desc()).all()
    
    logger.info(f"Retrieved {len(history)} history records for rule {rule_id}")
    return history


# ============================================================================
# Amenities Endpoints
# ============================================================================

@app.get("/amenities", response_model=List[AmenityResponse])
async def get_amenities(
    category: Optional[str] = None,
    active_only: bool = Query(True, description="Only return active amenities"),
    db: Session = Depends(get_db)
):
    """Get all amenities with optional filtering"""
    query = db.query(Amenity)
    
    if active_only:
        query = query.filter(Amenity.is_active == True)
    
    if category:
        query = query.filter(Amenity.category == category)
    
    query = query.order_by(Amenity.category, Amenity.name)
    amenities = query.all()
    
    logger.info(f"Retrieved {len(amenities)} amenities")
    return amenities


@app.post("/amenities", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
    amenity: AmenityCreate,
    db: Session = Depends(get_db)
):
    """Create a new amenity"""
    logger.info(f"Creating amenity: {amenity.name}")
    
    db_amenity = Amenity(**amenity.model_dump())
    db.add(db_amenity)
    db.commit()
    db.refresh(db_amenity)
    
    logger.info(f"Amenity created with ID: {db_amenity.id}")
    return db_amenity


@app.post("/quotes/{quote_id}/amenities", status_code=status.HTTP_201_CREATED)
async def add_amenity_to_quote(
    quote_id: int,
    amenity_data: QuoteAmenityAdd,
    db: Session = Depends(get_db)
):
    """Add an amenity to a quote"""
    logger.info(f"Adding amenity to quote {quote_id}")
    
    # Verify quote exists
    quote = db.query(QuoteCalculation).filter(QuoteCalculation.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote {quote_id} not found"
        )
    
    # Get amenity
    amenity = db.query(Amenity).filter(Amenity.id == amenity_data.amenity_id).first()
    if not amenity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Amenity {amenity_data.amenity_id} not found"
        )
    
    # Check if already added
    existing = db.query(QuoteAmenity).filter(
        QuoteAmenity.quote_id == quote_id,
        QuoteAmenity.amenity_id == amenity_data.amenity_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amenity already added to quote"
        )
    
    # Create quote amenity (freeze price)
    db_quote_amenity = QuoteAmenity(
        quote_id=quote_id,
        amenity_id=amenity_data.amenity_id,
        quantity=amenity_data.quantity,
        price=amenity.price
    )
    
    db.add(db_quote_amenity)
    
    # Update quote total
    amenity_total = amenity.price * amenity_data.quantity
    quote.additional_fees = (quote.additional_fees or 0) + amenity_total
    quote.total_cost = quote.total_cost + amenity_total
    
    db.commit()
    db.refresh(db_quote_amenity)
    
    logger.info(f"Amenity {amenity_data.amenity_id} added to quote {quote_id}")
    return {
        "id": db_quote_amenity.id,
        "quote_id": quote_id,
        "amenity_id": amenity_data.amenity_id,
        "quantity": amenity_data.quantity,
        "price": db_quote_amenity.price,
        "created_at": db_quote_amenity.created_at
    }


@app.get("/quotes/{quote_id}/amenities")
async def get_quote_amenities(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Get all amenities for a quote"""
    # Verify quote exists
    quote = db.query(QuoteCalculation).filter(QuoteCalculation.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote {quote_id} not found"
        )
    
    # Get amenities
    amenities = db.query(QuoteAmenity, Amenity).join(
        Amenity, QuoteAmenity.amenity_id == Amenity.id
    ).filter(QuoteAmenity.quote_id == quote_id).all()
    
    result = []
    for quote_amenity, amenity in amenities:
        result.append({
            "id": quote_amenity.id,
            "quote_id": quote_id,
            "amenity_id": quote_amenity.amenity_id,
            "amenity_name": amenity.name,
            "quantity": quote_amenity.quantity,
            "price": quote_amenity.price,
            "total": quote_amenity.price * quote_amenity.quantity
        })
    
    logger.info(f"Retrieved {len(result)} amenities for quote {quote_id}")
    return result


# ============================================================================
# Promo Codes Endpoints
# ============================================================================

@app.get("/promo-codes", response_model=List[PromoCodeResponse])
async def get_promo_codes(
    active_only: bool = Query(True, description="Only return active promo codes"),
    db: Session = Depends(get_db)
):
    """Get all promo codes"""
    from datetime import date
    
    query = db.query(PromoCode)
    
    if active_only:
        today = date.today()
        query = query.filter(
            PromoCode.is_active == True,
            PromoCode.valid_from <= today,
            PromoCode.valid_until >= today
        )
    
    query = query.order_by(PromoCode.code)
    promo_codes = query.all()
    
    logger.info(f"Retrieved {len(promo_codes)} promo codes")
    return promo_codes


@app.post("/promo-codes", response_model=PromoCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    promo_code: PromoCodeCreate,
    db: Session = Depends(get_db)
):
    """Create a new promo code"""
    logger.info(f"Creating promo code: {promo_code.code}")
    
    # Check if code already exists
    existing = db.query(PromoCode).filter(PromoCode.code == promo_code.code.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Promo code '{promo_code.code}' already exists"
        )
    
    # Create promo code (uppercase the code)
    db_promo = PromoCode(**promo_code.model_dump())
    db_promo.code = db_promo.code.upper()
    
    db.add(db_promo)
    db.commit()
    db.refresh(db_promo)
    
    logger.info(f"Promo code created: {db_promo.code}")
    return db_promo


@app.post("/promo-codes/validate")
async def validate_promo_code(
    code: str = Query(..., min_length=1, max_length=50),
    order_value: float = Query(..., gt=0),
    db: Session = Depends(get_db)
):
    """Validate a promo code and calculate discount"""
    from datetime import date
    
    logger.info(f"Validating promo code: {code}")
    
    # Get promo code (case insensitive)
    promo = db.query(PromoCode).filter(PromoCode.code == code.upper()).first()
    
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promo code '{code}' not found"
        )
    
    # Check if active
    if not promo.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code is inactive"
        )
    
    # Check date validity
    today = date.today()
    if today < promo.valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Promo code not valid until {promo.valid_from}"
        )
    
    if today > promo.valid_until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Promo code expired on {promo.valid_until}"
        )
    
    # Check usage limit
    if promo.usage_limit and promo.usage_count >= promo.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code usage limit reached"
        )
    
    # Check minimum order value
    if promo.min_order_value and order_value < promo.min_order_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order value of ${promo.min_order_value} required"
        )
    
    # Calculate discount
    if promo.discount_type == "percentage":
        discount = order_value * (promo.discount_value / 100)
        # Apply max discount if set
        if promo.max_discount and discount > promo.max_discount:
            discount = promo.max_discount
    else:  # fixed
        discount = promo.discount_value
    
    # Don't allow discount greater than order value
    if discount > order_value:
        discount = order_value
    
    final_amount = order_value - discount
    
    logger.info(f"Promo code {code} valid: ${order_value} - ${discount} = ${final_amount}")
    
    return {
        "valid": True,
        "promo_code_id": promo.id,
        "code": promo.code,
        "description": promo.description,
        "discount_type": promo.discount_type,
        "discount_value": promo.discount_value,
        "order_value": order_value,
        "discount_amount": round(discount, 2),
        "final_amount": round(final_amount, 2)
    }


@app.post("/quotes/{quote_id}/apply-promo")
async def apply_promo_to_quote(
    quote_id: int,
    code: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(get_db)
):
    """Apply a promo code to a quote"""
    logger.info(f"Applying promo code {code} to quote {quote_id}")
    
    # Get quote
    quote = db.query(QuoteCalculation).filter(QuoteCalculation.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote {quote_id} not found"
        )
    
    # Validate promo code
    promo = db.query(PromoCode).filter(PromoCode.code == code.upper()).first()
    
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promo code '{code}' not found"
        )
    
    from datetime import date
    today = date.today()
    
    # Validate promo code
    if not promo.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code is inactive")
    
    if today < promo.valid_from or today > promo.valid_until:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code is not valid on this date")
    
    if promo.usage_limit and promo.usage_count >= promo.usage_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code usage limit reached")
    
    order_value = quote.total_cost
    
    if promo.min_order_value and order_value < promo.min_order_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order value of ${promo.min_order_value} required"
        )
    
    # Calculate discount
    if promo.discount_type == "percentage":
        discount = order_value * (promo.discount_value / 100)
        if promo.max_discount and discount > promo.max_discount:
            discount = promo.max_discount
    else:
        discount = promo.discount_value
    
    if discount > order_value:
        discount = order_value
    
    # Apply to quote
    quote.promo_code_id = promo.id
    quote.discount_amount = discount
    quote.total_cost = order_value - discount
    
    # Increment usage count
    promo.usage_count += 1
    
    db.commit()
    db.refresh(quote)
    
    logger.info(f"Promo code {code} applied to quote {quote_id}: ${discount} discount")
    
    return {
        "quote_id": quote_id,
        "promo_code": promo.code,
        "discount_amount": round(discount, 2),
        "original_total": round(order_value, 2),
        "final_total": round(quote.total_cost, 2)
    }


# ============================================================================
# DOT Compliance Endpoints
# ============================================================================

@app.post("/check-dot-compliance")
async def check_dot_compliance(
    distance_miles: float = Query(..., gt=0, description="Total trip distance in miles"),
    stops_count: int = Query(0, ge=0, description="Number of stops"),
    trip_hours: Optional[float] = Query(None, gt=0, description="Estimated trip duration"),
    is_multi_day: bool = Query(False, description="Whether trip spans multiple days"),
    driver_hours_this_week: float = Query(0, ge=0, description="Driver's hours already worked this week")
):
    """
    Check if a charter trip complies with DOT Hours of Service regulations.
    
    Returns compliance status, violations, warnings, and recommendations.
    """
    logger.info(f"Checking DOT compliance for {distance_miles} miles, {stops_count} stops")
    
    result = dot_compliance.check_dot_compliance(
        distance_miles=distance_miles,
        stops_count=stops_count,
        trip_hours=trip_hours,
        is_multi_day=is_multi_day,
        driver_hours_this_week=driver_hours_this_week
    )
    
    logger.info(f"DOT compliance check: {'COMPLIANT' if result['compliant'] else 'NON-COMPLIANT'}")
    
    return result


@app.get("/dot-compliance/estimate-hours")
async def estimate_hours(
    distance_miles: float = Query(..., gt=0),
    stops_count: int = Query(0, ge=0),
    trip_hours: Optional[float] = Query(None, gt=0)
):
    """Calculate estimated driving and duty hours for a trip"""
    logger.info(f"Estimating hours for {distance_miles} miles")
    
    result = dot_compliance.calculate_estimated_hours(
        distance_miles=distance_miles,
        stops_count=stops_count,
        trip_hours=trip_hours
    )
    
    return result


@app.get("/dot-compliance/second-driver-split")
async def second_driver_split(
    total_hours: float = Query(..., gt=0, description="Total trip hours")
):
    """Get recommendation for splitting hours between two drivers"""
    logger.info(f"Calculating second driver split for {total_hours} hours")
    
    result = dot_compliance.suggest_second_driver_split(total_hours)
    
    return result


# ============================================================================
# PHASE 4 TASK 4.3: Pricing Modifier Management
# ============================================================================

@app.get("/modifiers", response_model=List[PricingModifierResponse])
async def list_pricing_modifiers(
    is_active: Optional[bool] = None,
    modifier_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List pricing modifiers
    
    - Filter by active status
    - Filter by modifier type
    - Ordered by priority (highest first)
    """
    query = db.query(PricingModifier)
    
    if is_active is not None:
        query = query.filter(PricingModifier.is_active == is_active)
    
    if modifier_type:
        query = query.filter(PricingModifier.modifier_type == modifier_type)
    
    return query.order_by(PricingModifier.priority.desc()).offset(skip).limit(limit).all()


@app.post("/modifiers", response_model=PricingModifierResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_modifier(
    modifier: PricingModifierCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new pricing modifier
    
    Examples:
    - Weekend Premium: 15% increase on Sat/Sun
    - Holiday Premium: 25% increase on holidays
    - Large Group Discount: -10% for 50+ passengers
    - Long Distance Premium: 20% increase for 200+ miles
    """
    db_modifier = PricingModifier(**modifier.dict())
    db.add(db_modifier)
    db.commit()
    db.refresh(db_modifier)
    
    logger.info(f"Created pricing modifier: {db_modifier.modifier_name}")
    return db_modifier


@app.get("/modifiers/types/available")
async def get_available_modifier_types():
    """Get list of available modifier types for configuration"""
    return {
        "types": [
            {
                "value": "seasonal",
                "label": "Seasonal",
                "description": "Apply modifiers during specific seasons or date ranges"
            },
            {
                "value": "day_of_week",
                "label": "Day of Week",
                "description": "Apply modifiers on specific days (e.g., weekends)"
            },
            {
                "value": "time_of_day",
                "label": "Time of Day",
                "description": "Apply modifiers during specific hours (e.g., peak hours)"
            },
            {
                "value": "distance",
                "label": "Distance-Based",
                "description": "Apply modifiers based on trip distance"
            },
            {
                "value": "passenger_count",
                "label": "Passenger Count",
                "description": "Apply modifiers based on number of passengers"
            },
            {
                "value": "event_type",
                "label": "Event Type",
                "description": "Apply modifiers for specific event types"
            },
            {
                "value": "custom",
                "label": "Custom",
                "description": "Custom logic-based modifiers"
            }
        ],
        "operators": [
            "equals", "not_equals", "greater_than", "less_than",
            "greater_equal", "less_equal", "in", "between", "contains"
        ],
        "adjustment_types": [
            {"value": "percentage", "label": "Percentage", "example": "15.00 = 15% increase"},
            {"value": "fixed_amount", "label": "Fixed Amount", "example": "50.00 = $50 increase"}
        ]
    }


@app.get("/modifiers/{modifier_id}", response_model=PricingModifierResponse)
async def get_pricing_modifier(modifier_id: int, db: Session = Depends(get_db)):
    """Get a specific pricing modifier"""
    modifier = db.query(PricingModifier).filter(PricingModifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(status_code=404, detail="Pricing modifier not found")
    return modifier


@app.put("/modifiers/{modifier_id}", response_model=PricingModifierResponse)
async def update_pricing_modifier(
    modifier_id: int,
    modifier: PricingModifierUpdate,
    db: Session = Depends(get_db)
):
    """Update a pricing modifier"""
    db_modifier = db.query(PricingModifier).filter(PricingModifier.id == modifier_id).first()
    if not db_modifier:
        raise HTTPException(status_code=404, detail="Pricing modifier not found")
    
    for key, value in modifier.dict(exclude_unset=True).items():
        setattr(db_modifier, key, value)
    
    db.commit()
    db.refresh(db_modifier)
    
    logger.info(f"Updated pricing modifier {modifier_id}")
    return db_modifier


@app.delete("/modifiers/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pricing_modifier(modifier_id: int, db: Session = Depends(get_db)):
    """Delete a pricing modifier"""
    modifier = db.query(PricingModifier).filter(PricingModifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(status_code=404, detail="Pricing modifier not found")
    
    db.delete(modifier)
    db.commit()
    
    logger.info(f"Deleted pricing modifier {modifier_id}")
    return None


@app.get("/modifiers/{modifier_id}/application-history", response_model=List[PricingModifierLogResponse])
async def get_modifier_application_history(
    modifier_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get history of when this modifier was applied"""
    modifier = db.query(PricingModifier).filter(PricingModifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(status_code=404, detail="Pricing modifier not found")
    
    return db.query(PricingModifierLog)\
        .filter(PricingModifierLog.modifier_id == modifier_id)\
        .order_by(PricingModifierLog.applied_at.desc())\
        .offset(skip).limit(limit).all()


# ============================================================================
# Geocoding Endpoints - Task 8.2
# ============================================================================

@app.post("/geocode", response_model=GeocodeResponse, tags=["Geocoding"])
async def geocode_address(
    request: GeocodeRequest,
    db: Session = Depends(get_db)
):
    """
    Geocode an address to latitude/longitude coordinates.
    
    Uses TomTom API with caching to reduce API calls.
    """
    tomtom = TomTomClient()
    try:
        result = await tomtom.geocode(
            address=request.address,
            db=db,
            use_cache=request.use_cache
        )
        return GeocodeResponse(**result)
    finally:
        await tomtom.close()


@app.post("/reverse-geocode", response_model=ReverseGeocodeResponse, tags=["Geocoding"])
async def reverse_geocode_coordinates(
    request: ReverseGeocodeRequest
):
    """
    Reverse geocode latitude/longitude to an address.
    
    Converts coordinates back to a human-readable address.
    """
    tomtom = TomTomClient()
    try:
        result = await tomtom.reverse_geocode(
            latitude=request.latitude,
            longitude=request.longitude
        )
        return ReverseGeocodeResponse(**result)
    finally:
        await tomtom.close()


@app.post("/autocomplete", response_model=AutocompleteResponse, tags=["Geocoding"])
async def autocomplete_address(
    request: AutocompleteRequest
):
    """
    Get address suggestions as user types.
    
    Provides typeahead functionality for address input fields.
    Optionally biases results around a center point.
    """
    tomtom = TomTomClient()
    try:
        suggestions = await tomtom.autocomplete(
            query=request.query,
            center_lat=request.center_lat,
            center_lon=request.center_lon
        )
        return AutocompleteResponse(
            suggestions=[AutocompleteSuggestion(**s) for s in suggestions]
        )
    finally:
        await tomtom.close()


@app.post("/calculate-route", response_model=RouteResponse, tags=["Geocoding"])
async def calculate_route(
    request: RouteRequest
):
    """
    Calculate route distance and travel time between two points.
    
    Includes real-time traffic data for accurate ETAs.
    """
    tomtom = TomTomClient()
    try:
        result = await tomtom.calculate_route(
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon,
            dest_lat=request.dest_lat,
            dest_lon=request.dest_lon
        )
        return RouteResponse(**result)
    finally:
        await tomtom.close()


# ============================================================================
# Task 8.3: Multi-Vehicle Pricing
# ============================================================================

@app.post("/calculate-multi-vehicle", response_model=schemas.MultiVehiclePricingResponse, tags=["Pricing"])
async def calculate_multi_vehicle_price(
    request: schemas.MultiVehiclePricingRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate pricing for multi-vehicle charter.
    
    Distributes passengers evenly across vehicles and calculates cost per vehicle.
    **Note:** No bulk discount is applied. Each vehicle is priced independently.
    
    Example scenarios:
    - 100 passengers, 2 vehicles → 50 passengers per vehicle
    - 150 passengers, 3 vehicles → 50 passengers per vehicle
    - 155 passengers, 3 vehicles → 52, 52, 51 passengers (remainder distributed)
    
    Returns:
    - Detailed breakdown per vehicle
    - Total cost across all vehicles
    - Passenger distribution
    """
    try:
        from business_logic import MultiVehiclePricingEngine
        
        result = MultiVehiclePricingEngine.calculate_multi_vehicle_pricing(
            total_passengers=request.total_passengers,
            total_miles=request.total_miles,
            vehicle_count=request.vehicle_count,
            vehicle_type=request.vehicle_type,
            estimated_hours=request.estimated_hours,
            base_rate_per_mile=request.base_rate_per_mile,
            base_rate_per_hour=request.base_rate_per_hour
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Multi-vehicle pricing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-vehicle pricing calculation failed: {str(e)}"
        )


@app.get("/geocoding-cache/stats", tags=["Geocoding"])
async def get_cache_stats(db: Session = Depends(get_db)):
    """
    Get geocoding cache statistics.
    
    Returns metrics about cache usage and performance.
    """
    from sqlalchemy import func
    
    total_entries = db.query(func.count(GeocodingCache.id)).scalar()
    total_uses = db.query(func.sum(GeocodingCache.use_count)).scalar() or 0
    
    # Get most used addresses
    most_used = db.query(
        GeocodingCache.city,
        GeocodingCache.state,
        func.sum(GeocodingCache.use_count).label('uses')
    ).group_by(
        GeocodingCache.city,
        GeocodingCache.state
    ).order_by(
        func.sum(GeocodingCache.use_count).desc()
    ).limit(10).all()
    
    return {
        "total_cached_addresses": total_entries,
        "total_cache_hits": total_uses,
        "average_uses_per_address": round(total_uses / total_entries, 2) if total_entries > 0 else 0,
        "most_used_locations": [
            {"city": row.city, "state": row.state, "uses": row.uses}
            for row in most_used
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
