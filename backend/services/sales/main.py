"""
Sales Service - Lead Management and Assignment
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import engine, SessionLocal, Base, get_db
from models import (
    Lead, LeadActivity, AssignmentRule, EmailPreference, LeadStatus,
    FollowUp, LeadScoringRule, LeadScoreHistory, LeadTransfer,
    FollowUpType, FollowUpOutcome
)
from schemas import (
    LeadCreate, LeadUpdate, LeadResponse,
    LeadActivityCreate, LeadActivityResponse,
    AssignmentRuleCreate, AssignmentRuleUpdate, AssignmentRuleResponse,
    LeadConversionRequest, LeadConversionResponse,
    EmailPreferenceUpdate, EmailPreferenceResponse,
    FollowUpCreate, FollowUpUpdate, FollowUpComplete, FollowUpResponse,
    LeadScoringRuleCreate, LeadScoringRuleUpdate, LeadScoringRuleResponse,
    LeadScoreHistoryResponse, LeadScoreCalculateRequest,
    LeadTransferCreate, BulkLeadTransferCreate, LeadTransferResponse
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


@app.delete("/api/v1/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Delete a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        # Delete the lead - cascade will handle related records
        db.delete(lead)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete lead: {str(e)}")


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


# ==================== Phase 3: Sales & Lead Management Endpoints ====================

# Task 3.1: Follow-Up Tracking System

@app.post("/api/v1/follow-ups", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
def create_follow_up(
    follow_up_data: FollowUpCreate,
    current_user_id: int = Query(1, description="Current user ID"),
    db: Session = Depends(get_db)
):
    """
    Create a new follow-up task for a lead
    """
    # Verify lead exists
    lead = db.query(Lead).filter(Lead.id == follow_up_data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Use current user if assigned_to not provided
    assigned_to = follow_up_data.assigned_to if follow_up_data.assigned_to else current_user_id
    
    # Create follow-up
    follow_up = FollowUp(
        lead_id=follow_up_data.lead_id,
        follow_up_type=follow_up_data.follow_up_type,
        scheduled_date=follow_up_data.scheduled_date,
        scheduled_time=follow_up_data.scheduled_time,
        notes=follow_up_data.notes,
        assigned_to=assigned_to
    )
    
    db.add(follow_up)
    
    # Update lead follow-up tracking
    lead.next_follow_up_date = follow_up_data.scheduled_date
    lead.follow_up_count += 1
    
    db.commit()
    db.refresh(follow_up)
    
    logger.info(f"Created follow-up {follow_up.id} for lead {lead.id}")
    return follow_up


@app.get("/api/v1/follow-ups/my-tasks", response_model=List[FollowUpResponse])
def get_my_follow_ups(
    current_user_id: int = Query(1, description="Current user ID"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    overdue_only: bool = Query(False, description="Show only overdue tasks"),
    db: Session = Depends(get_db)
):
    """
    Get follow-up tasks assigned to current user
    """
    query = db.query(FollowUp).filter(FollowUp.assigned_to == current_user_id)
    
    if completed is not None:
        query = query.filter(FollowUp.completed == completed)
    
    if overdue_only:
        query = query.filter(
            FollowUp.completed == False,
            FollowUp.scheduled_date < datetime.now().date()
        )
    
    follow_ups = query.order_by(FollowUp.scheduled_date.asc()).all()
    return follow_ups


@app.get("/api/v1/leads/{lead_id}/follow-ups", response_model=List[FollowUpResponse])
def get_lead_follow_ups(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all follow-up tasks for a specific lead
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    follow_ups = db.query(FollowUp).filter(
        FollowUp.lead_id == lead_id
    ).order_by(FollowUp.scheduled_date.desc()).all()
    
    return follow_ups


@app.post("/api/v1/follow-ups/{follow_up_id}/complete", response_model=FollowUpResponse)
def complete_follow_up(
    follow_up_id: int,
    completion_data: FollowUpComplete,
    current_user_id: int = Query(1, description="Current user ID"),
    db: Session = Depends(get_db)
):
    """
    Mark a follow-up task as complete with outcome
    """
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    if follow_up.completed:
        raise HTTPException(status_code=400, detail="Follow-up already completed")
    
    # Update follow-up
    follow_up.completed = True
    follow_up.completed_at = datetime.now()
    follow_up.completed_by = current_user_id
    follow_up.outcome = completion_data.outcome
    if completion_data.notes:
        follow_up.notes = completion_data.notes
    
    # Update lead's last follow-up date
    lead = db.query(Lead).filter(Lead.id == follow_up.lead_id).first()
    if lead:
        lead.last_follow_up_date = datetime.now()
    
    # Create activity record
    activity = LeadActivity(
        lead_id=follow_up.lead_id,
        activity_type="note",
        subject=f"Follow-up completed: {follow_up.follow_up_type.value}",
        details=f"Outcome: {completion_data.outcome.value}. Notes: {completion_data.notes or 'None'}",
        performed_by=current_user_id
    )
    db.add(activity)
    follow_up.activity_id = activity.id
    
    db.commit()
    db.refresh(follow_up)
    
    logger.info(f"Completed follow-up {follow_up_id} with outcome {completion_data.outcome}")
    return follow_up


@app.get("/api/v1/reports/follow-up-performance", response_model=dict)
def get_follow_up_performance(
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get follow-up performance metrics
    """
    query = db.query(FollowUp)
    
    if agent_id:
        query = query.filter(FollowUp.assigned_to == agent_id)
    
    if start_date:
        query = query.filter(FollowUp.created_at >= start_date)
    
    if end_date:
        query = query.filter(FollowUp.created_at <= end_date)
    
    follow_ups = query.all()
    
    total_count = len(follow_ups)
    completed_count = len([f for f in follow_ups if f.completed])
    pending_count = total_count - completed_count
    
    # Outcome breakdown
    outcomes = {}
    for f in follow_ups:
        if f.outcome:
            outcome_str = f.outcome.value
            outcomes[outcome_str] = outcomes.get(outcome_str, 0) + 1
    
    # Overdue count
    now = datetime.now().date()
    overdue_count = len([f for f in follow_ups if not f.completed and f.scheduled_date.date() < now])
    
    return {
        "total_follow_ups": total_count,
        "completed": completed_count,
        "pending": pending_count,
        "overdue": overdue_count,
        "completion_rate": round(completed_count / total_count * 100, 2) if total_count > 0 else 0,
        "outcome_breakdown": outcomes
    }


# Task 3.2: Lead Scoring System

def calculate_lead_score(lead: Lead, db: Session) -> int:
    """Calculate lead score based on active scoring rules"""
    score = 0
    rules = db.query(LeadScoringRule).filter(LeadScoringRule.is_active == True).all()
    
    for rule in rules:
        if rule.rule_type.value == "attribute":
            # Evaluate attribute-based rules
            if rule.attribute_field and hasattr(lead, rule.attribute_field):
                value = getattr(lead, rule.attribute_field)
                if value is not None and rule.condition_operator and rule.condition_value:
                    try:
                        if rule.condition_operator == ">":
                            if float(value) > float(rule.condition_value):
                                score += rule.points
                        elif rule.condition_operator == ">=":
                            if float(value) >= float(rule.condition_value):
                                score += rule.points
                        elif rule.condition_operator == "<":
                            if float(value) < float(rule.condition_value):
                                score += rule.points
                        elif rule.condition_operator == "<=":
                            if float(value) <= float(rule.condition_value):
                                score += rule.points
                        elif rule.condition_operator == "==":
                            if str(value) == rule.condition_value:
                                score += rule.points
                    except (ValueError, TypeError):
                        pass
        elif rule.rule_type.value == "activity":
            # Activity-based scoring (e.g., number of activities)
            activity_count = db.query(LeadActivity).filter(LeadActivity.lead_id == lead.id).count()
            if activity_count > 0:
                score += rule.points
        elif rule.rule_type.value == "engagement":
            # Engagement-based scoring (e.g., has follow-ups)
            follow_up_count = db.query(FollowUp).filter(FollowUp.lead_id == lead.id).count()
            if follow_up_count > 0:
                score += rule.points
    
    return max(0, score)  # Ensure non-negative


@app.post("/api/v1/leads/{lead_id}/calculate-score", response_model=LeadResponse)
def recalculate_lead_score(
    lead_id: int,
    score_request: LeadScoreCalculateRequest,
    current_user_id: int = Query(1, description="Current user ID"),
    db: Session = Depends(get_db)
):
    """
    Recalculate lead score based on active scoring rules
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    old_score = lead.score
    new_score = calculate_lead_score(lead, db)
    
    # Update lead score
    lead.score = new_score
    lead.score_updated_at = datetime.now()
    
    # Record score history
    if old_score != new_score:
        history = LeadScoreHistory(
            lead_id=lead_id,
            old_score=old_score,
            new_score=new_score,
            reason=score_request.reason,
            changed_by=current_user_id
        )
        db.add(history)
    
    db.commit()
    db.refresh(lead)
    
    logger.info(f"Recalculated score for lead {lead_id}: {old_score} → {new_score}")
    return lead


@app.get("/api/v1/leads/high-score", response_model=List[LeadResponse])
def get_high_score_leads(
    min_score: int = Query(50, description="Minimum score threshold"),
    limit: int = Query(20, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get leads with high scores (hot leads)
    """
    leads = db.query(Lead).filter(
        Lead.score >= min_score,
        Lead.status != LeadStatus.CONVERTED,
        Lead.status != LeadStatus.DEAD
    ).order_by(Lead.score.desc()).limit(limit).all()
    
    return leads


@app.get("/api/v1/leads/{lead_id}/score-history", response_model=List[LeadScoreHistoryResponse])
def get_lead_score_history(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get score change history for a lead
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    history = db.query(LeadScoreHistory).filter(
        LeadScoreHistory.lead_id == lead_id
    ).order_by(LeadScoreHistory.created_at.desc()).all()
    
    return history


@app.get("/api/v1/scoring/rules", response_model=List[LeadScoringRuleResponse])
def get_scoring_rules(
    active_only: bool = Query(False, description="Show only active rules"),
    db: Session = Depends(get_db)
):
    """
    Get all lead scoring rules
    """
    query = db.query(LeadScoringRule)
    if active_only:
        query = query.filter(LeadScoringRule.is_active == True)
    
    rules = query.order_by(LeadScoringRule.rule_name).all()
    return rules


@app.post("/api/v1/scoring/rules", response_model=LeadScoringRuleResponse, status_code=status.HTTP_201_CREATED)
def create_scoring_rule(
    rule_data: LeadScoringRuleCreate,
    current_user_id: int = Query(1, description="Current user ID (manager only)"),
    db: Session = Depends(get_db)
):
    """
    Create a new lead scoring rule (manager only)
    """
    # Check if rule name already exists
    existing = db.query(LeadScoringRule).filter(LeadScoringRule.rule_name == rule_data.rule_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule name already exists")
    
    rule = LeadScoringRule(**rule_data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    logger.info(f"Created scoring rule: {rule.rule_name}")
    return rule


@app.put("/api/v1/scoring/rules/{rule_id}", response_model=LeadScoringRuleResponse)
def update_scoring_rule(
    rule_id: int,
    rule_data: LeadScoringRuleUpdate,
    current_user_id: int = Query(1, description="Current user ID (manager only)"),
    db: Session = Depends(get_db)
):
    """
    Update a lead scoring rule (manager only)
    """
    rule = db.query(LeadScoringRule).filter(LeadScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Scoring rule not found")
    
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    
    logger.info(f"Updated scoring rule {rule_id}")
    return rule


@app.post("/api/v1/scoring/recalculate-all", response_model=dict)
def recalculate_all_scores(
    current_user_id: int = Query(1, description="Current user ID (manager only)"),
    db: Session = Depends(get_db)
):
    """
    Recalculate scores for all active leads (bulk operation)
    """
    leads = db.query(Lead).filter(
        Lead.status != LeadStatus.CONVERTED,
        Lead.status != LeadStatus.DEAD
    ).all()
    
    updated_count = 0
    for lead in leads:
        old_score = lead.score
        new_score = calculate_lead_score(lead, db)
        
        if old_score != new_score:
            lead.score = new_score
            lead.score_updated_at = datetime.now()
            
            history = LeadScoreHistory(
                lead_id=lead.id,
                old_score=old_score,
                new_score=new_score,
                reason="Bulk recalculation",
                changed_by=current_user_id
            )
            db.add(history)
            updated_count += 1
    
    db.commit()
    
    logger.info(f"Recalculated scores for {updated_count} leads")
    return {
        "total_leads": len(leads),
        "updated_count": updated_count,
        "message": f"Recalculated scores for {updated_count} of {len(leads)} active leads"
    }


# Task 3.3: Lead Ownership Transfer

@app.post("/api/v1/leads/{lead_id}/transfer", response_model=LeadTransferResponse, status_code=status.HTTP_201_CREATED)
def transfer_lead(
    lead_id: int,
    transfer_data: LeadTransferCreate,
    current_user_id: int = Query(1, description="Current user ID"),
    db: Session = Depends(get_db)
):
    """
    Transfer lead ownership to another agent
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not lead.assigned_agent_id:
        raise HTTPException(status_code=400, detail="Lead is not currently assigned")
    
    if lead.assigned_agent_id == transfer_data.to_agent_id:
        raise HTTPException(status_code=400, detail="Lead is already assigned to this agent")
    
    # Record transfer
    transfer = LeadTransfer(
        lead_id=lead_id,
        from_agent_id=lead.assigned_agent_id,
        to_agent_id=transfer_data.to_agent_id,
        reason=transfer_data.reason,
        transferred_by=current_user_id
    )
    db.add(transfer)
    
    # Update lead assignment
    old_agent_id = lead.assigned_agent_id
    lead.assigned_agent_id = transfer_data.to_agent_id
    lead.assigned_at = datetime.now()
    
    # Create activity record
    activity = LeadActivity(
        lead_id=lead_id,
        activity_type="note",
        subject="Lead transferred",
        details=f"Lead transferred from agent {old_agent_id} to agent {transfer_data.to_agent_id}. Reason: {transfer_data.reason or 'Not specified'}",
        performed_by=current_user_id
    )
    db.add(activity)
    
    db.commit()
    db.refresh(transfer)
    
    logger.info(f"Transferred lead {lead_id} from agent {old_agent_id} to agent {transfer_data.to_agent_id}")
    return transfer


@app.post("/api/v1/leads/bulk-transfer", response_model=dict)
def bulk_transfer_leads(
    transfer_data: BulkLeadTransferCreate,
    current_user_id: int = Query(1, description="Current user ID"),
    db: Session = Depends(get_db)
):
    """
    Transfer multiple leads to a new agent
    """
    transferred_count = 0
    errors = []
    
    for lead_id in transfer_data.lead_ids:
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                errors.append(f"Lead {lead_id}: not found")
                continue
            
            if not lead.assigned_agent_id:
                errors.append(f"Lead {lead_id}: not assigned")
                continue
            
            if lead.assigned_agent_id == transfer_data.to_agent_id:
                errors.append(f"Lead {lead_id}: already assigned to target agent")
                continue
            
            # Record transfer
            transfer = LeadTransfer(
                lead_id=lead_id,
                from_agent_id=lead.assigned_agent_id,
                to_agent_id=transfer_data.to_agent_id,
                reason=transfer_data.reason,
                transferred_by=current_user_id
            )
            db.add(transfer)
            
            # Update lead
            lead.assigned_agent_id = transfer_data.to_agent_id
            lead.assigned_at = datetime.now()
            
            transferred_count += 1
            
        except Exception as e:
            errors.append(f"Lead {lead_id}: {str(e)}")
    
    db.commit()
    
    logger.info(f"Bulk transferred {transferred_count} of {len(transfer_data.lead_ids)} leads to agent {transfer_data.to_agent_id}")
    
    return {
        "total_requested": len(transfer_data.lead_ids),
        "transferred": transferred_count,
        "errors": errors,
        "message": f"Successfully transferred {transferred_count} of {len(transfer_data.lead_ids)} leads"
    }


@app.get("/api/v1/leads/{lead_id}/transfer-history", response_model=List[LeadTransferResponse])
def get_lead_transfer_history(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Get transfer history for a lead
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    transfers = db.query(LeadTransfer).filter(
        LeadTransfer.lead_id == lead_id
    ).order_by(LeadTransfer.created_at.desc()).all()
    
    return transfers


# ==================== DASHBOARD & METRICS ENDPOINTS ====================

@app.get("/api/v1/sales/metrics")
def get_sales_metrics(
    period: str = Query("today", description="Period: today, week, month, quarter"),
    agent_id: Optional[int] = Query(None, description="Filter by agent"),
    db: Session = Depends(get_db)
):
    """
    Get sales metrics for dashboard
    """
    # Calculate date range based on period
    now = datetime.now()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=30)
    
    # Base query
    query = db.query(Lead).filter(Lead.created_at >= start_date)
    if agent_id:
        query = query.filter(Lead.assigned_agent_id == agent_id)
    
    # Get all leads in period
    all_leads = query.all()
    
    # Calculate metrics
    total_leads = len(all_leads)
    new_leads = len([l for l in all_leads if l.status == LeadStatus.NEW])
    contacted = len([l for l in all_leads if l.status == LeadStatus.CONTACTED])
    qualified = len([l for l in all_leads if l.status == LeadStatus.QUALIFIED])
    converted = len([l for l in all_leads if l.status == LeadStatus.CONVERTED])
    
    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
    
    # Calculate average response time (time from creation to first activity)
    avg_response_hours = 0
    response_times = []
    for lead in all_leads:
        first_activity = db.query(LeadActivity).filter(
            LeadActivity.lead_id == lead.id
        ).order_by(LeadActivity.created_at.asc()).first()
        
        if first_activity:
            delta = first_activity.created_at - lead.created_at
            response_times.append(delta.total_seconds() / 3600)
    
    if response_times:
        avg_response_hours = sum(response_times) / len(response_times)
    
    return {
        "period": period,
        "total_leads": total_leads,
        "new_leads": new_leads,
        "contacted": contacted,
        "qualified": qualified,
        "converted": converted,
        "conversion_rate": round(conversion_rate, 2),
        "avg_response_time_hours": round(avg_response_hours, 2),
        "active_agents": len(set([l.assigned_agent_id for l in all_leads if l.assigned_agent_id]))
    }


@app.get("/api/v1/sales/funnel")
def get_conversion_funnel(
    period: str = Query("month", description="Period: week, month, quarter"),
    db: Session = Depends(get_db)
):
    """
    Get conversion funnel data
    """
    # Calculate date range
    now = datetime.now()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=30)
    
    # Get leads in period
    leads = db.query(Lead).filter(Lead.created_at >= start_date).all()
    
    # Count by status
    total = len(leads)
    new = len([l for l in leads if l.status == LeadStatus.NEW])
    contacted = len([l for l in leads if l.status == LeadStatus.CONTACTED])
    qualified = len([l for l in leads if l.status == LeadStatus.QUALIFIED])
    negotiating = len([l for l in leads if l.status == LeadStatus.NEGOTIATING])
    converted = len([l for l in leads if l.status == LeadStatus.CONVERTED])
    
    return {
        "period": period,
        "funnel": [
            {"stage": "New", "count": new, "percentage": round(new / total * 100, 1) if total > 0 else 0},
            {"stage": "Contacted", "count": contacted, "percentage": round(contacted / total * 100, 1) if total > 0 else 0},
            {"stage": "Qualified", "count": qualified, "percentage": round(qualified / total * 100, 1) if total > 0 else 0},
            {"stage": "Negotiating", "count": negotiating, "percentage": round(negotiating / total * 100, 1) if total > 0 else 0},
            {"stage": "Converted", "count": converted, "percentage": round(converted / total * 100, 1) if total > 0 else 0}
        ],
        "conversion_rate": round(converted / total * 100, 2) if total > 0 else 0
    }


@app.get("/api/v1/sales/top-performers")
def get_top_performers(
    period: str = Query("month", description="Period: week, month, quarter"),
    limit: int = Query(10, description="Number of top performers"),
    db: Session = Depends(get_db)
):
    """
    Get top performing agents
    """
    # Calculate date range
    now = datetime.now()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=30)
    
    # Group by agent and count conversions
    conversions = db.query(
        Lead.assigned_agent_id,
        func.count(Lead.id).label('total_leads'),
        func.sum(case((Lead.status == LeadStatus.CONVERTED, 1), else_=0)).label('conversions')
    ).filter(
        Lead.created_at >= start_date,
        Lead.assigned_agent_id.isnot(None)
    ).group_by(
        Lead.assigned_agent_id
    ).all()
    
    # Calculate conversion rates and sort
    performers = []
    for agent_id, total, converted in conversions:
        conversion_rate = (converted / total * 100) if total > 0 else 0
        performers.append({
            "agent_id": agent_id,
            "total_leads": total,
            "conversions": converted or 0,
            "conversion_rate": round(conversion_rate, 2)
        })
    
    performers.sort(key=lambda x: x['conversions'], reverse=True)
    
    return {
        "period": period,
        "performers": performers[:limit]
    }


@app.get("/api/v1/sales/activity")
def get_recent_activity(
    limit: int = Query(20, description="Number of activities"),
    agent_id: Optional[int] = Query(None, description="Filter by agent"),
    db: Session = Depends(get_db)
):
    """
    Get recent lead activities for dashboard
    """
    query = db.query(LeadActivity).join(Lead)
    
    if agent_id:
        query = query.filter(Lead.assigned_agent_id == agent_id)
    
    activities = query.order_by(
        LeadActivity.created_at.desc()
    ).limit(limit).all()
    
    return {
        "activities": [
            {
                "id": activity.id,
                "lead_id": activity.lead_id,
                "activity_type": activity.activity_type,
                "subject": activity.subject,
                "details": activity.details,
                "performed_by": activity.performed_by,
                "created_at": activity.created_at.isoformat() if activity.created_at else None
            }
            for activity in activities
        ]
    }


@app.get("/api/v1/sales/stats")
def get_sales_stats(
    db: Session = Depends(get_db)
):
    """
    Get overall sales statistics
    """
    total_leads = db.query(Lead).count()
    converted_leads = db.query(Lead).filter(Lead.status == LeadStatus.CONVERTED).count()
    active_leads = db.query(Lead).filter(
        Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED, LeadStatus.NEGOTIATING])
    ).count()
    
    # Get leads created in last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_leads = db.query(Lead).filter(Lead.created_at >= thirty_days_ago).count()
    
    return {
        "total_leads": total_leads,
        "converted_leads": converted_leads,
        "active_leads": active_leads,
        "recent_leads_30d": recent_leads,
        "overall_conversion_rate": round(converted_leads / total_leads * 100, 2) if total_leads > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
