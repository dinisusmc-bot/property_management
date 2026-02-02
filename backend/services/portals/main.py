"""
Portals Service - FastAPI Application

Backend-for-Frontend aggregator providing tailored APIs for:
- Client Portal: Trip management, quotes, payments
- Vendor Portal: Bid opportunities, schedules, performance
- Admin Dashboard: System-wide analytics and management
"""
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime

import config
import models
import schemas
from database import engine, get_db, Base, SCHEMA_NAME
from business_logic import (
    ClientPortalService,
    VendorPortalService,
    AdminDashboardService,
    PreferenceService
)

# Create FastAPI app
app = FastAPI(
    title="CoachWay Portals Service",
    description="Backend-for-Frontend aggregator for client, vendor, and admin portals",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instances
client_portal_service = ClientPortalService()
vendor_portal_service = VendorPortalService()
admin_dashboard_service = AdminDashboardService()
preference_service = PreferenceService()


# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database schema on startup"""
    with engine.connect() as conn:
        # Create schema if it doesn't exist
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"✅ Portals Service started on port {config.SERVICE_PORT}")
    print(f"✅ Database schema '{SCHEMA_NAME}' ready")


# ==================== Health Check ====================

@app.get("/health", response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return schemas.HealthResponse(
        status="healthy",
        service="portals-service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies={
            "auth": "unknown",
            "charter": "unknown",
            "client": "unknown",
            "sales": "unknown",
            "pricing": "unknown",
            "vendor": "unknown",
            "payment": "unknown",
            "document": "unknown",
            "notification": "unknown"
        }
    )


# ==================== Helper Functions ====================

def get_auth_headers(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and format authorization headers"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return {"Authorization": authorization}


# ==================== Client Portal Endpoints ====================

@app.get("/client/dashboard", response_model=schemas.ClientDashboard)
async def get_client_dashboard(
    user_id: int = Query(..., description="User ID from auth token"),
    client_id: int = Query(..., description="Client entity ID"),
    authorization: Optional[str] = Header(None)
):
    """
    Get aggregated dashboard data for client portal.
    
    Aggregates data from:
    - Charter Service: Active and upcoming trips
    - Sales Service: Pending quotes
    - Payment Service: Payment history and totals
    - Notification Service: Unread notifications
    """
    auth_headers = get_auth_headers(authorization)
    dashboard = await client_portal_service.get_dashboard(user_id, client_id, auth_headers)
    return dashboard


@app.get("/client/charters", response_model=List[schemas.ClientCharterSummary])
async def get_client_charters(
    client_id: int = Query(..., description="Client ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100),
    authorization: Optional[str] = Header(None)
):
    """Get charters for client with simplified view"""
    # This would call charter service and transform response
    # For now, return empty list
    return []


@app.get("/client/quotes", response_model=List[schemas.ClientQuoteSummary])
async def get_client_quotes(
    client_id: int = Query(..., description="Client ID"),
    status: Optional[str] = Query("pending", description="Filter by status"),
    limit: int = Query(20, le=100),
    authorization: Optional[str] = Header(None)
):
    """Get quotes for client review"""
    # This would call sales service and transform response
    return []


@app.post("/client/quotes/{quote_id}/accept")
async def accept_quote(
    quote_id: int,
    payment_method_id: str,
    agree_to_terms: bool,
    authorization: Optional[str] = Header(None)
):
    """
    Accept a quote and initiate booking/payment process.
    
    This endpoint orchestrates:
    1. Update quote status in sales service
    2. Create charter in charter service
    3. Process payment via payment service
    4. Send confirmation notifications
    """
    if not agree_to_terms:
        raise HTTPException(status_code=400, detail="Must agree to terms")
    
    # TODO: Implement quote acceptance workflow
    return {"message": "Quote accepted", "quote_id": quote_id}


@app.get("/client/payments", response_model=List[schemas.ClientPaymentHistory])
async def get_client_payments(
    client_id: int = Query(..., description="Client ID"),
    limit: int = Query(50, le=100),
    authorization: Optional[str] = Header(None)
):
    """Get payment history for client"""
    auth_headers = get_auth_headers(authorization)
    payments = await client_portal_service.get_payment_history(client_id, auth_headers, limit)
    return payments


# ==================== Vendor Portal Endpoints ====================

@app.get("/vendor/dashboard", response_model=schemas.VendorDashboard)
async def get_vendor_dashboard(
    user_id: int = Query(..., description="User ID from auth token"),
    vendor_id: int = Query(..., description="Vendor entity ID"),
    authorization: Optional[str] = Header(None)
):
    """
    Get aggregated dashboard data for vendor portal.
    
    Aggregates data from:
    - Vendor Service: Profile, bids, ratings, compliance
    - Charter Service: Upcoming trips, opportunities
    - Payment Service: Earnings and pending payments
    """
    auth_headers = get_auth_headers(authorization)
    dashboard = await vendor_portal_service.get_dashboard(user_id, vendor_id, auth_headers)
    return dashboard


@app.get("/vendor/opportunities", response_model=List[schemas.VendorBidOpportunity])
async def get_bid_opportunities(
    vendor_id: int = Query(..., description="Vendor ID"),
    limit: int = Query(20, le=100),
    authorization: Optional[str] = Header(None)
):
    """Get available charters for bidding"""
    # This would call charter service filtered for open bids
    return []


@app.get("/vendor/schedule", response_model=List[schemas.VendorScheduledTrip])
async def get_vendor_schedule(
    vendor_id: int = Query(..., description="Vendor ID"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=100),
    authorization: Optional[str] = Header(None)
):
    """Get scheduled trips for vendor"""
    # This would call charter service for confirmed trips with this vendor
    return []


@app.post("/vendor/bids")
async def submit_bid(
    charter_id: int,
    quoted_price: float,
    vehicle_type: str,
    notes: Optional[str] = None,
    vendor_id: int = Query(..., description="Vendor ID"),
    authorization: Optional[str] = Header(None)
):
    """Submit a bid on a charter opportunity"""
    # This would call vendor service to create bid
    return {"message": "Bid submitted", "charter_id": charter_id}


# ==================== Admin Dashboard Endpoints ====================

@app.get("/admin/dashboard", response_model=schemas.AdminDashboard)
async def get_admin_dashboard(
    authorization: Optional[str] = Header(None)
):
    """
    Get system-wide dashboard for admin.
    
    Aggregates data from all services:
    - User counts, active charters, revenue
    - Pending approvals across services
    - Recent system activity
    - System health and alerts
    """
    auth_headers = get_auth_headers(authorization)
    dashboard = await admin_dashboard_service.get_dashboard(auth_headers)
    return dashboard


@app.get("/admin/recent-activity", response_model=List[schemas.AdminRecentActivity])
async def get_recent_activity(
    limit: int = Query(50, le=200),
    activity_category: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Get recent system-wide activity"""
    # This would query activity logs
    return []


@app.get("/admin/pending-approvals")
async def get_pending_approvals(
    approval_type: Optional[str] = Query(None, description="vendor, charter, change_request"),
    authorization: Optional[str] = Header(None)
):
    """Get pending items requiring admin approval"""
    # This would aggregate from vendor, charter, and change management services
    return {
        "pending_vendor_approvals": 0,
        "pending_charter_approvals": 0,
        "pending_change_requests": 0,
        "total": 0
    }


# ==================== User Preferences Endpoints ====================

@app.get("/preferences", response_model=schemas.PortalUserPreferenceResponse)
async def get_user_preferences(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get user portal preferences"""
    preferences = preference_service.get_preferences(db, user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


@app.post("/preferences", response_model=schemas.PortalUserPreferenceResponse, status_code=201)
async def create_user_preferences(
    preferences: schemas.PortalUserPreferenceCreate,
    db: Session = Depends(get_db)
):
    """Create user portal preferences"""
    # Check if preferences already exist
    existing = preference_service.get_preferences(db, preferences.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="Preferences already exist. Use PUT to update.")
    
    return preference_service.create_preferences(db, preferences)


@app.put("/preferences", response_model=schemas.PortalUserPreferenceResponse)
async def update_user_preferences(
    user_id: int = Query(..., description="User ID"),
    updates: schemas.PortalUserPreferenceUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update user portal preferences"""
    preferences = preference_service.update_preferences(db, user_id, updates)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return preferences


# ==================== Activity Logging ====================

@app.post("/activity-log", status_code=201)
async def log_activity(
    activity: schemas.PortalActivityLogCreate,
    db: Session = Depends(get_db)
):
    """Log portal activity for analytics and audit"""
    db_activity = models.PortalActivityLog(**activity.dict())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return {"message": "Activity logged", "id": db_activity.id}


@app.get("/activity-log", response_model=List[schemas.PortalActivityLogResponse])
async def get_activity_logs(
    user_id: Optional[int] = Query(None),
    activity_type: Optional[str] = Query(None),
    activity_category: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get activity logs with filters"""
    query = db.query(models.PortalActivityLog)
    
    if user_id:
        query = query.filter(models.PortalActivityLog.user_id == user_id)
    if activity_type:
        query = query.filter(models.PortalActivityLog.activity_type == activity_type)
    if activity_category:
        query = query.filter(models.PortalActivityLog.activity_category == activity_category)
    
    logs = query.order_by(models.PortalActivityLog.created_at.desc()).limit(limit).all()
    return logs


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.SERVICE_PORT)
