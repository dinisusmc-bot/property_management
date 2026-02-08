"""
Pydantic schemas for Auth Service
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str

class AdminPasswordChange(BaseModel):
    """Schema for admin changing user password"""
    new_password: str

class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_superuser: bool
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token schema"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data schema"""
    email: Optional[str] = None


# ============================================================================
# PHASE 5 TASK 5.1: Multi-Factor Authentication (MFA) Schemas
# ============================================================================

class MFASetupRequest(BaseModel):
    """Request to setup MFA (email-based 6-digit code)"""
    pass  # Uses authenticated user's email


class MFASetupResponse(BaseModel):
    """Response from MFA setup"""
    message: str
    email: str  # Email where code was sent (partially masked)


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code"""
    code: str  # 6-digit code from email
    use_backup: bool = False  # Use backup code instead


class MFAEnableResponse(BaseModel):
    """Response after enabling MFA"""
    message: str
    backup_codes: list[str]
    warning: str


class MFAVerifyResponse(BaseModel):
    """Response from MFA verification"""
    success: bool
    message: str
    remaining_backup_codes: Optional[int] = None


class MFAStatusResponse(BaseModel):
    """MFA status for user"""
    mfa_enabled: bool
    email: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    backup_codes_remaining: int = 0


# ============================================================================
# PHASE 5 TASK 5.2: Password Reset Flow Schemas
# ============================================================================

class PasswordResetRequest(BaseModel):
    """Request to initiate password reset"""
    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Response to password reset request"""
    message: str
    email: Optional[str] = None


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str


class PasswordResetConfirmResponse(BaseModel):
    """Response to password reset confirmation"""
    message: str
    success: bool


# ============================================================================
# PHASE 5 TASK 5.3: Account Impersonation Schemas
# ============================================================================

class ImpersonationStartRequest(BaseModel):
    """Request to start impersonation"""
    user_id: int
    reason: str


class ImpersonationStartResponse(BaseModel):
    """Response when starting impersonation"""
    session_id: int
    impersonated_user: UserResponse
    message: str
    token: str  # New token for impersonated session


class ImpersonationEndRequest(BaseModel):
    """Request to end impersonation"""
    session_id: int


class ImpersonationEndResponse(BaseModel):
    """Response when ending impersonation"""
    message: str
    session_duration_seconds: int


class ImpersonationSessionResponse(BaseModel):
    """Impersonation session details"""
    id: int
    admin_user_id: int
    impersonated_user_id: int
    reason: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class ImpersonationAuditResponse(BaseModel):
    """Impersonation audit log entry"""
    id: int
    session_id: int
    action: str
    resource: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

