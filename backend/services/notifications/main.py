from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from database import get_db, engine, Base
from models import Notification, NotificationTemplate, SMSPreference, EmailTracking
from schemas import (
    NotificationCreate, NotificationResponse,
    TemplateCreate, TemplateResponse,
    SMSOptOutRequest, SMSOptInRequest, SMSOptOutResponse, SMSOptStatusResponse,
    EmailTrackingStats, EmailTrackingResponse
)
from notification_service import NotificationService
from config import settings
import threading
from rabbitmq_consumer import start_consumer
from datetime import datetime
import secrets

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service", version="1.0.0")
notification_service = NotificationService()

# Start RabbitMQ consumer in background thread
def start_background_consumer():
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    start_background_consumer()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification",
        "sendgrid_configured": bool(settings.SENDGRID_API_KEY),
        "twilio_configured": bool(settings.TWILIO_ACCOUNT_SID)
    }

@app.post("/notifications", response_model=NotificationResponse)
def create_notification(notification_data: NotificationCreate, db: Session = Depends(get_db)):
    """Create and send a notification"""
    try:
        import json
        notification = Notification(
            recipient_email=notification_data.recipient_email,
            recipient_phone=notification_data.recipient_phone,
            recipient_name=notification_data.recipient_name,
            notification_type=notification_data.notification_type,
            template_name=notification_data.template_name,
            template_data=json.dumps(notification_data.template_data),
            priority=notification_data.priority,
            charter_id=notification_data.charter_id,
            client_id=notification_data.client_id,
            payment_id=notification_data.payment_id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Send notification
        notification_service.send_notification(db, notification.id)
        
        return notification
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """Get notification details"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@app.get("/notifications/charter/{charter_id}", response_model=List[NotificationResponse])
def get_charter_notifications(charter_id: int, db: Session = Depends(get_db)):
    """Get all notifications for a charter"""
    notifications = db.query(Notification).filter(
        Notification.charter_id == charter_id
    ).order_by(Notification.created_at.desc()).all()
    return notifications

@app.post("/notifications/{notification_id}/retry")
def retry_notification(notification_id: int, db: Session = Depends(get_db)):
    """Manually retry a failed notification"""
    try:
        notification_service.send_notification(db, notification_id)
        return {"status": "retry_initiated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/templates", response_model=TemplateResponse)
def create_template(template_data: TemplateCreate, db: Session = Depends(get_db)):
    """Create a notification template"""
    try:
        template = NotificationTemplate(**template_data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/templates", response_model=List[TemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    """List all notification templates"""
    templates = db.query(NotificationTemplate).filter(
        NotificationTemplate.is_active == True
    ).all()
    return templates

@app.get("/templates/{template_name}", response_model=TemplateResponse)
def get_template(template_name: str, db: Session = Depends(get_db)):
    """Get a specific template"""
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == template_name
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@app.put("/templates/{template_name}")
def update_template(template_name: str, template_data: TemplateCreate, db: Session = Depends(get_db)):
    """Update a notification template"""
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == template_name
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template_data.model_dump().items():
        setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    return template


# ============================================================================
# Phase 7: SMS Preferences Endpoints
# ============================================================================

def normalize_phone(phone: str) -> str:
    """Normalize phone number by removing spaces and dashes"""
    return phone.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")


@app.post("/sms/opt-out", response_model=SMSOptOutResponse)
async def sms_opt_out(
    request: SMSOptOutRequest,
    db: Session = Depends(get_db)
):
    """Opt-out from SMS notifications"""
    phone = normalize_phone(request.phone_number)
    
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if preference:
        preference.opted_out = True
        preference.opted_out_at = datetime.utcnow()
        preference.opt_out_reason = request.reason
        preference.updated_at = datetime.utcnow()
    else:
        preference = SMSPreference(
            phone_number=phone,
            opted_out=True,
            opted_out_at=datetime.utcnow(),
            opt_out_reason=request.reason
        )
        db.add(preference)
    
    db.commit()
    
    return SMSOptOutResponse(
        phone_number=phone,
        opted_out=True,
        message="Successfully opted out of SMS notifications"
    )


@app.post("/sms/opt-in", response_model=SMSOptOutResponse)
async def sms_opt_in(
    request: SMSOptInRequest,
    db: Session = Depends(get_db)
):
    """Opt-in to SMS notifications"""
    phone = normalize_phone(request.phone_number)
    
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if preference:
        preference.opted_out = False
        preference.opted_out_at = None
        preference.opt_out_reason = None
        preference.updated_at = datetime.utcnow()
    else:
        preference = SMSPreference(
            phone_number=phone,
            opted_out=False
        )
        db.add(preference)
    
    db.commit()
    
    return SMSOptOutResponse(
        phone_number=phone,
        opted_out=False,
        message="Successfully opted in to SMS notifications"
    )


@app.get("/sms/check-opt-out/{phone_number}", response_model=SMSOptStatusResponse)
async def check_sms_opt_out(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Check if phone number has opted out"""
    phone = normalize_phone(phone_number)
    
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if not preference:
        return SMSOptStatusResponse(
            phone_number=phone,
            opted_out=False
        )
    
    return SMSOptStatusResponse(
        phone_number=phone,
        opted_out=preference.opted_out,
        opted_out_at=preference.opted_out_at.isoformat() if preference.opted_out_at else None,
        reason=preference.opt_out_reason
    )


# ============================================================================
# Phase 7: Email Tracking Endpoints
# ============================================================================

def generate_tracking_token() -> str:
    """Generate unique tracking token"""
    return secrets.token_urlsafe(32)


@app.get("/track/open/{tracking_token}")
async def track_email_open(
    tracking_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track email open via pixel"""
    tracking = db.query(EmailTracking).filter(
        EmailTracking.tracking_token == tracking_token
    ).first()
    
    if tracking:
        if not tracking.opened:
            tracking.opened = True
            tracking.opened_at = datetime.utcnow()
        
        tracking.open_count += 1
        tracking.ip_address = request.client.host if request.client else None
        tracking.user_agent = request.headers.get('user-agent')
        
        db.commit()
    
    # Return 1x1 transparent GIF pixel
    pixel_data = bytes.fromhex('47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b')
    return Response(content=pixel_data, media_type="image/gif")


@app.get("/track/stats", response_model=EmailTrackingStats)
async def get_email_tracking_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get email tracking statistics"""
    query = db.query(EmailTracking)
    
    if start_date:
        query = query.filter(EmailTracking.created_at >= start_date)
    if end_date:
        query = query.filter(EmailTracking.created_at <= end_date)
    
    all_emails = query.all()
    total = len(all_emails)
    opened = len([e for e in all_emails if e.opened])
    clicked = len([e for e in all_emails if e.clicked])
    
    return EmailTrackingStats(
        total_emails=total,
        opened=opened,
        clicked=clicked,
        open_rate=(opened / total * 100) if total > 0 else 0,
        click_rate=(clicked / total * 100) if total > 0 else 0
    )


@app.get("/track/{tracking_token}", response_model=EmailTrackingResponse)
async def get_tracking_details(
    tracking_token: str,
    db: Session = Depends(get_db)
):
    """Get details for a specific tracking token"""
    tracking = db.query(EmailTracking).filter(
        EmailTracking.tracking_token == tracking_token
    ).first()
    
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking token not found")
    
    return EmailTrackingResponse(
        tracking_token=tracking.tracking_token,
        opened=tracking.opened,
        opened_at=tracking.opened_at.isoformat() if tracking.opened_at else None,
        open_count=tracking.open_count,
        clicked=tracking.clicked,
        clicked_at=tracking.clicked_at.isoformat() if tracking.clicked_at else None,
        click_count=tracking.click_count
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
