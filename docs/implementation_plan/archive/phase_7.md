# Phase 7: Dispatch & Notification Enhancements

**Duration:** 1-2 weeks  
**Priority:** 🟡 NICE TO HAVE  
**Goal:** Polish existing dispatch and notification features

---

## Overview

Enhancements to existing services:
- Driver recovery workflow improvements
- Charter splitting for multi-stage trips
- SMS preferences and opt-out management
- Email tracking and open rates
- Notification templates management

These are quality-of-life improvements to already-functional services.

---

## Task 7.1: Enhanced Recovery Workflow

**Estimated Time:** 6-8 hours  
**Services:** Dispatch  
**Impact:** MEDIUM - Improves dispatch efficiency

### Database Changes

```sql
\c athena
SET search_path TO dispatch, public;

-- Add recovery workflow fields
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS recovery_priority VARCHAR(20) DEFAULT 'normal';
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS estimated_recovery_time TIMESTAMP;
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS recovery_attempts INTEGER DEFAULT 0;
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS last_contact_at TIMESTAMP;
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS escalated BOOLEAN DEFAULT FALSE;
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS escalated_to INTEGER;
ALTER TABLE driver_recoveries ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP;

CREATE INDEX idx_recoveries_priority ON driver_recoveries(recovery_priority, status);
CREATE INDEX idx_recoveries_escalated ON driver_recoveries(escalated) WHERE escalated = TRUE;

-- Add constraint
ALTER TABLE driver_recoveries ADD CONSTRAINT valid_priority 
  CHECK (recovery_priority IN ('low', 'normal', 'high', 'critical'));
```

### Implementation Steps

#### Step 1: Update Recovery Model

**File:** `backend/services/dispatch/models.py`

```python
class DriverRecovery(Base):
    # ... existing fields ...
    
    recovery_priority = Column(String(20), default='normal')
    estimated_recovery_time = Column(DateTime)
    recovery_attempts = Column(Integer, default=0)
    last_contact_at = Column(DateTime)
    escalated = Column(Boolean, default=False)
    escalated_to = Column(Integer)
    escalated_at = Column(DateTime)
```

#### Step 2: Create Enhanced Recovery Endpoints

**File:** `backend/services/dispatch/main.py`

```python
@app.post("/recoveries/{recovery_id}/attempt-contact")
async def attempt_driver_contact(
    recovery_id: int,
    contact_method: str,  # call, sms, app_notification
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record contact attempt for recovery"""
    recovery = db.query(DriverRecovery).filter(DriverRecovery.id == recovery_id).first()
    if not recovery:
        raise HTTPException(404, "Recovery not found")
    
    recovery.recovery_attempts += 1
    recovery.last_contact_at = datetime.utcnow()
    
    # Auto-escalate after 3 failed attempts
    if recovery.recovery_attempts >= 3 and recovery.status == 'in_progress':
        recovery.recovery_priority = 'high'
        # TODO: Notify dispatch manager
    
    # Log the attempt
    event = DispatchEvent(
        charter_id=recovery.charter_id,
        driver_id=recovery.driver_id,
        event_type='recovery_contact_attempt',
        description=f"Contact attempt #{recovery.recovery_attempts} via {contact_method}",
        notes=notes
    )
    db.add(event)
    
    db.commit()
    db.refresh(recovery)
    
    return {
        "recovery_id": recovery_id,
        "attempts": recovery.recovery_attempts,
        "priority": recovery.recovery_priority,
        "last_contact": recovery.last_contact_at.isoformat()
    }

@app.post("/recoveries/{recovery_id}/escalate")
async def escalate_recovery(
    recovery_id: int,
    escalate_to_user_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("dispatcher"))
):
    """Escalate recovery to manager"""
    recovery = db.query(DriverRecovery).filter(DriverRecovery.id == recovery_id).first()
    if not recovery:
        raise HTTPException(404, "Recovery not found")
    
    recovery.escalated = True
    recovery.escalated_to = escalate_to_user_id
    recovery.escalated_at = datetime.utcnow()
    recovery.recovery_priority = 'critical'
    
    # Create event
    event = DispatchEvent(
        charter_id=recovery.charter_id,
        driver_id=recovery.driver_id,
        event_type='recovery_escalated',
        description=f"Recovery escalated to user {escalate_to_user_id}",
        notes=reason
    )
    db.add(event)
    
    # TODO: Send notification to manager
    
    db.commit()
    
    return {
        "recovery_id": recovery_id,
        "escalated": True,
        "escalated_to": escalate_to_user_id
    }

@app.get("/recoveries/dashboard")
async def get_recovery_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("dispatcher"))
):
    """Dashboard view of all active recoveries"""
    active_recoveries = db.query(DriverRecovery, Charter).join(
        Charter, DriverRecovery.charter_id == Charter.id
    ).filter(
        DriverRecovery.status.in_(['in_progress', 'pending'])
    ).order_by(
        DriverRecovery.recovery_priority.desc(),
        DriverRecovery.created_at
    ).all()
    
    # Group by priority
    dashboard = {
        "critical": [],
        "high": [],
        "normal": [],
        "low": []
    }
    
    for recovery, charter in active_recoveries:
        item = {
            "recovery_id": recovery.id,
            "charter_id": charter.id,
            "driver_id": recovery.driver_id,
            "reason": recovery.reason,
            "attempts": recovery.recovery_attempts,
            "last_contact": recovery.last_contact_at.isoformat() if recovery.last_contact_at else None,
            "escalated": recovery.escalated,
            "created_at": recovery.created_at.isoformat()
        }
        dashboard[recovery.recovery_priority].append(item)
    
    return {
        "summary": {
            "critical": len(dashboard["critical"]),
            "high": len(dashboard["high"]),
            "normal": len(dashboard["normal"]),
            "low": len(dashboard["low"]),
            "total": sum(len(v) for v in dashboard.values())
        },
        "recoveries": dashboard
    }
```

#### Step 3: Test Recovery Workflow

**Create:** `test_recovery_workflow.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create Recovery ==="
RECOVERY_ID=$(curl -s -X POST "$BASE_URL/dispatch/recoveries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 1,
    "driver_id": 101,
    "reason": "Driver not responding to dispatch"
  }' | jq -r '.recovery_id')

echo "Recovery ID: $RECOVERY_ID"

echo -e "\n=== Attempt Contact ==="
curl -s -X POST "$BASE_URL/dispatch/recoveries/$RECOVERY_ID/attempt-contact?contact_method=sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Sent SMS to driver"}' | jq

echo -e "\n=== Escalate Recovery ==="
curl -s -X POST "$BASE_URL/dispatch/recoveries/$RECOVERY_ID/escalate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "escalate_to_user_id": 2,
    "reason": "Driver not responding after 3 attempts"
  }' | jq

echo -e "\n=== Recovery Dashboard ==="
curl -s -X GET "$BASE_URL/dispatch/recoveries/dashboard" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Recovery priority fields added
- [ ] Contact attempts tracked
- [ ] Auto-escalation after 3 attempts
- [ ] Manual escalation works
- [ ] Recovery dashboard functional
- [ ] Test script passes

---

## Task 7.2: Charter Splitting

**Estimated Time:** 8-10 hours  
**Services:** Charter  
**Impact:** MEDIUM - For complex multi-leg trips

### Database Changes

```sql
\c athena
SET search_path TO charter, public;

-- Link charters for splits
ALTER TABLE charters ADD COLUMN IF NOT EXISTS parent_charter_id INTEGER REFERENCES charters(id);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS is_split_charter BOOLEAN DEFAULT FALSE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS split_sequence INTEGER;

CREATE INDEX idx_charters_parent ON charters(parent_charter_id) WHERE parent_charter_id IS NOT NULL;
CREATE INDEX idx_charters_split ON charters(is_split_charter) WHERE is_split_charter = TRUE;
```

### Implementation Steps

#### Step 1: Update Charter Model

**File:** `backend/services/charters/models.py`

```python
class Charter(Base):
    # ... existing fields ...
    
    parent_charter_id = Column(Integer, ForeignKey('charter.charters.id'))
    is_split_charter = Column(Boolean, default=False)
    split_sequence = Column(Integer)
    
    # Relationships
    parent_charter = relationship("Charter", remote_side=[id], backref="split_charters")
```

#### Step 2: Create Split Charter Endpoint

**File:** `backend/services/charters/main.py`

```python
@app.post("/charters/{charter_id}/split")
async def split_charter(
    charter_id: int,
    split_config: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Split charter into multiple legs
    
    Body: {
        "legs": [
            {
                "pickup_date": "2026-03-15",
                "pickup_time": "08:00",
                "pickup_location": "Hotel A",
                "dropoff_location": "Airport",
                "passenger_count": 50
            },
            {
                "pickup_date": "2026-03-15",
                "pickup_time": "18:00",
                "pickup_location": "Airport",
                "dropoff_location": "Hotel B",
                "passenger_count": 45
            }
        ]
    }
    """
    parent_charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not parent_charter:
        raise HTTPException(404, "Charter not found")
    
    if parent_charter.is_split_charter:
        raise HTTPException(400, "Cannot split an already-split charter")
    
    legs = split_config.get('legs', [])
    if len(legs) < 2:
        raise HTTPException(400, "Must have at least 2 legs to split")
    
    # Mark parent as split
    parent_charter.is_split_charter = True
    
    # Create child charters for each leg
    split_charters = []
    for idx, leg_data in enumerate(legs, start=1):
        # Clone parent charter
        child_charter_data = {
            column.name: getattr(parent_charter, column.name)
            for column in Charter.__table__.columns
            if column.name not in ['id', 'created_at', 'updated_at', 'parent_charter_id', 'is_split_charter', 'split_sequence']
        }
        
        # Override with leg-specific data
        child_charter_data.update(leg_data)
        child_charter_data['parent_charter_id'] = charter_id
        child_charter_data['is_split_charter'] = True
        child_charter_data['split_sequence'] = idx
        
        child_charter = Charter(**child_charter_data)
        db.add(child_charter)
        split_charters.append(child_charter)
    
    db.commit()
    
    return {
        "parent_charter_id": charter_id,
        "split_count": len(split_charters),
        "split_charters": [
            {
                "id": c.id,
                "sequence": c.split_sequence,
                "pickup_date": c.pickup_date.isoformat(),
                "pickup_location": c.pickup_location,
                "dropoff_location": c.dropoff_location
            }
            for c in split_charters
        ]
    }

@app.get("/charters/{charter_id}/split-charters")
async def get_split_charters(
    charter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all split charters for a parent charter"""
    parent_charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not parent_charter:
        raise HTTPException(404, "Charter not found")
    
    if not parent_charter.is_split_charter:
        return {
            "parent_charter_id": charter_id,
            "is_split": False,
            "split_charters": []
        }
    
    # Get child charters
    children = db.query(Charter).filter(
        Charter.parent_charter_id == charter_id
    ).order_by(Charter.split_sequence).all()
    
    return {
        "parent_charter_id": charter_id,
        "is_split": True,
        "split_count": len(children),
        "split_charters": [
            {
                "id": c.id,
                "sequence": c.split_sequence,
                "pickup_date": c.pickup_date.isoformat(),
                "pickup_time": c.pickup_time,
                "pickup_location": c.pickup_location,
                "dropoff_location": c.dropoff_location,
                "status": c.status,
                "total_cost": float(c.total_cost) if c.total_cost else 0
            }
            for c in children
        ]
    }
```

#### Step 3: Test Charter Splitting

**Create:** `test_charter_splitting.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Split Charter into Legs ==="
curl -s -X POST "$BASE_URL/charters/charters/1/split" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "legs": [
      {
        "pickup_date": "2026-03-15",
        "pickup_time": "08:00",
        "pickup_location": "Downtown Hotel",
        "dropoff_location": "Airport Terminal A",
        "passenger_count": 50
      },
      {
        "pickup_date": "2026-03-15",
        "pickup_time": "18:00",
        "pickup_location": "Airport Terminal B",
        "dropoff_location": "Resort Hotel",
        "passenger_count": 48
      }
    ]
  }' | jq

echo -e "\n=== Get Split Charters ==="
curl -s -X GET "$BASE_URL/charters/charters/1/split-charters" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Split charter fields added
- [ ] Can split charter into multiple legs
- [ ] Parent-child relationship maintained
- [ ] Can list split charters
- [ ] Test script passes

---

## Task 7.3: SMS Preferences & Opt-Out

**Estimated Time:** 4-6 hours  
**Services:** Notification  
**Impact:** MEDIUM - Legal compliance

### Database Changes

```sql
\c athena
SET search_path TO notification, public;

CREATE TABLE IF NOT EXISTS sms_preferences (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(20) UNIQUE NOT NULL,
  opted_out BOOLEAN DEFAULT FALSE,
  opted_out_at TIMESTAMP,
  opt_out_reason VARCHAR(255),
  preferences JSONB DEFAULT '{}',  -- marketing, transactional, reminders
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sms_prefs_phone ON sms_preferences(phone_number);
CREATE INDEX idx_sms_prefs_opted_out ON sms_preferences(opted_out) WHERE opted_out = TRUE;

-- Track sent messages
ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS recipient_opted_out BOOLEAN DEFAULT FALSE;
```

### Implementation Steps

#### Step 1: Create SMS Preferences Model

**File:** `backend/services/notifications/models.py`

```python
from sqlalchemy.dialects.postgresql import JSONB

class SMSPreference(Base):
    __tablename__ = "sms_preferences"
    __table_args__ = {'schema': 'notification'}
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    opted_out = Column(Boolean, default=False)
    opted_out_at = Column(DateTime)
    opt_out_reason = Column(String(255))
    preferences = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Step 2: Create SMS Preference Endpoints

**File:** `backend/services/notifications/main.py`

```python
@app.post("/sms/opt-out")
async def sms_opt_out(
    phone_number: str,
    reason: Optional[str] = "User request",
    db: Session = Depends(get_db)
):
    """Opt-out from SMS notifications"""
    # Normalize phone number
    phone = phone_number.strip().replace("-", "").replace(" ", "")
    
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if preference:
        preference.opted_out = True
        preference.opted_out_at = datetime.utcnow()
        preference.opt_out_reason = reason
    else:
        preference = SMSPreference(
            phone_number=phone,
            opted_out=True,
            opted_out_at=datetime.utcnow(),
            opt_out_reason=reason
        )
        db.add(preference)
    
    db.commit()
    
    return {
        "phone_number": phone,
        "opted_out": True,
        "message": "Successfully opted out of SMS notifications"
    }

@app.post("/sms/opt-in")
async def sms_opt_in(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Opt-in to SMS notifications"""
    phone = phone_number.strip().replace("-", "").replace(" ", "")
    
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if preference:
        preference.opted_out = False
        preference.opted_out_at = None
        preference.opt_out_reason = None
    else:
        preference = SMSPreference(
            phone_number=phone,
            opted_out=False
        )
        db.add(preference)
    
    db.commit()
    
    return {
        "phone_number": phone,
        "opted_out": False,
        "message": "Successfully opted in to SMS notifications"
    }

@app.get("/sms/check-opt-out/{phone_number}")
async def check_sms_opt_out(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if phone number has opted out"""
    phone = phone_number.strip().replace("-", "").replace(" ", "")
    
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if not preference:
        return {"phone_number": phone, "opted_out": False}
    
    return {
        "phone_number": phone,
        "opted_out": preference.opted_out,
        "opted_out_at": preference.opted_out_at.isoformat() if preference.opted_out_at else None,
        "reason": preference.opt_out_reason
    }

# Update send_sms to check opt-out
@app.post("/sms/send")
async def send_sms_enhanced(
    notification: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send SMS with opt-out check"""
    phone = notification['to'].strip().replace("-", "").replace(" ", "")
    
    # Check opt-out status
    preference = db.query(SMSPreference).filter(
        SMSPreference.phone_number == phone
    ).first()
    
    if preference and preference.opted_out:
        # Log but don't send
        log = NotificationLog(
            notification_type='sms',
            recipient=phone,
            subject=notification.get('subject', ''),
            status='blocked',
            error_message='Recipient opted out',
            recipient_opted_out=True
        )
        db.add(log)
        db.commit()
        
        return {
            "message": "SMS blocked - recipient opted out",
            "opted_out": True
        }
    
    # Send SMS (existing logic)
    # ...
    
    return {"message": "SMS sent successfully"}
```

#### Step 3: Test SMS Preferences

**Create:** `test_sms_preferences.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

PHONE="+15555551234"

echo "=== Check Opt-Out Status ==="
curl -s -X GET "$BASE_URL/notifications/sms/check-opt-out/$PHONE" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Opt-Out from SMS ==="
curl -s -X POST "$BASE_URL/notifications/sms/opt-out?phone_number=$PHONE&reason=User%20request" | jq

echo -e "\n=== Verify Opt-Out ==="
curl -s -X GET "$BASE_URL/notifications/sms/check-opt-out/$PHONE" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Attempt to Send SMS (should be blocked) ==="
curl -s -X POST "$BASE_URL/notifications/sms/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"to\": \"$PHONE\",
    \"message\": \"Test message\"
  }" | jq

echo -e "\n=== Opt-In to SMS ==="
curl -s -X POST "$BASE_URL/notifications/sms/opt-in?phone_number=$PHONE" | jq
```

### Success Criteria

- [ ] SMS preferences table created
- [ ] Can opt-out from SMS
- [ ] Can opt-in to SMS
- [ ] SMS sending checks opt-out status
- [ ] Blocked messages logged
- [ ] Test script passes

---

## Task 7.4: Email Tracking & Analytics

**Estimated Time:** 6-8 hours  
**Services:** Notification  
**Impact:** LOW - Nice to have metrics

### Database Changes

```sql
\c athena
SET search_path TO notification, public;

CREATE TABLE IF NOT EXISTS email_tracking (
  id SERIAL PRIMARY KEY,
  notification_log_id INTEGER REFERENCES notification_logs(id) ON DELETE CASCADE,
  tracking_token VARCHAR(255) UNIQUE NOT NULL,
  opened BOOLEAN DEFAULT FALSE,
  opened_at TIMESTAMP,
  open_count INTEGER DEFAULT 0,
  clicked BOOLEAN DEFAULT FALSE,
  clicked_at TIMESTAMP,
  click_count INTEGER DEFAULT 0,
  user_agent TEXT,
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_email_tracking_token ON email_tracking(tracking_token);
CREATE INDEX idx_email_tracking_log ON email_tracking(notification_log_id);
CREATE INDEX idx_email_tracking_opened ON email_tracking(opened, opened_at);
```

### Implementation Overview

**File:** `backend/services/notifications/email_tracking.py` (New file)

```python
"""Email tracking - open and click tracking"""
import secrets
from fastapi.responses import Response

def generate_tracking_token() -> str:
    """Generate unique tracking token"""
    return secrets.token_urlsafe(32)

def inject_tracking_pixel(html_content: str, tracking_token: str, base_url: str) -> str:
    """Inject tracking pixel into HTML email"""
    tracking_url = f"{base_url}/api/v1/notifications/track/open/{tracking_token}"
    pixel = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" />'
    
    # Insert before closing body tag
    if '</body>' in html_content:
        return html_content.replace('</body>', f'{pixel}</body>')
    else:
        return html_content + pixel

# Tracking endpoints
@app.get("/track/open/{tracking_token}")
async def track_email_open(
    tracking_token: str,
    db: Session = Depends(get_db),
    request: Request
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
        tracking.ip_address = request.client.host
        tracking.user_agent = request.headers.get('user-agent')
        
        db.commit()
    
    # Return 1x1 transparent pixel
    pixel_data = bytes.fromhex('47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b')
    return Response(content=pixel_data, media_type="image/gif")

@app.get("/track/stats")
async def get_email_tracking_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
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
    
    return {
        "total_emails": total,
        "opened": opened,
        "clicked": clicked,
        "open_rate": (opened / total * 100) if total > 0 else 0,
        "click_rate": (clicked / total * 100) if total > 0 else 0
    }
```

### Success Criteria

- [ ] Email tracking table created
- [ ] Tracking pixel injected
- [ ] Open tracking works
- [ ] Click tracking works (optional)
- [ ] Analytics endpoint works

---

## Phase 7 Completion Checklist

### Database Migrations
- [ ] Recovery workflow fields added
- [ ] Charter split fields added
- [ ] SMS preferences table created
- [ ] Email tracking table created

### API Endpoints
- [ ] Enhanced recovery workflow
- [ ] Recovery dashboard
- [ ] Charter splitting
- [ ] SMS opt-out/opt-in
- [ ] SMS preference checking
- [ ] Email tracking pixel
- [ ] Email analytics

### Testing
- [ ] Recovery workflow tested
- [ ] Charter splitting tested
- [ ] SMS preferences tested
- [ ] Email tracking tested
- [ ] All tests pass through Kong Gateway

### Documentation
- [ ] Recovery procedures documented
- [ ] Charter splitting guide
- [ ] SMS compliance documented
- [ ] Email tracking explained

---

## Final Project Status

After Phase 7 completion:
- **Backend Services:** 100% complete
- **Total Implementation Time:** 348-476 hours (9-12 weeks)
- **Services Operational:** 13 backend services
- **API Endpoints:** 250+ endpoints
- **Test Coverage:** Comprehensive test suite
- **Documentation:** Complete implementation guides

**Next Steps:**
1. Begin frontend portal development
2. User acceptance testing
3. Production deployment planning

---

**Estimated Total Time:** 24-32 hours (1-2 weeks)  
**Priority:** 🟡 NICE TO HAVE - Polish and optimization
