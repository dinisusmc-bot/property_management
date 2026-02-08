# Phase 5: Portal Security & User Management

**Duration:** 2 weeks  
**Priority:** 🟠 IMPORTANT  
**Goal:** Enhance authentication and security features for all portals

---

## Overview

Security enhancements needed:
- Multi-factor authentication (MFA/2FA)
- Password reset flow with email tokens
- Account impersonation for support (admin only)
- Session management and security
- Audit logging for sensitive actions

These features improve security and meet compliance requirements.

---

## Task 5.1: Multi-Factor Authentication (MFA)

**Estimated Time:** 12-15 hours  
**Services:** Auth  
**Impact:** HIGH - Critical security feature

### Database Changes

```sql
-- MFA settings table (email-based 6-digit codes)
CREATE TABLE IF NOT EXISTS user_mfa (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_type VARCHAR(20) DEFAULT 'email',  -- Simplified to email only
  current_code VARCHAR(6),  -- Current active 6-digit code
  code_expires_at TIMESTAMP,  -- Code expiration time
  backup_codes TEXT[],  -- Array of hashed backup codes
  last_verified_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_mfa_user ON user_mfa(user_id);
CREATE INDEX idx_user_mfa_enabled ON user_mfa(mfa_enabled) WHERE mfa_enabled = TRUE;

-- MFA verification attempts (audit trail)
CREATE TABLE IF NOT EXISTS mfa_attempts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  attempt_type VARCHAR(20) NOT NULL,  -- email, backup_code
  success BOOLEAN NOT NULL,
  ip_address VARCHAR(45),
  user_agent TEXT,
  attempted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mfa_attempts_user ON mfa_attempts(user_id, attempted_at DESC);

-- Update users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS require_mfa BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enforced_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_password_change TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_required BOOLEAN DEFAULT FALSE;
```

### Implementation Steps

#### Step 1: MFA Dependencies

**File:** `backend/services/auth/requirements.txt`

```txt
# No additional dependencies needed - using built-in libraries
# passlib[bcrypt] already included for backup code hashing
```

#### Step 2: Create MFA Models

**File:** `backend/services/auth/models.py`

```python
from sqlalchemy.dialects.postgresql import ARRAY

class UserMFA(Base):
    __tablename__ = "user_mfa"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_type = Column(String(20), default='email')
    current_code = Column(String(6))  # Active 6-digit code
    code_expires_at = Column(DateTime)  # Code expiration
    backup_codes = Column(ARRAY(String))  # Hashed backup codes
    last_verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="mfa_settings")

class MFAAttempt(Base):
    __tablename__ = "mfa_attempts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    attempt_type = Column(String(20), nullable=False)  # email, backup_code
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    attempted_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    # ... existing fields ...
    
    require_mfa = Column(Boolean, default=False)
    mfa_enforced_at = Column(DateTime)
    last_password_change = Column(DateTime)
    password_reset_required = Column(Boolean, default=False)
    
    mfa_settings = relationship("UserMFA", back_populates="user", uselist=False)
```

#### Step 3: Create MFA Service

**File:** `backend/services/auth/mfa_service.py` (New file)

```python
"""MFA (Multi-Factor Authentication) service - Email-based 6-digit codes"""
import secrets
import string
from passlib.hash import bcrypt
from typing import List, Tuple
from datetime import datetime, timedelta

def generate_mfa_code() -> str:
    """Generate 6-digit verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def verify_mfa_code(stored_code: str, provided_code: str, expiry_time: datetime) -> bool:
    """Verify MFA code is correct and not expired"""
    if datetime.utcnow() > expiry_time:
        return False
    return stored_code == provided_code

def generate_backup_codes(count: int = 8) -> List[str]:
    """Generate backup codes (format: XXXX-XXXX)"""
    codes = []
    for _ in range(count):
        code = '-'.join([
            ''.join(secrets.choice('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(4))
            for _ in range(2)
        ])
        codes.append(code)
    return codes

def hash_backup_codes(codes: List[str]) -> List[str]:
    """Hash backup codes for secure storage"""
    return [bcrypt.hash(code) for code in codes]

def verify_backup_code(hashed_codes: List[str], code: str) -> Tuple[bool, int]:
    """Verify backup code and return index for removal"""
    for idx, hashed in enumerate(hashed_codes):
        if bcrypt.verify(code, hashed):
            return True, idx
    return False, -1

def get_code_expiry_time(minutes: int = 10) -> datetime:
    """Get expiry time for verification code (default 10 minutes)"""
    return datetime.utcnow() + timedelta(minutes=minutes)
```
        issuer_name=issuer
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 30s window

def generate_backup_codes(count: int = 8) -> list:
    """Generate backup codes"""
    codes = []
    for _ in range(count):
        code = '-'.join([
            ''.join(secrets.choice('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(4))
            for _ in range(2)
        ])
        codes.append(code)
    return codes

def hash_backup_codes(codes: list) -> list:
    """Hash backup codes for storage"""
    return [bcrypt.hash(code) for code in codes]

def verify_backup_code(hashed_codes: list, code: str) -> bool:
    """Verify backup code against hashed list"""
    for hashed in hashed_codes:
        if bcrypt.verify(code, hashed):
            return True
    return False
```

#### Step 4: Create MFA Endpoints

**File:** `backend/services/auth/main.py`

```python
from .mfa_service import (
    generate_mfa_code,
    verify_mfa_code,
    generate_backup_codes,
    hash_backup_codes,
    verify_backup_code,
    get_code_expiry_time
)

@app.post("/mfa/setup")
async def setup_mfa(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize MFA setup - sends 6-digit code to user's email
    """
    user_id = current_user["user_id"]
    email = current_user["email"]
    
    # Check if MFA already enabled
    existing_mfa = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
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
            user_id=user_id,
            mfa_type="email",
            current_code=code,
            code_expires_at=expiry,
            mfa_enabled=False
        )
        db.add(mfa_settings)
    
    db.commit()
    
    # TODO: Send email with code
    # For now, return code in response (remove in production)
    
    masked_email = email[:3] + "***@" + email.split('@')[1]
    
    return {
        "message": f"Verification code sent to {masked_email}",
        "email": masked_email,
        "code": code  # TODO: Remove in production - only for testing
    }

@app.post("/mfa/verify-and-enable")
async def verify_and_enable_mfa(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Verify code and enable MFA, returns backup codes"""
    user_id = current_user["user_id"]
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    if not mfa_settings:
        raise HTTPException(400, "MFA not set up. Call /mfa/setup first.")
    
    if mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA already enabled")
    
    # Verify code
    is_valid = verify_mfa_code(
        mfa_settings.current_code,
        code,
        mfa_settings.code_expires_at
    )
    
    # Log attempt
    attempt = MFAAttempt(
        user_id=user_id,
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
    
    user = db.query(User).filter(User.id == user_id).first()
    user.mfa_enforced_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "MFA enabled successfully",
        "backup_codes": backup_codes,
        "warning": "Save these backup codes securely. They won't be shown again."
    }

@app.post("/mfa/verify")
async def verify_mfa_login(
    code: str,
    use_backup: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Verify MFA code during login"""
    user_id = current_user["user_id"]
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    if not mfa_settings or not mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA not enabled")
    
    if use_backup:
        # Verify backup code
        is_valid, index = verify_backup_code(mfa_settings.backup_codes, code)
        
        attempt = MFAAttempt(
            user_id=user_id,
            attempt_type="backup_code",
            success=is_valid
        )
        db.add(attempt)
        
        if is_valid:
            # Remove used backup code
            remaining = list(mfa_settings.backup_codes)
            remaining.pop(index)
            mfa_settings.backup_codes = remaining
            mfa_settings.last_verified_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "message": "Backup code verified",
                "remaining_backup_codes": len(remaining)
            }
        else:
            db.commit()
            raise HTTPException(400, "Invalid backup code")
    else:
        # Verify email code
        is_valid = verify_mfa_code(
            mfa_settings.current_code,
            code,
            mfa_settings.code_expires_at
        )
        
        attempt = MFAAttempt(
            user_id=user_id,
            attempt_type="email",
            success=is_valid
        )
        db.add(attempt)
        
        if is_valid:
            mfa_settings.last_verified_at = datetime.utcnow()
            mfa_settings.current_code = None  # Clear used code
            db.commit()
            
            return {
                "success": True,
                "message": "MFA verified successfully"
            }
        else:
            db.commit()
            raise HTTPException(400, "Invalid or expired code")

@app.get("/mfa/status")
async def get_mfa_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's MFA status"""
    user_id = current_user["user_id"]
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    
    if not mfa_settings:
        return {
            "mfa_enabled": False,
            "email": None,
            "backup_codes_remaining": 0
        }
    
    masked_email = current_user["email"][:3] + "***@" + current_user["email"].split('@')[1]
    
    return {
        "mfa_enabled": mfa_settings.mfa_enabled,
        "email": masked_email if mfa_settings.mfa_enabled else None,
        "last_verified_at": mfa_settings.last_verified_at,
        "backup_codes_remaining": len(mfa_settings.backup_codes) if mfa_settings.backup_codes else 0
    }

@app.post("/mfa/disable")
async def disable_mfa(
    password: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Disable MFA (requires password confirmation)"""
    user_id = current_user["user_id"]
    
    # Verify password
    user = db.query(User).filter(User.id == user_id).first()
    if not pwd_context.verify(password, user.password):
        raise HTTPException(401, "Invalid password")
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    if not mfa_settings or not mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA not enabled")
    
    # Delete MFA settings
    db.delete(mfa_settings)
    user.mfa_enforced_at = None
    
    db.commit()
    
    return {"message": "MFA disabled successfully"}

@app.post("/mfa/regenerate-backup-codes")
async def regenerate_backup_codes(
    password: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate new backup codes (requires password)"""
    user_id = current_user["user_id"]
    
    # Verify password
    user = db.query(User).filter(User.id == user_id).first()
    if not pwd_context.verify(password, user.password):
        raise HTTPException(401, "Invalid password")
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    if not mfa_settings or not mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA not enabled")
    
    # Generate new backup codes
    backup_codes = generate_backup_codes()
    hashed_codes = hash_backup_codes(backup_codes)
    
    mfa_settings.backup_codes = hashed_codes
    db.commit()
    
    return {
        "message": "New backup codes generated",
        "backup_codes": backup_codes,
        "warning": "Old backup codes are now invalid. Save these securely."
    }
```
        secret = generate_totp_secret()
        qr_code = generate_totp_qr_code(current_user["email"], secret)
        
        # Store secret (not yet enabled)
        if existing_mfa:
            existing_mfa.mfa_type = "totp"
            existing_mfa.mfa_secret = secret  # TODO: Encrypt in production
            existing_mfa.mfa_enabled = False
        else:
            mfa_settings = UserMFA(
                user_id=user_id,
                mfa_type="totp",
                mfa_secret=secret,
                mfa_enabled=False
            )
            db.add(mfa_settings)
        
        db.commit()
        
        return {
            "mfa_type": "totp",
            "secret": secret,
            "qr_code": qr_code,
            "message": "Scan QR code with authenticator app, then verify to enable"
        }
    
    elif mfa_type == "sms":
        if not phone_number:
            raise HTTPException(400, "Phone number required for SMS MFA")
        
        # TODO: Send SMS verification code
        # For now, just store phone number
        
        if existing_mfa:
            existing_mfa.mfa_type = "sms"
            existing_mfa.phone_number = phone_number
            existing_mfa.mfa_enabled = False
        else:
            mfa_settings = UserMFA(
                user_id=user_id,
                mfa_type="sms",
                phone_number=phone_number,
                mfa_enabled=False
            )
            db.add(mfa_settings)
        
        db.commit()
        
        return {
            "mfa_type": "sms",
            "phone_number": phone_number,
            "message": "SMS verification code sent. Verify to enable MFA."
        }
    
    else:
        raise HTTPException(400, f"Unsupported MFA type: {mfa_type}")

@app.post("/mfa/verify-and-enable")
async def verify_and_enable_mfa(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Verify MFA code and enable MFA for user"""
    user_id = current_user["user_id"]
    
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    if not mfa_settings:
        raise HTTPException(400, "MFA not set up. Call /mfa/setup first.")
    
    if mfa_settings.mfa_enabled:
        raise HTTPException(400, "MFA already enabled")
    
    # Verify code based on type
    if mfa_settings.mfa_type == "totp":
        if not verify_totp_code(mfa_settings.mfa_secret, code):
            # Log failed attempt
            attempt = MFAAttempt(
                user_id=user_id,
                attempt_type="totp",
                success=False
            )
            db.add(attempt)
            db.commit()
            raise HTTPException(400, "Invalid verification code")
    
    # Generate and store backup codes
    backup_codes = generate_backup_codes()
    hashed_codes = hash_backup_codes(backup_codes)
    
    # Enable MFA
    mfa_settings.mfa_enabled = True
    mfa_settings.backup_codes = hashed_codes
    mfa_settings.last_verified_at = datetime.utcnow()
    
    # Update user
    user = db.query(User).filter(User.id == user_id).first()
    user.require_mfa = True
    user.mfa_enforced_at = datetime.utcnow()
    
    # Log successful setup
    attempt = MFAAttempt(
        user_id=user_id,
        attempt_type=mfa_settings.mfa_type,
        success=True
    )
    db.add(attempt)
    
    db.commit()
    
    return {
        "message": "MFA enabled successfully",
        "backup_codes": backup_codes,  # Show once, user must save
        "warning": "Save backup codes securely. They will not be shown again."
    }

@app.post("/mfa/verify")
async def verify_mfa_code(
    code: str,
    use_backup: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Verify MFA code during login"""
    user_id = current_user["user_id"]
    
    mfa_settings = db.query(UserMFA).filter(
        UserMFA.user_id == user_id,
        UserMFA.mfa_enabled == True
    ).first()
    
    if not mfa_settings:
        raise HTTPException(400, "MFA not enabled for this user")
    
    success = False
    attempt_type = mfa_settings.mfa_type
    
    if use_backup:
        # Verify backup code
        success = verify_backup_code(mfa_settings.backup_codes, code)
        attempt_type = "backup_code"
        
        if success:
            # Remove used backup code
            updated_codes = [
                hashed for hashed in mfa_settings.backup_codes
                if not bcrypt.verify(code, hashed)
            ]
            mfa_settings.backup_codes = updated_codes
    else:
        # Verify TOTP
        if mfa_settings.mfa_type == "totp":
            success = verify_totp_code(mfa_settings.mfa_secret, code)
    
    # Log attempt
    attempt = MFAAttempt(
        user_id=user_id,
        attempt_type=attempt_type,
        success=success
    )
    db.add(attempt)
    
    if success:
        mfa_settings.last_verified_at = datetime.utcnow()
    
    db.commit()
    
    if not success:
        raise HTTPException(401, "Invalid MFA code")
    
    return {
        "verified": True,
        "message": "MFA verification successful"
    }

@app.post("/mfa/disable")
async def disable_mfa(
    password: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Disable MFA (requires password confirmation)"""
    user_id = current_user["user_id"]
    
    # Verify password
    user = db.query(User).filter(User.id == user_id).first()
    if not bcrypt.verify(password, user.password_hash):
        raise HTTPException(401, "Invalid password")
    
    # Disable MFA
    mfa_settings = db.query(UserMFA).filter(UserMFA.user_id == user_id).first()
    if mfa_settings:
        mfa_settings.mfa_enabled = False
        mfa_settings.backup_codes = []
        
    user.require_mfa = False
    
    db.commit()
    
    return {"message": "MFA disabled successfully"}

@app.get("/mfa/status")
async def get_mfa_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current MFA status for user"""
    mfa_settings = db.query(UserMFA).filter(
        UserMFA.user_id == current_user["user_id"]
    ).first()
    
    if not mfa_settings:
        return {
            "mfa_enabled": False,
            "mfa_type": None
        }
    
    return {
        "mfa_enabled": mfa_settings.mfa_enabled,
        "mfa_type": mfa_settings.mfa_type,
        "backup_codes_remaining": len(mfa_settings.backup_codes) if mfa_settings.backup_codes else 0,
        "last_verified": mfa_settings.last_verified_at.isoformat() if mfa_settings.last_verified_at else None
    }
```

#### Step 5: Update Login Flow for MFA

**File:** `backend/services/auth/main.py`

```python
@app.post("/login-with-mfa")
async def login_with_mfa(
    credentials: dict,
    mfa_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Enhanced login with MFA support
    
    Step 1: Verify email/password
    Step 2: If MFA enabled, require MFA code
    """
    email = credentials.get("email")
    password = credentials.get("password")
    
    # Step 1: Verify credentials
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.verify(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    # Check if MFA is required
    mfa_settings = db.query(UserMFA).filter(
        UserMFA.user_id == user.id,
        UserMFA.mfa_enabled == True
    ).first()
    
    if mfa_settings and not mfa_code:
        # Return indication that MFA is required
        return {
            "mfa_required": True,
            "mfa_type": mfa_settings.mfa_type,
            "message": "MFA code required to complete login"
        }
    
    if mfa_settings and mfa_code:
        # Verify MFA code
        if mfa_settings.mfa_type == "totp":
            if not verify_totp_code(mfa_settings.mfa_secret, mfa_code):
                raise HTTPException(401, "Invalid MFA code")
        
        mfa_settings.last_verified_at = datetime.utcnow()
        db.commit()
    
    # Generate JWT token
    token = create_access_token({"user_id": user.id, "email": user.email, "role": user.role})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }
```

#### Step 6: Test MFA

**Create:** `test_mfa.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

# Login
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Check MFA Status ==="
curl -s -X GET "$BASE_URL/auth/mfa/status" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Setup MFA (TOTP) ==="
MFA_SETUP=$(curl -s -X POST "$BASE_URL/auth/mfa/setup?mfa_type=totp" \
  -H "Authorization: Bearer $TOKEN")
echo "$MFA_SETUP" | jq

SECRET=$(echo "$MFA_SETUP" | jq -r '.secret')
echo "TOTP Secret: $SECRET"

echo -e "\n=== Generate TOTP Code (use authenticator app in real scenario) ==="
# In production, user would scan QR code with app
# For testing, you can use: python -c "import pyotp; print(pyotp.TOTP('$SECRET').now())"

echo -e "\n=== Verify and Enable MFA ==="
read -p "Enter TOTP code from authenticator app: " TOTP_CODE
BACKUP_CODES=$(curl -s -X POST "$BASE_URL/auth/mfa/verify-and-enable?code=$TOTP_CODE" \
  -H "Authorization: Bearer $TOKEN")
echo "$BACKUP_CODES" | jq

echo -e "\n=== MFA Status After Setup ==="
curl -s -X GET "$BASE_URL/auth/mfa/status" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] MFA tables created
- [ ] TOTP setup with QR code works
- [ ] MFA verification works
- [ ] Backup codes generated and usable
- [ ] MFA can be disabled
- [ ] Login flow integrates MFA
- [ ] Test script passes

---

## Task 5.2: Password Reset Flow

**Estimated Time:** 6-8 hours  
**Services:** Auth, Notification  
**Impact:** HIGH - Critical user feature

### Database Changes

```sql
\c athena
SET search_path TO auth, public;

CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  used BOOLEAN DEFAULT FALSE,
  used_at TIMESTAMP,
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reset_tokens_token ON password_reset_tokens(token) WHERE NOT used;
CREATE INDEX idx_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_tokens_expiry ON password_reset_tokens(expires_at) WHERE NOT used;
```

### Implementation Steps

#### Step 1: Create Reset Token Model

**File:** `backend/services/auth/models.py`

```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {'schema': 'auth'}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('auth.users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Step 2: Create Password Reset Endpoints

**File:** `backend/services/auth/main.py`

```python
import secrets
from datetime import timedelta

@app.post("/password-reset/request")
async def request_password_reset(
    email: str,
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    user = db.query(User).filter(User.email == email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If email exists, reset link has been sent"}
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store token
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    # Send email (integrate with notification service)
    reset_link = f"https://app.coachway.com/reset-password?token={token}"
    # notification_service.send_email(
    #     to=email,
    #     subject="Password Reset Request",
    #     body=f"Click here to reset your password: {reset_link}\nExpires in 1 hour."
    # )
    
    return {
        "message": "If email exists, reset link has been sent",
        "token": token  # Only for testing, remove in production
    }

@app.post("/password-reset/verify")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify if reset token is valid"""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(400, "Invalid or expired reset token")
    
    return {
        "valid": True,
        "expires_at": reset_token.expires_at.isoformat()
    }

@app.post("/password-reset/confirm")
async def confirm_password_reset(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    # Verify token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(400, "Invalid or expired reset token")
    
    # Update password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    user.password_hash = bcrypt.hash(new_password)
    user.updated_at = datetime.utcnow()
    
    # Mark token as used
    reset_token.used = True
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password reset successfully"}

@app.post("/password/change")
async def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Change password for logged-in user"""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    # Verify current password
    if not bcrypt.verify(current_password, user.password_hash):
        raise HTTPException(401, "Current password is incorrect")
    
    # Update password
    user.password_hash = bcrypt.hash(new_password)
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password changed successfully"}
```

#### Step 3: Test Password Reset

**Create:** `test_password_reset.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

echo "=== Request Password Reset ==="
RESET_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/password-reset/request?email=admin@example.com")
echo "$RESET_RESPONSE" | jq

TOKEN=$(echo "$RESET_RESPONSE" | jq -r '.token')
echo "Reset Token: $TOKEN"

echo -e "\n=== Verify Reset Token ==="
curl -s -X POST "$BASE_URL/auth/password-reset/verify?token=$TOKEN" | jq

echo -e "\n=== Confirm Password Reset ==="
curl -s -X POST "$BASE_URL/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN\",
    \"new_password\": \"newpassword123\"
  }" | jq

echo -e "\n=== Test Login with New Password ==="
curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"newpassword123"}' | jq
```

### Success Criteria

- [ ] Reset token table created
- [ ] Can request password reset
- [ ] Reset email sent (or logged)
- [ ] Can verify token validity
- [ ] Can reset password with token
- [ ] Token marked as used after reset
- [ ] Test script passes

---

## Task 5.3: Account Impersonation

**Estimated Time:** 4-6 hours  
**Services:** Auth  
**Impact:** MEDIUM - Support/debugging tool

### Database Changes

```sql
\c athena
SET search_path TO auth, public;

CREATE TABLE IF NOT EXISTS impersonation_sessions (
  id SERIAL PRIMARY KEY,
  admin_user_id INTEGER NOT NULL REFERENCES users(id),
  impersonated_user_id INTEGER NOT NULL REFERENCES users(id),
  reason TEXT NOT NULL,
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_impersonation_admin ON impersonation_sessions(admin_user_id);
CREATE INDEX idx_impersonation_user ON impersonation_sessions(impersonated_user_id);
CREATE INDEX idx_impersonation_active ON impersonation_sessions(is_active) WHERE is_active = TRUE;

-- Add impersonation audit
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_impersonated_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_impersonated_by INTEGER;
```

### Implementation Steps

#### Step 1: Create Impersonation Model

**File:** `backend/services/auth/models.py`

```python
class ImpersonationSession(Base):
    __tablename__ = "impersonation_sessions"
    __table_args__ = {'schema': 'auth'}
    
    id = Column(Integer, primary_key=True)
    admin_user_id = Column(Integer, ForeignKey('auth.users.id'), nullable=False)
    impersonated_user_id = Column(Integer, ForeignKey('auth.users.id'), nullable=False)
    reason = Column(Text, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

class User(Base):
    # ... existing fields ...
    
    last_impersonated_at = Column(DateTime)
    last_impersonated_by = Column(Integer)
```

#### Step 2: Create Impersonation Endpoints

**File:** `backend/services/auth/main.py`

```python
@app.post("/impersonate/{user_id}")
async def start_impersonation(
    user_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Start impersonating another user (admin only)"""
    if current_user["user_id"] == user_id:
        raise HTTPException(400, "Cannot impersonate yourself")
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(404, "User not found")
    
    # Create impersonation session
    session = ImpersonationSession(
        admin_user_id=current_user["user_id"],
        impersonated_user_id=user_id,
        reason=reason
    )
    db.add(session)
    
    # Update user record
    target_user.last_impersonated_at = datetime.utcnow()
    target_user.last_impersonated_by = current_user["user_id"]
    
    db.commit()
    db.refresh(session)
    
    # Generate impersonation token
    token_data = {
        "user_id": user_id,
        "email": target_user.email,
        "role": target_user.role,
        "impersonation_session_id": session.id,
        "impersonated_by": current_user["user_id"]
    }
    token = create_access_token(token_data)
    
    return {
        "impersonation_token": token,
        "session_id": session.id,
        "impersonated_user": {
            "id": target_user.id,
            "email": target_user.email,
            "full_name": target_user.full_name
        },
        "warning": "You are now impersonating this user. All actions will be logged."
    }

@app.post("/impersonate/end/{session_id}")
async def end_impersonation(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """End impersonation session"""
    session = db.query(ImpersonationSession).filter(
        ImpersonationSession.id == session_id,
        ImpersonationSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, "Active session not found")
    
    # Verify user is either admin who started it or the impersonated user
    if session.admin_user_id != current_user.get("impersonated_by", current_user["user_id"]):
        raise HTTPException(403, "Not authorized to end this session")
    
    session.is_active = False
    session.ended_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Impersonation session ended", "session_id": session_id}

@app.get("/impersonate/sessions")
async def list_impersonation_sessions(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """List impersonation sessions"""
    query = db.query(ImpersonationSession, User).join(
        User, ImpersonationSession.impersonated_user_id == User.id
    )
    
    if active_only:
        query = query.filter(ImpersonationSession.is_active == True)
    
    sessions = query.order_by(ImpersonationSession.started_at.desc()).limit(50).all()
    
    return {
        "sessions": [
            {
                "session_id": session.id,
                "admin_user_id": session.admin_user_id,
                "impersonated_user_id": user.id,
                "impersonated_user_email": user.email,
                "reason": session.reason,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "is_active": session.is_active
            }
            for session, user in sessions
        ]
    }
```

#### Step 3: Test Impersonation

**Create:** `test_impersonation.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

# Admin login
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Start Impersonation ==="
IMPERSONATE_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/impersonate/2?reason=Support%20ticket%20investigation" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
echo "$IMPERSONATE_RESPONSE" | jq

IMPERSONATE_TOKEN=$(echo "$IMPERSONATE_RESPONSE" | jq -r '.impersonation_token')
SESSION_ID=$(echo "$IMPERSONATE_RESPONSE" | jq -r '.session_id')

echo -e "\n=== Test Action as Impersonated User ==="
curl -s -X GET "$BASE_URL/sales/leads" \
  -H "Authorization: Bearer $IMPERSONATE_TOKEN" | jq -c '.[:2]'

echo -e "\n=== List Active Impersonation Sessions ==="
curl -s -X GET "$BASE_URL/auth/impersonate/sessions?active_only=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

echo -e "\n=== End Impersonation ==="
curl -s -X POST "$BASE_URL/auth/impersonate/end/$SESSION_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
```

### Success Criteria

- [ ] Impersonation session table created
- [ ] Can start impersonation (admin only)
- [ ] Impersonation token works
- [ ] Can end impersonation
- [ ] Sessions are logged
- [ ] Test script passes

---

## Phase 5 Completion Checklist

### Database Migrations
- [ ] MFA tables created
- [ ] Password reset tokens table created
- [ ] Impersonation sessions table created
- [ ] MFA fields added to users

### API Endpoints
- [ ] MFA setup (TOTP/SMS)
- [ ] MFA verification
- [ ] MFA enable/disable
- [ ] Password reset request
- [ ] Password reset confirm
- [ ] Password change
- [ ] Start/end impersonation
- [ ] List impersonation sessions

### Security Features
- [ ] TOTP QR code generation
- [ ] Backup codes
- [ ] Secure token generation
- [ ] Password hashing
- [ ] MFA audit logging

### Testing
- [ ] MFA workflow tested
- [ ] Password reset tested
- [ ] Impersonation tested
- [ ] All tests pass through Kong Gateway

### Documentation
- [ ] MFA setup guide
- [ ] Password reset flow
- [ ] Impersonation policy

---

## Next Steps

After Phase 5 completion:
1. Review security implementations
2. Proceed to [Phase 6: QuickBooks Integration](phase_6.md)
3. Update progress tracking

---

**Estimated Total Time:** 22-29 hours (2 weeks)  
**Priority:** 🟠 IMPORTANT - Critical security enhancements
