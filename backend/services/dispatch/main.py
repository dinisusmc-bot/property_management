"""
Dispatch Service - FastAPI application
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging

import config
from database import get_db, engine, init_schema
from models import Dispatch, DispatchLocation, DispatchEvent, Recovery
from schemas import (
    DispatchCreate, DispatchUpdate, DispatchResponse,
    LocationUpdate, LocationResponse,
    DispatchEventCreate, DispatchEventResponse,
    RecoveryCreate, RecoveryUpdate, RecoveryResponse,
    DispatchBoard, DispatchBoardItem,
    ContactAttemptRequest, ContactAttemptResponse,
    EscalateRecoveryRequest, EscalateRecoveryResponse,
    RecoveryDashboard, RecoveryDashboardItem
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dispatch Service",
    version=config.SERVICE_VERSION
)


# Startup: Create schema and tables
@app.on_event("startup")
async def startup_event():
    """Create dispatch schema and tables on startup"""
    logger.info("Starting Dispatch Service...")
    init_schema()
    
    # Create tables
    from models import Base
    Base.metadata.create_all(bind=engine)
    logger.info(f"Schema '{config.SCHEMA_NAME}' and tables created successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION
    }


# ============================================================================
# Dispatch Endpoints
# ============================================================================

@app.post("/dispatches", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
async def create_dispatch(
    dispatch: DispatchCreate,
    db: Session = Depends(get_db)
):
    """Create a new dispatch for a charter"""
    logger.info(f"Creating dispatch for charter {dispatch.charter_id}")
    
    db_dispatch = Dispatch(
        **dispatch.model_dump(),
        status="pending",
        created_by=1  # TODO: Get from auth
    )
    
    db.add(db_dispatch)
    db.commit()
    db.refresh(db_dispatch)
    
    # Create initial event
    event = DispatchEvent(
        dispatch_id=db_dispatch.id,
        event_type="created",
        description="Dispatch created"
    )
    db.add(event)
    db.commit()
    
    logger.info(f"Dispatch {db_dispatch.id} created")
    return db_dispatch


@app.get("/dispatches", response_model=List[DispatchResponse])
async def list_dispatches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status"),
    date: Optional[str] = None,
    driver_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all dispatches with optional filters"""
    query = db.query(Dispatch)
    
    if status_filter:
        query = query.filter(Dispatch.status == status_filter)
    
    if date:
        # Filter by dispatch date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        query = query.filter(
            func.date(Dispatch.dispatch_time) == target_date
        )
    
    if driver_id:
        query = query.filter(Dispatch.driver_id == driver_id)
    
    dispatches = query.order_by(Dispatch.dispatch_time.desc()).offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(dispatches)} dispatches")
    return dispatches


@app.get("/dispatches/{dispatch_id}", response_model=DispatchResponse)
async def get_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db)
):
    """Get dispatch details"""
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispatch {dispatch_id} not found"
        )
    
    return dispatch


@app.put("/dispatches/{dispatch_id}", response_model=DispatchResponse)
async def update_dispatch(
    dispatch_id: int,
    dispatch_update: DispatchUpdate,
    db: Session = Depends(get_db)
):
    """Update dispatch details"""
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispatch {dispatch_id} not found"
        )
    
    # Track status changes
    old_status = dispatch.status
    
    # Update fields
    update_data = dispatch_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dispatch, field, value)
    
    db.commit()
    db.refresh(dispatch)
    
    # If status changed, create event
    if 'status' in update_data and old_status != dispatch.status:
        event = DispatchEvent(
            dispatch_id=dispatch_id,
            event_type="status_changed",
            description=f"Status changed from {old_status} to {dispatch.status}"
        )
        db.add(event)
        db.commit()
    
    logger.info(f"Dispatch {dispatch_id} updated")
    return dispatch


@app.delete("/dispatches/{dispatch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db)
):
    """Delete a dispatch"""
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispatch {dispatch_id} not found"
        )
    
    db.delete(dispatch)
    db.commit()
    
    logger.info(f"Dispatch {dispatch_id} deleted")


# ============================================================================
# Location Tracking Endpoints
# ============================================================================

@app.post("/dispatches/{dispatch_id}/location", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def update_location(
    dispatch_id: int,
    location: LocationUpdate,
    db: Session = Depends(get_db)
):
    """Update GPS location for a dispatch"""
    # Verify dispatch exists
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispatch {dispatch_id} not found"
        )
    
    db_location = DispatchLocation(
        dispatch_id=dispatch_id,
        **location.model_dump()
    )
    
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    logger.info(f"Location updated for dispatch {dispatch_id}")
    return db_location


@app.get("/dispatches/{dispatch_id}/location", response_model=List[LocationResponse])
async def get_location_history(
    dispatch_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get location history for a dispatch"""
    locations = db.query(DispatchLocation).filter(
        DispatchLocation.dispatch_id == dispatch_id
    ).order_by(DispatchLocation.recorded_at.desc()).limit(limit).all()
    
    return locations


@app.get("/dispatches/{dispatch_id}/location/latest", response_model=Optional[LocationResponse])
async def get_latest_location(
    dispatch_id: int,
    db: Session = Depends(get_db)
):
    """Get latest GPS location for a dispatch"""
    location = db.query(DispatchLocation).filter(
        DispatchLocation.dispatch_id == dispatch_id
    ).order_by(DispatchLocation.recorded_at.desc()).first()
    
    return location


# ============================================================================
# Event Timeline Endpoints
# ============================================================================

@app.post("/dispatches/{dispatch_id}/events", response_model=DispatchEventResponse, status_code=status.HTTP_201_CREATED)
async def add_dispatch_event(
    dispatch_id: int,
    event: DispatchEventCreate,
    db: Session = Depends(get_db)
):
    """Add an event to dispatch timeline"""
    # Verify dispatch exists
    dispatch = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispatch {dispatch_id} not found"
        )
    
    db_event = DispatchEvent(
        dispatch_id=dispatch_id,
        **event.model_dump(),
        recorded_by=1  # TODO: Get from auth
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    logger.info(f"Event '{event.event_type}' added to dispatch {dispatch_id}")
    return db_event


@app.get("/dispatches/{dispatch_id}/events", response_model=List[DispatchEventResponse])
async def get_dispatch_events(
    dispatch_id: int,
    db: Session = Depends(get_db)
):
    """Get event timeline for a dispatch"""
    events = db.query(DispatchEvent).filter(
        DispatchEvent.dispatch_id == dispatch_id
    ).order_by(DispatchEvent.occurred_at).all()
    
    return events


# ============================================================================
# Dispatch Board Endpoint
# ============================================================================

@app.get("/board")
async def get_dispatch_board(
    db: Session = Depends(get_db)
):
    """Get real-time dispatch board view"""
    # Get active dispatches (not completed or cancelled)
    active_statuses = ["pending", "assigned", "en_route", "arrived", "in_service"]
    
    dispatches = db.query(Dispatch).filter(
        Dispatch.status.in_(active_statuses)
    ).order_by(Dispatch.dispatch_time).all()
    
    # Count by status
    status_counts = {
        "pending": 0,
        "assigned": 0,
        "en_route": 0,
        "in_service": 0
    }
    
    for d in dispatches:
        if d.status in status_counts:
            status_counts[d.status] += 1
    
    # Build board items
    board_items = []
    for d in dispatches:
        # Get latest location
        latest_location = db.query(DispatchLocation).filter(
            DispatchLocation.dispatch_id == d.id
        ).order_by(DispatchLocation.recorded_at.desc()).first()
        
        # Get recent events (last 5)
        recent_events = db.query(DispatchEvent).filter(
            DispatchEvent.dispatch_id == d.id
        ).order_by(DispatchEvent.occurred_at.desc()).limit(5).all()
        
        board_items.append({
            "id": d.id,
            "charter_id": d.charter_id,
            "driver_id": d.driver_id,
            "vehicle_id": d.vehicle_id,
            "status": d.status,
            "dispatch_time": d.dispatch_time,
            "last_location": latest_location,
            "recent_events": recent_events
        })
    
    logger.info(f"Dispatch board: {len(dispatches)} active dispatches")
    return {
        "active_dispatches": len(dispatches),
        "pending_count": status_counts["pending"],
        "assigned_count": status_counts["assigned"],
        "en_route_count": status_counts["en_route"],
        "in_service_count": status_counts["in_service"],
        "dispatches": board_items
    }


# ============================================================================
# Recovery/Breakdown Endpoints
# ============================================================================

@app.post("/recoveries", response_model=RecoveryResponse, status_code=status.HTTP_201_CREATED)
async def create_recovery(
    recovery: RecoveryCreate,
    db: Session = Depends(get_db)
):
    """Report a breakdown or emergency"""
    logger.info(f"Creating recovery for dispatch {recovery.dispatch_id}")
    
    # Verify dispatch exists
    dispatch = db.query(Dispatch).filter(Dispatch.id == recovery.dispatch_id).first()
    if not dispatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispatch {recovery.dispatch_id} not found"
        )
    
    db_recovery = Recovery(
        **recovery.model_dump(),
        status="reported",
        reported_by=1  # TODO: Get from auth
    )
    
    db.add(db_recovery)
    db.commit()
    db.refresh(db_recovery)
    
    # Add event to dispatch
    event = DispatchEvent(
        dispatch_id=recovery.dispatch_id,
        event_type="breakdown",
        description=f"{recovery.issue_type}: {recovery.description}",
        latitude=recovery.latitude,
        longitude=recovery.longitude
    )
    db.add(event)
    db.commit()
    
    logger.info(f"Recovery {db_recovery.id} created")
    return db_recovery


@app.get("/recoveries", response_model=List[RecoveryResponse])
async def list_recoveries(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all recoveries with optional filters"""
    query = db.query(Recovery)
    
    if status_filter:
        query = query.filter(Recovery.status == status_filter)
    
    if severity:
        query = query.filter(Recovery.severity == severity)
    
    recoveries = query.order_by(Recovery.reported_at.desc()).all()
    
    logger.info(f"Retrieved {len(recoveries)} recoveries")
    return recoveries


@app.get("/recoveries/dashboard", response_model=RecoveryDashboard)
async def get_recovery_dashboard(
    db: Session = Depends(get_db)
):
    """Dashboard view of all active recoveries"""
    # Get active recoveries with dispatch info
    active_recoveries = db.query(Recovery, Dispatch).join(
        Dispatch, Recovery.dispatch_id == Dispatch.id
    ).filter(
        Recovery.status.in_(['reported', 'acknowledged', 'en_route'])
    ).order_by(
        desc(Recovery.recovery_priority),
        Recovery.reported_at
    ).all()
    
    # Group by priority
    dashboard = {
        "critical": [],
        "high": [],
        "normal": [],
        "low": []
    }
    
    for recovery, dispatch in active_recoveries:
        item = RecoveryDashboardItem(
            recovery_id=recovery.id,
            charter_id=dispatch.charter_id,
            driver_id=dispatch.driver_id,
            reason=recovery.description,
            priority=recovery.recovery_priority,
            attempts=recovery.recovery_attempts or 0,
            last_contact=recovery.last_contact_at.isoformat() if recovery.last_contact_at else None,
            escalated=recovery.escalated or False,
            created_at=recovery.reported_at.isoformat()
        )
        dashboard[recovery.recovery_priority].append(item)
    
    summary = {
        "critical": len(dashboard["critical"]),
        "high": len(dashboard["high"]),
        "normal": len(dashboard["normal"]),
        "low": len(dashboard["low"]),
        "total": sum(len(v) for v in dashboard.values())
    }
    
    logger.info(f"Recovery dashboard: {summary['total']} active recoveries")
    
    return RecoveryDashboard(
        summary=summary,
        recoveries=dashboard
    )


@app.get("/recoveries/{recovery_id}", response_model=RecoveryResponse)
async def get_recovery(
    recovery_id: int,
    db: Session = Depends(get_db)
):
    """Get recovery details"""
    recovery = db.query(Recovery).filter(Recovery.id == recovery_id).first()
    
    if not recovery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery {recovery_id} not found"
        )
    
    return recovery


@app.put("/recoveries/{recovery_id}", response_model=RecoveryResponse)
async def update_recovery(
    recovery_id: int,
    recovery_update: RecoveryUpdate,
    db: Session = Depends(get_db)
):
    """Update recovery status"""
    recovery = db.query(Recovery).filter(Recovery.id == recovery_id).first()
    
    if not recovery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery {recovery_id} not found"
        )
    
    # Update fields
    update_data = recovery_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recovery, field, value)
    
    db.commit()
    db.refresh(recovery)
    
    logger.info(f"Recovery {recovery_id} updated to status: {recovery.status}")
    return recovery


# ============================================================================
# Phase 7: Enhanced Recovery Workflow Endpoints
# ============================================================================

@app.post("/recoveries/{recovery_id}/attempt-contact", response_model=ContactAttemptResponse)
async def attempt_contact(
    recovery_id: int,
    request: ContactAttemptRequest,
    db: Session = Depends(get_db)
):
    """Log a contact attempt for a recovery"""
    recovery = db.query(Recovery).filter(Recovery.id == recovery_id).first()
    
    if not recovery:
        raise HTTPException(status_code=404, detail="Recovery not found")
    
    # Update recovery
    recovery.recovery_attempts = (recovery.recovery_attempts or 0) + 1
    recovery.last_contact_at = datetime.utcnow()
    recovery.last_contact_method = request.contact_method
    
    if request.notes:
        if recovery.recovery_notes:
            recovery.recovery_notes += f"\n{datetime.utcnow().isoformat()}: {request.notes}"
        else:
            recovery.recovery_notes = f"{datetime.utcnow().isoformat()}: {request.notes}"
    
    # Get dispatch to log event
    dispatch = db.query(Dispatch).filter(Dispatch.id == recovery.dispatch_id).first()
    
    # Create dispatch event
    if dispatch:
        event = DispatchEvent(
            dispatch_id=recovery.dispatch_id,
            event_type='recovery_contact_attempt',
            description=f"Contact attempt #{recovery.recovery_attempts} via {request.contact_method}"
        )
        db.add(event)
    
    db.commit()
    db.refresh(recovery)
    
    logger.info(f"Contact attempt logged for recovery {recovery_id} (attempt #{recovery.recovery_attempts})")
    
    return ContactAttemptResponse(
        recovery_id=recovery_id,
        attempts=recovery.recovery_attempts,
        priority=recovery.recovery_priority,
        last_contact=recovery.last_contact_at.isoformat()
    )


@app.post("/recoveries/{recovery_id}/escalate", response_model=EscalateRecoveryResponse)
async def escalate_recovery(
    recovery_id: int,
    request: EscalateRecoveryRequest,
    db: Session = Depends(get_db)
):
    """Escalate recovery to manager"""
    recovery = db.query(Recovery).filter(Recovery.id == recovery_id).first()
    
    if not recovery:
        raise HTTPException(status_code=404, detail="Recovery not found")
    
    # Update recovery
    recovery.escalated = True
    recovery.escalated_to = request.escalate_to_user_id
    recovery.escalated_at = datetime.utcnow()
    recovery.recovery_priority = 'critical'
    
    # Get dispatch to log event
    dispatch = db.query(Dispatch).filter(Dispatch.id == recovery.dispatch_id).first()
    
    # Create dispatch event
    if dispatch:
        event = DispatchEvent(
            dispatch_id=recovery.dispatch_id,
            event_type='recovery_escalated',
            description=f"Recovery escalated to user {request.escalate_to_user_id}: {request.reason}"
        )
        db.add(event)
    
    # TODO: Send notification to manager
    
    db.commit()
    db.refresh(recovery)
    
    logger.info(f"Recovery {recovery_id} escalated to user {request.escalate_to_user_id}")
    
    return EscalateRecoveryResponse(
        recovery_id=recovery_id,
        escalated=True,
        escalated_to=request.escalate_to_user_id,
        priority=recovery.recovery_priority
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
