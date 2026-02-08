"""
Change Management Service - Track and manage post-booking changes
"""
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime

import config
import models
import schemas
import database
from business_logic import (
    ChangeWorkflowService,
    ApprovalService,
    AuditService,
    NotificationService,
    AnalyticsService
)

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Change Management Service",
    description="Track and manage post-booking changes with approval workflows",
    version="1.0.0"
)


def get_user_info(request: Request) -> dict:
    """Extract user info from request headers"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }


# Change Case Endpoints
@app.post("/cases", response_model=schemas.ChangeCaseResponse, status_code=201)
def create_change_case(
    change_data: schemas.ChangeCaseCreate,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Create a new change case"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.create_change_case(change_data, user_info)
        return change_case
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/cases/{case_id}", response_model=schemas.ChangeCaseResponse)
def get_change_case(
    case_id: int,
    db: Session = Depends(database.get_db)
):
    """Get a specific change case by ID"""
    change_case = db.query(models.ChangeCase).filter(
        models.ChangeCase.id == case_id
    ).first()
    
    if not change_case:
        raise HTTPException(status_code=404, detail=f"Change case {case_id} not found")
    
    return change_case


@app.get("/cases/number/{case_number}", response_model=schemas.ChangeCaseResponse)
def get_change_case_by_number(
    case_number: str,
    db: Session = Depends(database.get_db)
):
    """Get a specific change case by case number"""
    change_case = db.query(models.ChangeCase).filter(
        models.ChangeCase.case_number == case_number
    ).first()
    
    if not change_case:
        raise HTTPException(status_code=404, detail=f"Change case {case_number} not found")
    
    return change_case


@app.get("/cases", response_model=schemas.ChangeCaseListResponse)
def list_change_cases(
    charter_id: Optional[int] = None,
    client_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    status: Optional[schemas.ChangeStatus] = None,
    change_type: Optional[schemas.ChangeType] = None,
    priority: Optional[schemas.ChangePriority] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(database.get_db)
):
    """List change cases with optional filters"""
    query = db.query(models.ChangeCase)
    
    if charter_id:
        query = query.filter(models.ChangeCase.charter_id == charter_id)
    if client_id:
        query = query.filter(models.ChangeCase.client_id == client_id)
    if vendor_id:
        query = query.filter(models.ChangeCase.vendor_id == vendor_id)
    if status:
        query = query.filter(models.ChangeCase.status == status)
    if change_type:
        query = query.filter(models.ChangeCase.change_type == change_type)
    if priority:
        query = query.filter(models.ChangeCase.priority == priority)
    
    total = query.count()
    
    cases = query.order_by(
        models.ChangeCase.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return schemas.ChangeCaseListResponse(
        items=cases,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.put("/cases/{case_id}", response_model=schemas.ChangeCaseResponse)
def update_change_case(
    case_id: int,
    update_data: schemas.ChangeCaseUpdate,
    request: Request,
    updated_by: int = Query(...),
    updated_by_name: str = Query(...),
    db: Session = Depends(database.get_db)
):
    """Update a change case"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.update_change_case(
            case_id=case_id,
            update_data=update_data,
            updated_by=updated_by,
            updated_by_name=updated_by_name,
            user_info=user_info
        )
        return change_case
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


# State Transition Endpoints
@app.post("/cases/{case_id}/review", response_model=schemas.ChangeCaseResponse)
def move_to_review(
    case_id: int,
    request: Request,
    reviewed_by: int = Query(...),
    reviewed_by_name: str = Query(...),
    db: Session = Depends(database.get_db)
):
    """Move change case to under review"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.transition_to_review(
            case_id=case_id,
            reviewed_by=reviewed_by,
            reviewed_by_name=reviewed_by_name,
            user_info=user_info
        )
        return change_case
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


@app.post("/cases/{case_id}/approve", response_model=schemas.ChangeCaseResponse)
def approve_change(
    case_id: int,
    approval_data: schemas.ApproveChangeRequest,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Approve a change case"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.approve_change(
            case_id=case_id,
            approval_data=approval_data,
            user_info=user_info
        )
        return change_case
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


@app.post("/cases/{case_id}/reject", response_model=schemas.ChangeCaseResponse)
def reject_change(
    case_id: int,
    rejection_data: schemas.RejectChangeRequest,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Reject a change case"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.reject_change(
            case_id=case_id,
            rejection_data=rejection_data,
            user_info=user_info
        )
        return change_case
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


@app.post("/cases/{case_id}/implement", response_model=schemas.ChangeCaseResponse)
def implement_change(
    case_id: int,
    implementation_data: schemas.ImplementChangeRequest,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Mark change as implemented"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.implement_change(
            case_id=case_id,
            implementation_data=implementation_data,
            user_info=user_info
        )
        return change_case
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


@app.post("/cases/{case_id}/cancel", response_model=schemas.ChangeCaseResponse)
def cancel_change(
    case_id: int,
    cancellation_data: schemas.CancelChangeRequest,
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Cancel a change case"""
    workflow_service = ChangeWorkflowService(db)
    user_info = get_user_info(request)
    
    try:
        change_case = workflow_service.cancel_change(
            case_id=case_id,
            cancellation_data=cancellation_data,
            user_info=user_info
        )
        return change_case
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))


# History Endpoints
@app.get("/cases/{case_id}/history", response_model=List[schemas.ChangeHistoryResponse])
def get_case_history(
    case_id: int,
    db: Session = Depends(database.get_db)
):
    """Get complete audit trail for a change case"""
    # Verify case exists
    change_case = db.query(models.ChangeCase).filter(
        models.ChangeCase.id == case_id
    ).first()
    
    if not change_case:
        raise HTTPException(status_code=404, detail=f"Change case {case_id} not found")
    
    audit_service = AuditService(db)
    history = audit_service.get_case_history(case_id)
    
    return history


# Approval Endpoints
@app.post("/approvals", response_model=schemas.ChangeApprovalResponse, status_code=201)
def add_approver(
    approval_data: schemas.ChangeApprovalCreate,
    db: Session = Depends(database.get_db)
):
    """Add an approver to a change case"""
    # Verify case exists
    change_case = db.query(models.ChangeCase).filter(
        models.ChangeCase.id == approval_data.change_case_id
    ).first()
    
    if not change_case:
        raise HTTPException(
            status_code=404,
            detail=f"Change case {approval_data.change_case_id} not found"
        )
    
    approval_service = ApprovalService(db)
    
    try:
        approval = approval_service.add_approver(approval_data)
        return approval
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/approvals/{approval_id}", response_model=schemas.ChangeApprovalResponse)
def get_approval(
    approval_id: int,
    db: Session = Depends(database.get_db)
):
    """Get a specific approval"""
    approval = db.query(models.ChangeApproval).filter(
        models.ChangeApproval.id == approval_id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    
    return approval


@app.put("/approvals/{approval_id}", response_model=schemas.ChangeApprovalResponse)
def update_approval(
    approval_id: int,
    update_data: schemas.ChangeApprovalUpdate,
    db: Session = Depends(database.get_db)
):
    """Update approval status"""
    approval_service = ApprovalService(db)
    
    try:
        approval = approval_service.update_approval(approval_id, update_data)
        return approval
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/approvals/pending/{approver_id}", response_model=List[schemas.ChangeApprovalResponse])
def get_pending_approvals(
    approver_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(database.get_db)
):
    """Get pending approvals for a specific approver"""
    approval_service = ApprovalService(db)
    approvals = approval_service.get_pending_approvals(approver_id, limit)
    
    return approvals


@app.get("/cases/{case_id}/approvals", response_model=List[schemas.ChangeApprovalResponse])
def get_case_approvals(
    case_id: int,
    db: Session = Depends(database.get_db)
):
    """Get all approvals for a change case"""
    # Verify case exists
    change_case = db.query(models.ChangeCase).filter(
        models.ChangeCase.id == case_id
    ).first()
    
    if not change_case:
        raise HTTPException(status_code=404, detail=f"Change case {case_id} not found")
    
    approvals = db.query(models.ChangeApproval).filter(
        models.ChangeApproval.change_case_id == case_id
    ).order_by(models.ChangeApproval.approval_level.asc()).all()
    
    return approvals


# Notification Endpoints
@app.post("/notifications", response_model=schemas.ChangeNotificationResponse, status_code=201)
async def send_notification(
    notification_data: schemas.ChangeNotificationCreate,
    db: Session = Depends(database.get_db)
):
    """Send a change notification"""
    notification_service = NotificationService(db)
    
    try:
        notification = await notification_service.send_notification(notification_data)
        return notification
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/notifications/case/{case_id}", response_model=List[schemas.ChangeNotificationResponse])
def get_case_notifications(
    case_id: int,
    db: Session = Depends(database.get_db)
):
    """Get all notifications for a change case"""
    notifications = db.query(models.ChangeNotification).filter(
        models.ChangeNotification.change_case_id == case_id
    ).order_by(models.ChangeNotification.sent_at.desc()).all()
    
    return notifications


# Analytics Endpoints
@app.get("/analytics/metrics", response_model=schemas.ChangeMetrics)
def get_change_metrics(
    db: Session = Depends(database.get_db)
):
    """Get overall change management metrics"""
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_metrics()
    
    return metrics


@app.get("/analytics/dashboard", response_model=schemas.ChangeDashboard)
def get_change_dashboard(
    db: Session = Depends(database.get_db)
):
    """Get change management dashboard data"""
    analytics_service = AnalyticsService(db)
    
    metrics = analytics_service.get_metrics()
    
    # Get pending approvals count
    pending_approvals = db.query(models.ChangeApproval).filter(
        models.ChangeApproval.status == models.ApprovalStatus.PENDING
    ).count()
    
    # Get overdue changes (due_date passed and not completed)
    now = datetime.utcnow()
    overdue_changes = db.query(models.ChangeCase).filter(
        models.ChangeCase.due_date < now,
        models.ChangeCase.completed_at.is_(None)
    ).count()
    
    return schemas.ChangeDashboard(
        metrics=metrics,
        changes_by_type=[],  # Could be populated with actual data
        changes_by_priority=[],  # Could be populated with actual data
        pending_approvals=pending_approvals,
        overdue_changes=overdue_changes
    )


# Health Check
@app.get("/health", response_model=schemas.HealthResponse)
def health_check(db: Session = Depends(database.get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return schemas.HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service="change-management",
        version="1.0.0",
        database=db_status,
        timestamp=datetime.utcnow()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.SERVICE_PORT)
