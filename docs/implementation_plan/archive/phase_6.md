# Phase 6: QuickBooks Integration

**Duration:** 2-4 weeks  
**Priority:** 🟡 NICE TO HAVE  
**Goal:** Integrate with QuickBooks for accounting automation

---

## Overview

QuickBooks integration options:
1. **Export Only** (simpler, 1-2 weeks): Generate IIF files for manual import
2. **Full Sync** (complex, 3-4 weeks): OAuth2 + real-time bidirectional sync

This phase implements both approaches, starting with export for quick value.

---

## Task 6.1: QuickBooks Export (IIF Format)

**Estimated Time:** 8-12 hours  
**Services:** Payment, Analytics  
**Impact:** MEDIUM - Manual but functional

### Database Changes

```sql
\c athena
SET search_path TO analytics, public;

CREATE TABLE IF NOT EXISTS quickbooks_exports (
  id SERIAL PRIMARY KEY,
  export_type VARCHAR(50) NOT NULL,  -- invoices, payments, expenses, bills
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  record_count INTEGER NOT NULL,
  file_path VARCHAR(500),
  exported_by INTEGER NOT NULL,
  exported_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_export_type CHECK (export_type IN ('invoices', 'payments', 'expenses', 'bills'))
);

CREATE INDEX idx_qb_exports_type ON quickbooks_exports(export_type);
CREATE INDEX idx_qb_exports_date ON quickbooks_exports(exported_at DESC);
```

### Implementation Steps

#### Step 1: Create Export Model

**File:** `backend/services/analytics/models.py`

```python
class QuickBooksExport(Base):
    __tablename__ = "quickbooks_exports"
    __table_args__ = {'schema': 'analytics'}
    
    id = Column(Integer, primary_key=True)
    export_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    record_count = Column(Integer, nullable=False)
    file_path = Column(String(500))
    exported_by = Column(Integer, nullable=False)
    exported_at = Column(DateTime, default=datetime.utcnow)
```

#### Step 2: Create IIF Generator

**File:** `backend/services/analytics/quickbooks_iif.py` (New file)

```python
"""QuickBooks IIF (Intuit Interchange Format) generator"""
from typing import List, Dict
from datetime import date
from io import StringIO

class IIFGenerator:
    """Generate IIF files for QuickBooks import"""
    
    @staticmethod
    def generate_invoices_iif(invoices: List[Dict]) -> str:
        """
        Generate IIF file for customer invoices
        
        Format:
        !TRNS	TRNSID	TRNSTYPE	DATE	ACCNT	NAME	AMOUNT	DOCNUM	MEMO
        !SPL	SPLID	TRNSTYPE	DATE	ACCNT	NAME	AMOUNT	DOCNUM	MEMO
        !ENDTRNS
        """
        output = StringIO()
        
        # Header
        output.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\n")
        output.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\n")
        output.write("!ENDTRNS\n")
        
        # Transactions
        for invoice in invoices:
            trns_id = f"INV-{invoice['charter_id']}"
            date_str = invoice['pickup_date'].strftime('%m/%d/%Y')
            customer = invoice['client_name']
            amount = invoice['total_cost']
            doc_num = f"Charter-{invoice['charter_id']}"
            memo = f"Charter service on {date_str}"
            
            # Transaction line (debit accounts receivable)
            output.write(f"TRNS\t{trns_id}\tINVOICE\t{date_str}\tAccounts Receivable\t{customer}\t{amount:.2f}\t{doc_num}\t{memo}\n")
            
            # Split line (credit revenue account)
            output.write(f"SPL\t{trns_id}-1\tINVOICE\t{date_str}\tCharter Revenue\t{customer}\t-{amount:.2f}\t{doc_num}\t{memo}\n")
            
            output.write("ENDTRNS\n")
        
        return output.getvalue()
    
    @staticmethod
    def generate_payments_iif(payments: List[Dict]) -> str:
        """Generate IIF file for customer payments"""
        output = StringIO()
        
        # Header
        output.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\n")
        output.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\n")
        output.write("!ENDTRNS\n")
        
        for payment in payments:
            trns_id = f"PMT-{payment['id']}"
            date_str = payment['payment_date'].strftime('%m/%d/%Y')
            customer = payment['client_name']
            amount = payment['amount']
            method = payment['payment_method']
            memo = f"Payment via {method}"
            
            # Transaction line (debit cash/bank account)
            account = "Undeposited Funds" if method == "check" else "Checking Account"
            output.write(f"TRNS\t{trns_id}\tPAYMENT\t{date_str}\t{account}\t{customer}\t{amount:.2f}\t{trns_id}\t{memo}\n")
            
            # Split line (credit accounts receivable)
            output.write(f"SPL\t{trns_id}-1\tPAYMENT\t{date_str}\tAccounts Receivable\t{customer}\t-{amount:.2f}\t{trns_id}\t{memo}\n")
            
            output.write("ENDTRNS\n")
        
        return output.getvalue()
    
    @staticmethod
    def generate_vendor_bills_iif(bills: List[Dict]) -> str:
        """Generate IIF file for vendor bills"""
        output = StringIO()
        
        # Header
        output.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\n")
        output.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tDOCNUM\tMEMO\n")
        output.write("!ENDTRNS\n")
        
        for bill in bills:
            trns_id = f"BILL-{bill['id']}"
            date_str = bill['bill_date'].strftime('%m/%d/%Y')
            vendor = bill['vendor_name']
            amount = bill['amount']
            bill_num = bill['bill_number']
            memo = bill.get('notes', 'Vendor bill')
            
            # Transaction line (credit accounts payable)
            output.write(f"TRNS\t{trns_id}\tBILL\t{date_str}\tAccounts Payable\t{vendor}\t-{amount:.2f}\t{bill_num}\t{memo}\n")
            
            # Split line (debit expense account)
            output.write(f"SPL\t{trns_id}-1\tBILL\t{date_str}\tCharter Expenses\t{vendor}\t{amount:.2f}\t{bill_num}\t{memo}\n")
            
            output.write("ENDTRNS\n")
        
        return output.getvalue()
```

#### Step 3: Create Export Endpoints

**File:** `backend/services/analytics/main.py`

```python
from .quickbooks_iif import IIFGenerator
from fastapi.responses import StreamingResponse

@app.post("/quickbooks/export/invoices")
async def export_invoices_to_quickbooks(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Export invoices as QuickBooks IIF file"""
    # Get completed charters (invoices)
    query = """
        SELECT 
            c.id AS charter_id,
            c.pickup_date,
            c.total_cost,
            cl.name AS client_name
        FROM charter.charters c
        JOIN client.clients cl ON c.client_id = cl.id
        WHERE c.status = 'completed'
        AND c.pickup_date BETWEEN :start_date AND :end_date
        ORDER BY c.pickup_date
    """
    
    result = db.execute(text(query), {"start_date": start_date, "end_date": end_date})
    invoices = [dict(row) for row in result.fetchall()]
    
    if not invoices:
        raise HTTPException(404, "No invoices found in date range")
    
    # Generate IIF content
    iif_content = IIFGenerator.generate_invoices_iif(invoices)
    
    # Save export record
    export_record = QuickBooksExport(
        export_type='invoices',
        start_date=start_date,
        end_date=end_date,
        record_count=len(invoices),
        exported_by=current_user["user_id"]
    )
    db.add(export_record)
    db.commit()
    
    # Return as downloadable file
    filename = f"qb_invoices_{start_date}_{end_date}.iif"
    
    return StreamingResponse(
        iter([iif_content]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/quickbooks/export/payments")
async def export_payments_to_quickbooks(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Export customer payments as QuickBooks IIF file"""
    query = """
        SELECT 
            p.id,
            p.payment_date,
            p.amount,
            p.payment_method,
            cl.name AS client_name
        FROM payment.payments p
        JOIN charter.charters c ON p.charter_id = c.id
        JOIN client.clients cl ON c.client_id = cl.id
        WHERE p.status = 'completed'
        AND p.payment_type = 'receivable'
        AND p.payment_date BETWEEN :start_date AND :end_date
        ORDER BY p.payment_date
    """
    
    result = db.execute(text(query), {"start_date": start_date, "end_date": end_date})
    payments = [dict(row) for row in result.fetchall()]
    
    if not payments:
        raise HTTPException(404, "No payments found in date range")
    
    # Generate IIF content
    iif_content = IIFGenerator.generate_payments_iif(payments)
    
    # Save export record
    export_record = QuickBooksExport(
        export_type='payments',
        start_date=start_date,
        end_date=end_date,
        record_count=len(payments),
        exported_by=current_user["user_id"]
    )
    db.add(export_record)
    db.commit()
    
    filename = f"qb_payments_{start_date}_{end_date}.iif"
    
    return StreamingResponse(
        iter([iif_content]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/quickbooks/export/bills")
async def export_bills_to_quickbooks(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Export vendor bills as QuickBooks IIF file"""
    query = """
        SELECT 
            vb.id,
            vb.bill_date,
            vb.bill_number,
            vb.amount,
            vb.notes,
            v.name AS vendor_name
        FROM payment.vendor_bills vb
        JOIN vendor.vendors v ON vb.vendor_id = v.id
        WHERE vb.status IN ('approved', 'paid')
        AND vb.bill_date BETWEEN :start_date AND :end_date
        ORDER BY vb.bill_date
    """
    
    result = db.execute(text(query), {"start_date": start_date, "end_date": end_date})
    bills = [dict(row) for row in result.fetchall()]
    
    if not bills:
        raise HTTPException(404, "No bills found in date range")
    
    # Generate IIF content
    iif_content = IIFGenerator.generate_vendor_bills_iif(bills)
    
    # Save export record
    export_record = QuickBooksExport(
        export_type='bills',
        start_date=start_date,
        end_date=end_date,
        record_count=len(bills),
        exported_by=current_user["user_id"]
    )
    db.add(export_record)
    db.commit()
    
    filename = f"qb_bills_{start_date}_{end_date}.iif"
    
    return StreamingResponse(
        iter([iif_content]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/quickbooks/export/history")
async def get_export_history(
    export_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Get history of QuickBooks exports"""
    query = db.query(QuickBooksExport)
    
    if export_type:
        query = query.filter(QuickBooksExport.export_type == export_type)
    
    exports = query.order_by(QuickBooksExport.exported_at.desc()).limit(limit).all()
    
    return {
        "exports": [
            {
                "id": exp.id,
                "export_type": exp.export_type,
                "start_date": exp.start_date.isoformat(),
                "end_date": exp.end_date.isoformat(),
                "record_count": exp.record_count,
                "exported_at": exp.exported_at.isoformat()
            }
            for exp in exports
        ]
    }
```

#### Step 4: Test QuickBooks Export

**Create:** `test_quickbooks_export.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Export Invoices to QuickBooks ==="
curl -s -X POST "$BASE_URL/analytics/quickbooks/export/invoices?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/qb_invoices.iif

echo "File saved to /tmp/qb_invoices.iif"
head -20 /tmp/qb_invoices.iif

echo -e "\n=== Export Payments to QuickBooks ==="
curl -s -X POST "$BASE_URL/analytics/quickbooks/export/payments?start_date=2026-01-01&end_date=2026-01-31" \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/qb_payments.iif

echo "File saved to /tmp/qb_payments.iif"

echo -e "\n=== Export History ==="
curl -s -X GET "$BASE_URL/analytics/quickbooks/export/history" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] Export history table created
- [ ] IIF generator working
- [ ] Can export invoices
- [ ] Can export payments
- [ ] Can export vendor bills
- [ ] Files download correctly
- [ ] Export history tracked
- [ ] Test script passes

---

## Task 6.2: QuickBooks OAuth Integration (Optional - Full Sync)

**Estimated Time:** 20-30 hours  
**Services:** Analytics (new QB service)  
**Impact:** HIGH if implemented - Real-time sync

### Prerequisites

```bash
# Install QuickBooks SDK
pip install intuitlib
pip install python-quickbooks
```

### Database Changes

```sql
\c athena
SET search_path TO analytics, public;

CREATE TABLE IF NOT EXISTS quickbooks_config (
  id SERIAL PRIMARY KEY,
  company_id VARCHAR(100) UNIQUE NOT NULL,
  realm_id VARCHAR(100) NOT NULL,
  access_token TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  token_expires_at TIMESTAMP NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  connected_at TIMESTAMP DEFAULT NOW(),
  last_sync_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quickbooks_sync_log (
  id SERIAL PRIMARY KEY,
  sync_type VARCHAR(50) NOT NULL,  -- invoice, payment, bill, customer, vendor
  direction VARCHAR(20) NOT NULL,  -- to_qb, from_qb
  entity_id INTEGER NOT NULL,
  qb_entity_id VARCHAR(100),
  status VARCHAR(20) NOT NULL,  -- success, failed, skipped
  error_message TEXT,
  synced_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_qb_sync_log_type ON quickbooks_sync_log(sync_type, synced_at DESC);
CREATE INDEX idx_qb_sync_log_entity ON quickbooks_sync_log(sync_type, entity_id);
```

### Implementation Overview

**File:** `backend/services/analytics/quickbooks_sync.py` (New file)

```python
"""QuickBooks Online API integration"""
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.customer import Customer
from quickbooks.objects.payment import Payment

class QuickBooksSync:
    """Handle QuickBooks OAuth and sync"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_client = None
        self.qb_client = None
    
    def get_authorization_url(self) -> str:
        """Get OAuth authorization URL for user to connect QuickBooks"""
        self.auth_client = AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            environment='production'  # or 'sandbox'
        )
        
        auth_url = self.auth_client.get_authorization_url(
            scopes=['com.intuit.quickbooks.accounting']
        )
        return auth_url
    
    def exchange_code_for_tokens(self, code: str, realm_id: str) -> dict:
        """Exchange authorization code for access/refresh tokens"""
        self.auth_client.get_bearer_token(code, realm_id=realm_id)
        
        return {
            'access_token': self.auth_client.access_token,
            'refresh_token': self.auth_client.refresh_token,
            'expires_at': self.auth_client.expires_in,
            'realm_id': realm_id
        }
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh expired access token"""
        self.auth_client.refresh(refresh_token=refresh_token)
        
        return {
            'access_token': self.auth_client.access_token,
            'refresh_token': self.auth_client.refresh_token,
            'expires_at': self.auth_client.expires_in
        }
    
    def initialize_client(self, access_token: str, realm_id: str):
        """Initialize QuickBooks API client"""
        self.qb_client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=self.auth_client.refresh_token,
            company_id=realm_id
        )
    
    def sync_invoice_to_qb(self, charter_data: dict) -> str:
        """Create invoice in QuickBooks"""
        # Create customer if not exists
        customer = Customer()
        customer.DisplayName = charter_data['client_name']
        customer.save(qb=self.qb_client)
        
        # Create invoice
        invoice = Invoice()
        invoice.CustomerRef = customer.to_ref()
        invoice.TxnDate = charter_data['pickup_date']
        invoice.DueDate = charter_data['due_date']
        
        # Add line items
        from quickbooks.objects.detailline import SalesItemLine
        line = SalesItemLine()
        line.Amount = charter_data['total_cost']
        line.Description = f"Charter service - {charter_data['event_type']}"
        invoice.Line.append(line)
        
        invoice.save(qb=self.qb_client)
        
        return invoice.Id
    
    def sync_payment_to_qb(self, payment_data: dict) -> str:
        """Record payment in QuickBooks"""
        payment = Payment()
        payment.TotalAmt = payment_data['amount']
        payment.TxnDate = payment_data['payment_date']
        # Link to invoice...
        
        payment.save(qb=self.qb_client)
        
        return payment.Id

# Endpoints for OAuth flow
@app.get("/quickbooks/connect")
async def connect_quickbooks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Initiate QuickBooks connection"""
    qb_sync = QuickBooksSync(
        client_id=settings.QB_CLIENT_ID,
        client_secret=settings.QB_CLIENT_SECRET,
        redirect_uri=settings.QB_REDIRECT_URI
    )
    
    auth_url = qb_sync.get_authorization_url()
    
    return {
        "authorization_url": auth_url,
        "message": "Redirect user to this URL to authorize QuickBooks"
    }

@app.get("/quickbooks/callback")
async def quickbooks_callback(
    code: str,
    realmId: str,
    db: Session = Depends(get_db)
):
    """Handle QuickBooks OAuth callback"""
    qb_sync = QuickBooksSync(
        client_id=settings.QB_CLIENT_ID,
        client_secret=settings.QB_CLIENT_SECRET,
        redirect_uri=settings.QB_REDIRECT_URI
    )
    
    tokens = qb_sync.exchange_code_for_tokens(code, realmId)
    
    # Store tokens in database
    config = QuickBooksConfig(
        company_id=realmId,
        realm_id=realmId,
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        token_expires_at=datetime.utcnow() + timedelta(seconds=tokens['expires_at'])
    )
    db.add(config)
    db.commit()
    
    return {
        "message": "QuickBooks connected successfully",
        "realm_id": realmId
    }

# NOTE: Full implementation requires:
# - Token refresh logic
# - Sync scheduler (celery/airflow)
# - Conflict resolution
# - Error handling & retry logic
# - Webhook support for real-time updates
```

### Full Sync Success Criteria

- [ ] OAuth flow working
- [ ] Tokens stored securely
- [ ] Token refresh working
- [ ] Can sync invoices to QB
- [ ] Can sync payments to QB
- [ ] Can sync customers/vendors
- [ ] Sync logs maintained
- [ ] Error handling robust

---

## Phase 6 Completion Checklist

### Database Migrations
- [ ] Export history table created
- [ ] QB config table created (if full sync)
- [ ] Sync log table created (if full sync)

### Export Features
- [ ] IIF generator for invoices
- [ ] IIF generator for payments
- [ ] IIF generator for bills
- [ ] Export history tracking
- [ ] File download working

### Full Sync Features (Optional)
- [ ] OAuth flow implemented
- [ ] Token management
- [ ] Invoice sync
- [ ] Payment sync
- [ ] Customer sync
- [ ] Vendor sync

### Testing
- [ ] IIF files generate correctly
- [ ] Files import to QuickBooks
- [ ] OAuth flow tested (if implemented)
- [ ] All tests pass through Kong Gateway

### Documentation
- [ ] Export process documented
- [ ] QuickBooks import instructions
- [ ] OAuth setup guide (if implemented)
- [ ] Sync frequency and limitations

---

## Next Steps

After Phase 6 completion:
1. Test QuickBooks integration
2. Proceed to [Phase 7: Dispatch & Notification Enhancements](phase_7.md)
3. Update progress tracking

---

**Estimated Total Time:**  
- Export Only: 8-12 hours (1-2 weeks)  
- Full Sync: 28-42 hours (3-4 weeks)

**Priority:** 🟡 NICE TO HAVE - Valuable but not critical
