# Phase 4: Manager/Config Tools

**Duration:** 1-2 weeks  
**Priority:** 🟠 IMPORTANT  
**Goal:** Build manager dashboards and configuration interfaces

---

## Overview

Managers need tools to:
- View cross-agent reports and performance
- Track Certificate of Insurance (COI) requirements
- Configure pricing modifiers and rules
- Manage lead queue distribution
- Set system-wide preferences

These tools enable operational oversight and system tuning.

---

## Task 4.1: Cross-Agent Performance Reports

**Estimated Time:** 12-18 hours  
**Services:** Analytics  
**Impact:** HIGH - Critical for management visibility

### Database Changes

```sql
-- No new tables needed, uses existing analytics service
-- Add materialized view for performance

\c athena
SET search_path TO analytics, public;

CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_summary AS
SELECT 
  u.id AS agent_id,
  u.full_name AS agent_name,
  COUNT(DISTINCT c.id) AS total_charters,
  COUNT(DISTINCT CASE WHEN c.status = 'completed' THEN c.id END) AS completed_charters,
  COUNT(DISTINCT CASE WHEN c.status = 'cancelled' THEN c.id END) AS cancelled_charters,
  COALESCE(SUM(CASE WHEN c.status = 'completed' THEN c.total_cost ELSE 0 END), 0) AS total_revenue,
  COALESCE(AVG(CASE WHEN c.status = 'completed' THEN c.total_cost END), 0) AS avg_charter_value,
  COUNT(DISTINCT l.id) AS total_leads,
  COUNT(DISTINCT CASE WHEN l.status = 'converted' THEN l.id END) AS converted_leads,
  CASE 
    WHEN COUNT(DISTINCT l.id) > 0 
    THEN COUNT(DISTINCT CASE WHEN l.status = 'converted' THEN l.id END)::FLOAT / COUNT(DISTINCT l.id) * 100
    ELSE 0 
  END AS conversion_rate,
  MAX(c.created_at) AS last_charter_date
FROM auth.users u
LEFT JOIN charter.charters c ON c.assigned_to = u.id
LEFT JOIN sales.leads l ON l.assigned_to = u.id
WHERE u.role IN ('agent', 'manager')
GROUP BY u.id, u.full_name;

CREATE INDEX idx_agent_perf_revenue ON agent_performance_summary(total_revenue DESC);
CREATE INDEX idx_agent_perf_conversion ON agent_performance_summary(conversion_rate DESC);

-- Refresh schedule (run daily via cron/airflow)
-- REFRESH MATERIALIZED VIEW agent_performance_summary;
```

### Implementation Steps

#### Step 1: Create Performance Endpoints

**File:** `backend/services/analytics/main.py`

```python
@app.get("/reports/agent-performance")
async def get_agent_performance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """
    Comprehensive agent performance report
    
    Metrics:
    - Total charters (completed, cancelled)
    - Revenue generated
    - Average charter value
    - Lead conversion rate
    - Follow-up completion rate
    """
    # Base query
    query = """
        SELECT 
            u.id AS agent_id,
            u.full_name AS agent_name,
            COUNT(DISTINCT c.id) AS total_charters,
            COUNT(DISTINCT CASE WHEN c.status = 'completed' THEN c.id END) AS completed_charters,
            COALESCE(SUM(CASE WHEN c.status = 'completed' THEN c.total_cost ELSE 0 END), 0) AS total_revenue,
            COUNT(DISTINCT l.id) AS total_leads,
            COUNT(DISTINCT CASE WHEN l.status = 'converted' THEN l.id END) AS converted_leads,
            COUNT(DISTINCT f.id) AS total_follow_ups,
            COUNT(DISTINCT CASE WHEN f.completed THEN f.id END) AS completed_follow_ups
        FROM auth.users u
        LEFT JOIN charter.charters c ON c.assigned_to = u.id
        LEFT JOIN sales.leads l ON l.assigned_to = u.id
        LEFT JOIN sales.follow_ups f ON f.assigned_to = u.id
        WHERE u.role IN ('agent', 'manager')
    """
    
    filters = []
    params = {}
    
    if agent_id:
        filters.append("u.id = :agent_id")
        params['agent_id'] = agent_id
    
    if start_date:
        filters.append("c.created_at >= :start_date")
        params['start_date'] = start_date
    
    if end_date:
        filters.append("c.created_at <= :end_date")
        params['end_date'] = end_date
    
    if filters:
        query += " AND " + " AND ".join(filters)
    
    query += " GROUP BY u.id, u.full_name ORDER BY total_revenue DESC"
    
    result = db.execute(text(query), params)
    agents = result.fetchall()
    
    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "agents": [
            {
                "agent_id": row.agent_id,
                "agent_name": row.agent_name,
                "charters": {
                    "total": row.total_charters,
                    "completed": row.completed_charters,
                    "revenue": float(row.total_revenue),
                    "avg_value": float(row.total_revenue / row.completed_charters) if row.completed_charters > 0 else 0
                },
                "leads": {
                    "total": row.total_leads,
                    "converted": row.converted_leads,
                    "conversion_rate": (row.converted_leads / row.total_leads * 100) if row.total_leads > 0 else 0
                },
                "follow_ups": {
                    "total": row.total_follow_ups,
                    "completed": row.completed_follow_ups,
                    "completion_rate": (row.completed_follow_ups / row.total_follow_ups * 100) if row.total_follow_ups > 0 else 0
                }
            }
            for row in agents
        ]
    }

@app.get("/reports/team-comparison")
async def get_team_comparison(
    metric: str = "revenue",  # revenue, charters, conversion_rate
    period: str = "month",  # week, month, quarter, year
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Compare agents by key metrics"""
    # Use materialized view for faster queries
    if metric == "revenue":
        query = """
            SELECT agent_id, agent_name, total_revenue AS value
            FROM analytics.agent_performance_summary
            ORDER BY total_revenue DESC
            LIMIT 10
        """
    elif metric == "charters":
        query = """
            SELECT agent_id, agent_name, completed_charters AS value
            FROM analytics.agent_performance_summary
            ORDER BY completed_charters DESC
            LIMIT 10
        """
    elif metric == "conversion_rate":
        query = """
            SELECT agent_id, agent_name, conversion_rate AS value
            FROM analytics.agent_performance_summary
            WHERE total_leads > 5
            ORDER BY conversion_rate DESC
            LIMIT 10
        """
    else:
        raise HTTPException(400, f"Invalid metric: {metric}")
    
    result = db.execute(text(query))
    rankings = result.fetchall()
    
    return {
        "metric": metric,
        "period": period,
        "rankings": [
            {
                "rank": idx + 1,
                "agent_id": row.agent_id,
                "agent_name": row.agent_name,
                "value": float(row.value)
            }
            for idx, row in enumerate(rankings)
        ]
    }

@app.get("/reports/agent-activity-timeline")
async def get_agent_activity_timeline(
    agent_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Get daily activity timeline for an agent"""
    start_date = date.today() - timedelta(days=days)
    
    # Aggregate activities by day
    query = """
        SELECT 
            DATE(activity_date) AS activity_day,
            activity_type,
            COUNT(*) AS count
        FROM (
            SELECT created_at AS activity_date, 'charter' AS activity_type
            FROM charter.charters
            WHERE assigned_to = :agent_id AND created_at >= :start_date
            
            UNION ALL
            
            SELECT created_at AS activity_date, 'lead' AS activity_type
            FROM sales.leads
            WHERE assigned_to = :agent_id AND created_at >= :start_date
            
            UNION ALL
            
            SELECT created_at AS activity_date, 'follow_up' AS activity_type
            FROM sales.follow_ups
            WHERE assigned_to = :agent_id AND created_at >= :start_date
        ) activities
        GROUP BY DATE(activity_date), activity_type
        ORDER BY activity_day, activity_type
    """
    
    result = db.execute(text(query), {"agent_id": agent_id, "start_date": start_date})
    activities = result.fetchall()
    
    # Organize by day
    timeline = {}
    for row in activities:
        day = row.activity_day.isoformat()
        if day not in timeline:
            timeline[day] = {}
        timeline[day][row.activity_type] = row.count
    
    return {
        "agent_id": agent_id,
        "period_days": days,
        "timeline": [
            {
                "date": day,
                "activities": data
            }
            for day, data in sorted(timeline.items())
        ]
    }

@app.post("/analytics/refresh-performance")
async def refresh_performance_cache(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Manually refresh agent performance materialized view"""
    db.execute(text("REFRESH MATERIALIZED VIEW analytics.agent_performance_summary"))
    db.commit()
    
    return {"message": "Performance cache refreshed", "timestamp": datetime.utcnow().isoformat()}
```

#### Step 2: Test Agent Performance Reports

**Create:** `test_agent_performance.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Agent Performance Report ==="
curl -s -X GET "$BASE_URL/analytics/reports/agent-performance?start_date=2026-01-01" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Team Comparison (Revenue) ==="
curl -s -X GET "$BASE_URL/analytics/reports/team-comparison?metric=revenue" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Team Comparison (Conversion Rate) ==="
curl -s -X GET "$BASE_URL/analytics/reports/team-comparison?metric=conversion_rate" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Agent Activity Timeline ==="
curl -s -X GET "$BASE_URL/analytics/reports/agent-activity-timeline?agent_id=1&days=30" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Refresh Performance Cache ==="
curl -s -X POST "$BASE_URL/analytics/analytics/refresh-performance" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Agent performance materialized view created
- [ ] Performance report endpoint works
- [ ] Team comparison works
- [ ] Activity timeline works
- [ ] Cache refresh works
- [ ] Test script passes

---

## Task 4.2: Certificate of Insurance (COI) Tracking

**Estimated Time:** 8-12 hours  
**Services:** Client  
**Impact:** HIGH - Legal/compliance requirement

### Database Changes

```sql
\c athena
SET search_path TO client, public;

CREATE TABLE IF NOT EXISTS client_insurance (
  id SERIAL PRIMARY KEY,
  client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  policy_type VARCHAR(100) NOT NULL,  -- general_liability, auto, workers_comp, umbrella
  insurance_company VARCHAR(255) NOT NULL,
  policy_number VARCHAR(100) NOT NULL,
  coverage_amount DECIMAL(12,2) NOT NULL,
  effective_date DATE NOT NULL,
  expiration_date DATE NOT NULL,
  certificate_holder VARCHAR(255),
  document_id INTEGER,  -- Reference to document service
  status VARCHAR(20) DEFAULT 'active',
  verified_by INTEGER,
  verified_at TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_insurance_status CHECK (status IN ('active', 'expired', 'pending_renewal', 'cancelled'))
);

CREATE INDEX idx_client_insurance_client ON client_insurance(client_id);
CREATE INDEX idx_client_insurance_expiration ON client_insurance(expiration_date);
CREATE INDEX idx_client_insurance_status ON client_insurance(status);

-- Alert for expiring insurance
CREATE INDEX idx_client_insurance_expiring ON client_insurance(expiration_date)
  WHERE status = 'active' AND expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days';

-- Add insurance required flag to clients
ALTER TABLE clients ADD COLUMN IF NOT EXISTS requires_insurance BOOLEAN DEFAULT FALSE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS min_coverage_amount DECIMAL(12,2) DEFAULT 1000000.00;
```

### Implementation Steps

#### Step 1: Create COI Models

**File:** `backend/services/clients/models.py`

```python
class ClientInsurance(Base):
    __tablename__ = "client_insurance"
    __table_args__ = {'schema': 'client'}
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client.clients.id'), nullable=False)
    policy_type = Column(String(100), nullable=False)
    insurance_company = Column(String(255), nullable=False)
    policy_number = Column(String(100), nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    certificate_holder = Column(String(255))
    document_id = Column(Integer)
    status = Column(String(20), default='active')
    verified_by = Column(Integer)
    verified_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Client(Base):
    # ... existing fields ...
    
    requires_insurance = Column(Boolean, default=False)
    min_coverage_amount = Column(Numeric(12, 2), default=1000000.00)
```

#### Step 2: Create COI Endpoints

**File:** `backend/services/clients/main.py`

```python
@app.post("/clients/{client_id}/insurance", response_model=dict)
async def add_client_insurance(
    client_id: int,
    insurance_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add insurance certificate for client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")
    
    insurance = ClientInsurance(
        client_id=client_id,
        **insurance_data
    )
    db.add(insurance)
    db.commit()
    db.refresh(insurance)
    
    return {
        "insurance_id": insurance.id,
        "client_id": client_id,
        "policy_type": insurance.policy_type,
        "expiration_date": insurance.expiration_date.isoformat(),
        "status": insurance.status
    }

@app.get("/clients/{client_id}/insurance", response_model=List[dict])
async def get_client_insurance(
    client_id: int,
    include_expired: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all insurance certificates for a client"""
    query = db.query(ClientInsurance).filter(ClientInsurance.client_id == client_id)
    
    if not include_expired:
        query = query.filter(ClientInsurance.status == 'active')
    
    certificates = query.order_by(ClientInsurance.expiration_date).all()
    
    return [
        {
            "id": cert.id,
            "policy_type": cert.policy_type,
            "insurance_company": cert.insurance_company,
            "policy_number": cert.policy_number,
            "coverage_amount": float(cert.coverage_amount),
            "expiration_date": cert.expiration_date.isoformat(),
            "status": cert.status,
            "days_until_expiration": (cert.expiration_date - date.today()).days
        }
        for cert in certificates
    ]

@app.get("/insurance/expiring", response_model=List[dict])
async def get_expiring_insurance(
    days_ahead: int = 60,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Get client insurance expiring soon"""
    expiring_date = date.today() + timedelta(days=days_ahead)
    
    certificates = db.query(ClientInsurance, Client).join(
        Client, ClientInsurance.client_id == Client.id
    ).filter(
        ClientInsurance.status == 'active',
        ClientInsurance.expiration_date <= expiring_date,
        ClientInsurance.expiration_date >= date.today()
    ).order_by(ClientInsurance.expiration_date).all()
    
    return [
        {
            "insurance_id": cert.id,
            "client_id": client.id,
            "client_name": client.name,
            "policy_type": cert.policy_type,
            "insurance_company": cert.insurance_company,
            "policy_number": cert.policy_number,
            "expiration_date": cert.expiration_date.isoformat(),
            "days_until_expiration": (cert.expiration_date - date.today()).days,
            "coverage_amount": float(cert.coverage_amount)
        }
        for cert, client in certificates
    ]

@app.post("/insurance/{insurance_id}/verify")
async def verify_insurance(
    insurance_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Mark insurance certificate as verified"""
    insurance = db.query(ClientInsurance).filter(ClientInsurance.id == insurance_id).first()
    if not insurance:
        raise HTTPException(404, "Insurance certificate not found")
    
    insurance.verified_by = current_user["user_id"]
    insurance.verified_at = datetime.utcnow()
    
    db.commit()
    return {"insurance_id": insurance_id, "verified": True}

@app.get("/charters/{charter_id}/insurance-compliance")
async def check_charter_insurance_compliance(
    charter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if client has valid insurance for charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(404, "Charter not found")
    
    client = db.query(Client).filter(Client.id == charter.client_id).first()
    
    # Check if insurance is required
    if not client.requires_insurance:
        return {
            "charter_id": charter_id,
            "insurance_required": False,
            "is_compliant": True,
            "message": "Insurance not required for this client"
        }
    
    # Check for valid general liability insurance
    valid_insurance = db.query(ClientInsurance).filter(
        ClientInsurance.client_id == client.id,
        ClientInsurance.policy_type == 'general_liability',
        ClientInsurance.status == 'active',
        ClientInsurance.expiration_date >= charter.pickup_date,
        ClientInsurance.coverage_amount >= client.min_coverage_amount
    ).first()
    
    is_compliant = valid_insurance is not None
    
    return {
        "charter_id": charter_id,
        "client_id": client.id,
        "insurance_required": True,
        "is_compliant": is_compliant,
        "min_coverage_required": float(client.min_coverage_amount),
        "valid_insurance": {
            "policy_number": valid_insurance.policy_number,
            "coverage_amount": float(valid_insurance.coverage_amount),
            "expiration_date": valid_insurance.expiration_date.isoformat()
        } if valid_insurance else None,
        "message": "Client has valid insurance" if is_compliant else "Client insurance missing or insufficient"
    }
```

#### Step 3: Test COI Tracking

**Create:** `test_coi_tracking.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Add Client Insurance ==="
curl -s -X POST "$BASE_URL/clients/clients/1/insurance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_type": "general_liability",
    "insurance_company": "State Farm",
    "policy_number": "GL-123456789",
    "coverage_amount": 2000000.00,
    "effective_date": "2026-01-01",
    "expiration_date": "2027-01-01",
    "certificate_holder": "CoachWay Transportation"
  }' | jq

echo -e "\n=== Get Client Insurance ==="
curl -s -X GET "$BASE_URL/clients/clients/1/insurance" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Get Expiring Insurance ==="
curl -s -X GET "$BASE_URL/clients/insurance/expiring?days_ahead=90" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Check Charter Insurance Compliance ==="
curl -s -X GET "$BASE_URL/clients/charters/1/insurance-compliance" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `client_insurance` table created
- [ ] Can add insurance certificates
- [ ] Can list client insurance
- [ ] Expiring insurance report works
- [ ] Charter compliance check works
- [ ] Test script passes

---

## Task 4.3: Pricing Configuration System

**Estimated Time:** 10-15 hours  
**Services:** Pricing  
**Impact:** MEDIUM - Dynamic pricing control

### Database Changes

```sql
\c athena
SET search_path TO pricing, public;

CREATE TABLE IF NOT EXISTS pricing_modifiers (
  id SERIAL PRIMARY KEY,
  modifier_name VARCHAR(100) NOT NULL,
  modifier_type VARCHAR(50) NOT NULL,  -- seasonal, day_of_week, time_of_day, distance, passenger_count
  condition_field VARCHAR(100),
  condition_operator VARCHAR(20),
  condition_value VARCHAR(255),
  adjustment_type VARCHAR(20) NOT NULL,  -- percentage, fixed_amount
  adjustment_value DECIMAL(10,2) NOT NULL,
  priority INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  valid_from DATE,
  valid_until DATE,
  notes TEXT,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_modifier_type CHECK (modifier_type IN ('seasonal', 'day_of_week', 'time_of_day', 'distance', 'passenger_count', 'event_type', 'custom')),
  CONSTRAINT valid_adjustment_type CHECK (adjustment_type IN ('percentage', 'fixed_amount'))
);

CREATE INDEX idx_pricing_modifiers_active ON pricing_modifiers(is_active, priority);
CREATE INDEX idx_pricing_modifiers_type ON pricing_modifiers(modifier_type);

-- Insert default modifiers
INSERT INTO pricing_modifiers (modifier_name, modifier_type, condition_field, condition_operator, condition_value, adjustment_type, adjustment_value, priority, created_by) VALUES
('Weekend Premium', 'day_of_week', 'day_of_week', 'in', 'saturday,sunday', 'percentage', 15.00, 10, 1),
('Holiday Premium', 'seasonal', 'is_holiday', 'equals', 'true', 'percentage', 25.00, 20, 1),
('Large Group Discount', 'passenger_count', 'passenger_count', 'greater_than', '50', 'percentage', -10.00, 5, 1),
('Long Distance Premium', 'distance', 'total_miles', 'greater_than', '200', 'percentage', 20.00, 8, 1);
```

### Implementation Steps

#### Step 1: Create Pricing Modifier Models

**File:** `backend/services/pricing/models.py`

```python
class PricingModifier(Base):
    __tablename__ = "pricing_modifiers"
    __table_args__ = {'schema': 'pricing'}
    
    id = Column(Integer, primary_key=True)
    modifier_name = Column(String(100), nullable=False)
    modifier_type = Column(String(50), nullable=False)
    condition_field = Column(String(100))
    condition_operator = Column(String(20))
    condition_value = Column(String(255))
    adjustment_type = Column(String(20), nullable=False)
    adjustment_value = Column(Numeric(10, 2), nullable=False)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_until = Column(Date)
    notes = Column(Text)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Step 2: Update Pricing Engine

**File:** `backend/services/pricing/engine.py`

```python
"""Enhanced pricing engine with modifiers"""
from sqlalchemy.orm import Session
from .models import PricingModifier
from datetime import date, datetime

def calculate_price_with_modifiers(base_price: float, charter_data: dict, db: Session) -> dict:
    """
    Calculate final price with all applicable modifiers
    
    Returns:
    {
        "base_price": float,
        "modifiers_applied": [{"name": str, "adjustment": float}],
        "total_adjustments": float,
        "final_price": float
    }
    """
    # Get all active modifiers
    modifiers = db.query(PricingModifier).filter(
        PricingModifier.is_active == True
    ).order_by(PricingModifier.priority.desc()).all()
    
    applied_modifiers = []
    total_adjustment = 0
    
    for modifier in modifiers:
        # Check date validity
        if modifier.valid_from and charter_data.get('pickup_date'):
            if charter_data['pickup_date'] < modifier.valid_from:
                continue
        if modifier.valid_until and charter_data.get('pickup_date'):
            if charter_data['pickup_date'] > modifier.valid_until:
                continue
        
        # Evaluate condition
        if evaluate_modifier_condition(charter_data, modifier):
            # Calculate adjustment
            if modifier.adjustment_type == 'percentage':
                adjustment = base_price * (modifier.adjustment_value / 100)
            else:  # fixed_amount
                adjustment = modifier.adjustment_value
            
            applied_modifiers.append({
                "name": modifier.modifier_name,
                "type": modifier.adjustment_type,
                "value": float(modifier.adjustment_value),
                "adjustment": float(adjustment)
            })
            total_adjustment += adjustment
    
    final_price = base_price + total_adjustment
    
    return {
        "base_price": base_price,
        "modifiers_applied": applied_modifiers,
        "total_adjustments": total_adjustment,
        "final_price": max(0, final_price)  # Never negative
    }

def evaluate_modifier_condition(charter_data: dict, modifier: PricingModifier) -> bool:
    """Check if charter matches modifier condition"""
    if not modifier.condition_field:
        return True  # No condition means always apply
    
    field_value = charter_data.get(modifier.condition_field)
    if field_value is None:
        return False
    
    operator = modifier.condition_operator
    condition_value = modifier.condition_value
    
    if operator == 'equals':
        return str(field_value) == condition_value
    elif operator == 'greater_than':
        return float(field_value) > float(condition_value)
    elif operator == 'less_than':
        return float(field_value) < float(condition_value)
    elif operator == 'in':
        values = condition_value.split(',')
        return str(field_value).lower() in [v.strip().lower() for v in values]
    elif operator == 'contains':
        return condition_value.lower() in str(field_value).lower()
    
    return False
```

#### Step 3: Create Modifier Management Endpoints

**File:** `backend/services/pricing/main.py`

```python
from .engine import calculate_price_with_modifiers

@app.get("/modifiers", response_model=List[dict])
async def list_pricing_modifiers(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """List all pricing modifiers"""
    query = db.query(PricingModifier)
    
    if is_active is not None:
        query = query.filter(PricingModifier.is_active == is_active)
    
    modifiers = query.order_by(PricingModifier.priority.desc()).all()
    
    return [
        {
            "id": m.id,
            "modifier_name": m.modifier_name,
            "modifier_type": m.modifier_type,
            "adjustment_type": m.adjustment_type,
            "adjustment_value": float(m.adjustment_value),
            "priority": m.priority,
            "is_active": m.is_active
        }
        for m in modifiers
    ]

@app.post("/modifiers", response_model=dict)
async def create_pricing_modifier(
    modifier_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Create new pricing modifier"""
    modifier = PricingModifier(
        **modifier_data,
        created_by=current_user["user_id"]
    )
    db.add(modifier)
    db.commit()
    db.refresh(modifier)
    
    return {
        "modifier_id": modifier.id,
        "modifier_name": modifier.modifier_name
    }

@app.patch("/modifiers/{modifier_id}", response_model=dict)
async def update_pricing_modifier(
    modifier_id: int,
    updates: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Update pricing modifier"""
    modifier = db.query(PricingModifier).filter(PricingModifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(404, "Modifier not found")
    
    for key, value in updates.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)
    
    modifier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(modifier)
    
    return {"modifier_id": modifier_id, "updated": True}

@app.delete("/modifiers/{modifier_id}")
async def delete_pricing_modifier(
    modifier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Delete pricing modifier"""
    modifier = db.query(PricingModifier).filter(PricingModifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(404, "Modifier not found")
    
    db.delete(modifier)
    db.commit()
    
    return {"modifier_id": modifier_id, "deleted": True}

@app.post("/calculate-with-modifiers")
async def calculate_price_with_modifiers_endpoint(
    charter_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate price with all modifiers applied
    
    Body: {
        "base_price": 1500.00,
        "pickup_date": "2026-03-15",
        "passenger_count": 55,
        "total_miles": 250,
        "event_type": "wedding",
        "day_of_week": "saturday"
    }
    """
    base_price = charter_data.get('base_price', 0)
    
    result = calculate_price_with_modifiers(base_price, charter_data, db)
    
    return result
```

#### Step 4: Test Pricing Configuration

**Create:** `test_pricing_config.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== List Pricing Modifiers ==="
curl -s -X GET "$BASE_URL/pricing/modifiers" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Create Custom Modifier ==="
curl -s -X POST "$BASE_URL/pricing/modifiers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "modifier_name": "Corporate Client Discount",
    "modifier_type": "custom",
    "adjustment_type": "percentage",
    "adjustment_value": -5.00,
    "priority": 15,
    "notes": "5% discount for corporate accounts"
  }' | jq

echo -e "\n=== Calculate Price with Modifiers ==="
curl -s -X POST "$BASE_URL/pricing/calculate-with-modifiers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_price": 2000.00,
    "pickup_date": "2026-03-15",
    "passenger_count": 60,
    "total_miles": 150,
    "event_type": "wedding",
    "day_of_week": "saturday"
  }' | jq
```

### Success Criteria

- [ ] `pricing_modifiers` table created
- [ ] Default modifiers inserted
- [ ] Can list/create/update modifiers
- [ ] Price calculation with modifiers works
- [ ] Modifiers applied in priority order
- [ ] Test script passes

---

## Phase 4 Completion Checklist

### Database Migrations
- [ ] Agent performance materialized view created
- [ ] Client insurance table created
- [ ] Pricing modifiers table created
- [ ] Insurance fields added to clients

### API Endpoints
- [ ] Agent performance reports
- [ ] Team comparison metrics
- [ ] Activity timeline
- [ ] COI management (CRUD)
- [ ] Expiring insurance report
- [ ] Charter insurance compliance check
- [ ] Pricing modifiers management
- [ ] Price calculation with modifiers

### Background Jobs
- [ ] Daily performance view refresh
- [ ] Insurance expiration notifications

### Testing
- [ ] Performance reports tested
- [ ] COI tracking tested
- [ ] Pricing modifiers tested
- [ ] All tests pass through Kong Gateway

### Documentation
- [ ] Manager reports documented
- [ ] COI requirements documented
- [ ] Pricing configuration documented

---

## Next Steps

After Phase 4 completion:
1. Review manager tools and configurations
2. Proceed to [Phase 5: Portal Security](phase_5.md)
3. Update progress tracking

---

**Estimated Total Time:** 30-45 hours (1-2 weeks)  
**Priority:** 🟠 IMPORTANT - Enables operational oversight
