"""
Email Service for sending notifications
Supports SMTP and development mode (prints to console)
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os

logger = logging.getLogger(__name__)

# Email configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@coachway.com")
FROM_NAME = os.getenv("FROM_NAME", "CoachWay Charter Management")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send email via SMTP
    
    In development mode (no SMTP credentials), logs email to console
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML version of email body
        text_content: Plain text version (optional, falls back to HTML)
        
    Returns:
        True if sent successfully, False otherwise
    """
    # Development mode - just log the email
    if not SMTP_USER or not SMTP_PASSWORD or ENVIRONMENT == "development":
        logger.info("=" * 60)
        logger.info(f"📧 EMAIL (Development Mode)")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"From: {FROM_NAME} <{FROM_EMAIL}>")
        logger.info("-" * 60)
        logger.info(html_content if not text_content else text_content)
        logger.info("=" * 60)
        return True
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        
        # Add both text and HTML versions
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(html_content, 'html')
        msg.attach(part2)
        
        # Send via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False


def send_mfa_code(email: str, code: str) -> bool:
    """Send MFA verification code via email"""
    subject = "Your CoachWay Verification Code"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Multi-Factor Authentication</h2>
        <p>Your verification code is:</p>
        <div style="background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
          {code}
        </div>
        <p style="color: #666;">This code will expire in 10 minutes.</p>
        <p style="color: #666;">If you didn't request this code, please ignore this email.</p>
        <hr style="margin-top: 30px;">
        <p style="font-size: 12px; color: #999;">CoachWay Charter Management System</p>
      </body>
    </html>
    """
    
    text_content = f"""
    Multi-Factor Authentication
    
    Your verification code is: {code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this code, please ignore this email.
    
    ---
    CoachWay Charter Management System
    """
    
    return send_email(email, subject, html_content, text_content)


def send_password_reset(email: str, token: str, reset_url: Optional[str] = None) -> bool:
    """Send password reset email with token"""
    subject = "Reset Your CoachWay Password"
    
    # If no URL provided, use a default (in production, this should be the frontend URL)
    if not reset_url:
        reset_url = f"http://localhost:3000/reset-password?token={token}"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Password Reset Request</h2>
        <p>We received a request to reset your password for your CoachWay account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="margin: 30px 0; text-align: center;">
          <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
            Reset Password
          </a>
        </div>
        <p style="color: #666;">Or copy and paste this link into your browser:</p>
        <p style="background-color: #f0f0f0; padding: 10px; word-break: break-all; font-size: 12px;">
          {reset_url}
        </p>
        <p style="color: #666; margin-top: 20px;">This link will expire in 1 hour.</p>
        <p style="color: #666;">If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
        <hr style="margin-top: 30px;">
        <p style="font-size: 12px; color: #999;">CoachWay Charter Management System</p>
      </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    We received a request to reset your password for your CoachWay account.
    
    Click this link to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    
    ---
    CoachWay Charter Management System
    """
    
    return send_email(email, subject, html_content, text_content)


def send_impersonation_notification(
    admin_email: str,
    impersonated_email: str,
    reason: str,
    session_id: int
) -> bool:
    """Send notification when admin starts impersonating a user"""
    subject = "Admin Impersonation Session Started"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>⚠️ Impersonation Session Started</h2>
        <p>An administrator has started an impersonation session:</p>
        <ul>
          <li><strong>Admin:</strong> {admin_email}</li>
          <li><strong>Impersonating:</strong> {impersonated_email}</li>
          <li><strong>Reason:</strong> {reason}</li>
          <li><strong>Session ID:</strong> {session_id}</li>
        </ul>
        <p style="color: #666;">All actions during this session will be logged in the audit trail.</p>
        <hr style="margin-top: 30px;">
        <p style="font-size: 12px; color: #999;">CoachWay Security Alert</p>
      </body>
    </html>
    """
    
    text_content = f"""
    ⚠️ Impersonation Session Started
    
    An administrator has started an impersonation session:
    
    Admin: {admin_email}
    Impersonating: {impersonated_email}
    Reason: {reason}
    Session ID: {session_id}
    
    All actions during this session will be logged in the audit trail.
    
    ---
    CoachWay Security Alert
    """
    
    # Send to both admin and impersonated user
    send_email(admin_email, subject, html_content, text_content)
    return send_email(impersonated_email, subject, html_content, text_content)
