import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client
from jinja2 import Template
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from config import settings
from models import Notification, NotificationTemplate, NotificationStatus, NotificationType

class NotificationService:
    
    def __init__(self):
        # Initialize SendGrid
        if settings.SENDGRID_API_KEY:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        else:
            self.sendgrid_client = None
        
        # Initialize Twilio
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID, 
                settings.TWILIO_AUTH_TOKEN
            )
        else:
            self.twilio_client = None
    
    def send_notification(self, db: Session, notification_id: int):
        """Process and send a notification"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if not notification:
            raise Exception("Notification not found")
        
        # Get template
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.name == notification.template_name,
            NotificationTemplate.is_active == True
        ).first()
        
        if not template:
            self._mark_failed(db, notification, "Template not found or inactive")
            return
        
        try:
            # Parse template data
            template_data = json.loads(notification.template_data) if notification.template_data else {}
            
            # Send based on type
            if notification.notification_type == NotificationType.EMAIL or notification.notification_type == NotificationType.BOTH:
                self._send_email(db, notification, template, template_data)
            
            if notification.notification_type == NotificationType.SMS or notification.notification_type == NotificationType.BOTH:
                self._send_sms(db, notification, template, template_data)
            
            # Mark as sent
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            self._handle_failure(db, notification, str(e))
    
    def _send_email(self, db: Session, notification: Notification, template: NotificationTemplate, data: dict):
        """Send email via SendGrid"""
        if not self.sendgrid_client:
            raise Exception("SendGrid not configured")
        
        if not notification.recipient_email:
            raise Exception("No email address provided")
        
        # Render subject
        subject_template = Template(template.email_subject)
        subject = subject_template.render(**data)
        
        # Render HTML body
        html_template = Template(template.email_body_html)
        html_content = html_template.render(**data)
        
        # Render text body
        text_template = Template(template.email_body_text)
        text_content = text_template.render(**data)
        
        # Create message
        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=To(notification.recipient_email, notification.recipient_name),
            subject=subject,
            plain_text_content=Content("text/plain", text_content),
            html_content=Content("text/html", html_content)
        )
        
        # Send
        response = self.sendgrid_client.send(message)
        
        # Store message ID
        if response.headers.get('X-Message-Id'):
            notification.sendgrid_message_id = response.headers['X-Message-Id']
            db.commit()
    
    def _send_sms(self, db: Session, notification: Notification, template: NotificationTemplate, data: dict):
        """Send SMS via Twilio"""
        if not self.twilio_client:
            raise Exception("Twilio not configured")
        
        if not notification.recipient_phone:
            raise Exception("No phone number provided")
        
        # Render SMS body
        sms_template = Template(template.sms_body)
        sms_body = sms_template.render(**data)
        
        # Send SMS
        message = self.twilio_client.messages.create(
            body=sms_body,
            from_=settings.TWILIO_FROM_PHONE,
            to=notification.recipient_phone
        )
        
        # Store message SID
        notification.twilio_message_sid = message.sid
        db.commit()
    
    def _handle_failure(self, db: Session, notification: Notification, error: str):
        """Handle notification failure with retry logic"""
        notification.retry_count += 1
        notification.error_message = error
        
        if notification.retry_count < settings.MAX_RETRY_ATTEMPTS:
            # Schedule retry
            notification.status = NotificationStatus.RETRYING
            notification.next_retry_at = datetime.utcnow() + timedelta(
                seconds=settings.RETRY_DELAY_SECONDS * notification.retry_count
            )
        else:
            # Max retries reached
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
        
        db.commit()
    
    def _mark_failed(self, db: Session, notification: Notification, error: str):
        """Mark notification as permanently failed"""
        notification.status = NotificationStatus.FAILED
        notification.error_message = error
        notification.failed_at = datetime.utcnow()
        db.commit()
    
    def retry_failed_notifications(self, db: Session):
        """Retry notifications that are due for retry"""
        notifications = db.query(Notification).filter(
            Notification.status == NotificationStatus.RETRYING,
            Notification.next_retry_at <= datetime.utcnow()
        ).all()
        
        for notification in notifications:
            try:
                self.send_notification(db, notification.id)
            except Exception as e:
                print(f"Retry failed for notification {notification.id}: {e}")
