# Phase 1: Financial Foundation

**Duration:** 3-4 weeks  
**Priority:** 🔴 CRITICAL  
**Goal:** Complete AR/AP tracking, profit reporting, and financial workflows

---

## Overview

Financial tracking is the most requested and highest-value missing capability. This phase implements:

- AR/AP aging reports (30/60/90/120 days)
- Vendor bills management with approval workflow
- Profit tracking per charter and agent
- Multi-charter payment application
- PO & check tracking
- Cancellation fees

All features will be added to existing Payment, Charter, and Analytics services.

---

## Task 1.1: AR/AP Aging Reports

**Estimated Time:** 20-25 hours  
**Services:** Payment, Analytics  
**Impact:** HIGH - Cannot track overdue payments without this

### Database Changes

```sql
-- Connect to payment schema
\c athena
SET search_path TO payment, public;

-- Add aging tracking to payments
ALTER TABLE payments ADD COLUMN IF NOT EXISTS due_date DATE;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS aging_days INTEGER GENERATED ALWAYS AS 
  (CASE 
    WHEN status = 'pending' AND due_date IS NOT NULL 
    THEN EXTRACT(DAY FROM (CURRENT_DATE - due_date))::INTEGER 
    ELSE NULL 
  END) STORED;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS aging_bucket VARCHAR(10) GENERATED ALWAYS AS
  (CASE
    WHEN aging_days IS NULL THEN NULL
    WHEN aging_days <= 30 THEN '0-30'
    WHEN aging_days <= 60 THEN '31-60'
    WHEN aging_days <= 90 THEN '61-90'
    ELSE '90+'
  END) STORED;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_payments_aging ON payments(aging_bucket, status) 
  WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_payments_due_date ON payments(due_date) 
  WHERE due_date IS NOT NULL;
```

### Implementation Steps

#### Step 1: Update Payment Models

**File:** `backend/services/payments/models.py`

```python
# Add to Payment model
class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {'schema': 'payment'}
    
    # ... existing fields ...
    
    # New fields for aging
    due_date = Column(Date, nullable=True)
    # aging_days and aging_bucket are generated columns (defined in SQL above)
```

#### Step 2: Update Payment Schemas

**File:** `backend/services/payments/schemas.py`

```python
from typing import Optional
from datetime import date

class PaymentCreate(BaseModel):
    # ... existing fields ...
    due_date: Optional[date] = None

class PaymentResponse(BaseModel):
    # ... existing fields ...
    due_date: Optional[date] = None
    aging_days: Optional[int] = None
    aging_bucket: Optional[str] = None
```

#### Step 3: Create AR Aging Report Endpoint

**File:** `backend/services/payments/main.py`

```python
from sqlalchemy import func, case
from datetime import datetime, timedelta

@app.get("/reports/ar-aging")
async def get_ar_aging_report(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    AR Aging Report - Outstanding receivables by aging bucket
    
    Returns breakdown of unpaid client payments by age:
    - 0-30 days
    - 31-60 days
    - 61-90 days
    - 90+ days
    """
    as_of = as_of_date or date.today()
    
    # Query payments by aging bucket
    aging_query = db.query(
        Payment.aging_bucket,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total_amount'),
        func.array_agg(Payment.charter_id).label('charter_ids')
    ).filter(
        Payment.status == 'pending',
        Payment.payment_type == 'receivable',  # From clients
        Payment.due_date <= as_of
    ).group_by(Payment.aging_bucket).all()
    
    # Format response
    aging_summary = []
    total_outstanding = 0
    
    for bucket, count, amount, charter_ids in aging_query:
        aging_summary.append({
            "aging_bucket": bucket or "current",
            "invoice_count": count,
            "total_amount": float(amount),
            "charter_ids": charter_ids
        })
        total_outstanding += float(amount)
    
    # Get client breakdown
    client_breakdown = db.query(
        Charter.client_id,
        Client.name,
        func.sum(Payment.amount).label('total_owed'),
        func.min(Payment.due_date).label('oldest_due_date')
    ).join(
        Charter, Payment.charter_id == Charter.id
    ).join(
        Client, Charter.client_id == Client.id
    ).filter(
        Payment.status == 'pending',
        Payment.payment_type == 'receivable',
        Payment.due_date <= as_of
    ).group_by(
        Charter.client_id, Client.name
    ).order_by(
        func.sum(Payment.amount).desc()
    ).limit(20).all()
    
    return {
        "as_of_date": as_of.isoformat(),
        "total_outstanding": total_outstanding,
        "aging_breakdown": aging_summary,
        "top_clients": [
            {
                "client_id": client_id,
                "client_name": name,
                "amount_owed": float(total),
                "oldest_due_date": oldest.isoformat() if oldest else None
            }
            for client_id, name, total, oldest in client_breakdown
        ]
    }
```

#### Step 4: Create AP Aging Report Endpoint

**File:** `backend/services/payments/main.py`

```python
@app.get("/reports/ap-aging")
async def get_ap_aging_report(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    AP Aging Report - Outstanding payables to vendors by aging bucket
    
    Tracks what we owe vendors, organized by how overdue the payment is.
    """
    as_of = as_of_date or date.today()
    
    # Query vendor bills by aging bucket
    aging_query = db.query(
        VendorBill.aging_bucket,
        func.count(VendorBill.id).label('count'),
        func.sum(VendorBill.amount - VendorBill.paid_amount).label('total_owed'),
        func.array_agg(VendorBill.vendor_id).label('vendor_ids')
    ).filter(
        VendorBill.status.in_(['pending', 'approved', 'overdue']),
        VendorBill.due_date <= as_of
    ).group_by(VendorBill.aging_bucket).all()
    
    # Format response
    aging_summary = []
    total_payable = 0
    
    for bucket, count, amount, vendor_ids in aging_query:
        aging_summary.append({
            "aging_bucket": bucket or "current",
            "bill_count": count,
            "total_amount": float(amount),
            "unique_vendors": len(set(vendor_ids))
        })
        total_payable += float(amount)
    
    # Get vendor breakdown
    vendor_breakdown = db.query(
        Vendor.id,
        Vendor.name,
        func.sum(VendorBill.amount - VendorBill.paid_amount).label('total_owed'),
        func.count(VendorBill.id).label('bill_count'),
        func.min(VendorBill.due_date).label('oldest_due_date')
    ).join(
        VendorBill, Vendor.id == VendorBill.vendor_id
    ).filter(
        VendorBill.status.in_(['pending', 'approved', 'overdue']),
        VendorBill.due_date <= as_of
    ).group_by(
        Vendor.id, Vendor.name
    ).order_by(
        func.sum(VendorBill.amount - VendorBill.paid_amount).desc()
    ).limit(20).all()
    
    return {
        "as_of_date": as_of.isoformat(),
        "total_payable": total_payable,
        "aging_breakdown": aging_summary,
        "top_vendors": [
            {
                "vendor_id": vendor_id,
                "vendor_name": name,
                "amount_owed": float(total),
                "bill_count": count,
                "oldest_due_date": oldest.isoformat() if oldest else None
            }
            for vendor_id, name, total, count, oldest in vendor_breakdown
        ]
    }
```

#### Step 5: Test AR/AP Aging Reports

**Create:** `test_aging_reports.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

# Authenticate
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== AR Aging Report ==="
curl -s -X GET "$BASE_URL/payments/reports/ar-aging" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== AP Aging Report ==="
curl -s -X GET "$BASE_URL/payments/reports/ap-aging" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `due_date` field added to payments
- [ ] Generated columns (`aging_days`, `aging_bucket`) working
- [ ] AR aging report returns correct buckets
- [ ] AP aging report returns vendor payables
- [ ] Both reports accessible through Kong Gateway
- [ ] Test script passes

---

## Task 1.2: Vendor Bills Management

**Estimated Time:** 15-20 hours  
**Services:** Payment  
**Impact:** HIGH - Track what we owe vendors

### Database Changes

```sql
-- Connect to payment schema
\c athena
SET search_path TO payment, public;

CREATE TABLE IF NOT EXISTS vendor_bills (
  id SERIAL PRIMARY KEY,
  vendor_id INTEGER NOT NULL,
  charter_id INTEGER,
  bill_number VARCHAR(100) UNIQUE NOT NULL,
  bill_date DATE NOT NULL,
  due_date DATE NOT NULL,
  amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
  paid_amount DECIMAL(10,2) DEFAULT 0 CHECK (paid_amount >= 0),
  status VARCHAR(20) DEFAULT 'pending',
  -- pending, approved, paid, overdue, cancelled
  approval_status VARCHAR(20) DEFAULT 'pending',
  -- pending, approved, rejected
  approved_by INTEGER,
  approved_at TIMESTAMP,
  rejection_reason TEXT,
  notes TEXT,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Aging tracking
  aging_days INTEGER GENERATED ALWAYS AS 
    (CASE 
      WHEN status IN ('pending', 'approved', 'overdue') AND due_date IS NOT NULL
      THEN EXTRACT(DAY FROM (CURRENT_DATE - due_date))::INTEGER 
      ELSE NULL 
    END) STORED,
  aging_bucket VARCHAR(10) GENERATED ALWAYS AS
    (CASE
      WHEN aging_days IS NULL THEN NULL
      WHEN aging_days <= 30 THEN '0-30'
      WHEN aging_days <= 60 THEN '31-60'
      WHEN aging_days <= 90 THEN '61-90'
      ELSE '90+'
    END) STORED,
  
  -- Constraints
  CONSTRAINT amount_paid_check CHECK (paid_amount <= amount),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'paid', 'overdue', 'cancelled')),
  CONSTRAINT valid_approval_status CHECK (approval_status IN ('pending', 'approved', 'rejected'))
);

-- Indexes
CREATE INDEX idx_vendor_bills_vendor ON vendor_bills(vendor_id);
CREATE INDEX idx_vendor_bills_charter ON vendor_bills(charter_id);
CREATE INDEX idx_vendor_bills_status ON vendor_bills(status);
CREATE INDEX idx_vendor_bills_due_date ON vendor_bills(due_date);
CREATE INDEX idx_vendor_bills_aging ON vendor_bills(aging_bucket, status);

-- Trigger to auto-update status to overdue
CREATE OR REPLACE FUNCTION update_vendor_bill_overdue_status()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status IN ('pending', 'approved') AND NEW.due_date < CURRENT_DATE THEN
    NEW.status := 'overdue';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_vendor_bill_overdue
  BEFORE INSERT OR UPDATE ON vendor_bills
  FOR EACH ROW
  EXECUTE FUNCTION update_vendor_bill_overdue_status();
```

### Implementation Steps

#### Step 1: Create Vendor Bill Models

**File:** `backend/services/payments/models.py`

```python
class VendorBill(Base):
    __tablename__ = "vendor_bills"
    __table_args__ = {'schema': 'payment'}
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, nullable=False)
    charter_id = Column(Integer, nullable=True)
    bill_number = Column(String(100), unique=True, nullable=False)
    bill_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='pending')
    approval_status = Column(String(20), default='pending')
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Step 2: Create Vendor Bill Schemas

**File:** `backend/services/payments/schemas.py`

```python
from decimal import Decimal

class VendorBillCreate(BaseModel):
    vendor_id: int
    charter_id: Optional[int] = None
    bill_number: str
    bill_date: date
    due_date: date
    amount: Decimal
    notes: Optional[str] = None

class VendorBillUpdate(BaseModel):
    bill_date: Optional[date] = None
    due_date: Optional[date] = None
    amount: Optional[Decimal] = None
    notes: Optional[str] = None

class VendorBillResponse(BaseModel):
    id: int
    vendor_id: int
    charter_id: Optional[int]
    bill_number: str
    bill_date: date
    due_date: date
    amount: Decimal
    paid_amount: Decimal
    status: str
    approval_status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    aging_days: Optional[int]
    aging_bucket: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Step 3: Implement Vendor Bill CRUD Endpoints

**File:** `backend/services/payments/main.py`

```python
@app.post("/vendor-bills", response_model=VendorBillResponse)
async def create_vendor_bill(
    bill: VendorBillCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new vendor bill"""
    # Check if bill number already exists
    existing = db.query(VendorBill).filter(
        VendorBill.bill_number == bill.bill_number
    ).first()
    if existing:
        raise HTTPException(400, "Bill number already exists")
    
    db_bill = VendorBill(
        **bill.dict(),
        created_by=current_user["user_id"]
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill

@app.get("/vendor-bills", response_model=List[VendorBillResponse])
async def list_vendor_bills(
    vendor_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List vendor bills with optional filters"""
    query = db.query(VendorBill)
    
    if vendor_id:
        query = query.filter(VendorBill.vendor_id == vendor_id)
    if charter_id:
        query = query.filter(VendorBill.charter_id == charter_id)
    if status:
        query = query.filter(VendorBill.status == status)
    
    return query.order_by(VendorBill.due_date.desc()).all()

@app.get("/vendor-bills/{bill_id}", response_model=VendorBillResponse)
async def get_vendor_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get vendor bill by ID"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "Vendor bill not found")
    return bill

@app.post("/vendor-bills/{bill_id}/approve")
async def approve_vendor_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Approve vendor bill for payment"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "Vendor bill not found")
    
    if bill.approval_status != 'pending':
        raise HTTPException(400, "Bill already processed")
    
    bill.approval_status = 'approved'
    bill.approved_by = current_user["user_id"]
    bill.approved_at = datetime.utcnow()
    bill.status = 'approved'
    
    db.commit()
    db.refresh(bill)
    return bill

@app.post("/vendor-bills/{bill_id}/reject")
async def reject_vendor_bill(
    bill_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Reject vendor bill"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "Vendor bill not found")
    
    if bill.approval_status != 'pending':
        raise HTTPException(400, "Bill already processed")
    
    bill.approval_status = 'rejected'
    bill.rejection_reason = reason
    bill.status = 'cancelled'
    
    db.commit()
    return {"message": "Bill rejected", "bill_id": bill_id}

@app.post("/vendor-bills/{bill_id}/record-payment")
async def record_vendor_bill_payment(
    bill_id: int,
    payment_amount: Decimal,
    payment_date: date,
    payment_method: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record payment against vendor bill"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "Vendor bill not found")
    
    if bill.approval_status != 'approved':
        raise HTTPException(400, "Bill must be approved before payment")
    
    # Update paid amount
    new_paid_amount = bill.paid_amount + payment_amount
    if new_paid_amount > bill.amount:
        raise HTTPException(400, "Payment exceeds bill amount")
    
    bill.paid_amount = new_paid_amount
    
    # Update status
    if bill.paid_amount >= bill.amount:
        bill.status = 'paid'
    
    db.commit()
    db.refresh(bill)
    return bill
```

#### Step 4: Test Vendor Bills

**Create:** `test_vendor_bills.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

# Authenticate
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create Vendor Bill ==="
BILL_ID=$(curl -s -X POST "$BASE_URL/payments/vendor-bills" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": 1,
    "charter_id": 10,
    "bill_number": "VB-2026-001",
    "bill_date": "2026-02-01",
    "due_date": "2026-03-01",
    "amount": 2500.00,
    "notes": "Charter service for Feb 15 trip"
  }' | jq -r '.id')

echo "Bill ID: $BILL_ID"

echo -e "\n=== List Vendor Bills ==="
curl -s -X GET "$BASE_URL/payments/vendor-bills?vendor_id=1" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Approve Bill ==="
curl -s -X POST "$BASE_URL/payments/vendor-bills/$BILL_ID/approve" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Record Payment ==="
curl -s -X POST "$BASE_URL/payments/vendor-bills/$BILL_ID/record-payment" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_amount": 1000.00,
    "payment_date": "2026-02-15",
    "payment_method": "check"
  }' | jq
```

### Success Criteria

- [ ] `vendor_bills` table created
- [ ] CRUD endpoints working
- [ ] Approval workflow functional
- [ ] Payment recording works
- [ ] Aging calculations correct
- [ ] Test script passes through Kong

---

## Task 1.3: Profit Tracking

**Estimated Time:** 10-12 hours  
**Services:** Charter, Analytics  
**Impact:** HIGH - Required for reporting

### Database Changes

```sql
-- Connect to charter schema
\c athena
SET search_path TO charter, public;

ALTER TABLE charters ADD COLUMN IF NOT EXISTS cost_estimate DECIMAL(10,2) DEFAULT 0;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS actual_cost DECIMAL(10,2) DEFAULT 0;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS profit_amount DECIMAL(10,2) GENERATED ALWAYS AS 
  (total_cost - actual_cost) STORED;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS profit_margin DECIMAL(5,2) GENERATED ALWAYS AS 
  (CASE 
    WHEN total_cost > 0 THEN ((total_cost - actual_cost) / total_cost * 100)
    ELSE 0 
  END) STORED;

CREATE INDEX IF NOT EXISTS idx_charters_profit ON charters(profit_amount, profit_margin);
```

### Implementation Steps

#### Step 1: Update Charter Model

**File:** `backend/services/charters/models.py`

```python
class Charter(Base):
    # ... existing fields ...
    
    # Profit tracking
    cost_estimate = Column(Numeric(10, 2), default=0)
    actual_cost = Column(Numeric(10, 2), default=0)
    # profit_amount and profit_margin are generated columns
```

#### Step 2: Add Profit Endpoints to Analytics Service

**File:** `backend/services/analytics/main.py`

```python
@app.get("/profit/by-agent")
async def get_profit_by_agent(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Profit breakdown by sales agent"""
    query = db.query(
        Charter.assigned_to,
        User.full_name,
        func.count(Charter.id).label('total_charters'),
        func.sum(Charter.total_cost).label('total_revenue'),
        func.sum(Charter.actual_cost).label('total_cost'),
        func.sum(Charter.profit_amount).label('total_profit'),
        func.avg(Charter.profit_margin).label('avg_margin')
    ).join(
        User, Charter.assigned_to == User.id
    ).filter(
        Charter.status.in_(['completed', 'in_progress'])
    )
    
    if start_date:
        query = query.filter(Charter.pickup_date >= start_date)
    if end_date:
        query = query.filter(Charter.pickup_date <= end_date)
    
    query = query.group_by(
        Charter.assigned_to, User.full_name
    ).order_by(
        func.sum(Charter.profit_amount).desc()
    )
    
    results = query.all()
    
    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "agents": [
            {
                "agent_id": agent_id,
                "agent_name": name,
                "total_charters": count,
                "total_revenue": float(revenue),
                "total_cost": float(cost),
                "profit": float(profit),
                "avg_profit_margin": float(margin)
            }
            for agent_id, name, count, revenue, cost, profit, margin in results
        ]
    }

@app.get("/profit/by-month")
async def get_profit_by_month(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Monthly profit trends"""
    year = year or datetime.now().year
    
    query = db.query(
        func.date_trunc('month', Charter.pickup_date).label('month'),
        func.count(Charter.id).label('charter_count'),
        func.sum(Charter.total_cost).label('revenue'),
        func.sum(Charter.actual_cost).label('cost'),
        func.sum(Charter.profit_amount).label('profit')
    ).filter(
        func.extract('year', Charter.pickup_date) == year,
        Charter.status.in_(['completed', 'in_progress'])
    ).group_by(
        func.date_trunc('month', Charter.pickup_date)
    ).order_by(
        func.date_trunc('month', Charter.pickup_date)
    )
    
    results = query.all()
    
    return {
        "year": year,
        "months": [
            {
                "month": month.strftime('%Y-%m'),
                "charter_count": count,
                "revenue": float(revenue),
                "cost": float(cost),
                "profit": float(profit),
                "profit_margin": (float(profit) / float(revenue) * 100) if revenue > 0 else 0
            }
            for month, count, revenue, cost, profit in results
        ]
    }
```

#### Step 3: Test Profit Tracking

**Create:** `test_profit_tracking.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Update Charter with Costs ==="
curl -s -X PATCH "$BASE_URL/charters/charters/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_estimate": 2000.00,
    "actual_cost": 1800.00
  }' | jq '{id, total_cost, cost_estimate, actual_cost, profit_amount, profit_margin}'

echo -e "\n=== Profit by Agent ==="
curl -s -X GET "$BASE_URL/analytics/profit/by-agent?start_date=2026-01-01" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Profit by Month ==="
curl -s -X GET "$BASE_URL/analytics/profit/by-month?year=2026" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Profit fields added to charters
- [ ] Profit calculations working (generated columns)
- [ ] Profit by agent report functional
- [ ] Profit by month report functional
- [ ] Test script passes

---

## Task 1.4: Multi-Charter Payment Application

**Estimated Time:** 8-10 hours  
**Services:** Payment  
**Impact:** MEDIUM - Needed for bulk payments

### Database Changes

```sql
\c athena
SET search_path TO payment, public;

CREATE TABLE IF NOT EXISTS payment_allocations (
  id SERIAL PRIMARY KEY,
  payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
  charter_id INTEGER NOT NULL,
  allocated_amount DECIMAL(10,2) NOT NULL CHECK (allocated_amount > 0),
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_payment_charter UNIQUE (payment_id, charter_id)
);

CREATE INDEX idx_payment_allocations_payment ON payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_charter ON payment_allocations(charter_id);
```

### Implementation Steps

#### Step 1: Create Allocation Models

**File:** `backend/services/payments/models.py`

```python
class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"
    __table_args__ = {'schema': 'payment'}
    
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey('payment.payments.id'), nullable=False)
    charter_id = Column(Integer, nullable=False)
    allocated_amount = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Step 2: Create Allocation Endpoints

**File:** `backend/services/payments/main.py`

```python
@app.post("/payments/{payment_id}/allocate")
async def allocate_payment(
    payment_id: int,
    allocations: List[dict],  # [{"charter_id": 1, "amount": 500}, ...]
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Allocate a payment to multiple charters
    
    Body: [
        {"charter_id": 1, "allocated_amount": 500.00, "notes": "Partial payment"},
        {"charter_id": 2, "allocated_amount": 300.00}
    ]
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    
    # Validate total doesn't exceed payment amount
    total_allocated = sum(a['allocated_amount'] for a in allocations)
    if total_allocated > payment.amount:
        raise HTTPException(400, f"Total allocation ({total_allocated}) exceeds payment amount ({payment.amount})")
    
    # Create allocations
    created_allocations = []
    for alloc in allocations:
        db_alloc = PaymentAllocation(
            payment_id=payment_id,
            charter_id=alloc['charter_id'],
            allocated_amount=alloc['allocated_amount'],
            notes=alloc.get('notes')
        )
        db.add(db_alloc)
        created_allocations.append(db_alloc)
    
    db.commit()
    
    return {
        "payment_id": payment_id,
        "allocations_created": len(created_allocations),
        "total_allocated": float(total_allocated)
    }

@app.get("/payments/{payment_id}/allocations")
async def get_payment_allocations(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all allocations for a payment"""
    allocations = db.query(PaymentAllocation).filter(
        PaymentAllocation.payment_id == payment_id
    ).all()
    
    return {
        "payment_id": payment_id,
        "allocations": [
            {
                "charter_id": a.charter_id,
                "allocated_amount": float(a.allocated_amount),
                "notes": a.notes,
                "created_at": a.created_at.isoformat()
            }
            for a in allocations
        ]
    }

@app.get("/charters/{charter_id}/allocated-payments")
async def get_charter_allocated_payments(
    charter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payment allocations for a charter"""
    allocations = db.query(PaymentAllocation, Payment).join(
        Payment, PaymentAllocation.payment_id == Payment.id
    ).filter(
        PaymentAllocation.charter_id == charter_id
    ).all()
    
    return {
        "charter_id": charter_id,
        "total_allocated": sum(float(a.allocated_amount) for a, p in allocations),
        "payments": [
            {
                "payment_id": p.id,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "payment_method": p.payment_method,
                "allocated_amount": float(a.allocated_amount),
                "notes": a.notes
            }
            for a, p in allocations
        ]
    }
```

#### Step 3: Test Payment Allocation

**Create:** `test_payment_allocation.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create Payment ==="
PAYMENT_ID=$(curl -s -X POST "$BASE_URL/payments/payments/create-intent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.00,
    "payment_method": "check",
    "charter_id": null
  }' | jq -r '.id')

echo "Payment ID: $PAYMENT_ID"

echo -e "\n=== Allocate to Multiple Charters ==="
curl -s -X POST "$BASE_URL/payments/payments/$PAYMENT_ID/allocate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"charter_id": 1, "allocated_amount": 600.00, "notes": "Partial payment charter 1"},
    {"charter_id": 2, "allocated_amount": 400.00, "notes": "Full payment charter 2"}
  ]' | jq

echo -e "\n=== View Payment Allocations ==="
curl -s -X GET "$BASE_URL/payments/payments/$PAYMENT_ID/allocations" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== View Charter Allocated Payments ==="
curl -s -X GET "$BASE_URL/payments/charters/1/allocated-payments" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `payment_allocations` table created
- [ ] Can allocate payment to multiple charters
- [ ] Validation prevents over-allocation
- [ ] Can query allocations by payment
- [ ] Can query allocations by charter
- [ ] Test script passes

---

## Task 1.5: PO & Check Tracking

**Estimated Time:** 8-10 hours  
**Services:** Payment  
**Impact:** MEDIUM - Required for school/government clients

### Database Changes

```sql
\c athena
SET search_path TO payment, public;

ALTER TABLE payments ADD COLUMN IF NOT EXISTS po_number VARCHAR(100);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS check_number VARCHAR(100);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS expected_payment_date DATE;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS is_overdue BOOLEAN GENERATED ALWAYS AS 
  (status = 'pending' AND expected_payment_date IS NOT NULL AND expected_payment_date < CURRENT_DATE) STORED;

CREATE INDEX IF NOT EXISTS idx_payments_po ON payments(po_number) WHERE po_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payments_check ON payments(check_number) WHERE check_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payments_expected_date ON payments(expected_payment_date) WHERE expected_payment_date IS NOT NULL;
```

### Implementation Steps

#### Step 1: Update Payment Schemas

**File:** `backend/services/payments/schemas.py`

```python
class PaymentCreate(BaseModel):
    # ... existing fields ...
    po_number: Optional[str] = None
    check_number: Optional[str] = None
    expected_payment_date: Optional[date] = None

class PaymentResponse(BaseModel):
    # ... existing fields ...
    po_number: Optional[str] = None
    check_number: Optional[str] = None
    expected_payment_date: Optional[date] = None
    is_overdue: Optional[bool] = None
```

#### Step 2: Create PO/Check Report Endpoints

**File:** `backend/services/payments/main.py`

```python
@app.get("/reports/po-overdue")
async def get_overdue_pos(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get overdue PO payments"""
    overdue = db.query(Payment).filter(
        Payment.po_number.isnot(None),
        Payment.status == 'pending',
        Payment.is_overdue == True
    ).order_by(Payment.expected_payment_date).all()
    
    return {
        "count": len(overdue),
        "total_amount": sum(float(p.amount) for p in overdue),
        "overdue_pos": [
            {
                "payment_id": p.id,
                "po_number": p.po_number,
                "charter_id": p.charter_id,
                "amount": float(p.amount),
                "expected_date": p.expected_payment_date.isoformat(),
                "days_overdue": (date.today() - p.expected_payment_date).days
            }
            for p in overdue
        ]
    }

@app.get("/reports/checks-expected")
async def get_expected_checks(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get expected check payments within date range"""
    start = start_date or date.today()
    end = end_date or (date.today() + timedelta(days=7))
    
    expected = db.query(Payment).filter(
        Payment.payment_method == 'check',
        Payment.status == 'pending',
        Payment.expected_payment_date >= start,
        Payment.expected_payment_date <= end
    ).order_by(Payment.expected_payment_date).all()
    
    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat()
        },
        "count": len(expected),
        "total_amount": sum(float(p.amount) for p in expected),
        "expected_checks": [
            {
                "payment_id": p.id,
                "check_number": p.check_number,
                "charter_id": p.charter_id,
                "amount": float(p.amount),
                "expected_date": p.expected_payment_date.isoformat()
            }
            for p in expected
        ]
    }

@app.post("/payments/{payment_id}/mark-received")
async def mark_payment_received(
    payment_id: int,
    received_date: date,
    received_amount: Decimal,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark PO or check payment as received"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    
    if payment.status != 'pending':
        raise HTTPException(400, "Payment already processed")
    
    payment.status = 'completed'
    payment.payment_date = received_date
    payment.amount = received_amount  # Update if different
    if notes:
        payment.notes = notes
    
    db.commit()
    db.refresh(payment)
    
    return payment
```

#### Step 3: Test PO/Check Tracking

**Create:** `test_po_check_tracking.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create PO Payment ==="
PO_PAYMENT_ID=$(curl -s -X POST "$BASE_URL/payments/payments/create-intent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 10,
    "amount": 5000.00,
    "payment_method": "invoice",
    "po_number": "PO-2026-12345",
    "expected_payment_date": "2026-02-20"
  }' | jq -r '.id')

echo "PO Payment ID: $PO_PAYMENT_ID"

echo -e "\n=== Create Check Payment ==="
curl -s -X POST "$BASE_URL/payments/payments/create-intent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 11,
    "amount": 1500.00,
    "payment_method": "check",
    "check_number": "CHK-9876",
    "expected_payment_date": "2026-02-18"
  }' | jq

echo -e "\n=== Overdue POs ==="
curl -s -X GET "$BASE_URL/payments/reports/po-overdue" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Expected Checks ==="
curl -s -X GET "$BASE_URL/payments/reports/checks-expected?start_date=2026-02-01&end_date=2026-02-28" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Mark Payment Received ==="
curl -s -X POST "$BASE_URL/payments/payments/$PO_PAYMENT_ID/mark-received" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "received_date": "2026-02-20",
    "received_amount": 5000.00,
    "notes": "Check received via mail"
  }' | jq
```

### Success Criteria

- [ ] PO/check fields added to payments
- [ ] Overdue PO report working
- [ ] Expected checks report working
- [ ] Mark received endpoint working
- [ ] Test script passes

---

## Task 1.6: Cancellation Fees

**Estimated Time:** 6-8 hours  
**Services:** Charter  
**Impact:** MEDIUM - Track lost revenue

### Database Changes

```sql
\c athena
SET search_path TO charter, public;

ALTER TABLE charters ADD COLUMN IF NOT EXISTS cancellation_fee DECIMAL(10,2) DEFAULT 0;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS cancellation_date DATE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS cancel_fee_collected BOOLEAN DEFAULT FALSE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS cancelled_by INTEGER;

CREATE INDEX IF NOT EXISTS idx_charters_cancelled ON charters(status) WHERE status = 'cancelled';
```

### Implementation Steps

#### Step 1: Update Charter Model

**File:** `backend/services/charters/models.py`

```python
class Charter(Base):
    # ... existing fields ...
    
    # Cancellation tracking
    cancellation_fee = Column(Numeric(10, 2), default=0)
    cancellation_reason = Column(Text)
    cancellation_date = Column(Date)
    cancel_fee_collected = Column(Boolean, default=False)
    cancelled_by = Column(Integer)
```

#### Step 2: Create Cancellation Endpoint

**File:** `backend/services/charters/main.py`

```python
@app.post("/charters/{charter_id}/cancel")
async def cancel_charter(
    charter_id: int,
    reason: str,
    cancellation_fee: Decimal = 0,
    waive_fee: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a charter with optional cancellation fee
    
    Body: {
        "reason": "Client cancelled",
        "cancellation_fee": 500.00,
        "waive_fee": false
    }
    """
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(404, "Charter not found")
    
    if charter.status == 'cancelled':
        raise HTTPException(400, "Charter already cancelled")
    
    # Update charter
    charter.status = 'cancelled'
    charter.cancellation_date = date.today()
    charter.cancellation_reason = reason
    charter.cancelled_by = current_user["user_id"]
    
    if not waive_fee:
        charter.cancellation_fee = cancellation_fee
    else:
        charter.cancellation_fee = 0
    
    # Create change case for audit
    # (Assuming change_mgmt service integration)
    
    db.commit()
    db.refresh(charter)
    
    return {
        "charter_id": charter_id,
        "status": "cancelled",
        "cancellation_date": charter.cancellation_date.isoformat(),
        "cancellation_fee": float(charter.cancellation_fee),
        "reason": reason
    }

@app.get("/reports/cancellations")
async def get_cancellation_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancellation report with fee tracking"""
    query = db.query(Charter).filter(Charter.status == 'cancelled')
    
    if start_date:
        query = query.filter(Charter.cancellation_date >= start_date)
    if end_date:
        query = query.filter(Charter.cancellation_date <= end_date)
    
    cancelled = query.order_by(Charter.cancellation_date.desc()).all()
    
    total_fees = sum(float(c.cancellation_fee) for c in cancelled)
    fees_collected = sum(float(c.cancellation_fee) for c in cancelled if c.cancel_fee_collected)
    fees_uncollected = total_fees - fees_collected
    
    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "total_cancellations": len(cancelled),
        "total_fees": total_fees,
        "fees_collected": fees_collected,
        "fees_uncollected": fees_uncollected,
        "cancellations": [
            {
                "charter_id": c.id,
                "cancellation_date": c.cancellation_date.isoformat() if c.cancellation_date else None,
                "reason": c.cancellation_reason,
                "fee": float(c.cancellation_fee),
                "fee_collected": c.cancel_fee_collected,
                "original_value": float(c.total_cost)
            }
            for c in cancelled
        ]
    }
```

#### Step 3: Test Cancellation Fees

**Create:** `test_cancellation_fees.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Cancel Charter with Fee ==="
curl -s -X POST "$BASE_URL/charters/charters/1/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Client cancelled - weather concerns",
    "cancellation_fee": 500.00,
    "waive_fee": false
  }' | jq

echo -e "\n=== Cancellation Report ==="
curl -s -X GET "$BASE_URL/charters/reports/cancellations?start_date=2026-01-01" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Cancellation fields added to charters
- [ ] Cancel endpoint with fee calculation works
- [ ] Cancellation report functional
- [ ] Test script passes

---

## Phase 1 Completion Checklist

### Database Migrations
- [ ] Payment schema updated (due_date, aging fields)
- [ ] Vendor bills table created
- [ ] Charter schema updated (profit fields)
- [ ] Payment allocations table created
- [ ] PO/check tracking fields added
- [ ] Cancellation fields added

### API Endpoints
- [ ] AR aging report
- [ ] AP aging report
- [ ] Vendor bills CRUD
- [ ] Vendor bill approval workflow
- [ ] Profit by agent report
- [ ] Profit by month report
- [ ] Payment allocation endpoints
- [ ] PO/check tracking endpoints
- [ ] Cancellation with fees endpoint
- [ ] Cancellation report

### Testing
- [ ] All endpoints tested through Kong Gateway
- [ ] Test scripts created and passing
- [ ] Integration tests for cross-service workflows
- [ ] Error handling tested

### Documentation
- [ ] API endpoints documented
- [ ] Database schema documented
- [ ] Test examples provided
- [ ] README updated

---

## Next Steps

After Phase 1 completion:
1. Review and test all financial features
2. Proceed to [Phase 2: Charter Enhancements](phase_2.md)
3. Update implementation progress tracking

---

**Estimated Total Time:** 80-100 hours (3-4 weeks)  
**Priority:** 🔴 CRITICAL - Highest business value
