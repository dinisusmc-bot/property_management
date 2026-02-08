"""
Auth Service - User Authentication and Authorization
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import logging
import secrets

from database import engine, SessionLocal, Base
from models import User, UserMFA, MFAAttempt, PasswordResetToken, ImpersonationSession, ImpersonationAuditLog, SecurityAuditLog
from schemas import (
    UserCreate, UserResponse, Token, UserUpdate, PasswordChange, AdminPasswordChange,
    # Phase 5 schemas
    MFASetupRequest, MFASetupResponse, MFAVerifyRequest, MFAEnableResponse, MFAVerifyResponse, MFAStatusResponse,
    PasswordResetRequest, PasswordResetResponse, PasswordResetConfirm, PasswordResetConfirmResponse,
    ImpersonationStartRequest, ImpersonationStartResponse, ImpersonationEndRequest, ImpersonationEndResponse
)
from auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token
)
from mfa_service import (
    generate_mfa_code,
    verify_mfa_code,
    generate_backup_codes,
    hash_backup_codes,
    verify_backup_code,
    get_code_expiry_time,
    remove_used_backup_code
)
from email_service import send_mfa_code, send_password_reset, send_impersonation_notification
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Athena Auth Service",
    description="Authentication and user management service",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,
    openapi_url="/openapi.json",
    servers=[
        {"url": "/api/v1/auth", "description": "API Gateway"}
    ]
)

# Custom Swagger UI with correct openapi URL
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <title>{app.title} - Swagger UI</title>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/api/v1/auth/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

@app.on_event("startup")
async def startup_event():
    """Initialize database with default admin user if not exists"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@athena.com").first()
        if not admin:
            admin = User(
                email="admin@athena.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            db.add(admin)
            db.commit()
            logger.info("Created default admin user")
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "auth", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        role="user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user registered: {user.email}")
    return db_user

@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint - returns access and refresh tokens"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/vendors", response_model=list[UserResponse])
async def list_vendors(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all vendor users"""
    vendors = db.query(User).filter(User.role == "vendor").offset(skip).limit(limit).all()
    return vendors

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    # Check permissions
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only admins can change role and is_active
    if not current_user.is_superuser:
        if user_update.role is not None or user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to change role or status"
            )
    
    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None and current_user.is_superuser:
        user.is_active = user_update.is_active
    if user_update.role is not None and current_user.is_superuser:
        user.role = user_update.role
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated: {user.email} by {current_user.email}")
    return user

@app.post("/users/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password (requires current password)"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only change your own password"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_change.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    
    logger.info(f"Password changed for user: {user.email}")
    return {"message": "Password changed successfully"}

@app.post("/users/{user_id}/admin-change-password")
async def admin_change_password(
    user_id: int,
    password_change: AdminPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin change user password (no current password required)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    
    logger.info(f"Password changed by admin for user: {user.email}")
    return {"message": "Password changed successfully"}

@app.post("/users/create", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        role="user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user created by admin: {user.email}")
    return db_user


# ============================================================================
# PHASE 5: MFA ENDPOINTS
# ============================================================================

@app.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize MFA setup - sends 6-digit code to user's email"""
    # Check if MFA already enabled
    existing_mfa = db.query(UserMFA).filter(UserMFA.user_id == current_user.id).first()
    if existing_mfa and existing_mfa.mfa_enabled:
        raise HTTPException(400, "MFA already enabled. Disable first to change settings.")
    
    # Generate 6-digit code
    code = generate_mfa_code()
    expiry = get_code_expiry_time(minutes=10)
    
    # Store code (create or update)
    if existing_mfa:
        existing_mfa.current_code = code
        existing_mfa.code_expires_at = expiry
        existing_mfa.mfa_enabled = False
    else:
        mfa_settings = UserMFA(
            user_id=current_user.id,
            mfa_type="email",
            current_code=code,
            code_expires_at=expiry,
            mfa_enabled=False
        )
        db.add(mfa_settings)
    
    db.commit()
    
    # Send MFA code via email
    send_mfa_code(current_user.email, code)
    logger.info(f"MFA code sent to {current_user.email}")
    
    masked_email = current_user.email[:3] + "***@" + current_user.email.split('@')[1]
    
    return MFASetupResponse(
        message=f"Verification code sent to {masked_email}",
        email=masked_email
    )


@app.post("/mfa/verify-and-enable", response_model=MFAEnableResponse)
async def verify_and_enable_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify code and enable MFA, returns backup codes"""
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == current_user.id).first()
    if not mfa_settings:
        raise HTTPException(400, "MFA not set up. Call /mfa/setup first.")
    
    if mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA already enabled")
    
    # Verify code
    is_valid = verify_mfa_code(
        mfa_settings.current_code,
        request.code,
        mfa_settings.code_expires_at
    )
    
    # Log attempt
    attempt = MFAAttempt(
        user_id=current_user.id,
        attempt_type="email",
        success=is_valid
    )
    db.add(attempt)
    
    if not is_valid:
        db.commit()
        raise HTTPException(400, "Invalid or expired code")
    
    # Generate and hash backup codes
    backup_codes = generate_backup_codes()
    hashed_codes = hash_backup_codes(backup_codes)
    
    # Enable MFA
    mfa_settings.mfa_enabled = True
    mfa_settings.backup_codes = hashed_codes
    mfa_settings.last_verified_at = datetime.utcnow()
    mfa_settings.current_code = None  # Clear used code
    
    current_user.mfa_enforced_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"MFA enabled for user: {current_user.email}")
    
    return MFAEnableResponse(
        message="MFA enabled successfully",
        backup_codes=backup_codes,
        warning="Save these backup codes securely. They won't be shown again."
    )


@app.post("/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa_login(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify MFA code during login"""
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == current_user.id).first()
    if not mfa_settings or not mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA not enabled")
    
    if request.use_backup:
        # Verify backup code
        is_valid, index = verify_backup_code(mfa_settings.backup_codes, request.code)
        
        attempt = MFAAttempt(
            user_id=current_user.id,
            attempt_type="backup_code",
            success=is_valid
        )
        db.add(attempt)
        
        if is_valid:
            # Remove used backup code
            remaining = remove_used_backup_code(mfa_settings.backup_codes, index)
            mfa_settings.backup_codes = remaining
            mfa_settings.last_verified_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Backup code used for {current_user.email}, {len(remaining)} remaining")
            
            return MFAVerifyResponse(
                success=True,
                message="Backup code verified",
                remaining_backup_codes=len(remaining)
            )
        else:
            db.commit()
            raise HTTPException(400, "Invalid backup code")
    else:
        # Verify email code
        is_valid = verify_mfa_code(
            mfa_settings.current_code,
            request.code,
            mfa_settings.code_expires_at
        )
        
        attempt = MFAAttempt(
            user_id=current_user.id,
            attempt_type="email",
            success=is_valid
        )
        db.add(attempt)
        
        if is_valid:
            mfa_settings.last_verified_at = datetime.utcnow()
            mfa_settings.current_code = None  # Clear used code
            db.commit()
            
            return MFAVerifyResponse(
                success=True,
                message="MFA verified successfully"
            )
        else:
            db.commit()
            raise HTTPException(400, "Invalid or expired code")


@app.get("/mfa/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's MFA status"""
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == current_user.id).first()
    
    if not mfa_settings:
        return MFAStatusResponse(
            mfa_enabled=False,
            email=None,
            backup_codes_remaining=0
        )
    
    masked_email = current_user.email[:3] + "***@" + current_user.email.split('@')[1]
    
    return MFAStatusResponse(
        mfa_enabled=mfa_settings.mfa_enabled,
        email=masked_email if mfa_settings.mfa_enabled else None,
        last_verified_at=mfa_settings.last_verified_at,
        backup_codes_remaining=len(mfa_settings.backup_codes) if mfa_settings.backup_codes else 0
    )


@app.post("/mfa/disable")
async def disable_mfa(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA (requires password confirmation)"""
    # Verify password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(401, "Invalid password")
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == current_user.id).first()
    if not mfa_settings or not mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA not enabled")
    
    # Delete MFA settings
    db.delete(mfa_settings)
    current_user.mfa_enforced_at = None
    
    db.commit()
    
    logger.info(f"MFA disabled for user: {current_user.email}")
    
    return {"message": "MFA disabled successfully"}


@app.post("/mfa/regenerate-backup-codes")
async def regenerate_backup_codes(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate new backup codes (requires password)"""
    # Verify password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(401, "Invalid password")
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == current_user.id).first()
    if not mfa_settings or not mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA not enabled")
    
    # Generate new backup codes
    backup_codes_plain = generate_backup_codes()
    hashed_codes = hash_backup_codes(backup_codes_plain)
    
    mfa_settings.backup_codes = hashed_codes
    db.commit()
    
    logger.info(f"Backup codes regenerated for user: {current_user.email}")
    
    return {
        "message": "New backup codes generated",
        "backup_codes": backup_codes_plain,
        "warning": "Old backup codes are now invalid. Save these securely."
    }


# ============================================================================
# PHASE 5: PASSWORD RESET ENDPOINTS
# ============================================================================

@app.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Initiate password reset - sends token to email"""
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to prevent email enumeration
    response = PasswordResetResponse(
        message="If the email exists, a password reset link has been sent.",
        email=None
    )
    
    if not user:
        return response
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    token_hash = get_password_hash(token)
    expiry = datetime.utcnow() + timedelta(hours=1)
    
    # Store token
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        token_hash=token_hash,
        expires_at=expiry,
        used=False
    )
    db.add(reset_token)
    db.commit()
    
    # Send password reset email
    send_password_reset(user.email, token)
    logger.info(f"Password reset email sent to {user.email}")
    
    return response


@app.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    # Find valid token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(400, "Invalid or expired reset token")
    
    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.last_password_change = datetime.utcnow()
    
    # Mark token as used
    reset_token.used = True
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Password reset completed for user: {user.email}")
    
    return PasswordResetConfirmResponse(
        message="Password reset successful. You can now log in with your new password.",
        success=True
    )


# ============================================================================
# PHASE 5: IMPERSONATION ENDPOINTS (Admin Only)
# ============================================================================

@app.post("/impersonation/start", response_model=ImpersonationStartResponse)
async def start_impersonation(
    request: ImpersonationStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start impersonating another user (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin privileges required")
    
    # Get target user
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(404, "User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(400, "Cannot impersonate yourself")
    
    # Check for existing active session
    existing_session = db.query(ImpersonationSession).filter(
        ImpersonationSession.admin_user_id == current_user.id,
        ImpersonationSession.is_active == True
    ).first()
    
    if existing_session:
        raise HTTPException(400, "You already have an active impersonation session. End it first.")
    
    # Create session
    session = ImpersonationSession(
        admin_user_id=current_user.id,
        impersonated_user_id=target_user.id,
        reason=request.reason,
        started_at=datetime.utcnow(),
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Generate impersonation token
    token_data = {
        "sub": target_user.email,
        "impersonation_session_id": session.id,
        "admin_user_id": current_user.id
    }
    access_token = create_access_token(data=token_data)
    
    # Send impersonation notification
    send_impersonation_notification(
        current_user.email,
        target_user.email,
        request.reason,
        session.id
    )
    logger.info(f"Admin {current_user.email} started impersonating {target_user.email}")
    
    return ImpersonationStartResponse(
        session_id=session.id,
        impersonated_user=UserResponse.from_orm(target_user),
        message=f"Now impersonating {target_user.full_name}",
        token=access_token
    )


@app.post("/impersonation/end", response_model=ImpersonationEndResponse)
async def end_impersonation(
    request: ImpersonationEndRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End an impersonation session"""
    session = db.query(ImpersonationSession).filter(
        ImpersonationSession.id == request.session_id,
        ImpersonationSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, "Active impersonation session not found")
    
    # Only admin who started or super admin can end
    if session.admin_user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(403, "Can only end your own impersonation sessions")
    
    # End session
    session.is_active = False
    session.ended_at = datetime.utcnow()
    
    duration = (session.ended_at - session.started_at).total_seconds()
    
    db.commit()
    
    logger.info(f"Impersonation session {session.id} ended after {duration}s")
    
    return ImpersonationEndResponse(
        message="Impersonation session ended",
        session_duration_seconds=int(duration)
    )


@app.get("/impersonation/sessions")
async def list_impersonation_sessions(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List impersonation sessions (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin privileges required")
    
    query = db.query(ImpersonationSession)
    
    if active_only:
        query = query.filter(ImpersonationSession.is_active == True)
    
    sessions = query.order_by(ImpersonationSession.started_at.desc()).limit(50).all()
    
    return {"sessions": sessions, "count": len(sessions)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
