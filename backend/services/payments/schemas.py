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


# ============================================================================
# Saved Payment Methods Schemas
# ============================================================================

class PaymentMethodBase(BaseModel):
    """Base schema for payment method."""
    nickname: Optional[str] = None
    is_default: bool = False

class PaymentMethodCreate(PaymentMethodBase):
    """Create new payment method."""
    stripe_token: str  # Stripe token from frontend (tok_xxx)

class PaymentMethodUpdate(BaseModel):
    """Update payment method settings."""
    nickname: Optional[str] = None
    is_default: Optional[bool] = None

class PaymentMethodResponse(PaymentMethodBase):
    """Payment method response."""
    id: int
    client_id: int
    stripe_payment_method_id: str
    
    # Card details
    card_brand: Optional[str]
    card_last4: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    
    # Metadata
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ChargePaymentMethodRequest(BaseModel):
    """Request to charge a saved payment method."""
    payment_method_id: int
    amount: float
    description: str
    charter_id: Optional[int] = None

class WebhookEvent(BaseModel):
    type: str
    data: Dict[str, Any]
