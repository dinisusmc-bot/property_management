from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from database import get_db, engine, Base
from models import Payment, PaymentSchedule, PaymentRefund
from schemas import (
    PaymentCreate, PaymentResponse, PaymentIntentCreate, 
    RefundCreate, RefundResponse, WebhookEvent
)
from payment_service import PaymentService
from webhook_handler import StripeWebhookHandler
from config import settings

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
