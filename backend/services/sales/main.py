"""
Sales Service - Lead Management and Assignment
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import engine, SessionLocal, Base, get_db
from models import Lead, LeadActivity, AssignmentRule, EmailPreference, LeadStatus
from schemas import (
    LeadCreate, LeadUpdate, LeadResponse,
    LeadActivityCreate, LeadActivityResponse,
    AssignmentRuleCreate, AssignmentRuleUpdate, AssignmentRuleResponse,
    LeadConversionRequest, LeadConversionResponse,
    EmailPreferenceUpdate, EmailPreferenceResponse
)
from business_logic import LeadAssignmentService, LeadConversionService
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create schema if it doesn't exist
with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {config.SCHEMA_NAME}"))
    conn.commit()

# Create database tables in the schema
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Athena Sales Service",
    description="Lead management and sales pipeline service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sales"}


# ==================== LEAD ENDPOINTS ====================

@app.post("/api/v1/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new lead and auto-assign to an agent
    """
    try:
        # Create lead
        lead = Lead(**lead_data.dict())
        db.add(lead)
        db.flush()  # Get lead.id without committing
        
        # Auto-assign to agent
        assigned_agent_id = await LeadAssignmentService.assign_lead_to_agent(db, lead)
        if assigned_agent_id:
            lead.assigned_agent_id = assigned_agent_id
            lead.assigned_at = datetime.now()
        
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Created lead {lead.id}, assigned to agent {assigned_agent_id}")
        return lead
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/leads", response_model=List[LeadResponse])
async def get_leads(
    status: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get leads with optional filters
    """
    query = db.query(Lead)
    
    if status:
        query = query.filter(Lead.status == status)
    if assigned_to:
        query = query.filter(Lead.assigned_agent_id == assigned_to)
    if created_after:
        query = query.filter(Lead.created_at >= created_after)
    if created_before:
        query = query.filter(Lead.created_at <= created_before)
    
    leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    return leads


@app.get("/api/v1/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.put("/api/v1/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db)
):
    """Update a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Update fields
    update_data = lead_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/v1/leads/my-leads", response_model=List[LeadResponse])
async def get_my_leads(
    agent_id: int = Query(..., description="Current user's agent ID"),
    db: Session = Depends(get_db)
):
    """Get leads assigned to current user"""
    leads = db.query(Lead).filter(
        Lead.assigned_agent_id == agent_id
    ).order_by(Lead.created_at.desc()).all()
    return leads


@app.get("/api/v1/leads/pipeline", response_model=dict)
async def get_pipeline_view(
    assigned_to: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get pipeline view grouped by status
    """
    query = db.query(Lead)
    if assigned_to:
        query = query.filter(Lead.assigned_agent_id == assigned_to)
    
    # Group by status
    pipeline = {}
    for status_value in LeadStatus:
        count = query.filter(Lead.status == status_value).count()
        leads = query.filter(Lead.status == status_value).order_by(Lead.created_at.desc()).limit(10).all()
        pipeline[status_value.value] = {
            "count": count,
            "leads": [LeadResponse.from_orm(lead) for lead in leads]
        }
    
    return pipeline


# ==================== LEAD ACTIVITY ENDPOINTS ====================

@app.post("/api/v1/leads/{lead_id}/activities", response_model=LeadActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_activity(
    lead_id: int,
    activity_data: LeadActivityCreate,
    user_id: int = Query(..., description="Current user ID"),
    db: Session = Depends(get_db)
):
    """Log an activity for a lead"""
    # Verify lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Create activity
    activity = LeadActivity(
        lead_id=lead_id,
        performed_by=user_id,
        **activity_data.dict()
    )
    db.add(activity)
    
    # Update lead follow-up count if it's a follow-up activity
    if activity_data.activity_type in ["call", "email"]:
        lead.follow_up_count += 1
    
    db.commit()
    db.refresh(activity)
    return activity


@app.get("/api/v1/leads/{lead_id}/activities", response_model=List[LeadActivityResponse])
async def get_lead_activities(lead_id: int, db: Session = Depends(get_db)):
    """Get all activities for a lead"""
    activities = db.query(LeadActivity).filter(
        LeadActivity.lead_id == lead_id
    ).order_by(LeadActivity.created_at.desc()).all()
    return activities


# ==================== LEAD CONVERSION ====================

@app.post("/api/v1/leads/{lead_id}/convert", response_model=LeadConversionResponse)
async def convert_lead(
    lead_id: int,
    conversion_data: LeadConversionRequest,
    user_id: int = Query(..., description="Current user ID"),
    db: Session = Depends(get_db)
):
    """
    Convert a lead to a client and charter
    """
    # Get lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.status == LeadStatus.CONVERTED:
        raise HTTPException(status_code=400, detail="Lead already converted")
    
    # Perform conversion
    result = await LeadConversionService.convert_lead(db, lead, user_id)
    
    if result.get("errors"):
        return LeadConversionResponse(
            success=False,
            lead_id=lead_id,
            message=f"Conversion failed: {', '.join(result['errors'])}"
        )
    
    return LeadConversionResponse(
        success=True,
        lead_id=lead_id,
        client_id=result["client_id"],
        charter_id=result["charter_id"],
        message="Lead successfully converted"
    )


# ==================== ASSIGNMENT RULE ENDPOINTS ====================

@app.post("/api/v1/assignment-rules", response_model=AssignmentRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment_rule(
    rule_data: AssignmentRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new assignment rule for an agent"""
    # Check if rule already exists
    existing = db.query(AssignmentRule).filter(
        AssignmentRule.agent_id == rule_data.agent_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Assignment rule already exists for this agent")
    
    rule = AssignmentRule(**rule_data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@app.get("/api/v1/assignment-rules", response_model=List[AssignmentRuleResponse])
async def get_assignment_rules(db: Session = Depends(get_db)):
    """Get all assignment rules"""
    rules = db.query(AssignmentRule).order_by(AssignmentRule.agent_name).all()
    return rules


@app.put("/api/v1/assignment-rules/{agent_id}", response_model=AssignmentRuleResponse)
async def update_assignment_rule(
    agent_id: int,
    rule_data: AssignmentRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an assignment rule"""
    rule = db.query(AssignmentRule).filter(AssignmentRule.agent_id == agent_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Assignment rule not found")
    
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    return rule


# ==================== EMAIL PREFERENCES ====================

@app.get("/api/v1/email-preferences/{client_id}", response_model=EmailPreferenceResponse)
async def get_email_preferences(client_id: int, db: Session = Depends(get_db)):
    """Get email preferences for a client"""
    prefs = db.query(EmailPreference).filter(EmailPreference.client_id == client_id).first()
    if not prefs:
        # Create default preferences
        prefs = EmailPreference(client_id=client_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@app.put("/api/v1/email-preferences/{client_id}", response_model=EmailPreferenceResponse)
async def update_email_preferences(
    client_id: int,
    prefs_data: EmailPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update email preferences for a client"""
    prefs = db.query(EmailPreference).filter(EmailPreference.client_id == client_id).first()
    if not prefs:
        prefs = EmailPreference(client_id=client_id)
        db.add(prefs)
    
    update_data = prefs_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    return prefs


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
