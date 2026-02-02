from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class PaymentCreate(BaseModel):
    charter_id: int
    amount: float
    payment_type: str  # deposit, balance, refund
    payment_method: str = "card"  # card, ach, check, cash
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    failure_reason: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    charter_id: int
    amount: float
    currency: str
    payment_type: str
    payment_method: str
    status: str
    stripe_payment_intent_id: Optional[str]
    card_last4: Optional[str]
    card_brand: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentIntentCreate(BaseModel):
    charter_id: int
    amount: float
    payment_type: str
    description: Optional[str] = None

class PaymentIntentResponse(BaseModel):
    payment_intent_id: str
    client_secret: str
    amount: float
    currency: str

class RefundCreate(BaseModel):
    payment_id: int
    amount: Optional[float] = None  # None = full refund
    reason: str = "requested_by_customer"

class RefundResponse(BaseModel):
    id: int
    payment_id: int
    amount: float
    reason: str
    status: str
    stripe_refund_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class WebhookEvent(BaseModel):
    type: str
    data: Dict[str, Any]
