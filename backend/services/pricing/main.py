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
from models import PricingRule, QuoteCalculation, PriceHistory
from schemas import (
    PricingRuleCreate, PricingRuleUpdate, PricingRuleResponse,
    QuoteRequest, QuoteResponse,
    QuoteCalculationResponse, PriceHistoryResponse,
    RuleTypeEnum, RuleScopeEnum
)
from business_logic import PricingEngine

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
