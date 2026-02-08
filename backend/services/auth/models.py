"""
Database models for Auth Service
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # admin, manager, sales, operations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Phase 5: MFA & Security
    require_mfa = Column(Boolean, default=False)
    mfa_enforced_at = Column(DateTime(timezone=True))
    last_password_change = Column(DateTime(timezone=True), server_default=func.now())
    password_reset_required = Column(Boolean, default=False)
    
    # Relationships
    mfa_settings = relationship("UserMFA", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email}>"


# ============================================================================
# PHASE 5 TASK 5.1: Multi-Factor Authentication (MFA)
# ============================================================================

class UserMFA(Base):
    """MFA settings for users (email-based 6-digit codes)"""
    __tablename__ = "user_mfa"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_type = Column(String(20), default='email')  # Simplified to email only
    current_code = Column(String(6))  # Current active 6-digit code
    code_expires_at = Column(DateTime(timezone=True))  # Code expiration
    backup_codes = Column(ARRAY(Text))  # Array of hashed backup codes
    last_verified_at = Column(DateTime(timezone=True))
    last_verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="mfa_settings")


class MFAAttempt(Base):
    """MFA verification attempts (audit log)"""
    __tablename__ = "mfa_attempts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    attempt_type = Column(String(20), nullable=False)  # totp, sms, email, backup_code
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
# PHASE 5 TASK 5.2: Password Reset Flow
# ============================================================================

class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordHistory(Base):
    """Password history to prevent reuse"""
    __tablename__ = "password_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
# PHASE 5 TASK 5.3: Account Impersonation
# ============================================================================

class ImpersonationSession(Base):
    """Impersonation sessions for support/admin"""
    __tablename__ = "impersonation_sessions"
    
    id = Column(Integer, primary_key=True)
    admin_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    impersonated_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)


class ImpersonationAuditLog(Base):
    """Audit log for impersonation actions"""
    __tablename__ = "impersonation_audit_log"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('impersonation_sessions.id'), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    details = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SecurityAuditLog(Base):
    """General security audit log"""
    __tablename__ = "security_audit_log"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String(50), nullable=False)
    event_category = Column(String(30), nullable=False)
    severity = Column(String(20), default='info')
    success = Column(Boolean)
    details = Column(Text)  # JSON string
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

