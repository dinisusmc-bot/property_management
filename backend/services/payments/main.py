from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text, func, Column, String, Integer
from typing import List, Optional
from datetime import date, datetime
from database import get_db, engine, Base
from models import Payment, PaymentSchedule, PaymentRefund, VendorBill, PaymentAllocation, SavedPaymentMethod
from schemas import (
    PaymentCreate, PaymentResponse, PaymentIntentCreate, 
    RefundCreate, RefundResponse, WebhookEvent,
    PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse, ChargePaymentMethodRequest
)
from payment_service import PaymentService
from webhook_handler import StripeWebhookHandler
from stripe_customer_service import StripeCustomerService
from config import settings

# Temporary Client model reference for cross-service queries
# In production, this should be done via API calls
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    name = Column(String)
    stripe_customer_id = Column(String(100))

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Service", version="1.0.0")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "payment"}

@app.post("/payments/create-intent", response_model=dict)
def create_payment_intent(payment_data: PaymentIntentCreate, db: Session = Depends(get_db)):
    """Create a Stripe PaymentIntent for a charter"""
    try:
        result = PaymentService.create_payment_intent(
            db=db,
            charter_id=payment_data.charter_id,
            amount=payment_data.amount,
            payment_type=payment_data.payment_type,
            description=payment_data.description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/charge-saved-card", response_model=PaymentResponse)
def charge_saved_card(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    """Charge a saved payment method (for automated payments)"""
    try:
        payment = PaymentService.charge_saved_card(
            db=db,
            charter_id=payment_data.charter_id,
            customer_id=payment_data.customer_id,
            payment_method_id=payment_data.payment_method_id,
            amount=payment_data.amount,
            payment_type=payment_data.payment_type
        )
        return payment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payments/charter/{charter_id}", response_model=List[PaymentResponse])
def get_charter_payments(charter_id: int, db: Session = Depends(get_db)):
    """Get all payments for a charter"""
    payments = db.query(Payment).filter(Payment.charter_id == charter_id).all()
    return payments

@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get payment details"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@app.post("/payments/refund", response_model=RefundResponse)
def create_refund(refund_data: RefundCreate, db: Session = Depends(get_db)):
    """Process a refund"""
    try:
        refund = PaymentService.create_refund(db=db, refund_data=refund_data)
        return refund
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payments/{payment_id}/refunds", response_model=List[RefundResponse])
def get_payment_refunds(payment_id: int, db: Session = Depends(get_db)):
    """Get all refunds for a payment"""
    refunds = db.query(PaymentRefund).filter(PaymentRefund.payment_id == payment_id).all()
    return refunds

@app.post("/payments/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    try:
        event = await StripeWebhookHandler.construct_event(request)
        event_type = event.get('type')
        data = event.get('data', {}).get('object', {})
        
        if event_type == 'payment_intent.succeeded':
            payment_intent_id = data.get('id')
            charge = data.get('charges', {}).get('data', [{}])[0]
            PaymentService.process_payment_succeeded(
                db=db,
                payment_intent_id=payment_intent_id,
                charge_data=charge
            )
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent_id = data.get('id')
            last_error = data.get('last_payment_error', {})
            PaymentService.process_payment_failed(
                db=db,
                payment_intent_id=payment_intent_id,
                failure_code=last_error.get('code'),
                failure_message=last_error.get('message')
            )
        
        elif event_type == 'charge.refunded':
            # Handle refund completed
            charge_id = data.get('id')
            payment = db.query(Payment).filter(
                Payment.stripe_charge_id == charge_id
            ).first()
            if payment:
                refunds = db.query(PaymentRefund).filter(
                    PaymentRefund.payment_id == payment.id
                ).all()
                for refund in refunds:
                    refund.status = "succeeded"
                db.commit()
        
        return {"status": "success"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payment-schedules/charter/{charter_id}")
def get_charter_payment_schedule(charter_id: int, db: Session = Depends(get_db)):
    """Get payment schedule for a charter"""
    schedules = db.query(PaymentSchedule).filter(
        PaymentSchedule.charter_id == charter_id
    ).order_by(PaymentSchedule.due_date).all()
    return schedules

@app.post("/payment-schedules")
def create_payment_schedule(schedule_data: dict, db: Session = Depends(get_db)):
    """Create payment schedule for a charter"""
    try:
        schedule = PaymentSchedule(**schedule_data)
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Phase 1.1: AR/AP Aging Reports
@app.get("/reports/ar-aging")
def get_ar_aging_report(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Accounts Receivable (AR) Aging Report
    Shows outstanding customer payments grouped by aging bucket
    """
    # Use today if not specified
    target_date = as_of_date or date.today()
    
    # Query for AR aging summary by bucket
    query = text("""
        WITH ar_payments AS (
            SELECT 
                p.id,
                p.charter_id,
                p.amount,
                p.due_date,
                p.aging_days,
                p.aging_bucket,
                p.created_at,
                c.client_id,
                cl.name as client_name
            FROM payments p
            JOIN charters c ON p.charter_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE p.payment_type = 'receivable'
            AND p.status != 'completed'
            AND p.due_date IS NOT NULL
        )
        SELECT 
            aging_bucket,
            COUNT(*) as invoice_count,
            SUM(amount) as total_amount,
            MIN(due_date) as oldest_due_date,
            MAX(due_date) as newest_due_date
        FROM ar_payments
        GROUP BY aging_bucket
        ORDER BY 
            CASE aging_bucket
                WHEN 'not_due' THEN 0
                WHEN '0-30' THEN 1
                WHEN '31-60' THEN 2
                WHEN '61-90' THEN 3
                WHEN '90+' THEN 4
                ELSE 5
            END
    """)
    
    result = db.execute(query)
    aging_summary = [
        {
            "aging_bucket": row[0],
            "invoice_count": row[1],
            "total_amount": float(row[2]) if row[2] else 0,
            "oldest_due_date": row[3].isoformat() if row[3] else None,
            "newest_due_date": row[4].isoformat() if row[4] else None
        }
        for row in result.fetchall()
    ]
    
    # Query for top 20 clients by amount owed
    top_clients_query = text("""
        WITH ar_payments AS (
            SELECT 
                p.charter_id,
                p.amount,
                p.due_date,
                p.aging_days,
                c.client_id,
                cl.name as client_name
            FROM payments p
            JOIN charters c ON p.charter_id = c.id
            JOIN clients cl ON c.client_id = cl.id
            WHERE p.payment_type = 'receivable'
            AND p.status != 'completed'
            AND p.due_date IS NOT NULL
        )
        SELECT 
            client_id,
            client_name,
            COUNT(*) as outstanding_invoices,
            SUM(amount) as total_owed,
            MIN(due_date) as oldest_due_date,
            MAX(aging_days) as max_days_overdue
        FROM ar_payments
        GROUP BY client_id, client_name
        ORDER BY total_owed DESC
        LIMIT 20
    """)
    
    result = db.execute(top_clients_query)
    top_clients = [
        {
            "client_id": row[0],
            "client_name": row[1],
            "outstanding_invoices": row[2],
            "total_owed": float(row[3]) if row[3] else 0,
            "oldest_due_date": row[4].isoformat() if row[4] else None,
            "max_days_overdue": row[5] if row[5] else 0
        }
        for row in result.fetchall()
    ]
    
    # Calculate grand total
    grand_total = sum(bucket["total_amount"] for bucket in aging_summary)
    
    return {
        "report_type": "accounts_receivable_aging",
        "as_of_date": target_date.isoformat(),
        "grand_total": grand_total,
        "aging_summary": aging_summary,
        "top_clients": top_clients
    }

@app.get("/reports/ap-aging")
def get_ap_aging_report(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Accounts Payable (AP) Aging Report
    Shows outstanding vendor payments grouped by aging bucket
    """
    target_date = as_of_date or date.today()
    
    # Query for AP aging summary by bucket
    query = text("""
        WITH ap_payments AS (
            SELECT 
                p.id,
                p.charter_id,
                p.amount,
                p.due_date,
                p.aging_days,
                p.aging_bucket,
                p.created_at,
                c.vendor_id,
                COALESCE(v.business_name, 'Unknown Vendor') as vendor_name
            FROM payments p
            JOIN charters c ON p.charter_id = c.id
            LEFT JOIN vendor.vendors v ON c.vendor_id = v.id
            WHERE p.payment_type = 'payable'
            AND p.status != 'completed'
            AND p.due_date IS NOT NULL
        )
        SELECT 
            aging_bucket,
            COUNT(*) as bill_count,
            SUM(amount) as total_amount,
            MIN(due_date) as oldest_due_date,
            MAX(due_date) as newest_due_date
        FROM ap_payments
        GROUP BY aging_bucket
        ORDER BY 
            CASE aging_bucket
                WHEN 'not_due' THEN 0
                WHEN '0-30' THEN 1
                WHEN '31-60' THEN 2
                WHEN '61-90' THEN 3
                WHEN '90+' THEN 4
                ELSE 5
            END
    """)
    
    result = db.execute(query)
    aging_summary = [
        {
            "aging_bucket": row[0],
            "bill_count": row[1],
            "total_amount": float(row[2]) if row[2] else 0,
            "oldest_due_date": row[3].isoformat() if row[3] else None,
            "newest_due_date": row[4].isoformat() if row[4] else None
        }
        for row in result.fetchall()
    ]
    
    # Query for top 20 vendors by amount owed
    top_vendors_query = text("""
        WITH ap_payments AS (
            SELECT 
                p.charter_id,
                p.amount,
                p.due_date,
                p.aging_days,
                c.vendor_id,
                COALESCE(v.business_name, 'Unknown Vendor') as vendor_name
            FROM payments p
            JOIN charters c ON p.charter_id = c.id
            LEFT JOIN vendor.vendors v ON c.vendor_id = v.id
            WHERE p.payment_type = 'payable'
            AND p.status != 'completed'
            AND p.due_date IS NOT NULL
        )
        SELECT 
            vendor_id,
            vendor_name,
            COUNT(*) as outstanding_bills,
            SUM(amount) as total_owed,
            MIN(due_date) as oldest_due_date,
            MAX(aging_days) as max_days_overdue
        FROM ap_payments
        GROUP BY vendor_id, vendor_name
        ORDER BY total_owed DESC
        LIMIT 20
    """)
    
    result = db.execute(top_vendors_query)
    top_vendors = [
        {
            "vendor_id": row[0],
            "vendor_name": row[1],
            "outstanding_bills": row[2],
            "total_owed": float(row[3]) if row[3] else 0,
            "oldest_due_date": row[4].isoformat() if row[4] else None,
            "max_days_overdue": row[5] if row[5] else 0
        }
        for row in result.fetchall()
    ]
    
    # Calculate grand total
    grand_total = sum(bucket["total_amount"] for bucket in aging_summary)
    
    return {
        "report_type": "accounts_payable_aging",
        "as_of_date": target_date.isoformat(),
        "grand_total": grand_total,
        "aging_summary": aging_summary,
        "top_vendors": top_vendors
    }

# Phase 1.2: Vendor Bills Management
@app.post("/vendor-bills")
def create_vendor_bill(
    bill_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new vendor bill"""
    try:
        bill = VendorBill(**bill_data)
        db.add(bill)
        db.commit()
        db.refresh(bill)
        return {
            "id": bill.id,
            "vendor_id": bill.vendor_id,
            "charter_id": bill.charter_id,
            "bill_number": bill.bill_number,
            "bill_date": bill.bill_date.isoformat(),
            "due_date": bill.due_date.isoformat(),
            "amount": float(bill.amount),
            "paid_amount": float(bill.paid_amount),
            "status": bill.status,
            "approval_status": bill.approval_status,
            "aging_days": bill.aging_days,
            "aging_bucket": bill.aging_bucket
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vendor-bills")
def get_vendor_bills(
    vendor_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    overdue_only: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get vendor bills with optional filters"""
    query = db.query(VendorBill)
    
    if vendor_id:
        query = query.filter(VendorBill.vendor_id == vendor_id)
    if charter_id:
        query = query.filter(VendorBill.charter_id == charter_id)
    if status:
        query = query.filter(VendorBill.status == status)
    if approval_status:
        query = query.filter(VendorBill.approval_status == approval_status)
    if overdue_only:
        query = query.filter(VendorBill.status == 'overdue')
    
    bills = query.order_by(VendorBill.due_date.desc()).limit(limit).all()
    
    return {
        "bills": [
            {
                "id": bill.id,
                "vendor_id": bill.vendor_id,
                "charter_id": bill.charter_id,
                "bill_number": bill.bill_number,
                "bill_date": bill.bill_date.isoformat(),
                "due_date": bill.due_date.isoformat(),
                "amount": float(bill.amount),
                "paid_amount": float(bill.paid_amount),
                "status": bill.status,
                "approval_status": bill.approval_status,
                "aging_days": bill.aging_days,
                "aging_bucket": bill.aging_bucket,
                "description": bill.description
            }
            for bill in bills
        ],
        "count": len(bills)
    }

@app.get("/vendor-bills/{bill_id}")
def get_vendor_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific vendor bill"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    return {
        "id": bill.id,
        "vendor_id": bill.vendor_id,
        "charter_id": bill.charter_id,
        "bill_number": bill.bill_number,
        "bill_date": bill.bill_date.isoformat(),
        "due_date": bill.due_date.isoformat(),
        "amount": float(bill.amount),
        "paid_amount": float(bill.paid_amount),
        "status": bill.status,
        "approval_status": bill.approval_status,
        "approved_by": bill.approved_by,
        "approved_at": bill.approved_at.isoformat() if bill.approved_at else None,
        "rejection_reason": bill.rejection_reason,
        "description": bill.description,
        "notes": bill.notes,
        "aging_days": bill.aging_days,
        "aging_bucket": bill.aging_bucket,
        "created_at": bill.created_at.isoformat(),
        "updated_at": bill.updated_at.isoformat() if bill.updated_at else None
    }

@app.post("/vendor-bills/{bill_id}/approve")
def approve_vendor_bill(
    bill_id: int,
    approval_data: dict,
    db: Session = Depends(get_db)
):
    """Approve a vendor bill"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    if bill.approval_status == 'approved':
        raise HTTPException(status_code=400, detail="Bill already approved")
    
    bill.approval_status = 'approved'
    bill.status = 'approved'
    bill.approved_by = approval_data.get('approved_by')
    bill.approved_at = func.now()
    
    db.commit()
    db.refresh(bill)
    
    return {
        "id": bill.id,
        "bill_number": bill.bill_number,
        "approval_status": bill.approval_status,
        "approved_by": bill.approved_by,
        "approved_at": bill.approved_at.isoformat() if bill.approved_at else None,
        "message": "Bill approved successfully"
    }

@app.post("/vendor-bills/{bill_id}/reject")
def reject_vendor_bill(
    bill_id: int,
    rejection_data: dict,
    db: Session = Depends(get_db)
):
    """Reject a vendor bill"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    if bill.approval_status == 'rejected':
        raise HTTPException(status_code=400, detail="Bill already rejected")
    
    bill.approval_status = 'rejected'
    bill.status = 'cancelled'
    bill.rejection_reason = rejection_data.get('reason', 'No reason provided')
    bill.approved_by = rejection_data.get('rejected_by')
    bill.approved_at = func.now()
    
    db.commit()
    db.refresh(bill)
    
    return {
        "id": bill.id,
        "bill_number": bill.bill_number,
        "approval_status": bill.approval_status,
        "rejection_reason": bill.rejection_reason,
        "message": "Bill rejected successfully"
    }

@app.post("/vendor-bills/{bill_id}/record-payment")
def record_bill_payment(
    bill_id: int,
    payment_data: dict,
    db: Session = Depends(get_db)
):
    """Record a payment against a vendor bill"""
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    if bill.approval_status != 'approved':
        raise HTTPException(status_code=400, detail="Bill must be approved before recording payment")
    
    payment_amount = payment_data.get('amount', 0)
    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    
    new_paid_amount = float(bill.paid_amount) + payment_amount
    if new_paid_amount > float(bill.amount):
        raise HTTPException(status_code=400, detail="Payment amount exceeds bill amount")
    
    bill.paid_amount = new_paid_amount
    # Status is auto-updated by trigger
    
    db.commit()
    db.refresh(bill)
    
    return {
        "id": bill.id,
        "bill_number": bill.bill_number,
        "amount": float(bill.amount),
        "paid_amount": float(bill.paid_amount),
        "remaining": float(bill.amount) - float(bill.paid_amount),
        "status": bill.status,
        "message": "Payment recorded successfully"
    }

@app.get("/vendor-bills/summary/overdue")
def get_overdue_bills_summary(
    db: Session = Depends(get_db)
):
    """Get summary of overdue vendor bills"""
    query = text("""
        SELECT 
            aging_bucket,
            COUNT(*) as bill_count,
            SUM(amount - paid_amount) as total_outstanding
        FROM vendor_bills
        WHERE status IN ('overdue', 'partially_paid', 'approved')
        AND aging_bucket != 'not_due'
        GROUP BY aging_bucket
        ORDER BY 
            CASE aging_bucket
                WHEN '0-30' THEN 1
                WHEN '31-60' THEN 2
                WHEN '61-90' THEN 3
                WHEN '90+' THEN 4
                ELSE 5
            END
    """)
    
    result = db.execute(query)
    summary = [
        {
            "aging_bucket": row[0],
            "bill_count": row[1],
            "total_outstanding": float(row[2]) if row[2] else 0
        }
        for row in result.fetchall()
    ]
    
    return {
        "overdue_summary": summary,
        "total_overdue_bills": sum(s["bill_count"] for s in summary),
        "total_overdue_amount": sum(s["total_outstanding"] for s in summary)
    }

# ============================================================================
# PAYMENT ALLOCATION ENDPOINTS (Phase 1.4)
# ============================================================================

@app.post("/payments/{payment_id}/allocate")
def allocate_payment(
    payment_id: int,
    allocations: List[dict],
    db: Session = Depends(get_db)
):
    """
    Allocate a payment to multiple charters
    
    Body: [
        {"charter_id": 1, "allocated_amount": 500.00, "notes": "Partial payment"},
        {"charter_id": 2, "allocated_amount": 300.00}
    ]
    """
    # Get payment
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Validate total doesn't exceed payment amount
    total_allocated = sum(float(a.get('allocated_amount', 0)) for a in allocations)
    if total_allocated > float(payment.amount):
        raise HTTPException(
            status_code=400,
            detail=f"Total allocation ({total_allocated}) exceeds payment amount ({payment.amount})"
        )
    
    # Check for existing allocations
    existing = db.query(PaymentAllocation).filter(
        PaymentAllocation.payment_id == payment_id
    ).count()
    if existing > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Payment already has {existing} allocations. Delete them first to re-allocate."
        )
    
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
        created_allocations.append({
            "charter_id": alloc['charter_id'],
            "allocated_amount": float(alloc['allocated_amount']),
            "notes": alloc.get('notes')
        })
    
    db.commit()
    
    return {
        "payment_id": payment_id,
        "allocations_created": len(created_allocations),
        "total_allocated": total_allocated,
        "allocations": created_allocations
    }

@app.get("/payments/{payment_id}/allocations")
def get_payment_allocations(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Get all allocations for a payment"""
    allocations = db.query(PaymentAllocation).filter(
        PaymentAllocation.payment_id == payment_id
    ).all()
    
    total_allocated = sum(float(a.allocated_amount) for a in allocations)
    
    return {
        "payment_id": payment_id,
        "allocation_count": len(allocations),
        "total_allocated": total_allocated,
        "allocations": [
            {
                "id": a.id,
                "charter_id": a.charter_id,
                "allocated_amount": float(a.allocated_amount),
                "notes": a.notes,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in allocations
        ]
    }

@app.get("/charters/{charter_id}/allocated-payments")
def get_charter_allocations(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """Get all payment allocations for a specific charter"""
    allocations = db.query(PaymentAllocation).filter(
        PaymentAllocation.charter_id == charter_id
    ).all()
    
    total_received = sum(float(a.allocated_amount) for a in allocations)
    
    return {
        "charter_id": charter_id,
        "allocation_count": len(allocations),
        "total_received": total_received,
        "allocations": [
            {
                "id": a.id,
                "payment_id": a.payment_id,
                "allocated_amount": float(a.allocated_amount),
                "notes": a.notes,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in allocations
        ]
    }

@app.delete("/payments/{payment_id}/allocations")
def delete_payment_allocations(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Delete all allocations for a payment (to allow re-allocation)"""
    deleted_count = db.query(PaymentAllocation).filter(
        PaymentAllocation.payment_id == payment_id
    ).delete()
    
    db.commit()
    
    return {
        "payment_id": payment_id,
        "deleted_count": deleted_count,
        "message": "Allocations deleted successfully"
    }


# ============================================================================
# Saved Payment Methods Endpoints (Task 8.1)
# ============================================================================

@app.post("/payment-methods", response_model=PaymentMethodResponse, status_code=201)
async def save_payment_method(
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    client_id: Optional[int] = None  # TODO: Get from auth token
):
    """
    Save a new payment method for client.
    
    - Creates Stripe Customer if doesn't exist
    - Attaches payment method to customer
    - Saves details in database
    - Optionally sets as default
    """
    if not client_id:
        # TODO: Get client_id from JWT token
        raise HTTPException(403, "Client ID required")
    
    try:
        # Get client details (cross-table query - in production use API call)
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(404, "Client not found")
        
        # Create or get Stripe Customer
        customer_id = await StripeCustomerService.create_or_get_customer(
            client_id=client_id,
            email=client.email,
            name=client.name,
            db=db,
            existing_stripe_customer_id=client.stripe_customer_id
        )
        
        # Save customer ID back to client if it was just created
        if not client.stripe_customer_id:
            client.stripe_customer_id = customer_id
            db.commit()
        
        # Attach payment method
        pm_details = await StripeCustomerService.attach_payment_method(
            stripe_customer_id=customer_id,
            stripe_token=payment_method.stripe_token
        )
        
        # If setting as default, unset other defaults
        if payment_method.is_default:
            db.query(SavedPaymentMethod).filter(
                SavedPaymentMethod.client_id == client_id,
                SavedPaymentMethod.is_default == True
            ).update({"is_default": False})
        
        # Save to database
        db_payment_method = SavedPaymentMethod(
            client_id=client_id,
            stripe_payment_method_id=pm_details["id"],
            card_brand=pm_details["brand"],
            card_last4=pm_details["last4"],
            card_exp_month=pm_details["exp_month"],
            card_exp_year=pm_details["exp_year"],
            nickname=payment_method.nickname,
            is_default=payment_method.is_default,
            created_by=None  # TODO: Get from auth token
        )
        
        db.add(db_payment_method)
        db.commit()
        db.refresh(db_payment_method)
        
        return db_payment_method
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to save payment method: {str(e)}")


@app.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def list_payment_methods(
    db: Session = Depends(get_db),
    client_id: Optional[int] = None  # TODO: Get from auth token
):
    """
    List all saved payment methods for current client.
    
    Returns active payment methods sorted by default first, then by created date.
    """
    if not client_id:
        raise HTTPException(403, "Client ID required")
    
    payment_methods = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.client_id == client_id,
        SavedPaymentMethod.is_active == True
    ).order_by(
        SavedPaymentMethod.is_default.desc(),
        SavedPaymentMethod.created_at.desc()
    ).all()
    
    return payment_methods


@app.get("/payment-methods/{payment_method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    client_id: Optional[int] = None  # TODO: Get from auth token
):
    """Get specific payment method by ID."""
    if not client_id:
        raise HTTPException(403, "Client ID required")
    
    payment_method = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.id == payment_method_id,
        SavedPaymentMethod.client_id == client_id
    ).first()
    
    if not payment_method:
        raise HTTPException(404, "Payment method not found")
    
    return payment_method


@app.patch("/payment-methods/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: int,
    updates: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    client_id: Optional[int] = None  # TODO: Get from auth token
):
    """
    Update payment method settings.
    
    Can update nickname and default status.
    """
    if not client_id:
        raise HTTPException(403, "Client ID required")
    
    payment_method = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.id == payment_method_id,
        SavedPaymentMethod.client_id == client_id
    ).first()
    
    if not payment_method:
        raise HTTPException(404, "Payment method not found")
    
    # If setting as default, unset other defaults
    if updates.is_default:
        db.query(SavedPaymentMethod).filter(
            SavedPaymentMethod.client_id == client_id,
            SavedPaymentMethod.is_default == True,
            SavedPaymentMethod.id != payment_method_id
        ).update({"is_default": False})
    
    # Update fields
    if updates.nickname is not None:
        payment_method.nickname = updates.nickname
    if updates.is_default is not None:
        payment_method.is_default = updates.is_default
    
    db.commit()
    db.refresh(payment_method)
    
    return payment_method


@app.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    client_id: Optional[int] = None  # TODO: Get from auth token
):
    """
    Delete (deactivate) payment method.
    
    Detaches from Stripe Customer and marks as inactive.
    """
    if not client_id:
        raise HTTPException(403, "Client ID required")
    
    payment_method = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.id == payment_method_id,
        SavedPaymentMethod.client_id == client_id
    ).first()
    
    if not payment_method:
        raise HTTPException(404, "Payment method not found")
    
    try:
        # Detach from Stripe
        await StripeCustomerService.detach_payment_method(
            payment_method.stripe_payment_method_id
        )
        
        # Mark as inactive
        payment_method.is_active = False
        db.commit()
        
        return {"message": "Payment method deleted", "id": payment_method_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to delete payment method: {str(e)}")


@app.post("/payment-methods/charge", status_code=200)
async def charge_saved_payment_method(
    charge_request: ChargePaymentMethodRequest,
    db: Session = Depends(get_db),
    client_id: Optional[int] = None  # TODO: Get from auth token
):
    """
    Charge a saved payment method.
    
    - Verifies payment method belongs to client
    - Creates Stripe PaymentIntent
    - Records payment in database
    - Updates last_used_at timestamp
    """
    if not client_id:
        raise HTTPException(403, "Client ID required")
    
    # Get payment method
    payment_method = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.id == charge_request.payment_method_id,
        SavedPaymentMethod.client_id == client_id,
        SavedPaymentMethod.is_active == True
    ).first()
    
    if not payment_method:
        raise HTTPException(404, "Payment method not found or inactive")
    
    try:
        # Get client for stripe_customer_id
        client = db.query(Client).filter(Client.id == client_id).first()
        
        # Charge payment method
        amount_cents = int(charge_request.amount * 100)
        metadata = {}
        if charge_request.charter_id:
            metadata["charter_id"] = str(charge_request.charter_id)
        
        payment_result = await StripeCustomerService.charge_payment_method(
            stripe_customer_id=client.stripe_customer_id,
            stripe_payment_method_id=payment_method.stripe_payment_method_id,
            amount_cents=amount_cents,
            description=charge_request.description,
            metadata=metadata
        )
        
        # Update last_used_at
        payment_method.last_used_at = datetime.utcnow()
        
        # Record payment in database
        db_payment = Payment(
            charter_id=charge_request.charter_id,
            amount=charge_request.amount,
            stripe_payment_intent_id=payment_result["id"],
            status=payment_result["status"],
            payment_method="saved_card",
            payment_type="payment",
            description=charge_request.description,
            created_by=None  # TODO: Get from auth token
        )
        
        db.add(db_payment)
        db.commit()
        
        return {
            "message": "Payment successful",
            "payment_id": db_payment.id,
            "amount": charge_request.amount,
            "stripe_payment_intent_id": payment_result["id"],
            "status": payment_result["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Payment failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
