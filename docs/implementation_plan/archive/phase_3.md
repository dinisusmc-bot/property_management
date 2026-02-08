# Phase 3: Sales & Lead Management

**Duration:** 1-2 weeks  
**Priority:** 🟠 IMPORTANT  
**Goal:** Complete CRM capabilities for lead tracking and follow-ups

---

## Overview

Sales service has basic lead management but needs:
- Follow-up tracking with reminders
- Lead scoring system
- Lead ownership transfer
- Activity timeline view
- Lead source tracking and ROI

These features improve sales efficiency and conversion rates.

---

## Task 3.1: Follow-Up Tracking System

**Estimated Time:** 8-12 hours  
**Services:** Sales, Notification  
**Impact:** HIGH - Prevents lost opportunities

### Database Changes

```sql
\c athena
SET search_path TO sales, public;

CREATE TABLE IF NOT EXISTS follow_ups (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  activity_id INTEGER REFERENCES activities(id),
  follow_up_type VARCHAR(50) NOT NULL,  -- call, email, meeting, quote
  scheduled_date DATE NOT NULL,
  scheduled_time TIME,
  completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  completed_by INTEGER,
  outcome VARCHAR(50),  -- successful, no_answer, voicemail, rescheduled, lost
  notes TEXT,
  reminder_sent BOOLEAN DEFAULT FALSE,
  assigned_to INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_follow_up_type CHECK (follow_up_type IN ('call', 'email', 'meeting', 'quote', 'other')),
  CONSTRAINT valid_outcome CHECK (outcome IS NULL OR outcome IN ('successful', 'no_answer', 'voicemail', 'rescheduled', 'lost'))
);

CREATE INDEX idx_follow_ups_lead ON follow_ups(lead_id);
CREATE INDEX idx_follow_ups_assigned ON follow_ups(assigned_to);
CREATE INDEX idx_follow_ups_scheduled ON follow_ups(scheduled_date, completed) WHERE NOT completed;
CREATE INDEX idx_follow_ups_overdue ON follow_ups(scheduled_date) 
  WHERE NOT completed AND scheduled_date < CURRENT_DATE;

-- Add follow-up tracking to leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_follow_up_date TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_follow_up_date TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_up_count INTEGER DEFAULT 0;
```

### Implementation Steps

#### Step 1: Create Follow-Up Models

**File:** `backend/services/sales/models.py`

```python
class FollowUp(Base):
    __tablename__ = "follow_ups"
    __table_args__ = {'schema': 'sales'}
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('sales.leads.id'), nullable=False)
    activity_id = Column(Integer, ForeignKey('sales.activities.id'))
    follow_up_type = Column(String(50), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    completed_by = Column(Integer)
    outcome = Column(String(50))
    notes = Column(Text)
    reminder_sent = Column(Boolean, default=False)
    assigned_to = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="follow_ups")

class Lead(Base):
    # ... existing fields ...
    
    last_follow_up_date = Column(DateTime)
    next_follow_up_date = Column(DateTime)
    follow_up_count = Column(Integer, default=0)
    
    follow_ups = relationship("FollowUp", back_populates="lead", cascade="all, delete-orphan")
```

#### Step 2: Create Follow-Up Schemas

**File:** `backend/services/sales/schemas.py`

```python
class FollowUpCreate(BaseModel):
    lead_id: int
    follow_up_type: str
    scheduled_date: date
    scheduled_time: Optional[time] = None
    notes: Optional[str] = None

class FollowUpUpdate(BaseModel):
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    notes: Optional[str] = None

class FollowUpComplete(BaseModel):
    outcome: str
    notes: Optional[str] = None
    schedule_next: Optional[bool] = False
    next_follow_up_days: Optional[int] = 3

class FollowUpResponse(BaseModel):
    id: int
    lead_id: int
    follow_up_type: str
    scheduled_date: date
    scheduled_time: Optional[time]
    completed: bool
    outcome: Optional[str]
    assigned_to: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Step 3: Create Follow-Up Endpoints

**File:** `backend/services/sales/main.py`

```python
from datetime import time, timedelta

@app.post("/follow-ups", response_model=FollowUpResponse)
async def create_follow_up(
    follow_up: FollowUpCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a follow-up task for a lead"""
    lead = db.query(Lead).filter(Lead.id == follow_up.lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    
    db_follow_up = FollowUp(
        **follow_up.dict(),
        assigned_to=current_user["user_id"]
    )
    db.add(db_follow_up)
    
    # Update lead next follow-up date
    scheduled_datetime = datetime.combine(follow_up.scheduled_date, follow_up.scheduled_time or time(9, 0))
    if not lead.next_follow_up_date or scheduled_datetime < lead.next_follow_up_date:
        lead.next_follow_up_date = scheduled_datetime
    
    db.commit()
    db.refresh(db_follow_up)
    return db_follow_up

@app.get("/follow-ups/my-tasks", response_model=List[dict])
async def get_my_follow_ups(
    date: Optional[date] = None,
    overdue: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get follow-ups assigned to current user"""
    query = db.query(FollowUp, Lead).join(
        Lead, FollowUp.lead_id == Lead.id
    ).filter(
        FollowUp.assigned_to == current_user["user_id"],
        FollowUp.completed == False
    )
    
    if date:
        query = query.filter(FollowUp.scheduled_date == date)
    elif overdue:
        query = query.filter(FollowUp.scheduled_date < date.today())
    else:
        # Default: today and upcoming
        query = query.filter(FollowUp.scheduled_date >= date.today())
    
    results = query.order_by(FollowUp.scheduled_date, FollowUp.scheduled_time).all()
    
    return [
        {
            "id": follow_up.id,
            "lead_id": lead.id,
            "lead_name": lead.company_name or lead.contact_name,
            "follow_up_type": follow_up.follow_up_type,
            "scheduled_date": follow_up.scheduled_date.isoformat(),
            "scheduled_time": follow_up.scheduled_time.isoformat() if follow_up.scheduled_time else None,
            "notes": follow_up.notes,
            "is_overdue": follow_up.scheduled_date < date.today()
        }
        for follow_up, lead in results
    ]

@app.get("/follow-ups/lead/{lead_id}", response_model=List[FollowUpResponse])
async def get_lead_follow_ups(
    lead_id: int,
    include_completed: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all follow-ups for a lead"""
    query = db.query(FollowUp).filter(FollowUp.lead_id == lead_id)
    
    if not include_completed:
        query = query.filter(FollowUp.completed == False)
    
    return query.order_by(FollowUp.scheduled_date.desc()).all()

@app.post("/follow-ups/{follow_up_id}/complete")
async def complete_follow_up(
    follow_up_id: int,
    completion: FollowUpComplete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark follow-up as completed"""
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(404, "Follow-up not found")
    
    if follow_up.assigned_to != current_user["user_id"]:
        raise HTTPException(403, "Not authorized to complete this follow-up")
    
    follow_up.completed = True
    follow_up.completed_at = datetime.utcnow()
    follow_up.completed_by = current_user["user_id"]
    follow_up.outcome = completion.outcome
    if completion.notes:
        follow_up.notes = completion.notes
    
    # Update lead
    lead = db.query(Lead).filter(Lead.id == follow_up.lead_id).first()
    lead.last_follow_up_date = datetime.utcnow()
    lead.follow_up_count += 1
    
    # Create activity record
    activity = Activity(
        lead_id=lead.id,
        activity_type=follow_up.follow_up_type,
        description=f"{follow_up.follow_up_type.title()} follow-up completed: {completion.outcome}",
        notes=completion.notes,
        user_id=current_user["user_id"]
    )
    db.add(activity)
    
    # Schedule next follow-up if requested
    next_follow_up_id = None
    if completion.schedule_next:
        days_ahead = completion.next_follow_up_days or 3
        next_date = date.today() + timedelta(days=days_ahead)
        
        next_follow_up = FollowUp(
            lead_id=lead.id,
            follow_up_type=follow_up.follow_up_type,
            scheduled_date=next_date,
            scheduled_time=follow_up.scheduled_time,
            notes=f"Follow-up from {follow_up.scheduled_date}",
            assigned_to=current_user["user_id"]
        )
        db.add(next_follow_up)
        db.flush()
        next_follow_up_id = next_follow_up.id
        
        lead.next_follow_up_date = datetime.combine(next_date, follow_up.scheduled_time or time(9, 0))
    else:
        # Find next scheduled follow-up
        next_scheduled = db.query(FollowUp).filter(
            FollowUp.lead_id == lead.id,
            FollowUp.completed == False,
            FollowUp.id != follow_up_id
        ).order_by(FollowUp.scheduled_date).first()
        
        if next_scheduled:
            lead.next_follow_up_date = datetime.combine(
                next_scheduled.scheduled_date,
                next_scheduled.scheduled_time or time(9, 0)
            )
        else:
            lead.next_follow_up_date = None
    
    db.commit()
    
    return {
        "follow_up_id": follow_up_id,
        "completed": True,
        "outcome": completion.outcome,
        "next_follow_up_id": next_follow_up_id
    }

@app.get("/reports/follow-up-performance")
async def get_follow_up_performance(
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Follow-up completion and effectiveness report"""
    query = db.query(FollowUp)
    
    if user_id:
        query = query.filter(FollowUp.assigned_to == user_id)
    if start_date:
        query = query.filter(FollowUp.scheduled_date >= start_date)
    if end_date:
        query = query.filter(FollowUp.scheduled_date <= end_date)
    
    all_follow_ups = query.all()
    
    total = len(all_follow_ups)
    completed = len([f for f in all_follow_ups if f.completed])
    overdue = len([f for f in all_follow_ups if not f.completed and f.scheduled_date < date.today()])
    
    # Outcome breakdown
    outcomes = {}
    for follow_up in all_follow_ups:
        if follow_up.outcome:
            outcomes[follow_up.outcome] = outcomes.get(follow_up.outcome, 0) + 1
    
    return {
        "total_follow_ups": total,
        "completed": completed,
        "pending": total - completed,
        "overdue": overdue,
        "completion_rate": (completed / total * 100) if total > 0 else 0,
        "outcomes": outcomes
    }
```

#### Step 4: Create Follow-Up Reminder Job

**File:** `backend/services/sales/reminders.py` (New file)

```python
"""Follow-up reminder background job"""
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from .models import FollowUp, Lead
from .database import SessionLocal

async def send_follow_up_reminders():
    """Send reminders for upcoming follow-ups (run daily)"""
    db = SessionLocal()
    
    try:
        # Get follow-ups due today that haven't sent reminder
        today_follow_ups = db.query(FollowUp, Lead).join(
            Lead, FollowUp.lead_id == Lead.id
        ).filter(
            FollowUp.scheduled_date == date.today(),
            FollowUp.completed == False,
            FollowUp.reminder_sent == False
        ).all()
        
        for follow_up, lead in today_follow_ups:
            # Send notification (integrate with notification service)
            # notification_service.send_email(
            #     to=user_email,
            #     subject=f"Follow-up reminder: {lead.company_name}",
            #     body=f"You have a {follow_up.follow_up_type} scheduled for {lead.company_name}"
            # )
            
            follow_up.reminder_sent = True
        
        db.commit()
        print(f"Sent {len(today_follow_ups)} follow-up reminders")
        
    finally:
        db.close()
```

#### Step 5: Test Follow-Ups

**Create:** `test_follow_ups.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create Follow-Up ==="
FOLLOW_UP_ID=$(curl -s -X POST "$BASE_URL/sales/follow-ups" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "follow_up_type": "call",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "10:00:00",
    "notes": "Call to discuss charter quote"
  }' | jq -r '.id')

echo "Follow-up ID: $FOLLOW_UP_ID"

echo -e "\n=== Get My Follow-Ups ==="
curl -s -X GET "$BASE_URL/sales/follow-ups/my-tasks" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Get Lead Follow-Ups ==="
curl -s -X GET "$BASE_URL/sales/follow-ups/lead/1" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Complete Follow-Up ==="
curl -s -X POST "$BASE_URL/sales/follow-ups/$FOLLOW_UP_ID/complete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "outcome": "successful",
    "notes": "Client interested, sending quote",
    "schedule_next": true,
    "next_follow_up_days": 3
  }' | jq

echo -e "\n=== Follow-Up Performance Report ==="
curl -s -X GET "$BASE_URL/sales/reports/follow-up-performance?start_date=2026-01-01" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `follow_ups` table created
- [ ] Can create follow-up tasks
- [ ] Can view assigned follow-ups
- [ ] Can complete follow-ups with outcomes
- [ ] Auto-schedule next follow-up works
- [ ] Performance report functional
- [ ] Test script passes

---

## Task 3.2: Lead Scoring System

**Estimated Time:** 6-10 hours  
**Services:** Sales  
**Impact:** MEDIUM - Prioritize high-value leads

### Database Changes

```sql
\c athena
SET search_path TO sales, public;

-- Add scoring to leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS score_updated_at TIMESTAMP;

-- Scoring rules table
CREATE TABLE IF NOT EXISTS lead_scoring_rules (
  id SERIAL PRIMARY KEY,
  rule_name VARCHAR(100) NOT NULL,
  rule_type VARCHAR(50) NOT NULL,  -- attribute, activity, engagement
  condition_field VARCHAR(100),
  condition_operator VARCHAR(20),  -- equals, contains, greater_than, etc.
  condition_value VARCHAR(255),
  points INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Score change history
CREATE TABLE IF NOT EXISTS lead_score_history (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  old_score INTEGER NOT NULL,
  new_score INTEGER NOT NULL,
  points_changed INTEGER NOT NULL,
  reason VARCHAR(255),
  changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_score_history_lead ON lead_score_history(lead_id);

-- Insert default scoring rules
INSERT INTO lead_scoring_rules (rule_name, rule_type, condition_field, condition_operator, condition_value, points) VALUES
('Large Group Size', 'attribute', 'estimated_passengers', 'greater_than', '50', 20),
('Medium Group Size', 'attribute', 'estimated_passengers', 'greater_than', '25', 10),
('High Budget', 'attribute', 'estimated_value', 'greater_than', '5000', 25),
('Medium Budget', 'attribute', 'estimated_value', 'greater_than', '2000', 15),
('Responded to Email', 'engagement', 'email_response', 'equals', 'true', 10),
('Called Back', 'engagement', 'phone_response', 'equals', 'true', 15),
('Requested Quote', 'activity', 'quote_requested', 'equals', 'true', 20),
('Repeat Client', 'attribute', 'is_repeat', 'equals', 'true', 30);
```

### Implementation Steps

#### Step 1: Create Scoring Models

**File:** `backend/services/sales/models.py`

```python
class Lead(Base):
    # ... existing fields ...
    
    score = Column(Integer, default=0)
    score_updated_at = Column(DateTime)

class LeadScoringRule(Base):
    __tablename__ = "lead_scoring_rules"
    __table_args__ = {'schema': 'sales'}
    
    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)
    condition_field = Column(String(100))
    condition_operator = Column(String(20))
    condition_value = Column(String(255))
    points = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class LeadScoreHistory(Base):
    __tablename__ = "lead_score_history"
    __table_args__ = {'schema': 'sales'}
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('sales.leads.id'), nullable=False)
    old_score = Column(Integer, nullable=False)
    new_score = Column(Integer, nullable=False)
    points_changed = Column(Integer, nullable=False)
    reason = Column(String(255))
    changed_at = Column(DateTime, default=datetime.utcnow)
```

#### Step 2: Create Scoring Service

**File:** `backend/services/sales/scoring.py` (New file)

```python
"""Lead scoring engine"""
from sqlalchemy.orm import Session
from .models import Lead, LeadScoringRule, LeadScoreHistory
from datetime import datetime

def calculate_lead_score(lead: Lead, db: Session) -> int:
    """Calculate score for a lead based on active rules"""
    total_score = 0
    rules = db.query(LeadScoringRule).filter(LeadScoringRule.is_active == True).all()
    
    for rule in rules:
        if evaluate_rule(lead, rule):
            total_score += rule.points
    
    return max(0, min(total_score, 100))  # Cap between 0-100

def evaluate_rule(lead: Lead, rule: LeadScoringRule) -> bool:
    """Evaluate if a lead matches a scoring rule"""
    if rule.rule_type == 'attribute':
        field_value = getattr(lead, rule.condition_field, None)
        if field_value is None:
            return False
        
        if rule.condition_operator == 'equals':
            return str(field_value) == rule.condition_value
        elif rule.condition_operator == 'greater_than':
            return float(field_value) > float(rule.condition_value)
        elif rule.condition_operator == 'less_than':
            return float(field_value) < float(rule.condition_value)
        elif rule.condition_operator == 'contains':
            return rule.condition_value.lower() in str(field_value).lower()
    
    # Add more rule type evaluations as needed
    return False

def update_lead_score(lead: Lead, db: Session, reason: str = "Score recalculated"):
    """Recalculate and update lead score"""
    old_score = lead.score
    new_score = calculate_lead_score(lead, db)
    
    if old_score != new_score:
        # Update lead
        lead.score = new_score
        lead.score_updated_at = datetime.utcnow()
        
        # Record history
        history = LeadScoreHistory(
            lead_id=lead.id,
            old_score=old_score,
            new_score=new_score,
            points_changed=new_score - old_score,
            reason=reason
        )
        db.add(history)
        db.commit()
    
    return new_score
```

#### Step 3: Create Scoring Endpoints

**File:** `backend/services/sales/main.py`

```python
from .scoring import calculate_lead_score, update_lead_score

@app.post("/leads/{lead_id}/calculate-score")
async def recalculate_lead_score(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually recalculate lead score"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    
    new_score = update_lead_score(lead, db, "Manual recalculation")
    
    return {
        "lead_id": lead_id,
        "score": new_score,
        "updated_at": lead.score_updated_at.isoformat()
    }

@app.get("/leads/high-score", response_model=List[dict])
async def get_high_score_leads(
    min_score: int = 50,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get leads with high scores (hot leads)"""
    leads = db.query(Lead).filter(
        Lead.score >= min_score,
        Lead.status.in_(['new', 'contacted', 'qualified'])
    ).order_by(Lead.score.desc()).limit(limit).all()
    
    return [
        {
            "id": lead.id,
            "company_name": lead.company_name,
            "contact_name": lead.contact_name,
            "score": lead.score,
            "estimated_value": float(lead.estimated_value) if lead.estimated_value else 0,
            "status": lead.status,
            "assigned_to": lead.assigned_to,
            "next_follow_up": lead.next_follow_up_date.isoformat() if lead.next_follow_up_date else None
        }
        for lead in leads
    ]

@app.get("/leads/{lead_id}/score-history")
async def get_lead_score_history(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get score change history for a lead"""
    history = db.query(LeadScoreHistory).filter(
        LeadScoreHistory.lead_id == lead_id
    ).order_by(LeadScoreHistory.changed_at.desc()).all()
    
    return {
        "lead_id": lead_id,
        "history": [
            {
                "old_score": h.old_score,
                "new_score": h.new_score,
                "points_changed": h.points_changed,
                "reason": h.reason,
                "changed_at": h.changed_at.isoformat()
            }
            for h in history
        ]
    }

@app.get("/scoring/rules", response_model=List[dict])
async def get_scoring_rules(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Get all scoring rules"""
    rules = db.query(LeadScoringRule).order_by(LeadScoringRule.points.desc()).all()
    
    return [
        {
            "id": r.id,
            "rule_name": r.rule_name,
            "rule_type": r.rule_type,
            "points": r.points,
            "is_active": r.is_active
        }
        for r in rules
    ]

@app.post("/scoring/rules", response_model=dict)
async def create_scoring_rule(
    rule_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Create new scoring rule"""
    rule = LeadScoringRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return {"rule_id": rule.id, "rule_name": rule.rule_name}

@app.post("/scoring/recalculate-all")
async def recalculate_all_scores(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Recalculate scores for all active leads"""
    leads = db.query(Lead).filter(
        Lead.status.in_(['new', 'contacted', 'qualified'])
    ).all()
    
    updated_count = 0
    for lead in leads:
        update_lead_score(lead, db, "Bulk recalculation")
        updated_count += 1
    
    return {
        "message": f"Recalculated scores for {updated_count} leads",
        "count": updated_count
    }
```

#### Step 4: Test Lead Scoring

**Create:** `test_lead_scoring.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Get Scoring Rules ==="
curl -s -X GET "$BASE_URL/sales/scoring/rules" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Recalculate Lead Score ==="
curl -s -X POST "$BASE_URL/sales/leads/1/calculate-score" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Get High Score Leads ==="
curl -s -X GET "$BASE_URL/sales/leads/high-score?min_score=30" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Get Score History ==="
curl -s -X GET "$BASE_URL/sales/leads/1/score-history" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Recalculate All Scores ==="
curl -s -X POST "$BASE_URL/sales/scoring/recalculate-all" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Scoring tables created
- [ ] Default rules inserted
- [ ] Score calculation works
- [ ] Can recalculate scores
- [ ] High-score leads query works
- [ ] Score history tracked
- [ ] Test script passes

---

## Task 3.3: Lead Ownership Transfer

**Estimated Time:** 4-6 hours  
**Services:** Sales  
**Impact:** MEDIUM - For team reorganization

### Database Changes

```sql
\c athena
SET search_path TO sales, public;

CREATE TABLE IF NOT EXISTS lead_transfers (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  from_user_id INTEGER NOT NULL,
  to_user_id INTEGER NOT NULL,
  transfer_reason TEXT,
  transferred_by INTEGER NOT NULL,
  transferred_at TIMESTAMP DEFAULT NOW(),
  notes TEXT
);

CREATE INDEX idx_lead_transfers_lead ON lead_transfers(lead_id);
CREATE INDEX idx_lead_transfers_from ON lead_transfers(from_user_id);
CREATE INDEX idx_lead_transfers_to ON lead_transfers(to_user_id);
```

### Implementation Steps

#### Step 1: Create Transfer Model

**File:** `backend/services/sales/models.py`

```python
class LeadTransfer(Base):
    __tablename__ = "lead_transfers"
    __table_args__ = {'schema': 'sales'}
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('sales.leads.id'), nullable=False)
    from_user_id = Column(Integer, nullable=False)
    to_user_id = Column(Integer, nullable=False)
    transfer_reason = Column(Text)
    transferred_by = Column(Integer, nullable=False)
    transferred_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
```

#### Step 2: Create Transfer Endpoints

**File:** `backend/services/sales/main.py`

```python
@app.post("/leads/{lead_id}/transfer")
async def transfer_lead(
    lead_id: int,
    to_user_id: int,
    reason: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Transfer lead to another user"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    
    from_user_id = lead.assigned_to
    
    # Record transfer
    transfer = LeadTransfer(
        lead_id=lead_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        transfer_reason=reason,
        transferred_by=current_user["user_id"],
        notes=notes
    )
    db.add(transfer)
    
    # Update lead
    lead.assigned_to = to_user_id
    
    # Create activity
    activity = Activity(
        lead_id=lead_id,
        activity_type="transfer",
        description=f"Lead transferred from user {from_user_id} to user {to_user_id}",
        notes=reason,
        user_id=current_user["user_id"]
    )
    db.add(activity)
    
    db.commit()
    
    return {
        "lead_id": lead_id,
        "transferred_to": to_user_id,
        "transfer_id": transfer.id
    }

@app.post("/leads/bulk-transfer")
async def bulk_transfer_leads(
    lead_ids: List[int],
    to_user_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Transfer multiple leads to a user"""
    transferred = []
    
    for lead_id in lead_ids:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            transfer = LeadTransfer(
                lead_id=lead_id,
                from_user_id=lead.assigned_to,
                to_user_id=to_user_id,
                transfer_reason=reason,
                transferred_by=current_user["user_id"]
            )
            db.add(transfer)
            
            lead.assigned_to = to_user_id
            transferred.append(lead_id)
    
    db.commit()
    
    return {
        "transferred_count": len(transferred),
        "lead_ids": transferred,
        "new_owner": to_user_id
    }

@app.get("/leads/{lead_id}/transfer-history")
async def get_lead_transfer_history(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get transfer history for a lead"""
    transfers = db.query(LeadTransfer).filter(
        LeadTransfer.lead_id == lead_id
    ).order_by(LeadTransfer.transferred_at.desc()).all()
    
    return {
        "lead_id": lead_id,
        "transfer_count": len(transfers),
        "transfers": [
            {
                "from_user_id": t.from_user_id,
                "to_user_id": t.to_user_id,
                "reason": t.transfer_reason,
                "transferred_at": t.transferred_at.isoformat()
            }
            for t in transfers
        ]
    }
```

#### Step 3: Test Lead Transfer

**Create:** `test_lead_transfer.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Transfer Single Lead ==="
curl -s -X POST "$BASE_URL/sales/leads/1/transfer?to_user_id=2&reason=Reassignment%20due%20to%20territory%20change" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Bulk Transfer Leads ==="
curl -s -X POST "$BASE_URL/sales/leads/bulk-transfer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids": [2, 3, 4],
    "to_user_id": 3,
    "reason": "Load balancing"
  }' | jq

echo -e "\n=== Get Transfer History ==="
curl -s -X GET "$BASE_URL/sales/leads/1/transfer-history" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `lead_transfers` table created
- [ ] Single lead transfer works
- [ ] Bulk transfer works
- [ ] Transfer history tracked
- [ ] Activities created for transfers
- [ ] Test script passes

---

## Phase 3 Completion Checklist

### Database Migrations
- [ ] Follow-ups table created
- [ ] Follow-up fields added to leads
- [ ] Scoring fields added to leads
- [ ] Scoring rules table created
- [ ] Score history table created
- [ ] Transfer history table created

### API Endpoints
- [ ] Create/list/complete follow-ups
- [ ] Follow-up reminders
- [ ] Follow-up performance report
- [ ] Calculate/update lead scores
- [ ] High-score leads query
- [ ] Score history tracking
- [ ] Scoring rules management
- [ ] Lead transfer (single & bulk)
- [ ] Transfer history

### Background Jobs
- [ ] Daily follow-up reminder job
- [ ] Nightly score recalculation (optional)

### Testing
- [ ] Follow-up workflow tested
- [ ] Scoring system tested
- [ ] Transfer functionality tested
- [ ] All tests pass through Kong Gateway

### Documentation
- [ ] Follow-up workflows documented
- [ ] Scoring rules documented
- [ ] Transfer process documented

---

## Next Steps

After Phase 3 completion:
1. Review and test all CRM features
2. Proceed to [Phase 4: Manager/Config Tools](phase_4.md)
3. Update progress tracking

---

**Estimated Total Time:** 18-28 hours (1-2 weeks)  
**Priority:** 🟠 IMPORTANT - Improves sales efficiency
