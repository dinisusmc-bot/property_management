from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, engine, Base
from models import Notification, NotificationTemplate
from schemas import (
    NotificationCreate, NotificationResponse,
    TemplateCreate, TemplateResponse
)
from notification_service import NotificationService
from config import settings
import threading
from rabbitmq_consumer import start_consumer

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
