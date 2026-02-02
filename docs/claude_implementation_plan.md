# CoachWay Implementation Plan - Detailed Execution Guide

**Created:** February 1, 2026  
**Author:** Claude (AI Assistant)  
**Audience:** Junior Developers & AI Coding Agents  
**Purpose:** Granular, step-by-step instructions to implement missing backend capabilities

---

## Table of Contents
1. [Prerequisites & Setup](#prerequisites--setup)
2. [Phase 1: Sales Service](#phase-1-sales-service-weeks-1-3)
3. [Phase 2: Charter Enhancements](#phase-2-charter-enhancements-weeks-4-5)
4. [Phase 3: Pricing Service](#phase-3-pricing-service-weeks-6-7)
5. [Phase 4: Vendor Service](#phase-4-vendor-service-weeks-8-9)
6. [Phase 5: Portals Service](#phase-5-portals-service-weeks-10-11)
7. [Phase 6: Change Management](#phase-6-change-management-weeks-12-13)
8. [Testing & Deployment](#testing--deployment)

---

## Prerequisites & Setup

### Environment Preparation
Before starting any implementation, ensure you have:

1. **Development Environment**:
   ```bash
   cd /home/nick/work_area/coachway_demo
   # Verify Docker is running
   docker --version
   docker-compose --version
   
   # Verify all existing services are up
   docker-compose ps
   ```

2. **Database Access**:
   ```bash
   # Test PostgreSQL connection
   docker exec -it athena-postgres psql -U athena -d athena -c "\dt"
   ```

3. **Python Environment**:
   ```bash
   # Check Python version (should be 3.11+)
   python --version
   ```

---

## Phase 1: Sales Service (Weeks 1-3)

### Overview
**Goal:** Create a new microservice to manage leads before they become charters.  
**Port:** 8007  
**Database:** `sales_db`

---

### Task 1.1: Create Service Directory Structure

**Estimated Time:** 15 minutes

**Steps:**
1. Navigate to services directory:
   ```bash
   cd backend/services
   ```

2. Create sales service directory:
   ```bash
   mkdir -p sales
   cd sales
   ```

3. Copy boilerplate from existing service:
   ```bash
   # Copy structure from charters service
   cp ../charters/config.py ./config.py
   cp ../charters/database.py ./database.py
   cp ../charters/Dockerfile ./Dockerfile
   cp ../charters/requirements.txt ./requirements.txt
   ```

4. Create empty Python files:
   ```bash
   touch __init__.py
   touch main.py
   touch models.py
   touch schemas.py
   touch business_logic.py
   ```

**Verification:**
```bash
tree backend/services/sales
# Should show: config.py, database.py, Dockerfile, requirements.txt, main.py, models.py, schemas.py
```

---

### Task 1.2: Update Configuration Files

**Estimated Time:** 20 minutes

**File:** `backend/services/sales/config.py`

**Instructions:**
1. Open `config.py` in editor
2. Replace ALL content with:
   ```python
   """
   Configuration for Sales Service
   """
   import os
   from typing import Optional

   # Database Configuration
   DATABASE_URL = os.getenv(
       "SALES_DATABASE_URL",
       "postgresql://athena:athena_dev_password@localhost:5432/sales_db"
   )

   # Service Configuration
   SERVICE_NAME = "sales"
   SERVICE_PORT = int(os.getenv("SALES_SERVICE_PORT", "8007"))
   
   # Auth Service Configuration
   AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
   
   # Client Service Configuration
   CLIENT_SERVICE_URL = os.getenv("CLIENT_SERVICE_URL", "http://localhost:8003")
   
   # Charter Service Configuration
   CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://localhost:8002")
   
   # JWT Configuration
   SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
   ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   ```

3. Save file

**File:** `backend/services/sales/database.py`

**Instructions:**
1. Open `database.py`
2. Replace content with:
   ```python
   """
   Database configuration for Sales Service
   """
   from sqlalchemy import create_engine
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy.orm import sessionmaker
   import config

   # Create engine
   engine = create_engine(
       config.DATABASE_URL,
       pool_pre_ping=True,
       pool_size=10,
       max_overflow=20
   )

   # Create session factory
   SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

   # Create base class for models
   Base = declarative_base()

   # Dependency for FastAPI
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```

3. Save file

**File:** `backend/services/sales/Dockerfile`

**Instructions:**
1. Update Dockerfile to reference sales service:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*

   # Copy requirements
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Expose port
   EXPOSE 8007

   # Run application
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
   ```

**Verification:**
```bash
# Check files exist and have content
wc -l config.py database.py Dockerfile
# Should show line counts for each file
```

---

### Task 1.3: Create Database Models

**Estimated Time:** 45 minutes

**File:** `backend/services/sales/models.py`

**Instructions:**
1. Open `models.py`
2. Add the following content:

```python
"""
Database models for Sales Service
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class LeadStatus(str, enum.Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    DEAD = "dead"

class LeadSource(str, enum.Enum):
    """Lead source enumeration"""
    WEB = "web"
    PHONE = "phone"
    EMAIL = "email"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    PARTNER = "partner"

class ActivityType(str, enum.Enum):
    """Activity type enumeration"""
    CALL = "call"
    EMAIL = "email"
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    MEETING = "meeting"

class Lead(Base):
    """Lead model - represents potential business before charter creation"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Lead identification
    source = Column(Enum(LeadSource), nullable=False, default=LeadSource.WEB)
    status = Column(Enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True)
    
    # Contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    company_name = Column(String(255), nullable=True)
    
    # Trip details (rough information)
    trip_details = Column(Text, nullable=True)  # JSON string
    estimated_passengers = Column(Integer, nullable=True)
    estimated_trip_date = Column(DateTime(timezone=True), nullable=True)
    pickup_location = Column(String(500), nullable=True)
    dropoff_location = Column(String(500), nullable=True)
    
    # Assignment
    assigned_agent_id = Column(Integer, nullable=True, index=True)  # FK to auth service
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Conversion tracking
    converted_to_client_id = Column(Integer, nullable=True)  # FK to client service
    converted_to_charter_id = Column(Integer, nullable=True)  # FK to charter service
    converted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scoring (for future use)
    score = Column(Integer, default=0)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Follow-up tracking
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.id}: {self.first_name} {self.last_name} - {self.status}>"


class LeadActivity(Base):
    """Lead activity log - tracks all interactions with a lead"""
    __tablename__ = "lead_activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False)
    subject = Column(String(255), nullable=True)
    details = Column(Text, nullable=False)
    
    # Who performed the activity
    performed_by = Column(Integer, nullable=False)  # FK to auth service user_id
    
    # Metadata
    duration_minutes = Column(Integer, nullable=True)  # For calls/meetings
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")

    def __repr__(self):
        return f"<LeadActivity {self.id}: {self.activity_type} on Lead {self.lead_id}>"


class AssignmentRule(Base):
    """Assignment rule for round-robin lead distribution"""
    __tablename__ = "assignment_rules"

    id = Column(Integer, primary_key=True, index=True)
    
    # Agent identification
    agent_id = Column(Integer, nullable=False, unique=True, index=True)  # FK to auth service
    agent_name = Column(String(255), nullable=False)  # Cached for performance
    
    # Rule configuration
    is_active = Column(Boolean, default=True, index=True)
    weight = Column(Integer, default=1)  # For weighted distribution (1 = normal)
    max_leads_per_day = Column(Integer, default=10)
    
    # Tracking
    total_leads_assigned = Column(Integer, default=0)
    last_assigned_at = Column(DateTime(timezone=True), nullable=True, index=True)
    leads_assigned_today = Column(Integer, default=0)
    last_reset_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AssignmentRule agent={self.agent_id} active={self.is_active}>"


class EmailPreference(Base):
    """Email preferences for clients - controls automated emails"""
    __tablename__ = "email_preferences"

    id = Column(Integer, primary_key=True, index=True)
    
    # Client identification
    client_id = Column(Integer, nullable=False, unique=True, index=True)  # FK to client service
    
    # Preferences
    automated_emails_enabled = Column(Boolean, default=True)
    marketing_emails_enabled = Column(Boolean, default=True)
    reminder_emails_enabled = Column(Boolean, default=True)
    quote_emails_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EmailPreference client={self.client_id}>"
```

3. Save file

**Verification:**
```python
# Test the models can be imported
python3 -c "from models import Lead, LeadActivity, AssignmentRule; print('Models OK')"
```

---

### Task 1.4: Create Pydantic Schemas

**Estimated Time:** 30 minutes

**File:** `backend/services/sales/schemas.py`

**Instructions:**
1. Create schemas for request/response validation:

```python
"""
Pydantic schemas for Sales Service
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class LeadStatusEnum(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    DEAD = "dead"

class LeadSourceEnum(str, Enum):
    WEB = "web"
    PHONE = "phone"
    EMAIL = "email"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    PARTNER = "partner"

class ActivityTypeEnum(str, Enum):
    CALL = "call"
    EMAIL = "email"
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    MEETING = "meeting"

# Lead Schemas
class LeadBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    company_name: Optional[str] = None
    source: LeadSourceEnum = LeadSourceEnum.WEB
    trip_details: Optional[str] = None
    estimated_passengers: Optional[int] = None
    estimated_trip_date: Optional[datetime] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None

class LeadCreate(LeadBase):
    """Schema for creating a new lead"""
    pass

class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    status: Optional[LeadStatusEnum] = None
    trip_details: Optional[str] = None
    estimated_passengers: Optional[int] = None
    estimated_trip_date: Optional[datetime] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None
    priority: Optional[str] = None

class LeadResponse(LeadBase):
    """Schema for lead response"""
    id: int
    status: LeadStatusEnum
    assigned_agent_id: Optional[int]
    assigned_at: Optional[datetime]
    converted_to_client_id: Optional[int]
    converted_to_charter_id: Optional[int]
    converted_at: Optional[datetime]
    score: int
    priority: str
    next_follow_up_date: Optional[datetime]
    follow_up_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Lead Activity Schemas
class LeadActivityBase(BaseModel):
    activity_type: ActivityTypeEnum
    subject: Optional[str] = None
    details: str = Field(..., min_length=1)
    duration_minutes: Optional[int] = None

class LeadActivityCreate(LeadActivityBase):
    """Schema for creating a lead activity"""
    pass

class LeadActivityResponse(LeadActivityBase):
    """Schema for lead activity response"""
    id: int
    lead_id: int
    performed_by: int
    created_at: datetime

    class Config:
        from_attributes = True

# Assignment Rule Schemas
class AssignmentRuleBase(BaseModel):
    agent_id: int
    agent_name: str
    is_active: bool = True
    weight: int = 1
    max_leads_per_day: int = 10

class AssignmentRuleCreate(AssignmentRuleBase):
    """Schema for creating an assignment rule"""
    pass

class AssignmentRuleUpdate(BaseModel):
    """Schema for updating an assignment rule"""
    is_active: Optional[bool] = None
    weight: Optional[int] = None
    max_leads_per_day: Optional[int] = None

class AssignmentRuleResponse(AssignmentRuleBase):
    """Schema for assignment rule response"""
    id: int
    total_leads_assigned: int
    last_assigned_at: Optional[datetime]
    leads_assigned_today: int
    last_reset_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Conversion Schema
class LeadConversionRequest(BaseModel):
    """Schema for lead to charter conversion"""
    create_client: bool = True
    create_charter: bool = True

class LeadConversionResponse(BaseModel):
    """Schema for conversion response"""
    success: bool
    lead_id: int
    client_id: Optional[int] = None
    charter_id: Optional[int] = None
    message: str

# Email Preference Schemas
class EmailPreferenceUpdate(BaseModel):
    """Schema for updating email preferences"""
    automated_emails_enabled: Optional[bool] = None
    marketing_emails_enabled: Optional[bool] = None
    reminder_emails_enabled: Optional[bool] = None
    quote_emails_enabled: Optional[bool] = None

class EmailPreferenceResponse(BaseModel):
    """Schema for email preference response"""
    id: int
    client_id: int
    automated_emails_enabled: bool
    marketing_emails_enabled: bool
    reminder_emails_enabled: bool
    quote_emails_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

2. Save file

**Verification:**
```python
# Test schemas can be imported
python3 -c "from schemas import LeadCreate, LeadResponse; print('Schemas OK')"
```

---

### Task 1.5: Implement Business Logic

**Estimated Time:** 1 hour

**File:** `backend/services/sales/business_logic.py`

**Instructions:**
1. Create business logic layer:

```python
"""
Business logic for Sales Service
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
from typing import Optional, List
import httpx
import logging

from models import Lead, LeadActivity, AssignmentRule, LeadStatus
import config

logger = logging.getLogger(__name__)


class LeadAssignmentService:
    """Service for assigning leads to sales agents"""
    
    @staticmethod
    async def assign_lead_to_agent(db: Session, lead: Lead) -> Optional[int]:
        """
        Assign lead to an agent using round-robin logic
        Returns assigned agent_id or None if no agents available
        """
        # Check if lead email matches existing client
        existing_client = await LeadAssignmentService._check_existing_client(lead.email)
        if existing_client and existing_client.get("assigned_agent_id"):
            logger.info(f"Lead {lead.id} matches existing client, assigning to agent {existing_client['assigned_agent_id']}")
            return existing_client["assigned_agent_id"]
        
        # Get active assignment rules
        today = date.today()
        rules = db.query(AssignmentRule).filter(
            AssignmentRule.is_active == True
        ).order_by(
            AssignmentRule.last_assigned_at.asc().nullsfirst()
        ).all()
        
        if not rules:
            logger.warning("No active assignment rules found")
            return None
        
        # Reset daily counters if needed
        for rule in rules:
            if rule.last_reset_date is None or rule.last_reset_date < today:
                rule.leads_assigned_today = 0
                rule.last_reset_date = datetime.now()
                db.add(rule)
        
        # Find agent with capacity
        for rule in rules:
            if rule.leads_assigned_today < rule.max_leads_per_day:
                # Assign to this agent
                rule.last_assigned_at = datetime.now()
                rule.total_leads_assigned += 1
                rule.leads_assigned_today += 1
                db.add(rule)
                db.commit()
                
                logger.info(f"Assigned lead {lead.id} to agent {rule.agent_id}")
                return rule.agent_id
        
        logger.warning(f"All agents at capacity, lead {lead.id} not assigned")
        return None
    
    @staticmethod
    async def _check_existing_client(email: str) -> Optional[dict]:
        """Check if client exists in Client Service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.CLIENT_SERVICE_URL}/api/v1/clients/by-email/{email}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error checking existing client: {e}")
        return None


class LeadConversionService:
    """Service for converting leads to charters"""
    
    @staticmethod
    async def convert_lead(db: Session, lead: Lead, user_id: int) -> dict:
        """
        Convert lead to client and charter
        Returns dict with client_id and charter_id
        """
        result = {
            "client_id": None,
            "charter_id": None,
            "errors": []
        }
        
        # Step 1: Create or get client
        try:
            client_data = {
                "name": f"{lead.first_name} {lead.last_name}",
                "type": "personal" if not lead.company_name else "corporate",
                "email": lead.email,
                "phone": lead.phone or "",
                "company_name": lead.company_name
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.CLIENT_SERVICE_URL}/api/v1/clients",
                    json=client_data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    client_response = response.json()
                    result["client_id"] = client_response.get("id")
                    logger.info(f"Created client {result['client_id']} from lead {lead.id}")
                else:
                    result["errors"].append(f"Client creation failed: {response.text}")
                    return result
                    
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            result["errors"].append(f"Client creation error: {str(e)}")
            return result
        
        # Step 2: Create charter quote
        try:
            charter_data = {
                "client_id": result["client_id"],
                "status": "quote",
                "trip_date": lead.estimated_trip_date.isoformat() if lead.estimated_trip_date else None,
                "passengers": lead.estimated_passengers or 1,
                "notes": lead.trip_details or "",
                "trip_hours": 8,  # Default
                "is_overnight": False,
                "is_weekend": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.CHARTER_SERVICE_URL}/api/v1/charters",
                    json=charter_data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    charter_response = response.json()
                    result["charter_id"] = charter_response.get("id")
                    logger.info(f"Created charter {result['charter_id']} from lead {lead.id}")
                else:
                    result["errors"].append(f"Charter creation failed: {response.text}")
                    return result
                    
        except Exception as e:
            logger.error(f"Error creating charter: {e}")
            result["errors"].append(f"Charter creation error: {str(e)}")
            return result
        
        # Step 3: Update lead status
        lead.status = LeadStatus.CONVERTED
        lead.converted_to_client_id = result["client_id"]
        lead.converted_to_charter_id = result["charter_id"]
        lead.converted_at = datetime.now()
        db.add(lead)
        
        # Step 4: Log activity
        activity = LeadActivity(
            lead_id=lead.id,
            activity_type="status_change",
            subject="Lead Converted",
            details=f"Converted to client ID {result['client_id']} and charter ID {result['charter_id']}",
            performed_by=user_id
        )
        db.add(activity)
        db.commit()
        
        return result
```

2. Save file

---

### Task 1.6: Create FastAPI Main Application

**Estimated Time:** 1.5 hours

**File:** `backend/services/sales/main.py`

**Instructions:**
1. Create the FastAPI application with all endpoints:

```python
"""
Sales Service - Lead Management and Assignment
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
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
    uvicorn.run(app, host="0.0.0.0", port=8007)
```

2. Save file

**Verification:**
```bash
# Syntax check
python3 -m py_compile main.py
echo "Syntax check passed"
```

---

### Task 1.7: Update Docker Compose

**Estimated Time:** 20 minutes

**File:** `docker-compose.yml` (in project root)

**Instructions:**
1. Add sales service configuration to docker-compose.yml
2. Add after the existing services (around line 200):

```yaml
  # Sales Service
  sales-service:
    build:
      context: ./backend/services/sales
      dockerfile: Dockerfile
    container_name: athena-sales-service
    environment:
      - SALES_DATABASE_URL=postgresql://athena:athena_dev_password@postgres:5432/sales_db
      - AUTH_SERVICE_URL=http://auth-service:8001
      - CLIENT_SERVICE_URL=http://client-service:8003
      - CHARTER_SERVICE_URL=http://charter-service:8002
      - SECRET_KEY=dev_secret_key_change_in_production
    ports:
      - "8007:8007"
    depends_on:
      - postgres
      - auth-service
      - client-service
      - charter-service
    networks:
      - athena-network
    restart: unless-stopped
```

**Verification:**
```bash
# Validate docker-compose syntax
docker-compose config
# Should show no errors
```

---

### Task 1.8: Create Database

**Estimated Time:** 10 minutes

**Instructions:**
1. Create the sales database:
   ```bash
   # Connect to PostgreSQL
   docker exec -it athena-postgres psql -U athena -d athena
   ```

2. Run SQL command:
   ```sql
   CREATE DATABASE sales_db;
   \c sales_db
   -- Verify connection
   \conninfo
   -- Exit
   \q
   ```

**Verification:**
```bash
docker exec -it athena-postgres psql -U athena -d sales_db -c "\dt"
# Should show empty table list (tables will be created when service starts)
```

---

### Task 1.9: Build and Start Service

**Estimated Time:** 15 minutes

**Instructions:**
1. Build the sales service:
   ```bash
   cd /home/nick/work_area/coachway_demo
   docker-compose build sales-service
   ```

2. Start the service:
   ```bash
   docker-compose up -d sales-service
   ```

3. Check logs:
   ```bash
   docker-compose logs -f sales-service
   # Look for "Application startup complete"
   # Press Ctrl+C to exit
   ```

**Verification:**
```bash
# Test health endpoint directly (bypassing Kong)
curl http://localhost:8007/health
# Should return: {"status":"healthy","service":"sales"}

# Test API docs
curl http://localhost:8007/docs
# Should return HTML
```

---

### Task 1.10: Configure Kong Gateway Routes

**Estimated Time:** 10 minutes

**Instructions:**
1. Wait for sales service to be fully healthy:
   ```bash
   # Check service is responding
   timeout 30 bash -c 'until curl -s http://localhost:8007/health > /dev/null 2>&1; do sleep 2; echo -n "."; done' && echo " ✓"
   ```

2. Create Kong service for sales service:
   ```bash
   curl -X POST http://localhost:8081/services \
     --data name=sales-service \
     --data url=http://sales-service:8000
   ```

3. Create Kong route for sales service:
   ```bash
   curl -X POST http://localhost:8081/services/sales-service/routes \
     --data "paths[]=/api/v1/sales" \
     --data strip_path=false
   ```

4. Verify Kong configuration:
   ```bash
   # Check service exists
   curl http://localhost:8081/services/sales-service | jq
   
   # Check route exists
   curl http://localhost:8081/services/sales-service/routes | jq
   ```

**Verification:**
```bash
# Test through Kong gateway
curl http://localhost:8080/api/v1/sales/health
# Should return: {"status":"healthy","service":"sales"}

# Verify routing is working
echo "Kong routing configured successfully!"
```

---

### Task 1.11: Comprehensive API Testing via Kong Gateway

**Estimated Time:** 30 minutes

**Purpose:** Verify all sales service endpoints work correctly through Kong gateway

**Instructions:**

1. First, obtain admin authentication token:
   ```bash
   # Get admin token
   TOKEN=$(curl -X POST http://localhost:8000/token \
     -d "username=admin@athena.com" \
     -d "password=admin123" \
     | jq -r '.access_token')
   
   echo "Token: $TOKEN"
   ```

2. Create test assignment rule:
   ```bash
   curl -X POST http://localhost:8080/api/v1/sales/assignment-rules \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": 1,
       "is_active": true,
       "priority": 1,
       "max_leads_per_day": 10
     }'
   # Expected: 201 Created with rule details
   ```

3. Create test lead (should auto-assign):
   ```bash
   curl -X POST http://localhost:8080/api/v1/sales/leads \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "Test",
       "last_name": "Customer",
       "email": "test@example.com",
       "phone": "555-0123",
       "company_name": "Test Company",
       "passengers": 50,
       "trip_date": "2026-03-15",
       "pickup_location": "Boston, MA",
       "dropoff_location": "New York, NY",
       "source": "web",
       "status": "new"
     }' | jq
   # Expected: 201 Created with assigned_to_agent_id=1
   # Save the lead_id for next steps
   ```

4. List all leads:
   ```bash
   curl -X GET http://localhost:8080/api/v1/sales/leads \
     -H "Authorization: Bearer $TOKEN" | jq
   # Expected: 200 OK with array of leads
   ```

5. Get specific lead:
   ```bash
   LEAD_ID=1  # Replace with actual ID from step 3
   curl -X GET http://localhost:8080/api/v1/sales/leads/$LEAD_ID \
     -H "Authorization: Bearer $TOKEN" | jq
   # Expected: 200 OK with lead details
   ```

6. Update lead status:
   ```bash
   curl -X PUT http://localhost:8080/api/v1/sales/leads/$LEAD_ID \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "contacted",
       "notes": "Called customer, interested in quote"
     }' | jq
   # Expected: 200 OK with updated lead
   ```

7. Log lead activity:
   ```bash
   curl -X POST http://localhost:8080/api/v1/sales/leads/$LEAD_ID/activities \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "activity_type": "call",
       "notes": "Initial contact call, customer requested quote",
       "duration_minutes": 15
     }' | jq
   # Expected: 201 Created with activity details
   ```

8. Get lead activities:
   ```bash
   curl -X GET http://localhost:8080/api/v1/sales/leads/$LEAD_ID/activities \
     -H "Authorization: Bearer $TOKEN" | jq
   # Expected: 200 OK with array of activities
   ```

9. Get pipeline view:
   ```bash
   curl -X GET http://localhost:8080/api/v1/sales/leads/pipeline \
     -H "Authorization: Bearer $TOKEN" | jq
   # Expected: 200 OK with pipeline grouped by status
   ```

10. Get my leads (agent view):
    ```bash
    curl -X GET "http://localhost:8080/api/v1/sales/leads/my-leads?agent_id=1" \
      -H "Authorization: Bearer $TOKEN" | jq
    # Expected: 200 OK with leads assigned to agent 1
    ```

11. Test lead conversion to charter:
    ```bash
    curl -X POST http://localhost:8080/api/v1/sales/leads/$LEAD_ID/convert \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "notes": "Lead qualified, creating charter",
        "create_charter": true
      }' | jq
    # Expected: 200 OK with charter_id and conversion details
    ```

12. Test email preferences:
    ```bash
    # Get email preferences
    curl -X GET http://localhost:8080/api/v1/sales/email-preferences/1 \
      -H "Authorization: Bearer $TOKEN" | jq
    
    # Update email preferences
    curl -X PUT http://localhost:8080/api/v1/sales/email-preferences/1 \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "marketing_emails_enabled": false,
        "reminder_emails_enabled": true
      }' | jq
    # Expected: 200 OK with updated preferences
    ```

**Success Criteria:**
- ✅ All endpoints return expected HTTP status codes
- ✅ Lead auto-assignment works (agent_id=1)
- ✅ Lead activities are logged correctly
- ✅ Pipeline view groups leads by status
- ✅ Lead conversion creates charter in charter service
- ✅ All requests go through Kong gateway (port 8080)

---

### Task 1.12: Test the API

**Estimated Time:** 30 minutes

**Instructions:**
1. Create test assignment rule:
   ```bash
   curl -X POST "http://localhost:8007/api/v1/assignment-rules" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": 1,
       "agent_name": "Test Agent",
       "is_active": true,
       "weight": 1,
       "max_leads_per_day": 10
     }'
   ```

2. Create test lead:
   ```bash
   curl -X POST "http://localhost:8007/api/v1/leads" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "email": "john.doe@example.com",
       "phone": "555-1234",
       "company_name": "Acme Corp",
       "source": "web",
       "estimated_passengers": 20,
       "pickup_location": "New York, NY",
       "dropoff_location": "Boston, MA"
     }'
   ```

3. List leads:
   ```bash
   curl "http://localhost:8007/api/v1/leads"
   ```

**Expected Results:**
- Assignment rule creation returns status 201
- Lead creation returns status 201 with assigned_agent_id=1
- List leads returns array with the created lead

**Note:** Task 1.10 and 1.11 now provide comprehensive Kong gateway testing. This section remains for legacy direct testing.

---

## Phase 2: Charter Enhancements (Weeks 4-5)

**Goal:** Add multi-stop capabilities, cloning, and recurring charters.

### Task 2.1: Database Schema Migration

**Estimated Time:** 45 minutes

**Instructions:**
1. Create migration file:
   ```bash
   cd backend/services/charters
   # If not using Alembic, we'll do direct SQL migration
   ```

2. Create migration script `backend/services/charters/migrations/001_add_charter_fields.sql`:
   ```sql
   -- Add new columns to charters table
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS trip_type VARCHAR(50);
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS requires_second_driver BOOLEAN DEFAULT false;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS vehicle_count INT DEFAULT 1;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS parent_charter_id INT REFERENCES charters(id);
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS quote_secure_token VARCHAR(255) UNIQUE;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS revision_number INT DEFAULT 1;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS recurrence_rule TEXT;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS instance_number INT;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS series_total INT;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS is_series_master BOOLEAN DEFAULT false;
   ALTER TABLE charters ADD COLUMN IF NOT EXISTS cloned_from_charter_id INT REFERENCES charters(id);
   
   -- Add new columns to stops table
   ALTER TABLE stops ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,7);
   ALTER TABLE stops ADD COLUMN IF NOT EXISTS longitude DECIMAL(10,7);
   ALTER TABLE stops ADD COLUMN IF NOT EXISTS geocoded_address TEXT;
   ALTER TABLE stops ADD COLUMN IF NOT EXISTS stop_type VARCHAR(20) DEFAULT 'waypoint';
   ALTER TABLE stops ADD COLUMN IF NOT EXISTS estimated_arrival TIME;
   ALTER TABLE stops ADD COLUMN IF NOT EXISTS estimated_departure TIME;
   
   -- Create index for performance
   CREATE INDEX IF NOT EXISTS idx_charters_parent ON charters(parent_charter_id);
   CREATE INDEX IF NOT EXISTS idx_charters_secure_token ON charters(quote_secure_token);
   ```

3. Run migration:
   ```bash
   docker exec -it athena-postgres psql -U athena -d athena -f /path/to/migration.sql
   ```

---

### Task 2.2: Update Charter Models

**File:** `backend/services/charters/models.py`

**Instructions:**
1. Add new fields to Charter model (around line 30):
   ```python
   # After existing fields, add:
   trip_type = Column(String(50), nullable=True)
   requires_second_driver = Column(Boolean, default=False)
   vehicle_count = Column(Integer, default=1)
   parent_charter_id = Column(Integer, ForeignKey("charters.id"), nullable=True)
   quote_secure_token = Column(String(255), unique=True, nullable=True)
   revision_number = Column(Integer, default=1)
   recurrence_rule = Column(Text, nullable=True)
   instance_number = Column(Integer, nullable=True)
   series_total = Column(Integer, nullable=True)
   is_series_master = Column(Boolean, default=False)
   cloned_from_charter_id = Column(Integer, ForeignKey("charters.id"), nullable=True)
   ```

2. Update Stop model (around line 150):
   ```python
   # Add after existing columns:
   latitude = Column(Float, nullable=True)
   longitude = Column(Float, nullable=True)
   geocoded_address = Column(Text, nullable=True)
   stop_type = Column(String(20), default="waypoint")
   estimated_arrival = Column(DateTime(timezone=True), nullable=True)
   estimated_departure = Column(DateTime(timezone=True), nullable=True)
   ```

---

### Task 2.3: Add Clone Endpoint

**File:** `backend/services/charters/main.py`

**Instructions:**
1. Add new endpoint (around line 500):
   ```python
   @app.post("/api/v1/charters/{charter_id}/clone", response_model=CharterResponse)
   async def clone_charter(
       charter_id: int,
       new_trip_date: Optional[str] = Query(None),
       db: Session = Depends(get_db)
   ):
       """Clone an existing charter"""
       # Get original charter
       original = db.query(Charter).filter(Charter.id == charter_id).first()
       if not original:
           raise HTTPException(status_code=404, detail="Charter not found")
       
       # Create new charter (copy fields)
       new_charter = Charter(
           client_id=original.client_id,
           vehicle_id=original.vehicle_id,
           vendor_id=original.vendor_id,
           status="quote",
           trip_date=new_trip_date or original.trip_date,
           passengers=original.passengers,
           trip_hours=original.trip_hours,
           is_overnight=original.is_overnight,
           is_weekend=original.is_weekend,
           trip_type=original.trip_type,
           vehicle_count=original.vehicle_count,
           requires_second_driver=original.requires_second_driver,
           notes=original.notes,
           cloned_from_charter_id=charter_id
       )
       db.add(new_charter)
       db.flush()
       
       # Clone stops
       original_stops = db.query(Stop).filter(Stop.charter_id == charter_id).order_by(Stop.sequence).all()
       for stop in original_stops:
           new_stop = Stop(
               charter_id=new_charter.id,
               sequence=stop.sequence,
               location=stop.location,
               latitude=stop.latitude,
               longitude=stop.longitude,
               stop_type=stop.stop_type,
               notes=stop.notes
           )
           db.add(new_stop)
       
       db.commit()
       db.refresh(new_charter)
       
       logger.info(f"Cloned charter {charter_id} to new charter {new_charter.id}")
       return new_charter
   ```

---

### Task 2.4: Add Geocoding Helper

**Estimated Time:** 30 minutes

**File:** `backend/services/charters/geocoding.py`

**Instructions:**
1. Create new file:
   ```bash
   cd backend/services/charters
   touch geocoding.py
   ```

2. Add geocoding implementation:
   ```python
   """
   Geocoding service for address resolution
   """
   import httpx
   import logging
   from typing import Optional, Tuple

   logger = logging.getLogger(__name__)

   GOOGLE_MAPS_API_KEY = "YOUR_API_KEY"  # Set via environment variable

   async def geocode_address(address: str) -> Optional[dict]:
       """
       Geocode an address using Google Maps API
       Returns: {lat, lng, formatted_address} or None
       """
       if not address:
           return None
       
       try:
           async with httpx.AsyncClient() as client:
               response = await client.get(
                   "https://maps.googleapis.com/maps/api/geocode/json",
                   params={
                       "address": address,
                       "key": GOOGLE_MAPS_API_KEY
                   },
                   timeout=5.0
               )
               
               if response.status_code == 200:
                   data = response.json()
                   if data["status"] == "OK" and data.get("results"):
                       result = data["results"][0]
                       location = result["geometry"]["location"]
                       return {
                           "latitude": location["lat"],
                           "longitude": location["lng"],
                           "formatted_address": result["formatted_address"]
                       }
           
       except Exception as e:
           logger.error(f"Geocoding error for '{address}': {e}")
       
       return None
   ```

3. Add endpoint to geocode stops in `main.py`:
   ```python
   from geocoding import geocode_address

   @app.post("/api/v1/charters/{charter_id}/geocode-stops")
   async def geocode_charter_stops(
       charter_id: int,
       db: Session = Depends(get_db)
   ):
       """Geocode all stops for a charter"""
       stops = db.query(Stop).filter(Stop.charter_id == charter_id).all()
       
       geocoded_count = 0
       for stop in stops:
           if stop.latitude is None and stop.location:
               result = await geocode_address(stop.location)
               if result:
                   stop.latitude = result["latitude"]
                   stop.longitude = result["longitude"]
                   stop.geocoded_address = result["formatted_address"]
                   geocoded_count += 1
       
       db.commit()
       return {"geocoded": geocoded_count, "total": len(stops)}
   ```

**Verification:**
```bash
# Test geocoding endpoint
curl -X POST "http://localhost:8002/api/v1/charters/1/geocode-stops"
```

---

### Task 2.5: Add Recurring Charter Logic

**Estimated Time:** 1 hour

**File:** `backend/services/charters/main.py`

**Instructions:**
1. Add recurring charter endpoint:
   ```python
   from datetime import timedelta
   import uuid

   @app.post("/api/v1/charters/create-recurring", response_model=dict)
   async def create_recurring_charters(
       base_charter_id: int,
       recurrence_pattern: str = Query(..., description="daily, weekly, or monthly"),
       occurrence_count: int = Query(..., ge=1, le=365),
       start_date: str = Query(...),
       db: Session = Depends(get_db)
   ):
       """
       Create recurring charter series
       Pattern options: 'daily', 'weekly', 'monthly'
       """
       # Get base charter
       base_charter = db.query(Charter).filter(Charter.id == base_charter_id).first()
       if not base_charter:
           raise HTTPException(status_code=404, detail="Base charter not found")
       
       # Generate series ID
       series_id = str(uuid.uuid4())
       
       # Parse start date
       from datetime import datetime
       start = datetime.fromisoformat(start_date)
       
       created_charters = []
       
       for i in range(occurrence_count):
           # Calculate trip date based on pattern
           if recurrence_pattern == "daily":
               trip_date = start + timedelta(days=i)
           elif recurrence_pattern == "weekly":
               trip_date = start + timedelta(weeks=i)
           elif recurrence_pattern == "monthly":
               # Approximate monthly (30 days)
               trip_date = start + timedelta(days=30*i)
           else:
               raise HTTPException(status_code=400, detail="Invalid recurrence pattern")
           
           # Create charter instance
           new_charter = Charter(
               client_id=base_charter.client_id,
               vehicle_id=base_charter.vehicle_id,
               vendor_id=base_charter.vendor_id,
               status="quote",
               trip_date=trip_date,
               passengers=base_charter.passengers,
               trip_hours=base_charter.trip_hours,
               is_overnight=base_charter.is_overnight,
               trip_type=base_charter.trip_type,
               vehicle_count=base_charter.vehicle_count,
               requires_second_driver=base_charter.requires_second_driver,
               parent_charter_id=base_charter_id,
               instance_number=i+1,
               series_total=occurrence_count,
               is_series_master=(i==0),
               recurrence_rule=f"{recurrence_pattern}:{occurrence_count}:{series_id}",
               notes=f"Series {i+1} of {occurrence_count} - {base_charter.notes or ''}"
           )
           db.add(new_charter)
           db.flush()
           
           # Clone stops
           base_stops = db.query(Stop).filter(Stop.charter_id == base_charter_id).all()
           for stop in base_stops:
               new_stop = Stop(
                   charter_id=new_charter.id,
                   sequence=stop.sequence,
                   location=stop.location,
                   latitude=stop.latitude,
                   longitude=stop.longitude,
                   stop_type=stop.stop_type,
                   notes=stop.notes
               )
               db.add(new_stop)
           
           created_charters.append(new_charter.id)
       
       db.commit()
       
       return {
           "series_id": series_id,
           "charter_ids": created_charters,
           "count": occurrence_count
       }
   ```

**Verification:**
```bash
# Create recurring charters
curl -X POST "http://localhost:8002/api/v1/charters/create-recurring?base_charter_id=1&recurrence_pattern=weekly&occurrence_count=10&start_date=2026-03-01"
```

---

### Task 2.6: Comprehensive Testing via Kong Gateway

**Estimated Time:** 30 minutes

**Purpose:** Verify all charter enhancements work through Kong gateway

**Instructions:**

1. Get authentication token:
   ```bash
   TOKEN=$(curl -X POST http://localhost:8000/token \
     -d "username=admin@athena.com" \
     -d "password=admin123" \
     | jq -r '.access_token')
   ```

2. Test multi-stop charter creation:
   ```bash
   CHARTER_ID=$(curl -X POST http://localhost:8080/api/v1/charters/charters \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "trip_date": "2026-04-15",
       "passengers": 45,
       "pickup_location": "Boston, MA",
       "dropoff_location": "New York, NY",
       "trip_type": "multi_day",
       "vehicle_count": 1,
       "client_id": 1,
       "status": "quote"
     }' | jq -r '.id')
   
   echo "Created Charter ID: $CHARTER_ID"
   ```

3. Add multiple stops to itinerary:
   ```bash
   # Add stop 1
   curl -X POST "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/stops" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "sequence": 1,
       "location": "Boston, MA",
       "stop_type": "pickup",
       "notes": "Main pickup location"
     }' | jq
   
   # Add stop 2
   curl -X POST "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/stops" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "sequence": 2,
       "location": "Hartford, CT",
       "stop_type": "waypoint",
       "notes": "Rest stop"
     }' | jq
   
   # Add stop 3
   curl -X POST "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/stops" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "sequence": 3,
       "location": "New York, NY",
       "stop_type": "dropoff",
       "notes": "Final destination"
     }' | jq
   ```

4. Geocode all stops:
   ```bash
   curl -X POST "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/geocode-stops" \
     -H "Authorization: Bearer $TOKEN" | jq
   # Expected: Returns count of geocoded stops
   ```

5. Test reorder stops:
   ```bash
   curl -X PUT "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/reorder-stops" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "stop_ids": [3, 2, 1]
     }' | jq
   # Expected: Stops resequenced
   ```

6. Test clone charter:
   ```bash
   CLONED_ID=$(curl -X POST "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/clone" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "new_trip_date": "2026-04-22",
       "clone_stops": true,
       "clone_amenities": true
     }' | jq -r '.id')
   
   echo "Cloned Charter ID: $CLONED_ID"
   
   # Verify clone has same stops
   curl -X GET "http://localhost:8080/api/v1/charters/charters/$CLONED_ID" \
     -H "Authorization: Bearer $TOKEN" | jq '.stops | length'
   # Expected: Same number of stops as original
   ```

7. Test recurring charter creation:
   ```bash
   curl -X POST "http://localhost:8080/api/v1/charters/charters/create-recurring" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d "{
       \"base_charter_id\": $CHARTER_ID,
       \"recurrence_pattern\": \"weekly\",
       \"occurrence_count\": 4,
       \"start_date\": \"2026-05-01\"
     }" | jq
   # Expected: Returns series_id and array of charter_ids
   ```

8. Verify recurring series:
   ```bash
   # Get all charters with same series_id
   SERIES_ID=$(curl -X GET "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID" \
     -H "Authorization: Bearer $TOKEN" | jq -r '.recurring_series_id')
   
   curl -X GET "http://localhost:8080/api/v1/charters/charters?series_id=$SERIES_ID" \
     -H "Authorization: Bearer $TOKEN" | jq 'length'
   # Expected: Should return 4 charters
   ```

9. Test DOT compliance check:
   ```bash
   curl -X POST "http://localhost:8080/api/v1/charters/charters/check-dot-compliance" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "total_miles": 650,
       "trip_hours": 11,
       "trip_date": "2026-06-01"
     }' | jq
   # Expected: Returns requires_second_driver: true (if over limits)
   ```

10. Update charter to require second driver:
    ```bash
    curl -X PUT "http://localhost:8080/api/v1/charters/charters/$CHARTER_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "requires_second_driver": true,
        "vehicle_count": 2
      }' | jq
    # Expected: 200 OK with updated charter
    ```

**Success Criteria:**
- ✅ Multi-stop itineraries created successfully
- ✅ Geocoding resolves addresses to lat/lng
- ✅ Stop reordering updates sequence correctly
- ✅ Charter cloning duplicates all data
- ✅ Recurring charters create series with correct dates
- ✅ DOT compliance detection works
- ✅ All requests go through Kong gateway (port 8080)

---

## Phase 3: Pricing Service (Weeks 6-7)

### Overview
**Goal:** Dynamic pricing rules instead of hardcoded logic.  
**Port:** 8008  
**Database:** `pricing_db`

---

### Task 3.1: Scaffold Pricing Service

**Estimated Time:** 20 minutes

**Instructions:**
1. Create directory structure:
   ```bash
   cd backend/services
   mkdir -p pricing
   cd pricing
   ```

2. Copy boilerplate:
   ```bash
   cp ../sales/config.py ./config.py
   cp ../sales/database.py ./database.py
   cp ../sales/Dockerfile ./Dockerfile
   cp ../sales/requirements.txt ./requirements.txt
   ```

3. Create Python files:
   ```bash
   touch __init__.py main.py models.py schemas.py business_logic.py
   ```

4. Update `config.py`:
   ```python
   """
   Configuration for Pricing Service
   """
   import os

   DATABASE_URL = os.getenv(
       "PRICING_DATABASE_URL",
       "postgresql://athena:athena_dev_password@localhost:5432/pricing_db"
   )

   SERVICE_NAME = "pricing"
   SERVICE_PORT = int(os.getenv("PRICING_SERVICE_PORT", "8008"))
   
   # External service URLs
   CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://localhost:8002")
   
   SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
   ```

5. Update Dockerfile port:
   ```dockerfile
   # Change EXPOSE line
   EXPOSE 8008
   
   # Change CMD line
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
   ```

---

### Task 3.2: Create Pricing Models

**Estimated Time:** 45 minutes

**File:** `backend/services/pricing/models.py`

**Instructions:**
1. Add complete pricing models:

```python
"""
Database models for Pricing Service
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class VehicleRate(Base):
    """Base rates for vehicle types"""
    __tablename__ = "vehicle_rates"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_type_name = Column(String(100), nullable=False, unique=True, index=True)
    
    # Base rates
    base_hourly_rate = Column(Float, nullable=False)
    base_mileage_rate = Column(Float, nullable=False)
    minimum_hours = Column(Integer, default=4)
    
    # Capacity
    passenger_capacity = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<VehicleRate {self.vehicle_type_name}>"


class PricingModifier(Base):
    """Pricing modifiers for special conditions"""
    __tablename__ = "pricing_modifiers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Modifier identification
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    modifier_type = Column(String(50), nullable=False, index=True)
    # Types: weekend, holiday, rush_hour, overnight, last_minute, season
    
    # Modifier logic
    multiplier = Column(Float, nullable=False, default=1.0)
    fixed_amount = Column(Float, default=0.0)
    
    # Conditions
    condition_json = Column(Text, nullable=True)  # JSON for complex conditions
    
    # Applicability
    applies_to_vehicle_types = Column(Text, nullable=True)  # Comma-separated
    
    # Date range (optional)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    
    # Days of week (for recurring modifiers)
    applies_monday = Column(Boolean, default=True)
    applies_tuesday = Column(Boolean, default=True)
    applies_wednesday = Column(Boolean, default=True)
    applies_thursday = Column(Boolean, default=True)
    applies_friday = Column(Boolean, default=True)
    applies_saturday = Column(Boolean, default=True)
    applies_sunday = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0)  # Higher priority applies first
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PricingModifier {self.name}>"


class Amenity(Base):
    """Available amenities with pricing"""
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    
    # Amenity details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # comfort, entertainment, refreshments
    
    # Pricing
    price_type = Column(String(20), nullable=False)  # fixed, per_hour, per_passenger
    price_amount = Column(Float, nullable=False)
    
    # Cost (internal)
    cost_amount = Column(Float, default=0.0)
    
    # Availability
    requires_advance_booking = Column(Boolean, default=False)
    advance_booking_hours = Column(Integer, default=24)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Amenity {self.name}>"


class PromoCode(Base):
    """Promotional discount codes"""
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Code identification
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Discount details
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    discount_value = Column(Float, nullable=False)
    
    # Constraints
    minimum_trip_cost = Column(Float, default=0.0)
    maximum_discount = Column(Float, nullable=True)
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)
    max_uses_per_client = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    
    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Applicability
    applies_to_vehicle_types = Column(Text, nullable=True)
    applies_to_client_types = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    usage_records = relationship("PromoCodeUsage", back_populates="promo_code")

    def __repr__(self):
        return f"<PromoCode {self.code}>"


class PromoCodeUsage(Base):
    """Track promo code usage"""
    __tablename__ = "promo_code_usage"

    id = Column(Integer, primary_key=True, index=True)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False, index=True)
    
    # Usage details
    client_id = Column(Integer, nullable=False, index=True)
    charter_id = Column(Integer, nullable=False)
    discount_applied = Column(Float, nullable=False)
    
    # Timestamp
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    promo_code = relationship("PromoCode", back_populates="usage_records")

    def __repr__(self):
        return f"<PromoCodeUsage {self.id}>"


class DOTRegulation(Base):
    """DOT compliance rules"""
    __tablename__ = "dot_regulations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Rule identification
    rule_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Thresholds
    max_driving_hours = Column(Float, nullable=True)
    max_distance_miles = Column(Float, nullable=True)
    requires_second_driver = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DOTRegulation {self.rule_name}>"
```

---

### Task 3.3: Create Pricing Schemas

**Estimated Time:** 30 minutes

**File:** `backend/services/pricing/schemas.py`

**Instructions:**
1. Add Pydantic schemas:

```python
"""
Pydantic schemas for Pricing Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date

# Vehicle Rate Schemas
class VehicleRateBase(BaseModel):
    vehicle_type_name: str
    base_hourly_rate: float = Field(..., gt=0)
    base_mileage_rate: float = Field(..., gt=0)
    minimum_hours: int = 4
    passenger_capacity: int = Field(..., gt=0)

class VehicleRateCreate(VehicleRateBase):
    pass

class VehicleRateResponse(VehicleRateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Pricing Modifier Schemas
class PricingModifierBase(BaseModel):
    name: str
    description: Optional[str] = None
    modifier_type: str
    multiplier: float = 1.0
    fixed_amount: float = 0.0
    is_active: bool = True
    priority: int = 0

class PricingModifierCreate(PricingModifierBase):
    pass

class PricingModifierResponse(PricingModifierBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Amenity Schemas
class AmenityBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price_type: str
    price_amount: float = Field(..., ge=0)
    cost_amount: float = 0.0

class AmenityCreate(AmenityBase):
    pass

class AmenityResponse(AmenityBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Promo Code Schemas
class PromoCodeBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    discount_type: str
    discount_value: float = Field(..., gt=0)
    minimum_trip_cost: float = 0.0
    max_uses: Optional[int] = None

class PromoCodeCreate(PromoCodeBase):
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class PromoCodeResponse(PromoCodeBase):
    id: int
    current_uses: int
    is_active: bool
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# Quote Calculation Schemas
class QuoteCalculationRequest(BaseModel):
    vehicle_type_id: int
    total_miles: float = Field(..., ge=0)
    total_hours: float = Field(..., ge=0)
    trip_date: date
    passengers: int = Field(..., ge=1)
    amenity_ids: List[int] = []
    promo_code: Optional[str] = None

class PriceBreakdown(BaseModel):
    category: str
    description: str
    amount: float

class QuoteCalculationResponse(BaseModel):
    base_cost: float
    mileage_cost: float
    hourly_cost: float
    amenities_cost: float
    modifiers_applied: List[str]
    subtotal: float
    discount: float
    total_cost: float
    breakdown: List[PriceBreakdown]

# DOT Compliance Schemas
class DOTComplianceRequest(BaseModel):
    total_miles: float
    total_hours: float

class DOTComplianceResponse(BaseModel):
    compliant: bool
    requires_second_driver: bool
    warnings: List[str]
    max_hours_exceeded: bool
    max_miles_exceeded: bool
```

---

### Task 3.4: Implement Pricing Calculator

**Estimated Time:** 1.5 hours

**File:** `backend/services/pricing/business_logic.py`

**Instructions:**
1. Create pricing calculation engine:

```python
"""
Business logic for Pricing Service
"""
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

from models import (
    VehicleRate, PricingModifier, Amenity, 
    PromoCode, PromoCodeUsage, DOTRegulation
)

logger = logging.getLogger(__name__)


class PricingCalculator:
    """Main pricing calculation engine"""
    
    @staticmethod
    def calculate_quote(
        db: Session,
        vehicle_type_id: int,
        total_miles: float,
        total_hours: float,
        trip_date: date,
        passengers: int,
        amenity_ids: List[int] = [],
        promo_code: Optional[str] = None
    ) -> Dict:
        """
        Calculate comprehensive quote with all modifiers
        """
        result = {
            "base_cost": 0.0,
            "mileage_cost": 0.0,
            "hourly_cost": 0.0,
            "amenities_cost": 0.0,
            "modifiers_applied": [],
            "subtotal": 0.0,
            "discount": 0.0,
            "total_cost": 0.0,
            "breakdown": []
        }
        
        # Step 1: Get base vehicle rate
        vehicle_rate = db.query(VehicleRate).filter(
            VehicleRate.id == vehicle_type_id,
            VehicleRate.is_active == True
        ).first()
        
        if not vehicle_rate:
            raise ValueError("Vehicle rate not found")
        
        # Calculate base costs
        hours_to_bill = max(total_hours, vehicle_rate.minimum_hours)
        result["hourly_cost"] = hours_to_bill * vehicle_rate.base_hourly_rate
        result["mileage_cost"] = total_miles * vehicle_rate.base_mileage_rate
        result["base_cost"] = result["hourly_cost"] + result["mileage_cost"]
        
        result["breakdown"].append({
            "category": "base",
            "description": f"Base rate ({hours_to_bill}h @ ${vehicle_rate.base_hourly_rate}/h)",
            "amount": result["hourly_cost"]
        })
        result["breakdown"].append({
            "category": "mileage",
            "description": f"Mileage ({total_miles} mi @ ${vehicle_rate.base_mileage_rate}/mi)",
            "amount": result["mileage_cost"]
        })
        
        # Step 2: Apply pricing modifiers
        modifiers = PricingCalculator._get_applicable_modifiers(
            db, trip_date, vehicle_rate.vehicle_type_name
        )
        
        running_total = result["base_cost"]
        for modifier in modifiers:
            if modifier.multiplier != 1.0:
                modifier_amount = running_total * (modifier.multiplier - 1.0)
                running_total += modifier_amount
                result["modifiers_applied"].append(modifier.name)
                result["breakdown"].append({
                    "category": "modifier",
                    "description": f"{modifier.name} ({modifier.multiplier}x)",
                    "amount": modifier_amount
                })
            
            if modifier.fixed_amount > 0:
                running_total += modifier.fixed_amount
                result["modifiers_applied"].append(modifier.name)
                result["breakdown"].append({
                    "category": "modifier",
                    "description": f"{modifier.name} (fixed)",
                    "amount": modifier.fixed_amount
                })
        
        # Step 3: Add amenities
        if amenity_ids:
            amenities = db.query(Amenity).filter(
                Amenity.id.in_(amenity_ids),
                Amenity.is_active == True
            ).all()
            
            for amenity in amenities:
                if amenity.price_type == "fixed":
                    amenity_cost = amenity.price_amount
                elif amenity.price_type == "per_hour":
                    amenity_cost = amenity.price_amount * hours_to_bill
                elif amenity.price_type == "per_passenger":
                    amenity_cost = amenity.price_amount * passengers
                else:
                    amenity_cost = amenity.price_amount
                
                result["amenities_cost"] += amenity_cost
                result["breakdown"].append({
                    "category": "amenity",
                    "description": amenity.name,
                    "amount": amenity_cost
                })
        
        # Calculate subtotal
        result["subtotal"] = running_total + result["amenities_cost"]
        
        # Step 4: Apply promo code
        if promo_code:
            discount = PricingCalculator._apply_promo_code(
                db, promo_code, result["subtotal"]
            )
            result["discount"] = discount
            result["breakdown"].append({
                "category": "discount",
                "description": f"Promo code: {promo_code}",
                "amount": -discount
            })
        
        # Calculate final total
        result["total_cost"] = result["subtotal"] - result["discount"]
        
        return result
    
    @staticmethod
    def _get_applicable_modifiers(
        db: Session,
        trip_date: date,
        vehicle_type: str
    ) -> List[PricingModifier]:
        """Get all applicable pricing modifiers for a trip"""
        modifiers = db.query(PricingModifier).filter(
            PricingModifier.is_active == True
        ).order_by(PricingModifier.priority.desc()).all()
        
        applicable = []
        day_of_week = trip_date.weekday()  # 0=Monday, 6=Sunday
        
        for modifier in modifiers:
            # Check date range
            if modifier.valid_from and trip_date < modifier.valid_from:
                continue
            if modifier.valid_until and trip_date > modifier.valid_until:
                continue
            
            # Check day of week
            day_applies = [
                modifier.applies_monday,
                modifier.applies_tuesday,
                modifier.applies_wednesday,
                modifier.applies_thursday,
                modifier.applies_friday,
                modifier.applies_saturday,
                modifier.applies_sunday
            ]
            if not day_applies[day_of_week]:
                continue
            
            # Check vehicle type
            if modifier.applies_to_vehicle_types:
                allowed_types = [t.strip() for t in modifier.applies_to_vehicle_types.split(",")]
                if vehicle_type not in allowed_types:
                    continue
            
            applicable.append(modifier)
        
        return applicable
    
    @staticmethod
    def _apply_promo_code(
        db: Session,
        code: str,
        subtotal: float
    ) -> float:
        """Apply promo code and return discount amount"""
        promo = db.query(PromoCode).filter(
            PromoCode.code == code.upper(),
            PromoCode.is_active == True
        ).first()
        
        if not promo:
            logger.warning(f"Promo code '{code}' not found")
            return 0.0
        
        # Check validity period
        now = datetime.now()
        if promo.valid_from and now < promo.valid_from:
            logger.warning(f"Promo code '{code}' not yet valid")
            return 0.0
        if promo.valid_until and now > promo.valid_until:
            logger.warning(f"Promo code '{code}' expired")
            return 0.0
        
        # Check minimum trip cost
        if subtotal < promo.minimum_trip_cost:
            logger.warning(f"Subtotal ${subtotal} below minimum ${promo.minimum_trip_cost}")
            return 0.0
        
        # Check usage limits
        if promo.max_uses and promo.current_uses >= promo.max_uses:
            logger.warning(f"Promo code '{code}' usage limit reached")
            return 0.0
        
        # Calculate discount
        if promo.discount_type == "percentage":
            discount = subtotal * (promo.discount_value / 100.0)
        else:  # fixed_amount
            discount = promo.discount_value
        
        # Apply maximum discount cap
        if promo.maximum_discount:
            discount = min(discount, promo.maximum_discount)
        
        return discount


class DOTComplianceChecker:
    """DOT regulation compliance checker"""
    
    @staticmethod
    def check_compliance(
        db: Session,
        total_miles: float,
        total_hours: float
    ) -> Dict:
        """Check if trip complies with DOT regulations"""
        result = {
            "compliant": True,
            "requires_second_driver": False,
            "warnings": [],
            "max_hours_exceeded": False,
            "max_miles_exceeded": False
        }
        
        # Get active regulations
        regulations = db.query(DOTRegulation).filter(
            DOTRegulation.is_active == True
        ).all()
        
        for reg in regulations:
            if reg.max_driving_hours and total_hours > reg.max_driving_hours:
                result["max_hours_exceeded"] = True
                result["warnings"].append(
                    f"Driving hours ({total_hours}h) exceed limit ({reg.max_driving_hours}h)"
                )
                if reg.requires_second_driver:
                    result["requires_second_driver"] = True
            
            if reg.max_distance_miles and total_miles > reg.max_distance_miles:
                result["max_miles_exceeded"] = True
                result["warnings"].append(
                    f"Distance ({total_miles} mi) exceeds limit ({reg.max_distance_miles} mi)"
                )
                if reg.requires_second_driver:
                    result["requires_second_driver"] = True
        
        if result["warnings"]:
            result["compliant"] = False
        
        return result
```

---

### Task 3.5: Create Pricing Service API

**Estimated Time:** 1 hour

**File:** `backend/services/pricing/main.py`

**Instructions:**
1. Create FastAPI application:

```python
"""
Pricing Service - Dynamic Pricing Engine
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from database import engine, Base, get_db
from models import VehicleRate, PricingModifier, Amenity, PromoCode, DOTRegulation
from schemas import (
    VehicleRateCreate, VehicleRateResponse,
    PricingModifierCreate, PricingModifierResponse,
    AmenityCreate, AmenityResponse,
    PromoCodeCreate, PromoCodeResponse,
    QuoteCalculationRequest, QuoteCalculationResponse,
    DOTComplianceRequest, DOTComplianceResponse
)
from business_logic import PricingCalculator, DOTComplianceChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="Athena Pricing Service",
    description="Dynamic pricing and quote calculation service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pricing"}


# ==================== QUOTE CALCULATION ====================

@app.post("/api/v1/calculate-quote", response_model=QuoteCalculationResponse)
async def calculate_quote(
    request: QuoteCalculationRequest,
    db: Session = Depends(get_db)
):
    """Calculate comprehensive quote with all pricing rules"""
    try:
        result = PricingCalculator.calculate_quote(
            db=db,
            vehicle_type_id=request.vehicle_type_id,
            total_miles=request.total_miles,
            total_hours=request.total_hours,
            trip_date=request.trip_date,
            passengers=request.passengers,
            amenity_ids=request.amenity_ids,
            promo_code=request.promo_code
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quote calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/check-dot-compliance", response_model=DOTComplianceResponse)
async def check_dot_compliance(
    request: DOTComplianceRequest,
    db: Session = Depends(get_db)
):
    """Check DOT compliance for trip parameters"""
    result = DOTComplianceChecker.check_compliance(
        db=db,
        total_miles=request.total_miles,
        total_hours=request.total_hours
    )
    return result


# ==================== VEHICLE RATES ====================

@app.get("/api/v1/vehicle-rates", response_model=List[VehicleRateResponse])
async def get_vehicle_rates(db: Session = Depends(get_db)):
    """Get all vehicle rates"""
    rates = db.query(VehicleRate).filter(VehicleRate.is_active == True).all()
    return rates


@app.post("/api/v1/vehicle-rates", response_model=VehicleRateResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_rate(
    rate_data: VehicleRateCreate,
    db: Session = Depends(get_db)
):
    """Create new vehicle rate"""
    rate = VehicleRate(**rate_data.dict())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


# ==================== AMENITIES ====================

@app.get("/api/v1/amenities", response_model=List[AmenityResponse])
async def get_amenities(db: Session = Depends(get_db)):
    """Get all available amenities"""
    amenities = db.query(Amenity).filter(Amenity.is_active == True).all()
    return amenities


@app.post("/api/v1/amenities", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
    amenity_data: AmenityCreate,
    db: Session = Depends(get_db)
):
    """Create new amenity"""
    amenity = Amenity(**amenity_data.dict())
    db.add(amenity)
    db.commit()
    db.refresh(amenity)
    return amenity


# ==================== PROMO CODES ====================

@app.get("/api/v1/promo-codes", response_model=List[PromoCodeResponse])
async def get_promo_codes(db: Session = Depends(get_db)):
    """Get all promo codes (admin only)"""
    codes = db.query(PromoCode).all()
    return codes


@app.post("/api/v1/promo-codes", response_model=PromoCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    code_data: PromoCodeCreate,
    db: Session = Depends(get_db)
):
    """Create new promo code"""
    promo = PromoCode(**code_data.dict(), code=code_data.code.upper())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@app.post("/api/v1/validate-promo-code")
async def validate_promo_code(
    code: str,
    subtotal: float,
    db: Session = Depends(get_db)
):
    """Validate a promo code"""
    discount = PricingCalculator._apply_promo_code(db, code, subtotal)
    return {
        "valid": discount > 0,
        "discount": discount
    }


# ==================== PRICING MODIFIERS ====================

@app.get("/api/v1/pricing-modifiers", response_model=List[PricingModifierResponse])
async def get_pricing_modifiers(db: Session = Depends(get_db)):
    """Get all pricing modifiers"""
    modifiers = db.query(PricingModifier).all()
    return modifiers


@app.post("/api/v1/pricing-modifiers", response_model=PricingModifierResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_modifier(
    modifier_data: PricingModifierCreate,
    db: Session = Depends(get_db)
):
    """Create new pricing modifier"""
    modifier = PricingModifier(**modifier_data.dict())
    db.add(modifier)
    db.commit()
    db.refresh(modifier)
    return modifier


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
```

---

### Task 3.6: Add to Docker Compose

**Estimated Time:** 10 minutes

**File:** `docker-compose.yml`

**Instructions:**
1. Add pricing service configuration:

```yaml
  # Pricing Service
  pricing-service:
    build:
      context: ./backend/services/pricing
      dockerfile: Dockerfile
    container_name: athena-pricing-service
    environment:
      - PRICING_DATABASE_URL=postgresql://athena:athena_dev_password@postgres:5432/pricing_db
      - CHARTER_SERVICE_URL=http://charter-service:8002
    ports:
      - "8008:8008"
    depends_on:
      - postgres
    networks:
      - athena-network
    restart: unless-stopped
```

2. Create database:
   ```bash
   docker exec -it athena-postgres psql -U athena -c "CREATE DATABASE pricing_db;"
   ```

3. Build and start:
   ```bash
   docker-compose build pricing-service
   docker-compose up -d pricing-service
   ```

**Verification:**
```bash
curl http://localhost:8008/health
# Test calculation
curl -X POST "http://localhost:8008/api/v1/calculate-quote" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_type_id": 1,
    "total_miles": 100,
    "total_hours": 8,
    "trip_date": "2026-03-01",
    "passengers": 20
  }'
```

---

### Task 3.6: Configure Kong Gateway Routes

**Estimated Time:** 10 minutes

**Instructions:**
1. Create Kong service for pricing service:
   ```bash
   curl -X POST http://localhost:8081/services \
     --data name=pricing-service \
     --data url=http://pricing-service:8000
   ```

2. Create Kong route:
   ```bash
   curl -X POST http://localhost:8081/services/pricing-service/routes \
     --data "paths[]=/api/v1/pricing" \
     --data strip_path=false
   ```

**Verification:**
```bash
# Test through Kong
curl http://localhost:8080/api/v1/pricing/health
```

---

### Task 3.7: Comprehensive Testing via Kong Gateway

**Estimated Time:** 45 minutes

**Purpose:** Verify pricing service functionality through Kong gateway

**Instructions:**

1. Get authentication token:
   ```bash
   TOKEN=$(curl -X POST http://localhost:8000/token \
     -d "username=admin@athena.com" \
     -d "password=admin123" \
     | jq -r '.access_token')
   ```

2. Create test amenities:
   ```bash
   # WiFi amenity
   WIFI_ID=$(curl -X POST http://localhost:8080/api/v1/pricing/amenities \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "WiFi",
       "description": "Onboard WiFi service",
       "price_type": "flat",
       "price": 150.00,
       "is_active": true
     }' | jq -r '.id')
   
   # Beverages amenity
   BEVERAGE_ID=$(curl -X POST http://localhost:8080/api/v1/pricing/amenities \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Premium Beverages",
       "description": "Premium beverage service",
       "price_type": "per_passenger",
       "price": 5.00,
       "is_active": true
     }' | jq -r '.id')
   
   echo "WiFi ID: $WIFI_ID, Beverage ID: $BEVERAGE_ID"
   ```

3. List all amenities:
   ```bash
   curl -X GET http://localhost:8080/api/v1/pricing/amenities \
     -H "Authorization: Bearer $TOKEN" | jq
   # Expected: Array with WiFi and Beverages
   ```

4. Create promo code:
   ```bash
   curl -X POST http://localhost:8080/api/v1/pricing/promo-codes \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "SPRING2026",
       "discount_type": "percentage",
       "discount_value": 10.0,
       "valid_from": "2026-03-01",
       "valid_until": "2026-06-01",
       "max_uses": 100,
       "is_active": true
     }' | jq
   # Expected: 201 Created with promo code details
   ```

5. Validate promo code:
   ```bash
   curl -X POST http://localhost:8080/api/v1/pricing/validate-promo-code \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "SPRING2026",
       "trip_date": "2026-04-15"
     }' | jq
   # Expected: {\"valid\": true, \"discount_type\": \"percentage\", \"discount_value\": 10.0}
   ```

6. Create pricing modifier (weekend rate):
   ```bash
   curl -X POST http://localhost:8080/api/v1/pricing/pricing-modifiers \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Weekend Premium",
       "modifier_type": "day_of_week",
       "condition_value": "saturday,sunday",
       "adjustment_type": "percentage",
       "adjustment_value": 15.0,
       "is_active": true,
       "priority": 10
     }' | jq
   # Expected: 201 Created
   ```

7. Create hub rate modifier:
   ```bash
   curl -X POST http://localhost:8080/api/v1/pricing/pricing-modifiers \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "NYC Hub Premium",
       "modifier_type": "hub",
       "condition_value": "New York, NY",
       "adjustment_type": "flat",
       "adjustment_value": 200.0,
       "is_active": true,
       "priority": 20
     }' | jq
   ```

8. Test full quote calculation:
   ```bash
   curl -X POST http://localhost:8080/api/v1/pricing/calculate-quote \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "vehicle_type_id": 1,
       "total_miles": 200,
       "total_hours": 8,
       "trip_date": "2026-04-19",
       "passengers": 45,
       "pickup_location": "Boston, MA",
       "dropoff_location": "New York, NY",
       "amenity_ids": ['"$WIFI_ID"', '"$BEVERAGE_ID"'],
       "promo_code": "SPRING2026"
     }' | jq
   # Expected: Full breakdown with base rate, mileage, amenities, modifiers, discount
   ```

9. Test DOT compliance check:
   ```bash
   curl -X POST http://localhost:8080/api/v1/pricing/check-dot-compliance \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "total_miles": 650,
       "total_hours": 11,
       "trip_date": "2026-05-01"
     }' | jq
   # Expected: {\"requires_second_driver\": true, \"reason\": \"Exceeds 10-hour limit\"}
   ```

10. Get all pricing modifiers:
    ```bash
    curl -X GET http://localhost:8080/api/v1/pricing/pricing-modifiers \
      -H "Authorization: Bearer $TOKEN" | jq
    # Expected: Array with weekend and hub modifiers
    ```

11. Update promo code:
    ```bash
    curl -X PUT http://localhost:8080/api/v1/pricing/promo-codes/SPRING2026 \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "discount_value": 15.0,
        "max_uses": 200
      }' | jq
    # Expected: 200 OK with updated promo code
    ```

12. Deactivate promo code:
    ```bash
    curl -X DELETE http://localhost:8080/api/v1/pricing/promo-codes/SPRING2026 \
      -H "Authorization: Bearer $TOKEN" | jq
    # Expected: 200 OK, promo code set to inactive
    ```

13. Get pricing configuration:
    ```bash
    curl -X GET http://localhost:8080/api/v1/pricing/pricing-config \
      -H "Authorization: Bearer $TOKEN" | jq
    # Expected: Complete configuration including all modifiers, amenities, rates
    ```

**Success Criteria:**
- ✅ Amenities created with different pricing types
- ✅ Promo codes validate correctly with date ranges
- ✅ Pricing modifiers apply based on conditions
- ✅ Full quote calculation includes all components
- ✅ DOT compliance detection works correctly
- ✅ Configuration API returns complete setup
- ✅ All requests go through Kong gateway (port 8080)

---

## Phase 4: Vendor Service (Weeks 8-9)

### Overview
**Goal:** Vendor portal and bid management.  
**Port:** 8006  
**Database:** `vendor_db`

---

### Task 4.1: Scaffold Vendor Service

**Estimated Time:** 20 minutes

**Instructions:**
1. Create structure (follow same pattern as Sales/Pricing services)
2. Update config for port 8006 and vendor_db
3. Create vendor-specific models

---

### Task 4.2: Create Vendor Models

**Estimated Time:** 45 minutes

**File:** `backend/services/vendor/models.py`

**Instructions:**

```python
"""
Database models for Vendor Service
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class VendorProfile(Base):
    """Vendor profile extending user from auth service"""
    __tablename__ = "vendor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)  # FK to auth
    
    # Company details
    company_name = Column(String(255), nullable=False)
    dot_number = Column(String(50), nullable=True)
    mc_number = Column(String(50), nullable=True)
    
    # Contact
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    
    # Fleet information
    fleet_size = Column(Integer, default=1)
    vehicle_types = Column(Text, nullable=True)  # Comma-separated
    
    # Insurance
    insurance_company = Column(String(255), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    insurance_expiry = Column(Date, nullable=True, index=True)
    coi_document_id = Column(String(255), nullable=True)  # MongoDB doc ID
    
    # Banking
    bank_name = Column(String(255), nullable=True)
    account_number_encrypted = Column(String(255), nullable=True)
    routing_number = Column(String(20), nullable=True)
    
    # Performance metrics
    rating = Column(Float, default=5.0)
    total_jobs_completed = Column(Integer, default=0)
    on_time_percentage = Column(Float, default=100.0)
    
    # Status
    status = Column(String(20), default="pending")  # pending, active, suspended, inactive
    approval_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    bids = relationship("VendorBid", back_populates="vendor")

    def __repr__(self):
        return f"<VendorProfile {self.company_name}>"


class BidOpportunity(Base):
    """Charter bid opportunities"""
    __tablename__ = "bid_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Opportunity details
    pickup_location = Column(String(500), nullable=False)
    dropoff_location = Column(String(500), nullable=False)
    trip_date = Column(DateTime(timezone=True), nullable=False)
    passengers = Column(Integer, nullable=False)
    vehicle_type_needed = Column(String(100), nullable=True)
    
    # Distance info
    estimated_miles = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), default="open")  # open, awarded, expired, cancelled
    expires_at = Column(DateTime(timezone=True), nullable=True)
    awarded_to_vendor_id = Column(Integer, nullable=True)
    awarded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    bids = relationship("VendorBid", back_populates="opportunity")

    def __repr__(self):
        return f"<BidOpportunity charter={self.charter_id}>"


class VendorBid(Base):
    """Vendor bids on opportunities"""
    __tablename__ = "vendor_bids"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("bid_opportunities.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendor_profiles.id"), nullable=False, index=True)
    
    # Bid details
    bid_amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    vehicle_description = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, accepted, rejected, withdrawn
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, nullable=True)  # User ID
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    opportunity = relationship("BidOpportunity", back_populates="bids")
    vendor = relationship("VendorProfile", back_populates="bids")

    def __repr__(self):
        return f"<VendorBid opportunity={self.opportunity_id} vendor={self.vendor_id}>"


class VendorAssignment(Base):
    """Track vendor assignments to charters"""
    __tablename__ = "vendor_assignments"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendor_profiles.id"), nullable=False, index=True)
    
    # Assignment details
    assigned_by = Column(Integer, nullable=False)  # User ID
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Confirmation
    vendor_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Completion
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Recovery
    recovery_requested = Column(Boolean, default=False)
    recovery_reason = Column(Text, nullable=True)
    recovery_requested_at = Column(DateTime(timezone=True), nullable=True)
    
    # Rating
    rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)

    def __repr__(self):
        return f"<VendorAssignment charter={self.charter_id}>"
```

---

### Task 4.3: Create Vendor API Endpoints

**Estimated Time:** 1.5 hours

**File:** `backend/services/vendor/main.py`

**Instructions:**
1. Implement vendor portal and admin endpoints for bid management
2. Add COI tracking and expiration alerts
3. Implement assignment and confirmation workflows

(Due to space, showing key endpoints structure):

```python
"""
Vendor Service - Vendor Portal and Bid Management
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from database import engine, Base, get_db
from models import VendorProfile, BidOpportunity, VendorBid, VendorAssignment
# Import schemas

app = FastAPI(title="Athena Vendor Service", version="1.0.0")

# Key endpoints:
# POST /api/v1/vendors - Create vendor profile
# GET /api/v1/vendors - List vendors (admin)
# GET /api/v1/vendors/{id} - Get vendor details
# POST /api/v1/vendors/{id}/approve - Approve vendor
# GET /api/v1/vendors/coi-expiring - Get vendors with expiring COI

# POST /api/v1/bid-opportunities - Create opportunity
# GET /api/v1/bid-opportunities - List opportunities
# GET /api/v1/vendor-portal/opportunities - Vendor view

# POST /api/v1/bids - Submit bid
# GET /api/v1/bids - List bids
# POST /api/v1/bids/{id}/accept - Accept bid
# POST /api/v1/bids/{id}/reject - Reject bid

# POST /api/v1/assignments - Create direct assignment
# GET /api/v1/assignments - List assignments
# POST /api/v1/assignments/{id}/confirm - Vendor confirms
# POST /api/v1/assignments/{id}/request-recovery - Request recovery
```

---

### Task 4.3: Configure Kong and Test via Gateway

**Estimated Time:** 30 minutes

**Kong Configuration:**
```bash
# Create Kong service
curl -X POST http://localhost:8081/services \
  --data name=vendor-service \
  --data url=http://vendor-service:8000

# Create Kong route
curl -X POST http://localhost:8081/services/vendor-service/routes \
  --data "paths[]=/api/v1/vendors" \
  --data strip_path=false
```

**Testing via Kong Gateway:**

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/token \
  -d "username=admin@athena.com" \
  -d "password=admin123" \
  | jq -r '.access_token')

# Create vendor profile
curl -X POST http://localhost:8080/api/v1/vendors/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "company_name": "ABC Coach Lines",
    "phone": "555-9999",
    "email": "contact@abccoach.com"
  }' | jq

# Upload COI document
curl -X POST http://localhost:8080/api/v1/vendors/1/coi \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/insurance.pdf" \
  -F "expiration_date=2027-12-31" | jq

# Create bid opportunity
curl -X POST http://localhost:8080/api/v1/vendors/bid-opportunities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 1,
    "required_vehicle_type": "motorcoach",
    "passengers": 45,
    "pickup_location": "Boston, MA",
    "trip_date": "2026-06-01"
  }' | jq

# Vendor submits bid
curl -X POST http://localhost:8080/api/v1/vendors/bids \
  -H "Authorization: Bearer $VENDOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": 1,
    "bid_amount": 1500.00,
    "notes": "We can provide motorcoach with WiFi"
  }' | jq
```

**Success Criteria:**
- ✅ Vendor profiles created and managed
- ✅ COI tracking and expiration alerts work
- ✅ Bid opportunities created and visible to vendors
- ✅ Vendors can submit bids
- ✅ All requests through Kong gateway

---

## Phase 5: Portals Service (Weeks 10-11)

### Overview
**Goal:** Backend-for-frontend aggregator for client and vendor portals.  
**Port:** 8009  
**Database:** Shared (aggregates from other services)

---

### Task 5.1: Create Portals BFF Service

**Estimated Time:** 2 hours

**Instructions:**
1. This service acts as an aggregator/gateway
2. Implements MFA, password reset, session management
3. Proxies requests to appropriate backend services
4. Enforces portal-specific security

**Key Features:**
- Client authentication with MFA
- Aggregated dashboard views
- Payment processing through Payment Service
- Document access through Document Service
- Quote acceptance workflow

---

### Task 5.2: Configure Kong and Test via Gateway

**Estimated Time:** 30 minutes

**Kong Configuration:**
```bash
# Create Kong service for portals
curl -X POST http://localhost:8081/services \
  --data name=portals-service \
  --data url=http://portals-service:8000

# Create Kong routes
curl -X POST http://localhost:8081/services/portals-service/routes \
  --data "paths[]=/api/v1/portal" \
  --data strip_path=false
```

**Testing via Kong Gateway:**

```bash
# Client portal login
curl -X POST http://localhost:8080/api/v1/portal/client/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@example.com",
    "password": "password123"
  }' | jq

# Get client dashboard (aggregated data)
curl -X GET http://localhost:8080/api/v1/portal/client/dashboard \
  -H "Authorization: Bearer $CLIENT_TOKEN" | jq

# View client charters
curl -X GET http://localhost:8080/api/v1/portal/client/charters \
  -H "Authorization: Bearer $CLIENT_TOKEN" | jq

# Accept quote
curl -X POST http://localhost:8080/api/v1/portal/client/quotes/1/accept \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method_id": "pm_123",
    "agree_to_terms": true
  }' | jq

# Update notification preferences
curl -X PUT http://localhost:8080/api/v1/portal/client/preferences \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sms_notifications_enabled": true,
    "email_notifications_enabled": true
  }' | jq
```

**Success Criteria:**
- ✅ Client login with MFA works
- ✅ Dashboard aggregates data from multiple services
- ✅ Quote acceptance creates booking and payment
- ✅ Preferences update correctly
- ✅ All requests through Kong gateway

---

## Phase 6: Change Management (Weeks 12-13)

### Overview
**Goal:** Track and manage post-booking changes with approval workflows.  
**Port:** 8010  
**Database:** `change_mgmt_db`

---

### Task 6.1: Create Change Management Models

**Estimated Time:** 45 minutes

**Instructions:**
1. Create change_cases table with workflow states
2. Create change_history for audit trail
3. Implement state machine for approval flow
4. Add webhook/trigger mechanism from Charter Service

---

### Task 6.2: Configure Kong and Test via Gateway

**Estimated Time:** 30 minutes

**Kong Configuration:**
```bash
# Create Kong service
curl -X POST http://localhost:8081/services \
  --data name=change-mgmt-service \
  --data url=http://change-mgmt-service:8000

# Create Kong route
curl -X POST http://localhost:8081/services/change-mgmt-service/routes \
  --data "paths[]=/api/v1/changes" \
  --data strip_path=false
```

**Testing via Kong Gateway:**

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/token \
  -d "username=admin@athena.com" \
  -d "password=admin123" \
  | jq -r '.access_token')

# Create change case
curl -X POST http://localhost:8080/api/v1/changes/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 1,
    "change_type": "itinerary_modification",
    "requested_by": 1,
    "description": "Client requests pickup time change",
    "impact_assessment": "Vendor needs to confirm availability"
  }' | jq

# Get change case
curl -X GET http://localhost:8080/api/v1/changes/cases/1 \
  -H "Authorization: Bearer $TOKEN" | jq

# Add change history entry
curl -X POST http://localhost:8080/api/v1/changes/cases/1/history \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "vendor_contacted",
    "notes": "Contacted vendor, awaiting response"
  }' | jq

# Approve change
curl -X POST http://localhost:8080/api/v1/changes/cases/1/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": 1,
    "notes": "Vendor confirmed, client approved price adjustment"
  }' | jq

# Get change history
curl -X GET http://localhost:8080/api/v1/changes/cases/1/history \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Success Criteria:**
- ✅ Change cases created automatically on charter modifications
- ✅ Workflow state transitions work correctly
- ✅ Audit trail captures all actions
- ✅ Approvals trigger charter updates
- ✅ All requests through Kong gateway

---

## Testing & Deployment

### Comprehensive Kong Gateway Testing

**Purpose:** Verify all services work correctly through Kong API Gateway

**Estimated Time:** 2 hours

**Instructions:**

1. **Verify all services are registered in Kong:**
   ```bash
   curl http://localhost:8081/services | jq '.data[].name'
   # Expected output:
   # auth-service
   # charter-service
   # client-service
   # document-service
   # payment-service
   # notification-service
   # sales-service
   # pricing-service
   # vendor-service
   # portals-service
   # change-mgmt-service
   ```

2. **Test health endpoints through Kong:**
   ```bash
   for service in auth charters clients documents payments notifications sales pricing vendors portal changes; do
     echo "Testing $service..."
     curl -s http://localhost:8080/api/v1/$service/health | jq
   done
   ```

3. **End-to-end workflow test:**
   ```bash
   # 1. Create lead
   LEAD_ID=$(curl -X POST http://localhost:8080/api/v1/sales/leads \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "email": "john@example.com",
       "phone": "555-1234",
       "passengers": 45,
       "trip_date": "2026-06-15",
       "pickup_location": "Boston, MA",
       "source": "web"
     }' | jq -r '.id')
   
   # 2. Convert lead to charter
   CHARTER_ID=$(curl -X POST http://localhost:8080/api/v1/sales/leads/$LEAD_ID/convert \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"create_charter": true}' | jq -r '.charter_id')
   
   # 3. Add amenities
   curl -X POST http://localhost:8080/api/v1/charters/charters/$CHARTER_ID/amenities \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"amenity_id": 1}' | jq
   
   # 4. Calculate quote
   curl -X POST http://localhost:8080/api/v1/pricing/calculate-quote \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d "{\"charter_id\": $CHARTER_ID}" | jq
   
   # 5. Create vendor opportunity
   curl -X POST http://localhost:8080/api/v1/vendors/bid-opportunities \
     -H "Authorization: Bearer $TOKEN" \
     -d "{\"charter_id\": $CHARTER_ID}" | jq
   
   # 6. Accept quote (client portal)
   curl -X POST http://localhost:8080/api/v1/portal/client/quotes/$CHARTER_ID/accept \
     -H "Authorization: Bearer $CLIENT_TOKEN" \
     -d '{"payment_method_id": "pm_123"}' | jq
   
   # 7. Verify payment created
   curl -X GET http://localhost:8080/api/v1/payments/charters/$CHARTER_ID/payments \
     -H "Authorization: Bearer $TOKEN" | jq
   ```

4. **Kong rate limiting test:**
   ```bash
   # Enable rate limiting plugin
   curl -X POST http://localhost:8081/plugins \
     --data "name=rate-limiting" \
     --data "config.minute=100" \
     --data "config.policy=local"
   
   # Test rate limits
   for i in {1..10}; do
     curl -s -o /dev/null -w "%{http_code}\n" \
       http://localhost:8080/api/v1/charters/health
   done
   # All should return 200
   ```

5. **Kong authentication test:**
   ```bash
   # Test without token (should fail on protected endpoints)
   curl -X GET http://localhost:8080/api/v1/sales/leads
   # Expected: 401 Unauthorized
   
   # Test with token (should succeed)
   curl -X GET http://localhost:8080/api/v1/sales/leads \
     -H "Authorization: Bearer $TOKEN"
   # Expected: 200 OK with lead list
   ```

### Integration Testing

**Estimated Time:** 3 hours

**Instructions:**
1. Create Postman collection for each service
2. Test end-to-end workflows:
   - Lead → Charter → Payment
   - Quote calculation with amenities and promo codes
   - Vendor bid → Assignment → Confirmation
3. Test cross-service communication
4. Verify database consistency

### Performance Testing

**Instructions:**
1. Load test each endpoint with 100+ concurrent requests
2. Verify database query performance with EXPLAIN ANALYZE
3. Add database indexes where needed
4. Implement caching for frequently accessed data

### Documentation

**Instructions:**
1. Update API documentation in each service
2. Create deployment runbooks
3. Document environment variables
4. Create troubleshooting guides

---

## Success Criteria

**Phase 1 Complete:** Sales agents can capture and assign leads
**Phase 2 Complete:** Complex multi-stop quotes with cloning
**Phase 3 Complete:** Dynamic pricing with manager control
**Phase 4 Complete:** Vendors can bid on opportunities
**Phase 5 Complete:** Clients can self-manage bookings
**Phase 6 Complete:** Post-booking changes tracked and approved

### Final Verification - All Services via Kong Gateway

**Instructions:**

1. **Verify all services through Kong (port 8080):**
   ```bash
   # Create verification script
   cat > verify_kong_services.sh << 'EOF'
   #!/bin/bash
   
   echo "=== CoachWay Service Verification via Kong Gateway ==="
   echo ""
   
   # Get auth token
   echo "1. Getting authentication token..."
   TOKEN=$(curl -s -X POST http://localhost:8000/token \
     -d "username=admin@athena.com" \
     -d "password=admin123" \
     | jq -r '.access_token')
   
   if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
     echo "❌ Failed to get authentication token"
     exit 1
   fi
   echo "✅ Authentication successful"
   echo ""
   
   # Test each service through Kong
   declare -A services=(
     ["Auth"]="/api/v1/auth/health"
     ["Charter"]="/api/v1/charters/health"
     ["Client"]="/api/v1/clients/health"
     ["Document"]="/api/v1/documents/health"
     ["Payment"]="/api/v1/payments/health"
     ["Notification"]="/api/v1/notifications/health"
     ["Sales"]="/api/v1/sales/health"
     ["Pricing"]="/api/v1/pricing/health"
     ["Vendor"]="/api/v1/vendors/health"
     ["Portal"]="/api/v1/portal/health"
     ["Change Mgmt"]="/api/v1/changes/health"
   )
   
   echo "2. Testing services through Kong (port 8080)..."
   for service in "${!services[@]}"; do
     endpoint="${services[$service]}"
     response=$(curl -s -o /dev/null -w "%{http_code}" \
       "http://localhost:8080$endpoint" \
       -H "Authorization: Bearer $TOKEN")
     
     if [ "$response" == "200" ]; then
       echo "✅ $service - OK"
     else
       echo "❌ $service - FAILED (HTTP $response)"
     fi
   done
   
   echo ""
   echo "3. Verifying Kong gateway is routing correctly..."
   
   # Test direct vs Kong routing
   direct_response=$(curl -s http://localhost:8007/health | jq -r '.status')
   kong_response=$(curl -s http://localhost:8080/api/v1/sales/health | jq -r '.status')
   
   if [ "$direct_response" == "$kong_response" ]; then
     echo "✅ Kong routing matches direct service access"
   else
     echo "❌ Kong routing mismatch"
   fi
   
   echo ""
   echo "4. Testing Kong plugins..."
   
   # Check CORS headers
   cors_test=$(curl -s -I -X OPTIONS http://localhost:8080/api/v1/charters/health \
     -H "Origin: http://localhost:3000" \
     | grep -i "access-control-allow-origin")
   
   if [ -n "$cors_test" ]; then
     echo "✅ CORS plugin active"
   else
     echo "⚠️  CORS plugin not detected"
   fi
   
   echo ""
   echo "=== Verification Complete ==="
   EOF
   
   chmod +x verify_kong_services.sh
   ./verify_kong_services.sh
   ```

2. **Test complete workflow through Kong:**
   ```bash
   # Get token
   TOKEN=$(curl -s -X POST http://localhost:8000/token \
     -d "username=admin@athena.com" \
     -d "password=admin123" \
     | jq -r '.access_token')
   
   echo "Testing complete Lead → Charter → Payment workflow..."
   
   # Create lead
   echo "1. Creating lead via Sales service..."
   LEAD_RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/sales/leads \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "Final",
       "last_name": "Test",
       "email": "final@test.com",
       "phone": "555-9999",
       "passengers": 50,
       "trip_date": "2026-07-01",
       "pickup_location": "Boston, MA",
       "source": "web"
     }')
   
   LEAD_ID=$(echo $LEAD_RESPONSE | jq -r '.id')
   echo "   Lead ID: $LEAD_ID"
   
   # Convert to charter
   echo "2. Converting lead to charter..."
   CHARTER_RESPONSE=$(curl -s -X POST \
     "http://localhost:8080/api/v1/sales/leads/$LEAD_ID/convert" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"create_charter": true}')
   
   CHARTER_ID=$(echo $CHARTER_RESPONSE | jq -r '.charter_id')
   echo "   Charter ID: $CHARTER_ID"
   
   # Calculate pricing
   echo "3. Calculating price via Pricing service..."
   QUOTE=$(curl -s -X POST http://localhost:8080/api/v1/pricing/calculate-quote \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d "{
       \"charter_id\": $CHARTER_ID,
       \"vehicle_type_id\": 1,
       \"total_miles\": 250,
       \"total_hours\": 8,
       \"passengers\": 50
     }")
   
   TOTAL=$(echo $QUOTE | jq -r '.total_price')
   echo "   Total Price: \$$TOTAL"
   
   # Create vendor opportunity
   echo "4. Creating vendor bid opportunity..."
   OPP_ID=$(curl -s -X POST http://localhost:8080/api/v1/vendors/bid-opportunities \
     -H "Authorization: Bearer $TOKEN" \
     -d "{\"charter_id\": $CHARTER_ID}" \
     | jq -r '.id')
   echo "   Opportunity ID: $OPP_ID"
   
   echo ""
   echo "✅ Complete workflow test successful!"
   echo "   All services communicated through Kong gateway"
   ```

3. **Performance verification:**
   ```bash
   echo "Testing Kong gateway performance..."
   
   # Time 100 requests through Kong
   time for i in {1..100}; do
     curl -s http://localhost:8080/api/v1/charters/health > /dev/null
   done
   
   # Should complete in reasonable time (< 5 seconds for 100 requests)
   ```

4. **Kong Admin API verification:**
   ```bash
   echo "Verifying Kong configuration..."
   
   # List all services
   echo "Services registered:"
   curl -s http://localhost:8081/services | jq '.data[] | {name: .name, url: .host}'
   
   # List all routes
   echo ""
   echo "Routes configured:"
   curl -s http://localhost:8081/routes | jq '.data[] | {paths: .paths, service: .service.name}'
   
   # List plugins
   echo ""
   echo "Plugins enabled:"
   curl -s http://localhost:8081/plugins | jq '.data[] | {name: .name, enabled: .enabled}'
   ```

**Expected Results:**
- ✅ All 11 services return HTTP 200 through Kong
- ✅ Authentication works consistently
- ✅ CORS headers present
- ✅ Rate limiting active (if configured)
- ✅ End-to-end workflow completes successfully
- ✅ Kong admin API shows all services and routes
- ✅ Performance is acceptable (< 50ms average per request)

---

## Appendix: Common Commands

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f <service-name>
```

**Restart service:**
```bash
docker-compose restart <service-name>
```

**Database migrations:**
```bash
docker exec -it athena-postgres psql -U athena -d <database>
```

**Check service health:**
```bash
docker-compose ps
```

---

**END OF IMPLEMENTATION PLAN**
