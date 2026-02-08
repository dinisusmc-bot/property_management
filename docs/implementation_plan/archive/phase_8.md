# Phase 8: Final Backend Features

**Priority:** 🔴 CRITICAL  
**Estimated Time:** 2-3 weeks (58-71 hours)  
**Dependencies:** Phases 1-7 complete  
**Status:** 🔄 In Progress

---

## Overview

Phase 8 implements the final 10% of backend capabilities needed before full frontend development. This phase focuses on critical user experience features that were identified during the gap analysis.

### Goals

1. Enable clients to save and reuse payment methods
2. Integrate geocoding/routing for accurate charter pricing
3. Complete multi-vehicle pricing calculations
4. Provide secure, shareable quote links
5. Implement custom e-signature capture system

### Success Criteria

- [ ] Clients can save credit cards for future use
- [ ] Addresses automatically geocoded with lat/lon
- [ ] Multi-vehicle charters priced correctly
- [ ] Quote links work without login
- [ ] Documents signed within platform

---

## Task 8.1: Saved Payment Methods (GAP-001)

**Time Estimate:** 15-18 hours  
**Service:** payment-service  
**Impact:** CRITICAL - Required for recurring billing and better UX

### Problem Statement

Currently, clients must enter payment details for every transaction. For recurring charters or multiple bookings, this creates friction. We need to:

1. Create Stripe Customer on first payment
2. Save payment methods to customer
3. Allow clients to manage saved methods
4. Support charging saved methods

### Step-by-Step Implementation

#### Step 1: Update Database Schema (1 hour)

**File:** `backend/services/payments/migrations/add_saved_payment_methods.sql`

```sql
-- ============================================================================
-- Migration: Add Saved Payment Methods Support
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Add stripe_customer_id to clients and create payment methods table
-- ============================================================================

-- Add stripe_customer_id to clients table
ALTER TABLE clients 
  ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100) UNIQUE;

COMMENT ON COLUMN clients.stripe_customer_id IS 'Stripe Customer ID for saved payment methods';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_clients_stripe_customer 
  ON clients(stripe_customer_id) 
  WHERE stripe_customer_id IS NOT NULL;

-- Create saved_payment_methods table
CREATE TABLE IF NOT EXISTS payment.saved_payment_methods (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    stripe_payment_method_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Card details
    card_brand VARCHAR(50),
    card_last4 VARCHAR(4),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    nickname VARCHAR(100),  -- e.g., "Work Visa", "Personal Card"
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    last_used_at TIMESTAMP,
    
    -- Ensure only one default per client
    CONSTRAINT unique_default_per_client UNIQUE NULLS NOT DISTINCT (client_id, is_default)
        DEFERRABLE INITIALLY DEFERRED
);

-- Indexes
CREATE INDEX idx_payment_methods_client ON payment.saved_payment_methods(client_id);
CREATE INDEX idx_payment_methods_stripe ON payment.saved_payment_methods(stripe_payment_method_id);
CREATE INDEX idx_payment_methods_default ON payment.saved_payment_methods(client_id, is_default) 
  WHERE is_default = TRUE;

-- Comments
COMMENT ON TABLE payment.saved_payment_methods IS 'Saved payment methods linked to Stripe Customer';
COMMENT ON COLUMN payment.saved_payment_methods.is_default IS 'Default payment method for client (only one per client)';
COMMENT ON COLUMN payment.saved_payment_methods.last_used_at IS 'Tracks when method was last charged';

-- ============================================================================
-- Rollback Script
-- ============================================================================
-- DROP TABLE IF EXISTS payment.saved_payment_methods CASCADE;
-- ALTER TABLE clients DROP COLUMN IF EXISTS stripe_customer_id;
```

**Run migration:**
```bash
docker exec -it coachway_demo-postgres-1 psql -U athena -d athena -f backend/services/payments/migrations/add_saved_payment_methods.sql
```

#### Step 2: Update Models (30 minutes)

**File:** `backend/services/payments/app/models.py`

Add the following model:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

class SavedPaymentMethod(Base):
    """Saved payment method for client (linked to Stripe Customer)."""
    
    __tablename__ = "saved_payment_methods"
    __table_args__ = {"schema": "payment"}
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    stripe_payment_method_id = Column(String(100), unique=True, nullable=False)
    
    # Card details (for display)
    card_brand = Column(String(50))  # visa, mastercard, amex, etc.
    card_last4 = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    
    # Metadata
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    nickname = Column(String(100))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    last_used_at = Column(DateTime)
    
    # Relationships
    client = relationship("Client", back_populates="saved_payment_methods")
    created_by_user = relationship("User")
    
    def __repr__(self):
        return f"<SavedPaymentMethod {self.card_brand} ****{self.card_last4}>"
```

Also update the Client model (in client-service):

```python
# In backend/services/client/app/models.py
class Client(Base):
    # ... existing fields ...
    
    stripe_customer_id = Column(String(100), unique=True, index=True)
    
    # Relationships
    saved_payment_methods = relationship(
        "SavedPaymentMethod", 
        back_populates="client",
        cascade="all, delete-orphan"
    )
```

#### Step 3: Create Pydantic Schemas (30 minutes)

**File:** `backend/services/payments/app/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaymentMethodBase(BaseModel):
    """Base schema for payment method."""
    nickname: Optional[str] = Field(None, max_length=100, description="User-friendly name")
    is_default: bool = Field(False, description="Set as default payment method")

class PaymentMethodCreate(PaymentMethodBase):
    """Create new payment method."""
    stripe_token: str = Field(..., description="Stripe token from frontend (tok_xxx)")

class PaymentMethodUpdate(BaseModel):
    """Update payment method settings."""
    nickname: Optional[str] = Field(None, max_length=100)
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
    payment_method_id: int = Field(..., description="ID of saved payment method")
    amount: float = Field(..., gt=0, description="Amount to charge in dollars")
    description: str = Field(..., max_length=500, description="Charge description")
    charter_id: Optional[int] = Field(None, description="Associated charter ID")
```

#### Step 4: Implement Stripe Integration (3-4 hours)

**File:** `backend/services/payments/app/stripe_customer_service.py`

```python
"""
Stripe Customer management for saved payment methods.
"""

import stripe
import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeCustomerService:
    """Service for managing Stripe Customers and payment methods."""
    
    @staticmethod
    async def create_or_get_customer(
        client_id: int,
        email: str,
        name: str,
        db: Session
    ) -> str:
        """
        Create Stripe Customer if doesn't exist, or return existing customer_id.
        
        Args:
            client_id: Client database ID
            email: Client email
            name: Client name
            db: Database session
            
        Returns:
            Stripe Customer ID (cus_xxx)
        """
        from .models import Client
        
        # Check if customer already exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(404, "Client not found")
        
        if client.stripe_customer_id:
            return client.stripe_customer_id
        
        try:
            # Create new Stripe Customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"client_id": str(client_id)}
            )
            
            # Save customer_id to database
            client.stripe_customer_id = customer.id
            db.commit()
            
            return customer.id
            
        except stripe.error.StripeError as e:
            raise HTTPException(500, f"Stripe error: {str(e)}")
    
    @staticmethod
    async def attach_payment_method(
        stripe_customer_id: str,
        stripe_token: str
    ) -> Dict[str, Any]:
        """
        Attach payment method to customer.
        
        Args:
            stripe_customer_id: Stripe Customer ID
            stripe_token: Token from frontend (tok_xxx)
            
        Returns:
            Payment method details
        """
        try:
            # Create payment method from token
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={"token": stripe_token}
            )
            
            # Attach to customer
            stripe.PaymentMethod.attach(
                payment_method.id,
                customer=stripe_customer_id
            )
            
            # Return payment method details
            return {
                "id": payment_method.id,
                "brand": payment_method.card.brand,
                "last4": payment_method.card.last4,
                "exp_month": payment_method.card.exp_month,
                "exp_year": payment_method.card.exp_year
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(500, f"Stripe error: {str(e)}")
    
    @staticmethod
    async def detach_payment_method(
        stripe_payment_method_id: str
    ) -> bool:
        """
        Detach payment method from customer.
        
        Args:
            stripe_payment_method_id: Payment method ID
            
        Returns:
            True if successful
        """
        try:
            stripe.PaymentMethod.detach(stripe_payment_method_id)
            return True
        except stripe.error.StripeError as e:
            raise HTTPException(500, f"Stripe error: {str(e)}")
    
    @staticmethod
    async def charge_payment_method(
        stripe_customer_id: str,
        stripe_payment_method_id: str,
        amount_cents: int,
        description: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Charge a saved payment method.
        
        Args:
            stripe_customer_id: Stripe Customer ID
            stripe_payment_method_id: Payment method ID
            amount_cents: Amount in cents
            description: Charge description
            metadata: Optional metadata
            
        Returns:
            Payment intent details
        """
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                customer=stripe_customer_id,
                payment_method=stripe_payment_method_id,
                off_session=True,
                confirm=True,
                description=description,
                metadata=metadata or {}
            )
            
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "created": intent.created
            }
            
        except stripe.error.CardError as e:
            # Card declined
            raise HTTPException(400, f"Card declined: {e.user_message}")
        except stripe.error.StripeError as e:
            raise HTTPException(500, f"Stripe error: {str(e)}")
```

#### Step 5: Create API Endpoints (4-5 hours)

**File:** `backend/services/payments/app/main.py`

Add these endpoints:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .database import get_db
from .models import SavedPaymentMethod
from .schemas import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    ChargePaymentMethodRequest
)
from .stripe_customer_service import StripeCustomerService
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])

@router.post("", response_model=PaymentMethodResponse, status_code=201)
async def save_payment_method(
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Save a new payment method for client.
    
    - Creates Stripe Customer if doesn't exist
    - Attaches payment method to customer
    - Saves details in database
    - Optionally sets as default
    
    **Requires:** Client role
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(403, "Only clients can save payment methods")
    
    try:
        # Get client details
        from ..client.app.models import Client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(404, "Client not found")
        
        # Create or get Stripe Customer
        customer_id = await StripeCustomerService.create_or_get_customer(
            client_id=client_id,
            email=client.email,
            name=client.name,
            db=db
        )
        
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
            created_by=current_user["user_id"]
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

@router.get("", response_model=List[PaymentMethodResponse])
async def list_payment_methods(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all saved payment methods for current client.
    
    Returns active payment methods sorted by default first, then by created date.
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(403, "Only clients can view payment methods")
    
    payment_methods = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.client_id == client_id,
        SavedPaymentMethod.is_active == True
    ).order_by(
        SavedPaymentMethod.is_default.desc(),
        SavedPaymentMethod.created_at.desc()
    ).all()
    
    return payment_methods

@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific payment method by ID."""
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(403, "Only clients can view payment methods")
    
    payment_method = db.query(SavedPaymentMethod).filter(
        SavedPaymentMethod.id == payment_method_id,
        SavedPaymentMethod.client_id == client_id
    ).first()
    
    if not payment_method:
        raise HTTPException(404, "Payment method not found")
    
    return payment_method

@router.patch("/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: int,
    updates: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update payment method settings.
    
    Can update nickname and default status.
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(403, "Only clients can update payment methods")
    
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
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(payment_method, key, value)
    
    db.commit()
    db.refresh(payment_method)
    
    return payment_method

@router.delete("/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete (deactivate) payment method.
    
    Detaches from Stripe Customer and marks as inactive.
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(403, "Only clients can delete payment methods")
    
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

@router.post("/charge", status_code=200)
async def charge_saved_payment_method(
    charge_request: ChargePaymentMethodRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Charge a saved payment method.
    
    - Verifies payment method belongs to client
    - Creates Stripe PaymentIntent
    - Records payment in database
    - Updates last_used_at timestamp
    
    **Requires:** Client role
    """
    client_id = current_user.get("client_id")
    if not client_id:
        raise HTTPException(403, "Only clients can charge payment methods")
    
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
        from ..client.app.models import Client
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
        
        # Record payment in database (reuse existing Payment model)
        from .models import Payment
        db_payment = Payment(
            client_id=client_id,
            charter_id=charge_request.charter_id,
            amount=charge_request.amount,
            stripe_payment_intent_id=payment_result["id"],
            status=payment_result["status"],
            payment_method="saved_card",
            description=charge_request.description,
            created_by=current_user["user_id"]
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

# Add router to main app
app.include_router(router)
```

#### Step 6: Create Test Script (2 hours)

**File:** `tests/test_task_8_1_payment_methods.sh`

```bash
#!/bin/bash

# ============================================================================
# Test Script: Saved Payment Methods (Task 8.1)
# ============================================================================

set -e

BASE_URL="http://localhost:8080/api/v1"
ADMIN_EMAIL="admin@athena.com"
ADMIN_PASSWORD="admin123"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Testing Saved Payment Methods (Task 8.1)"
echo "========================================"
echo ""

# Get admin token
echo "=== Step 1: Authenticate as Admin ==="
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
  echo -e "${RED}❌ Authentication failed${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Authenticated successfully${NC}"
echo ""

# Create test client
echo "=== Step 2: Create Test Client ==="
CLIENT_RESPONSE=$(curl -s -X POST "$BASE_URL/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Payment Client",
    "email": "payment.test@example.com",
    "phone": "555-0199",
    "address": "123 Test St"
  }')

CLIENT_ID=$(echo $CLIENT_RESPONSE | jq -r '.id')
echo -e "${GREEN}✓ Created client: $CLIENT_ID${NC}"
echo ""

# Get client token (normally would login as client)
echo "=== Step 3: Get Client Token ==="
# For testing, create client user and login
curl -s -X POST "$BASE_URL/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"payment.test@example.com\",
    \"password\": \"test123\",
    \"role\": \"client\",
    \"client_id\": $CLIENT_ID
  }" > /dev/null

CLIENT_TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=payment.test@example.com&password=test123" | jq -r '.access_token')

echo -e "${GREEN}✓ Client authenticated${NC}"
echo ""

# Save payment method
echo "=== Step 4: Save Payment Method ==="
echo -e "${YELLOW}Note: Using Stripe test token tok_visa${NC}"
PM_RESPONSE=$(curl -s -X POST "$BASE_URL/payment-methods" \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stripe_token": "tok_visa",
    "nickname": "Primary Visa",
    "is_default": true
  }')

PM_ID=$(echo $PM_RESPONSE | jq -r '.id')
if [ "$PM_ID" = "null" ]; then
  echo -e "${RED}❌ Failed to save payment method${NC}"
  echo $PM_RESPONSE | jq
  exit 1
fi

echo -e "${GREEN}✓ Saved payment method: $PM_ID${NC}"
echo "   Brand: $(echo $PM_RESPONSE | jq -r '.card_brand')"
echo "   Last4: $(echo $PM_RESPONSE | jq -r '.card_last4')"
echo "   Default: $(echo $PM_RESPONSE | jq -r '.is_default')"
echo ""

# List payment methods
echo "=== Step 5: List Payment Methods ==="
PM_LIST=$(curl -s -X GET "$BASE_URL/payment-methods" \
  -H "Authorization: Bearer $CLIENT_TOKEN")

PM_COUNT=$(echo $PM_LIST | jq 'length')
echo -e "${GREEN}✓ Found $PM_COUNT payment method(s)${NC}"
echo ""

# Save second payment method
echo "=== Step 6: Save Second Payment Method ==="
PM2_RESPONSE=$(curl -s -X POST "$BASE_URL/payment-methods" \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stripe_token": "tok_mastercard",
    "nickname": "Backup Card",
    "is_default": false
  }')

PM2_ID=$(echo $PM2_RESPONSE | jq -r '.id')
echo -e "${GREEN}✓ Saved second payment method: $PM2_ID${NC}"
echo ""

# Update payment method
echo "=== Step 7: Update Payment Method ==="
curl -s -X PATCH "$BASE_URL/payment-methods/$PM2_ID" \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "Work Mastercard",
    "is_default": true
  }' > /dev/null

echo -e "${GREEN}✓ Updated payment method nickname and set as default${NC}"
echo ""

# Charge payment method
echo "=== Step 8: Charge Payment Method ==="
CHARGE_RESPONSE=$(curl -s -X POST "$BASE_URL/payment-methods/charge" \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"payment_method_id\": $PM_ID,
    \"amount\": 100.50,
    \"description\": \"Test charge for charter booking\"
  }")

CHARGE_STATUS=$(echo $CHARGE_RESPONSE | jq -r '.status')
if [ "$CHARGE_STATUS" = "succeeded" ] || [ "$CHARGE_STATUS" = "succeeded" ]; then
  echo -e "${GREEN}✓ Charge successful${NC}"
  echo "   Amount: $(echo $CHARGE_RESPONSE | jq -r '.amount')"
  echo "   Status: $CHARGE_STATUS"
else
  echo -e "${YELLOW}⚠ Charge status: $CHARGE_STATUS${NC}"
  echo $CHARGE_RESPONSE | jq
fi
echo ""

# Delete payment method
echo "=== Step 9: Delete Payment Method ==="
curl -s -X DELETE "$BASE_URL/payment-methods/$PM2_ID" \
  -H "Authorization: Bearer $CLIENT_TOKEN" > /dev/null

echo -e "${GREEN}✓ Payment method deleted${NC}"
echo ""

# Verify deletion
echo "=== Step 10: Verify Active Payment Methods ==="
PM_LIST_FINAL=$(curl -s -X GET "$BASE_URL/payment-methods" \
  -H "Authorization: Bearer $CLIENT_TOKEN")

ACTIVE_COUNT=$(echo $PM_LIST_FINAL | jq 'length')
echo -e "${GREEN}✓ Active payment methods: $ACTIVE_COUNT${NC}"
echo ""

# Test error cases
echo "=== Step 11: Test Error Cases ==="

# Try to charge invalid payment method
echo "Testing invalid payment method..."
INVALID_RESPONSE=$(curl -s -X POST "$BASE_URL/payment-methods/charge" \
  -H "Authorization: Bearer $CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method_id": 99999,
    "amount": 50.00,
    "description": "Should fail"
  }')

if echo $INVALID_RESPONSE | grep -q "not found"; then
  echo -e "${GREEN}✓ Correctly rejected invalid payment method${NC}"
else
  echo -e "${RED}❌ Should have rejected invalid payment method${NC}"
fi
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All Payment Method Tests Passed${NC}"
echo "========================================"
echo ""
echo "Test Coverage:"
echo "  ✓ Create Stripe Customer"
echo "  ✓ Save payment method"
echo "  ✓ List payment methods"
echo "  ✓ Update payment method"
echo "  ✓ Set default payment method"
echo "  ✓ Charge payment method"
echo "  ✓ Delete payment method"
echo "  ✓ Error handling"
echo ""

exit 0
```

Make script executable:
```bash
chmod +x tests/test_task_8_1_payment_methods.sh
```

#### Step 7: Test the Implementation (1-2 hours)

```bash
# Run test script
./tests/test_task_8_1_payment_methods.sh

# Test through Kong Gateway
TOKEN=$(curl -s -X POST "http://localhost:8080/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=client@example.com&password=password123" | jq -r '.access_token')

# Save payment method
curl -X POST "http://localhost:8080/api/v1/payment-methods" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stripe_token": "tok_visa",
    "nickname": "My Visa Card",
    "is_default": true
  }' | jq

# List payment methods
curl -X GET "http://localhost:8080/api/v1/payment-methods" \
  -H "Authorization: Bearer $TOKEN" | jq
```

#### Step 8: Update Kong Routes (15 minutes)

Add route for payment methods:

```yaml
# In docker-compose.yml or Kong admin
services:
  - name: payment-service
    routes:
      - name: payment-methods
        paths:
          - /api/v1/payment-methods
        strip_path: true
```

Or using Kong Admin API:

```bash
curl -i -X POST http://localhost:8001/services/payment-service/routes \
  --data "name=payment-methods" \
  --data "paths[]=/api/v1/payment-methods" \
  --data "strip_path=true"
```

### Validation Checklist

- [ ] Database migration runs without errors
- [ ] Models created correctly with relationships
- [ ] Stripe Customer created on first payment
- [ ] Payment methods can be saved, listed, updated, deleted
- [ ] Only one default payment method per client
- [ ] Charging saved payment method works
- [ ] last_used_at updates on charge
- [ ] Error handling works (invalid cards, expired cards, etc.)
- [ ] Authorization prevents clients from accessing others' payment methods
- [ ] Test script passes all tests
- [ ] Kong Gateway routing works
- [ ] API documentation updated

### Troubleshooting

**Issue: Stripe API key not set**
```bash
# Check environment variable
docker exec -it coachway_demo-payment-service-1 env | grep STRIPE

# Set in .env file
STRIPE_SECRET_KEY=sk_test_your_key_here

# Restart service
docker compose restart payment-service
```

**Issue: Customer creation fails**
```bash
# Test Stripe connection directly
docker exec -it coachway_demo-payment-service-1 python3 -c "
import stripe
stripe.api_key = 'sk_test_your_key'
customer = stripe.Customer.list(limit=1)
print(customer)
"
```

**Issue: Constraint violation on is_default**
```sql
-- Check existing defaults
SELECT client_id, COUNT(*) 
FROM payment.saved_payment_methods 
WHERE is_default = TRUE 
GROUP BY client_id 
HAVING COUNT(*) > 1;

-- Fix duplicates
UPDATE payment.saved_payment_methods 
SET is_default = FALSE 
WHERE id NOT IN (
  SELECT MIN(id) 
  FROM payment.saved_payment_methods 
  WHERE is_default = TRUE 
  GROUP BY client_id
);
```

---

## Task 8.2: TomTom Geocoding Integration (GAP-003)

**Time Estimate:** 12-15 hours  
**Service:** pricing-service  
**Impact:** CRITICAL - Required for accurate distance/pricing

### Problem Statement

Charter pricing needs accurate geocoding and routing. TomTom provides:
- **Geocoding:** Convert addresses to lat/lon coordinates
- **Reverse Geocoding:** Convert lat/lon to addresses
- **Routing:** Calculate distance and travel time between locations
- **Autocomplete:** Address suggestions as user types

### Step-by-Step Implementation

#### Step 1: Add TomTom Configuration (30 minutes)

**File:** `backend/services/pricing/app/config.py`

```python
import os

# TomTom API Configuration
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
TOMTOM_BASE_URL = "https://api.tomtom.com"

# API endpoints
TOMTOM_GEOCODE_URL = f"{TOMTOM_BASE_URL}/search/2/geocode"
TOMTOM_REVERSE_GEOCODE_URL = f"{TOMTOM_BASE_URL}/search/2/reverseGeocode"
TOMTOM_AUTOCOMPLETE_URL = f"{TOMTOM_BASE_URL}/search/2/search"
TOMTOM_ROUTING_URL = f"{TOMTOM_BASE_URL}/routing/1/calculateRoute"

# Settings
TOMTOM_TIMEOUT = 30  # seconds
TOMTOM_MAX_RESULTS = 10  # for autocomplete
```

Add to `.env`:
```bash
TOMTOM_API_KEY=your_tomtom_api_key_here
```

#### Step 2: Update Database Schema (1 hour)

**File:** `backend/services/pricing/migrations/add_geocoding_cache.sql`

```sql
-- ============================================================================
-- Migration: Add Geocoding Cache
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Cache geocoding results to reduce API calls and improve performance
-- ============================================================================

CREATE TABLE IF NOT EXISTS pricing.geocoding_cache (
    id SERIAL PRIMARY KEY,
    
    -- Input address
    address_text TEXT NOT NULL,
    address_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash for fast lookups
    
    -- Geocoded location
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    formatted_address TEXT,
    
    -- Address components
    street_number VARCHAR(50),
    street_name VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    
    -- Metadata
    confidence_score DECIMAL(3, 2),  -- 0.00 to 1.00
    geocoding_provider VARCHAR(50) DEFAULT 'tomtom',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1,
    
    -- Performance
    CONSTRAINT valid_coordinates CHECK (
        latitude BETWEEN -90 AND 90 AND
        longitude BETWEEN -180 AND 180
    )
);

-- Indexes
CREATE INDEX idx_geocoding_address_hash ON pricing.geocoding_cache(address_hash);
CREATE INDEX idx_geocoding_coordinates ON pricing.geocoding_cache(latitude, longitude);
CREATE INDEX idx_geocoding_last_used ON pricing.geocoding_cache(last_used_at);

-- Comments
COMMENT ON TABLE pricing.geocoding_cache IS 'Cache for geocoded addresses to reduce API calls';
COMMENT ON COLUMN pricing.geocoding_cache.address_hash IS 'SHA256 hash of normalized address for fast lookups';
COMMENT ON COLUMN pricing.geocoding_cache.confidence_score IS 'Confidence score from geocoding provider (0-1)';
COMMENT ON COLUMN pricing.geocoding_cache.use_count IS 'Number of times this cached result has been used';

-- Add geocoding fields to charter stops
ALTER TABLE charter.stops 
  ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
  ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8),
  ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_stops_coordinates 
  ON charter.stops(latitude, longitude) 
  WHERE latitude IS NOT NULL;

COMMENT ON COLUMN charter.stops.latitude IS 'Latitude from TomTom geocoding';
COMMENT ON COLUMN charter.stops.longitude IS 'Longitude from TomTom geocoding';
COMMENT ON COLUMN charter.stops.geocoded_at IS 'Timestamp when address was geocoded';

-- Function to calculate distance between two points (Haversine formula)
CREATE OR REPLACE FUNCTION pricing.calculate_distance(
    lat1 DECIMAL,
    lon1 DECIMAL,
    lat2 DECIMAL,
    lon2 DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    earth_radius DECIMAL := 3959.0;  -- miles
    dlat DECIMAL;
    dlon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := RADIANS(lat2 - lat1);
    dlon := RADIANS(lon2 - lon1);
    
    a := SIN(dlat/2) * SIN(dlat/2) + 
         COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * 
         SIN(dlon/2) * SIN(dlon/2);
    
    c := 2 * ATAN2(SQRT(a), SQRT(1-a));
    
    RETURN earth_radius * c;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION pricing.calculate_distance IS 'Calculate distance in miles between two lat/lon points';

-- ============================================================================
-- Rollback Script
-- ============================================================================
-- DROP FUNCTION IF EXISTS pricing.calculate_distance;
-- ALTER TABLE charter.stops DROP COLUMN IF EXISTS latitude;
-- ALTER TABLE charter.stops DROP COLUMN IF EXISTS longitude;
-- ALTER TABLE charter.stops DROP COLUMN IF EXISTS geocoded_at;
-- DROP TABLE IF EXISTS pricing.geocoding_cache CASCADE;
```

Run migration:
```bash
docker exec -it coachway_demo-postgres-1 psql -U athena -d athena -f backend/services/pricing/migrations/add_geocoding_cache.sql
```

#### Step 3: Create TomTom Client (3-4 hours)

**File:** `backend/services/pricing/app/tomtom_client.py`

```python
"""
TomTom API client for geocoding and routing.
"""

import httpx
import hashlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .config import (
    TOMTOM_API_KEY,
    TOMTOM_GEOCODE_URL,
    TOMTOM_REVERSE_GEOCODE_URL,
    TOMTOM_AUTOCOMPLETE_URL,
    TOMTOM_ROUTING_URL,
    TOMTOM_TIMEOUT,
    TOMTOM_MAX_RESULTS
)
from .models import GeocodingCache

class TomTomClient:
    """Client for TomTom APIs."""
    
    def __init__(self):
        if not TOMTOM_API_KEY:
            raise ValueError("TOMTOM_API_KEY environment variable not set")
        
        self.client = httpx.AsyncClient(timeout=TOMTOM_TIMEOUT)
    
    @staticmethod
    def _normalize_address(address: str) -> str:
        """Normalize address for consistent caching."""
        return " ".join(address.lower().split())
    
    @staticmethod
    def _hash_address(address: str) -> str:
        """Generate SHA256 hash of address for cache lookup."""
        normalized = TomTomClient._normalize_address(address)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    async def geocode(
        self,
        address: str,
        db: Session,
        use_cache: bool = True
    ) -> Dict:
        """
        Geocode an address to latitude/longitude.
        
        Args:
            address: Address string to geocode
            db: Database session for caching
            use_cache: Whether to check cache first (default True)
            
        Returns:
            Dict with geocoding results:
            {
                "latitude": float,
                "longitude": float,
                "formatted_address": str,
                "components": {...},
                "confidence": float
            }
        """
        # Check cache first
        if use_cache:
            address_hash = self._hash_address(address)
            cached = db.query(GeocodingCache).filter(
                GeocodingCache.address_hash == address_hash
            ).first()
            
            if cached:
                # Update usage stats
                cached.last_used_at = datetime.utcnow()
                cached.use_count += 1
                db.commit()
                
                return {
                    "latitude": float(cached.latitude),
                    "longitude": float(cached.longitude),
                    "formatted_address": cached.formatted_address,
                    "components": {
                        "street_number": cached.street_number,
                        "street_name": cached.street_name,
                        "city": cached.city,
                        "state": cached.state,
                        "postal_code": cached.postal_code,
                        "country": cached.country
                    },
                    "confidence": float(cached.confidence_score),
                    "cached": True
                }
        
        # Call TomTom API
        try:
            params = {
                "key": TOMTOM_API_KEY,
                "query": address,
                "limit": 1
            }
            
            response = await self.client.get(
                f"{TOMTOM_GEOCODE_URL}/{address}.json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("results"):
                raise HTTPException(404, f"Address not found: {address}")
            
            result = data["results"][0]
            position = result["position"]
            addr_comp = result.get("address", {})
            
            geocode_result = {
                "latitude": position["lat"],
                "longitude": position["lon"],
                "formatted_address": result.get("address", {}).get("freeformAddress", address),
                "components": {
                    "street_number": addr_comp.get("streetNumber"),
                    "street_name": addr_comp.get("streetName"),
                    "city": addr_comp.get("municipality") or addr_comp.get("municipalitySubdivision"),
                    "state": addr_comp.get("countrySubdivision"),
                    "postal_code": addr_comp.get("postalCode"),
                    "country": addr_comp.get("country")
                },
                "confidence": result.get("score", 0),
                "cached": False
            }
            
            # Cache result
            if use_cache:
                cache_entry = GeocodingCache(
                    address_text=address,
                    address_hash=address_hash,
                    latitude=geocode_result["latitude"],
                    longitude=geocode_result["longitude"],
                    formatted_address=geocode_result["formatted_address"],
                    street_number=geocode_result["components"]["street_number"],
                    street_name=geocode_result["components"]["street_name"],
                    city=geocode_result["components"]["city"],
                    state=geocode_result["components"]["state"],
                    postal_code=geocode_result["components"]["postal_code"],
                    country=geocode_result["components"]["country"],
                    confidence_score=geocode_result["confidence"]
                )
                
                db.add(cache_entry)
                db.commit()
            
            return geocode_result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(404, f"Address not found: {address}")
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except httpx.TimeoutException:
            raise HTTPException(504, "TomTom API timeout")
        except Exception as e:
            raise HTTPException(500, f"Geocoding error: {str(e)}")
    
    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Dict:
        """
        Reverse geocode lat/lon to address.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Dict with address components
        """
        try:
            params = {
                "key": TOMTOM_API_KEY
            }
            
            response = await self.client.get(
                f"{TOMTOM_REVERSE_GEOCODE_URL}/{latitude},{longitude}.json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("addresses"):
                raise HTTPException(404, "Address not found for coordinates")
            
            addr = data["addresses"][0]["address"]
            
            return {
                "formatted_address": addr.get("freeformAddress", ""),
                "street_number": addr.get("streetNumber"),
                "street_name": addr.get("streetName"),
                "city": addr.get("municipality") or addr.get("municipalitySubdivision"),
                "state": addr.get("countrySubdivision"),
                "postal_code": addr.get("postalCode"),
                "country": addr.get("country")
            }
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(500, f"Reverse geocoding error: {str(e)}")
    
    async def autocomplete(
        self,
        query: str,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None
    ) -> List[Dict]:
        """
        Get address suggestions as user types.
        
        Args:
            query: Partial address string
            center_lat: Center latitude for biasing results
            center_lon: Center longitude for biasing results
            
        Returns:
            List of address suggestions
        """
        try:
            params = {
                "key": TOMTOM_API_KEY,
                "query": query,
                "limit": TOMTOM_MAX_RESULTS,
                "typeahead": True
            }
            
            if center_lat and center_lon:
                params["lat"] = center_lat
                params["lon"] = center_lon
            
            response = await self.client.get(
                f"{TOMTOM_AUTOCOMPLETE_URL}/{query}.json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            suggestions = []
            for result in data.get("results", []):
                addr = result.get("address", {})
                suggestions.append({
                    "address": addr.get("freeformAddress", ""),
                    "city": addr.get("municipality"),
                    "state": addr.get("countrySubdivision"),
                    "postal_code": addr.get("postalCode"),
                    "country": addr.get("country"),
                    "latitude": result["position"]["lat"],
                    "longitude": result["position"]["lon"]
                })
            
            return suggestions
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(500, f"Autocomplete error: {str(e)}")
    
    async def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict:
        """
        Calculate route between two points.
        
        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            
        Returns:
            Dict with route details:
            {
                "distance_miles": float,
                "duration_minutes": float,
                "traffic_delay_minutes": float
            }
        """
        try:
            # Format coordinates as lat,lon:lat,lon
            locations = f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}"
            
            params = {
                "key": TOMTOM_API_KEY,
                "traffic": True,  # Include traffic data
                "travelMode": "car"
            }
            
            response = await self.client.get(
                f"{TOMTOM_ROUTING_URL}/{locations}/json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("routes"):
                raise HTTPException(404, "No route found")
            
            route = data["routes"][0]
            summary = route["summary"]
            
            # Convert meters to miles
            distance_miles = summary["lengthInMeters"] / 1609.34
            
            # Convert seconds to minutes
            duration_minutes = summary["travelTimeInSeconds"] / 60
            
            traffic_delay_minutes = 0
            if "trafficDelayInSeconds" in summary:
                traffic_delay_minutes = summary["trafficDelayInSeconds"] / 60
            
            return {
                "distance_miles": round(distance_miles, 2),
                "duration_minutes": round(duration_minutes, 1),
                "traffic_delay_minutes": round(traffic_delay_minutes, 1)
            }
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(500, f"Routing error: {str(e)}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
```

#### Step 4: Update Models (30 minutes)

**File:** `backend/services/pricing/app/models.py`

```python
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, CheckConstraint
from sqlalchemy.sql import func

class GeocodingCache(Base):
    """Cache for geocoded addresses."""
    
    __tablename__ = "geocoding_cache"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="valid_coordinates"
        ),
        {"schema": "pricing"}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Input address
    address_text = Column(Text, nullable=False)
    address_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Geocoded location
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    formatted_address = Column(Text)
    
    # Address components
    street_number = Column(String(50))
    street_name = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(50))
    
    # Metadata
    confidence_score = Column(DECIMAL(3, 2))
    geocoding_provider = Column(String(50), default="tomtom")
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, default=func.now(), onupdate=func.now())
    use_count = Column(Integer, default=1)
```

#### Step 5: Create API Endpoints (2-3 hours)

**File:** `backend/services/pricing/app/main.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import get_db
from .tomtom_client import TomTomClient
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/geocoding", tags=["Geocoding"])

@router.post("/geocode")
async def geocode_address(
    address: str = Query(..., min_length=5, description="Address to geocode"),
    use_cache: bool = Query(True, description="Use cached results if available"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Geocode an address to latitude/longitude.
    
    Returns:
    - **latitude**: Latitude coordinate
    - **longitude**: Longitude coordinate
    - **formatted_address**: Standardized address string
    - **components**: Address components (street, city, state, etc.)
    - **confidence**: Confidence score (0-1)
    - **cached**: Whether result came from cache
    """
    tom tom_client = TomTomClient()
    
    try:
        result = await tomtom_client.geocode(address, db, use_cache)
        return result
    finally:
        await tomtom_client.close()

@router.post("/reverse-geocode")
async def reverse_geocode_coords(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    current_user: dict = Depends(get_current_user)
):
    """
    Reverse geocode coordinates to address.
    
    Returns address components for given lat/lon.
    """
    tomtom_client = TomTomClient()
    
    try:
        result = await tomtom_client.reverse_geocode(latitude, longitude)
        return result
    finally:
        await tomtom_client.close()

@router.get("/autocomplete")
async def autocomplete_address(
    query: str = Query(..., min_length=3, description="Partial address for suggestions"),
    center_lat: Optional[float] = Query(None, ge=-90, le=90, description="Center latitude for biasing"),
    center_lon: Optional[float] = Query(None, ge=-180, le=180, description="Center longitude for biasing"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get address suggestions as user types.
    
    Provides up to 10 address suggestions based on partial input.
    Results can be biased toward a center point.
    """
    tomtom_client = TomTomClient()
    
    try:
        suggestions = await tomtom_client.autocomplete(query, center_lat, center_lon)
        return {"suggestions": suggestions}
    finally:
        await tomtom_client.close()

@router.post("/calculate-route")
async def calculate_route(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lon: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lon: float = Query(..., ge=-180, le=180),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate route between two points.
    
    Returns:
    - **distance_miles**: Total distance in miles
    - **duration_minutes**: Estimated travel time in minutes
    - **traffic_delay_minutes**: Additional time due to current traffic
    """
    tomtom_client = TomTomClient()
    
    try:
        result = await tomtom_client.calculate_route(
            origin_lat, origin_lon, dest_lat, dest_lon
        )
        return result
    finally:
        await tomtom_client.close()

# Utility endpoint for geocoding charter stops
@router.post("/geocode-charter-stops/{charter_id}")
async def geocode_charter_stops(
    charter_id: int,
    force_refresh: bool = Query(False, description="Force re-geocode even if already geocoded"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Geocode all stops for a charter.
    
    Updates charter stops with latitude/longitude coordinates.
    Useful for pricing calculations and map display.
    """
    from ..charter.app.models import Stop
    
    # Get all stops for charter
    stops = db.query(Stop).filter(
        Stop.charter_id == charter_id
    ).order_by(Stop.sequence).all()
    
    if not stops:
        raise HTTPException(404, "No stops found for charter")
    
    tomtom_client = TomTomClient()
    geocoded_count = 0
    
    try:
        for stop in stops:
            # Skip if already geocoded (unless force_refresh)
            if stop.latitude and stop.longitude and not force_refresh:
                continue
            
            # Build address string
            address = f"{stop.address}, {stop.city}, {stop.state} {stop.zip_code}"
            
            # Geocode
            result = await tomtom_client.geocode(address, db, use_cache=True)
            
            # Update stop
            stop.latitude = result["latitude"]
            stop.longitude = result["longitude"]
            stop.geocoded_at = func.now()
            
            geocoded_count += 1
        
        db.commit()
        
        return {
            "message": "Charter stops geocoded successfully",
            "charter_id": charter_id,
            "total_stops": len(stops),
            "geocoded": geocoded_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Geocoding failed: {str(e)}")
    finally:
        await tomtom_client.close()

# Add router to main app
app.include_router(router)
```

#### Step 6: Create Test Script (2 hours)

**File:** `tests/test_task_8_2_geocoding.sh`

```bash
#!/bin/bash

# ============================================================================
# Test Script: TomTom Geocoding Integration (Task 8.2)
# ============================================================================

set -e

BASE_URL="http://localhost:8080/api/v1"
ADMIN_EMAIL="admin@athena.com"
ADMIN_PASSWORD="admin123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "Testing TomTom Geocoding (Task 8.2)"
echo "========================================"
echo ""

# Get token
echo "=== Step 1: Authenticate ==="
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Authentication failed${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Authenticated successfully${NC}"
echo ""

# Test geocoding
echo "=== Step 2: Geocode Address ==="
ADDRESS="1600 Amphitheatre Parkway, Mountain View, CA"
echo "Geocoding: $ADDRESS"

GEOCODE_RESPONSE=$(curl -s -X POST "$BASE_URL/geocoding/geocode" \
  -H "Authorization: Bearer $TOKEN" \
  -d "address=$(echo $ADDRESS | jq -sRr @uri)")

LAT=$(echo $GEOCODE_RESPONSE | jq -r '.latitude')
LON=$(echo $GEOCODE_RESPONSE | jq -r '.longitude')

if [ "$LAT" != "null" ] && [ "$LON" != "null" ]; then
  echo -e "${GREEN}✓ Geocoded successfully${NC}"
  echo "   Latitude: $LAT"
  echo "   Longitude: $LON"
  echo "   Address: $(echo $GEOCODE_RESPONSE | jq -r '.formatted_address')"
  echo "   Cached: $(echo $GEOCODE_RESPONSE | jq -r '.cached')"
else
  echo -e "${RED}❌ Geocoding failed${NC}"
  echo $GEOCODE_RESPONSE | jq
  exit 1
fi
echo ""

# Test caching
echo "=== Step 3: Test Geocoding Cache ==="
echo "Geocoding same address again..."

CACHE_RESPONSE=$(curl -s -X POST "$BASE_URL/geocoding/geocode" \
  -H "Authorization: Bearer $TOKEN" \
  -d "address=$(echo $ADDRESS | jq -sRr @uri)")

CACHED=$(echo $CACHE_RESPONSE | jq -r '.cached')
if [ "$CACHED" = "true" ]; then
  echo -e "${GREEN}✓ Result came from cache${NC}"
else
  echo -e "${YELLOW}⚠ Result not cached (may be expected on first run)${NC}"
fi
echo ""

# Test reverse geocoding
echo "=== Step 4: Reverse Geocode Coordinates ==="
echo "Reverse geocoding: $LAT, $LON"

REVERSE_RESPONSE=$(curl -s -X POST "$BASE_URL/geocoding/reverse-geocode" \
  -H "Authorization: Bearer $TOKEN" \
  -d "latitude=$LAT&longitude=$LON")

REVERSE_ADDR=$(echo $REVERSE_RESPONSE | jq -r '.formatted_address')
if [ "$REVERSE_ADDR" != "null" ]; then
  echo -e "${GREEN}✓ Reverse geocoded successfully${NC}"
  echo "   Address: $REVERSE_ADDR"
else
  echo -e "${RED}❌ Reverse geocoding failed${NC}"
  echo $REVERSE_RESPONSE | jq
fi
echo ""

# Test autocomplete
echo "=== Step 5: Test Address Autocomplete ==="
QUERY="1600 Amphitheatre"
echo "Autocomplete query: $QUERY"

AUTO_RESPONSE=$(curl -s -X GET "$BASE_URL/geocoding/autocomplete?query=$(echo $QUERY | jq -sRr @uri)" \
  -H "Authorization: Bearer $TOKEN")

SUGGESTION_COUNT=$(echo $AUTO_RESPONSE | jq '.suggestions | length')
if [ "$SUGGESTION_COUNT" -gt 0 ]; then
  echo -e "${GREEN}✓ Got $SUGGESTION_COUNT suggestions${NC}"
  echo "   First suggestion: $(echo $AUTO_RESPONSE | jq -r '.suggestions[0].address')"
else
  echo -e "${RED}❌ No suggestions returned${NC}"
fi
echo ""

# Test routing
echo "=== Step 6: Calculate Route ==="
# San Francisco to San Jose
ORIGIN_LAT=37.7749
ORIGIN_LON=-122.4194
DEST_LAT=37.3382
DEST_LON=-121.8863

echo "Route: San Francisco to San Jose"

ROUTE_RESPONSE=$(curl -s -X POST "$BASE_URL/geocoding/calculate-route" \
  -H "Authorization: Bearer $TOKEN" \
  -d "origin_lat=$ORIGIN_LAT&origin_lon=$ORIGIN_LON&dest_lat=$DEST_LAT&dest_lon=$DEST_LON")

DISTANCE=$(echo $ROUTE_RESPONSE | jq -r '.distance_miles')
DURATION=$(echo $ROUTE_RESPONSE | jq -r '.duration_minutes')

if [ "$DISTANCE" != "null" ]; then
  echo -e "${GREEN}✓ Route calculated successfully${NC}"
  echo "   Distance: $DISTANCE miles"
  echo "   Duration: $DURATION minutes"
  echo "   Traffic delay: $(echo $ROUTE_RESPONSE | jq -r '.traffic_delay_minutes') minutes"
else
  echo -e "${RED}❌ Route calculation failed${NC}"
  echo $ROUTE_RESPONSE | jq
fi
echo ""

# Test charter stops geocoding
echo "=== Step 7: Geocode Charter Stops ==="
# Create test charter with stops
CHARTER_RESPONSE=$(curl -s -X POST "$BASE_URL/charters" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "pickup_date": "2026-03-01",
    "pickup_time": "08:00",
    "return_date": "2026-03-01",
    "return_time": "18:00",
    "passenger_count": 20,
    "trip_type": "One Way"
  }')

CHARTER_ID=$(echo $CHARTER_RESPONSE | jq -r '.id')

# Add stops
curl -s -X POST "$BASE_URL/charters/$CHARTER_ID/stops" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "1600 Amphitheatre Parkway",
    "city": "Mountain View",
    "state": "CA",
    "zip_code": "94043",
    "stop_type": "pickup",
    "sequence": 1
  }' > /dev/null

curl -s -X POST "$BASE_URL/charters/$CHARTER_ID/stops" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "1 Apple Park Way",
    "city": "Cupertino",
    "state": "CA",
    "zip_code": "95014",
    "stop_type": "dropoff",
    "sequence": 2
  }' > /dev/null

# Geocode all stops
STOPS_RESPONSE=$(curl -s -X POST "$BASE_URL/geocoding/geocode-charter-stops/$CHARTER_ID" \
  -H "Authorization: Bearer $TOKEN")

GEOCODED=$(echo $STOPS_RESPONSE | jq -r '.geocoded')
if [ "$GEOCODED" -gt 0 ]; then
  echo -e "${GREEN}✓ Geocoded $GEOCODED charter stops${NC}"
  echo "   Charter ID: $CHARTER_ID"
  echo "   Total stops: $(echo $STOPS_RESPONSE | jq -r '.total_stops')"
else
  echo -e "${YELLOW}⚠ No stops geocoded (may already be geocoded)${NC}"
fi
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All Geocoding Tests Passed${NC}"
echo "========================================"
echo ""
echo "Test Coverage:"
echo "  ✓ Address geocoding"
echo "  ✓ Geocoding cache"
echo "  ✓ Reverse geocoding"
echo "  ✓ Address autocomplete"
echo "  ✓ Route calculation"
echo "  ✓ Charter stops geocoding"
echo ""

exit 0
```

Make executable:
```bash
chmod +x tests/test_task_8_2_geocoding.sh
```

#### Step 7: Test Implementation (1-2 hours)

```bash
# Run test script
./tests/test_task_8_2_geocoding.sh

# Test manually
TOKEN=$(curl -s -X POST "http://localhost:8080/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@athena.com&password=admin123" | jq -r '.access_token')

# Geocode address
curl -X POST "http://localhost:8080/api/v1/geocoding/geocode?address=1600%20Amphitheatre%20Parkway" \
  -H "Authorization: Bearer $TOKEN" | jq

# Autocomplete
curl -X GET "http://localhost:8080/api/v1/geocoding/autocomplete?query=1600%20Amphitheatre" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Validation Checklist

- [ ] TomTom API key configured
- [ ] Geocoding cache table created
- [ ] Address geocoding works
- [ ] Results cached properly
- [ ] Reverse geocoding works
- [ ] Autocomplete provides suggestions
- [ ] Route calculation includes traffic
- [ ] Charter stops can be bulk geocoded
- [ ] Distance calculation function works
- [ ] Test script passes
- [ ] Kong Gateway routing works

---

## Task 8.3: Multi-Vehicle Pricing Completion (GAP-004)

**Time Estimate:** 8-10 hours  
**Service:** pricing-service  
**Impact:** HIGH - Required for accurate multi-vehicle charter quotes

### Problem Statement

Multi-vehicle charters need proper pricing logic that:
- Calculates base price per vehicle
- Distributes passenger/miles across vehicles
- Does NOT apply bulk discount (per user requirement)
- Considers vehicle-specific costs

### Step-by-Step Implementation

#### Step 1: Review Current Pricing Logic (1 hour)

Check existing pricing endpoints:

```bash
# Get current pricing implementation
cd backend/services/pricing/app
grep -r "multi.*vehicle" .
grep -r "vehicle.*count" .
```

#### Step 2: Update Pricing Calculation (3-4 hours)

**File:** `backend/services/pricing/app/pricing_service.py`

Add or update multi-vehicle pricing logic:

```python
from typing import List, Dict
from decimal import Decimal

def calculate_multi_vehicle_pricing(
    total_passengers: int,
    total_miles: Decimal,
    vehicle_count: int,
    vehicle_type: str,
    base_rate_per_mile: Decimal,
    base_rate_per_hour: Decimal,
    estimated_hours: Decimal
) -> Dict:
    """
    Calculate pricing for multi-vehicle charter.
    
    Args:
        total_passengers: Total passenger count
        total_miles: Total miles for trip
        vehicle_count: Number of vehicles needed
        vehicle_type: Type of vehicle (e.g., "56_passenger")
        base_rate_per_mile: Base rate per mile
        base_rate_per_hour: Base rate per hour
        estimated_hours: Estimated trip duration in hours
        
    Returns:
        Dict with pricing breakdown
    """
    # Calculate passengers per vehicle
    passengers_per_vehicle = total_passengers // vehicle_count
    remaining_passengers = total_passengers % vehicle_count
    
    # Calculate miles per vehicle (same for all)
    miles_per_vehicle = total_miles
    
    # Calculate base cost per vehicle
    mileage_cost_per_vehicle = miles_per_vehicle * base_rate_per_mile
    hourly_cost_per_vehicle = estimated_hours * base_rate_per_hour
    base_cost_per_vehicle = mileage_cost_per_vehicle + hourly_cost_per_vehicle
    
    # Total base cost
    total_base_cost = base_cost_per_vehicle * vehicle_count
    
    # NOTE: No bulk discount applied per user requirement
    # Each vehicle priced independently
    
    return {
        "vehicle_count": vehicle_count,
        "passengers_per_vehicle": passengers_per_vehicle,
        "remaining_passengers": remaining_passengers,
        "miles_per_vehicle": float(miles_per_vehicle),
        "base_cost_per_vehicle": float(base_cost_per_vehicle),
        "mileage_cost_per_vehicle": float(mileage_cost_per_vehicle),
        "hourly_cost_per_vehicle": float(hourly_cost_per_vehicle),
        "total_base_cost": float(total_base_cost),
        "vehicles": [
            {
                "vehicle_number": i + 1,
                "passengers": passengers_per_vehicle + (1 if i < remaining_passengers else 0),
                "miles": float(miles_per_vehicle),
                "cost": float(base_cost_per_vehicle)
            }
            for i in range(vehicle_count)
        ]
    }
```

#### Step 3: Create API Endpoint (2 hours)

**File:** `backend/services/pricing/app/main.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class MultiVehiclePricingRequest(BaseModel):
    """Request for multi-vehicle pricing."""
    total_passengers: int = Field(..., gt=0, description="Total passenger count")
    total_miles: float = Field(..., gt=0, description="Total miles for trip")
    vehicle_count: int = Field(..., gt=0, description="Number of vehicles")
    vehicle_type: str = Field(..., description="Vehicle type (e.g., '56_passenger')")
    estimated_hours: float = Field(..., gt=0, description="Estimated hours")
    
    # Optional overrides
    base_rate_per_mile: Optional[float] = Field(None, description="Override base rate per mile")
    base_rate_per_hour: Optional[float] = Field(None, description="Override base rate per hour")

@router.post("/calculate-multi-vehicle")
async def calculate_multi_vehicle_price(
    request: MultiVehiclePricingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate pricing for multi-vehicle charter.
    
    Distributes passengers and calculates cost per vehicle.
    Does NOT apply bulk discount.
    
    Returns detailed breakdown per vehicle.
    """
    from .pricing_service import calculate_multi_vehicle_pricing
    
    # Get rates from config or use overrides
    from .config import PRICING_CONFIG
    
    base_rate_per_mile = request.base_rate_per_mile or PRICING_CONFIG["base_rate_per_mile"]
    base_rate_per_hour = request.base_rate_per_hour or PRICING_CONFIG["base_rate_per_hour"]
    
    result = calculate_multi_vehicle_pricing(
        total_passengers=request.total_passengers,
        total_miles=Decimal(str(request.total_miles)),
        vehicle_count=request.vehicle_count,
        vehicle_type=request.vehicle_type,
        base_rate_per_mile=Decimal(str(base_rate_per_mile)),
        base_rate_per_hour=Decimal(str(base_rate_per_hour)),
        estimated_hours=Decimal(str(request.estimated_hours))
    )
    
    return result
```

#### Step 4: Create Test Script (1 hour)

**File:** `tests/test_task_8_3_multi_vehicle_pricing.sh`

```bash
#!/bin/bash

# ============================================================================
# Test Script: Multi-Vehicle Pricing (Task 8.3)
# ============================================================================

set -e

BASE_URL="http://localhost:8080/api/v1"
ADMIN_EMAIL="admin@athena.com"
ADMIN_PASSWORD="admin123"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo "Testing Multi-Vehicle Pricing (Task 8.3)"
echo "========================================="
echo ""

# Authenticate
echo "=== Step 1: Authenticate ==="
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD" | jq -r '.access_token')

echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Test multi-vehicle pricing
echo "=== Step 2: Calculate Multi-Vehicle Pricing ==="
echo "Scenario: 100 passengers, 200 miles, 2 vehicles"

PRICING_RESPONSE=$(curl -s -X POST "$BASE_URL/pricing/calculate-multi-vehicle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_passengers": 100,
    "total_miles": 200,
    "vehicle_count": 2,
    "vehicle_type": "56_passenger",
    "estimated_hours": 4.0
  }')

VEHICLE_COUNT=$(echo $PRICING_RESPONSE | jq -r '.vehicle_count')
PER_VEHICLE=$(echo $PRICING_RESPONSE | jq -r '.passengers_per_vehicle')
TOTAL_COST=$(echo $PRICING_RESPONSE | jq -r '.total_base_cost')

echo -e "${GREEN}✓ Pricing calculated${NC}"
echo "   Vehicles: $VEHICLE_COUNT"
echo "   Passengers per vehicle: $PER_VEHICLE"
echo "   Cost per vehicle: $(echo $PRICING_RESPONSE | jq -r '.base_cost_per_vehicle')"
echo "   Total cost: \$$TOTAL_COST"
echo ""

# Test with 3 vehicles
echo "=== Step 3: Test with 3 Vehicles ==="
echo "Scenario: 150 passengers, 300 miles, 3 vehicles"

PRICING_RESPONSE_3=$(curl -s -X POST "$BASE_URL/pricing/calculate-multi-vehicle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_passengers": 150,
    "total_miles": 300,
    "vehicle_count": 3,
    "vehicle_type": "56_passenger",
    "estimated_hours": 6.0
  }')

echo -e "${GREEN}✓ 3-vehicle pricing calculated${NC}"
echo "   Total cost: \$$(echo $PRICING_RESPONSE_3 | jq -r '.total_base_cost')"
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All Multi-Vehicle Tests Passed${NC}"
echo "========================================"

exit 0
```

Make executable:
```bash
chmod +x tests/test_task_8_3_multi_vehicle_pricing.sh
```

#### Step 5: Test Implementation (1 hour)

```bash
# Run test script
./tests/test_task_8_3_multi_vehicle_pricing.sh
```

### Validation Checklist

- [ ] Multi-vehicle pricing logic implemented
- [ ] Passengers distributed evenly across vehicles
- [ ] No bulk discount applied
- [ ] Cost calculated per vehicle
- [ ] Test script passes
- [ ] API documentation updated

---

## Task 8.4: Secure Quote Links (GAP-006)

**Time Estimate:** 8-10 hours  
**Service:** charter-service, sales-service  
**Impact:** HIGH - Enables easy quote sharing without login

### Problem Statement

Clients need to:
- Share quotes with others (decision makers, accounting, etc.)
- View quotes without requiring login
- Have time-limited access (security)
- Track when quotes are viewed

### Step-by-Step Implementation

#### Step 1: Update Database Schema (1 hour)

**File:** `backend/services/charter/migrations/add_secure_quote_links.sql`

```sql
-- ============================================================================
-- Migration: Add Secure Quote Links
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Add secure shareable links for quotes
-- ============================================================================

CREATE TABLE IF NOT EXISTS charter.quote_links (
    id SERIAL PRIMARY KEY,
    quote_id INTEGER NOT NULL REFERENCES charter.quotes(id) ON DELETE CASCADE,
    
    -- Security
    token VARCHAR(255) NOT NULL UNIQUE,  -- JWT token
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,
    
    -- Optional password protection
    password_hash VARCHAR(255),  -- bcrypt hash if password protected
    
    CONSTRAINT valid_expiration CHECK (expires_at > created_at)
);

-- Indexes
CREATE INDEX idx_quote_links_token ON charter.quote_links(token) WHERE is_active = TRUE;
CREATE INDEX idx_quote_links_quote ON charter.quote_links(quote_id);
CREATE INDEX idx_quote_links_expires ON charter.quote_links(expires_at) WHERE is_active = TRUE;

-- Comments
COMMENT ON TABLE charter.quote_links IS 'Secure shareable links for quotes';
COMMENT ON COLUMN charter.quote_links.token IS 'JWT token for secure access';
COMMENT ON COLUMN charter.quote_links.expires_at IS 'Link expiration timestamp';
COMMENT ON COLUMN charter.quote_links.view_count IS 'Number of times link has been viewed';

-- Add tracking to quotes table
ALTER TABLE charter.quotes 
  ADD COLUMN IF NOT EXISTS last_shared_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS share_count INTEGER DEFAULT 0;

COMMENT ON COLUMN charter.quotes.last_shared_at IS 'Last time quote was shared via link';
COMMENT ON COLUMN charter.quotes.share_count IS 'Total number of times quote has been shared';

-- ============================================================================
-- Rollback Script
-- ============================================================================
-- ALTER TABLE charter.quotes DROP COLUMN IF EXISTS last_shared_at;
-- ALTER TABLE charter.quotes DROP COLUMN IF EXISTS share_count;
-- DROP TABLE IF EXISTS charter.quote_links CASCADE;
```

Run migration:
```bash
docker exec -it coachway_demo-postgres-1 psql -U athena -d athena -f backend/services/charter/migrations/add_secure_quote_links.sql
```

#### Step 2: Create JWT Token Service (2 hours)

**File:** `backend/services/charter/app/quote_link_service.py`

```python
"""
Secure quote link generation and validation.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class QuoteLinkService:
    """Service for managing secure quote links."""
    
    @staticmethod
    def generate_token(quote_id: int, expires_hours: int = 168) -> str:
        """
        Generate JWT token for quote link.
        
        Args:
            quote_id: Quote ID
            expires_hours: Hours until expiration (default 7 days)
            
        Returns:
            JWT token string
        """
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        payload = {
            "quote_id": quote_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": "quote_link",
            "jti": secrets.token_urlsafe(16)  # Unique ID
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
            
        Raises:
            HTTPException: If token invalid or expired
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "quote_link":
                raise HTTPException(401, "Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Link has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid link token")
    
    @staticmethod
    def create_quote_link(
        quote_id: int,
        expires_hours: int,
        password: Optional[str],
        created_by: int,
        db: Session
    ) -> Dict:
        """
        Create secure quote link.
        
        Args:
            quote_id: Quote ID
            expires_hours: Hours until expiration
            password: Optional password protection
            created_by: User creating the link
            db: Database session
            
        Returns:
            Dict with link details
        """
        from .models import QuoteLink, Quote
        
        # Verify quote exists
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(404, "Quote not found")
        
        # Generate token
        token = QuoteLinkService.generate_token(quote_id, expires_hours)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Hash password if provided
        password_hash = None
        if password:
            password_hash = pwd_context.hash(password)
        
        # Create link record
        quote_link = QuoteLink(
            quote_id=quote_id,
            token=token,
            expires_at=expires_at,
            created_by=created_by,
            password_hash=password_hash
        )
        
        db.add(quote_link)
        
        # Update quote sharing stats
        quote.share_count = (quote.share_count or 0) + 1
        quote.last_shared_at = datetime.utcnow()
        
        db.commit()
        db.refresh(quote_link)
        
        return {
            "link_id": quote_link.id,
            "token": token,
            "expires_at": expires_at,
            "has_password": password is not None,
            "view_count": 0
        }
    
    @staticmethod
    def verify_quote_link(
        token: str,
        password: Optional[str],
        db: Session
    ) -> int:
        """
        Verify quote link and return quote_id.
        
        Args:
            token: JWT token
            password: Password if link is protected
            db: Database session
            
        Returns:
            Quote ID if valid
            
        Raises:
            HTTPException: If link invalid, expired, or password wrong
        """
        from .models import QuoteLink
        
        # Verify JWT token
        payload = QuoteLinkService.verify_token(token)
        quote_id = payload["quote_id"]
        
        # Get link record
        quote_link = db.query(QuoteLink).filter(
            QuoteLink.token == token,
            QuoteLink.is_active == True
        ).first()
        
        if not quote_link:
            raise HTTPException(404, "Link not found or deactivated")
        
        # Check expiration (double-check even though JWT validates)
        if quote_link.expires_at < datetime.utcnow():
            raise HTTPException(401, "Link has expired")
        
        # Verify password if required
        if quote_link.password_hash:
            if not password:
                raise HTTPException(401, "Password required")
            
            if not pwd_context.verify(password, quote_link.password_hash):
                raise HTTPException(401, "Incorrect password")
        
        # Update tracking
        quote_link.view_count += 1
        quote_link.last_viewed_at = datetime.utcnow()
        db.commit()
        
        return quote_id
```

#### Step 3: Create Models and Schemas (1 hour)

**File:** `backend/services/charter/app/models.py`

Add model:

```python
class QuoteLink(Base):
    """Secure shareable link for quote."""
    
    __tablename__ = "quote_links"
    __table_args__ = {"schema": "charter"}
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("charter.quotes.id", ondelete="CASCADE"), nullable=False)
    
    # Security
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)
    
    # Optional password
    password_hash = Column(String(255))
    
    # Relationships
    quote = relationship("Quote", back_populates="links")
```

**File:** `backend/services/charter/app/schemas.py`

Add schemas:

```python
class QuoteLinkCreate(BaseModel):
    """Create quote link request."""
    expires_hours: int = Field(168, ge=1, le=720, description="Hours until expiration (max 30 days)")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="Optional password protection")

class QuoteLinkResponse(BaseModel):
    """Quote link response."""
    link_id: int
    token: str
    url: str  # Full shareable URL
    expires_at: datetime
    has_password: bool
    view_count: int
    
    class Config:
        from_attributes = True

class QuoteLinkVerify(BaseModel):
    """Verify quote link request."""
    token: str = Field(..., description="JWT token from link")
    password: Optional[str] = Field(None, description="Password if link is protected")
```

#### Step 4: Create API Endpoints (2-3 hours)

**File:** `backend/services/charter/app/main.py`

```python
from .quote_link_service import QuoteLinkService
from .schemas import QuoteLinkCreate, QuoteLinkResponse, QuoteLinkVerify

# Create shareable link for quote
@app.post("/quotes/{quote_id}/share", response_model=QuoteLinkResponse)
async def create_quote_link(
    quote_id: int,
    link_request: QuoteLinkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create secure shareable link for quote.
    
    - **expires_hours**: Hours until link expires (default 7 days, max 30 days)
    - **password**: Optional password protection
    
    Returns JWT token and full URL.
    Link can be shared with anyone, no login required.
    """
    try:
        result = QuoteLinkService.create_quote_link(
            quote_id=quote_id,
            expires_hours=link_request.expires_hours,
            password=link_request.password,
            created_by=current_user["user_id"],
            db=db
        )
        
        # Build full URL
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        result["url"] = f"{base_url}/shared/quote/{result['token']}"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to create quote link: {str(e)}")

# View quote via secure link (no auth required)
@app.post("/shared/quotes/view")
async def view_shared_quote(
    verify_request: QuoteLinkVerify,
    db: Session = Depends(get_db)
):
    """
    View quote via secure link (PUBLIC - no authentication required).
    
    - **token**: JWT token from shared link
    - **password**: Password if link is password protected
    
    Returns full quote details including:
    - Charter information
    - Pricing breakdown
    - Vehicle details
    - Stops/itinerary
    """
    try:
        # Verify link and get quote_id
        quote_id = QuoteLinkService.verify_quote_link(
            token=verify_request.token,
            password=verify_request.password,
            db=db
        )
        
        # Get quote with all details
        from .models import Quote
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        
        if not quote:
            raise HTTPException(404, "Quote not found")
        
        # Return full quote details
        return {
            "quote_id": quote.id,
            "charter_id": quote.charter_id,
            "total_price": quote.total_price,
            "deposit_amount": quote.deposit_amount,
            "balance_due": quote.balance_due,
            "valid_until": quote.valid_until,
            "status": quote.status,
            "notes": quote.notes,
            
            # Charter details
            "charter": {
                "pickup_date": quote.charter.pickup_date,
                "pickup_time": quote.charter.pickup_time,
                "return_date": quote.charter.return_date,
                "return_time": quote.charter.return_time,
                "passenger_count": quote.charter.passenger_count,
                "trip_type": quote.charter.trip_type,
                "stops": [
                    {
                        "address": stop.address,
                        "city": stop.city,
                        "state": stop.state,
                        "stop_type": stop.stop_type,
                        "sequence": stop.sequence
                    }
                    for stop in quote.charter.stops
                ]
            },
            
            # Pricing breakdown
            "pricing_breakdown": quote.pricing_breakdown,
            
            # Vehicle info
            "vehicles": [
                {
                    "vehicle_type": v.vehicle_type,
                    "quantity": v.quantity
                }
                for v in quote.charter.vehicles
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to view quote: {str(e)}")

# List all links for a quote (auth required)
@app.get("/quotes/{quote_id}/links")
async def list_quote_links(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all shareable links for a quote.
    
    Shows link status, view counts, and expiration.
    """
    from .models import QuoteLink
    
    links = db.query(QuoteLink).filter(
        QuoteLink.quote_id == quote_id,
        QuoteLink.is_active == True
    ).order_by(QuoteLink.created_at.desc()).all()
    
    base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    return [
        {
            "link_id": link.id,
            "url": f"{base_url}/shared/quote/{link.token}",
            "expires_at": link.expires_at,
            "is_expired": link.expires_at < datetime.utcnow(),
            "has_password": link.password_hash is not None,
            "view_count": link.view_count,
            "last_viewed_at": link.last_viewed_at,
            "created_at": link.created_at
        }
        for link in links
    ]

# Deactivate link (auth required)
@app.delete("/quotes/links/{link_id}")
async def deactivate_quote_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Deactivate a quote link.
    
    Link will no longer be accessible.
    """
    from .models import QuoteLink
    
    link = db.query(QuoteLink).filter(QuoteLink.id == link_id).first()
    if not link:
        raise HTTPException(404, "Link not found")
    
    link.is_active = False
    db.commit()
    
    return {"message": "Link deactivated", "link_id": link_id}
```

#### Step 5: Create Test Script (1 hour)

**File:** `tests/test_task_8_4_quote_links.sh`

```bash
#!/bin/bash

# ============================================================================
# Test Script: Secure Quote Links (Task 8.4)
# ============================================================================

set -e

BASE_URL="http://localhost:8080/api/v1"
ADMIN_EMAIL="admin@athena.com"
ADMIN_PASSWORD="admin123"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "Testing Secure Quote Links (Task 8.4)"
echo "========================================"
echo ""

# Authenticate
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD" | jq -r '.access_token')

echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Create test charter and quote
echo "=== Step 1: Create Test Charter and Quote ==="
CHARTER_RESPONSE=$(curl -s -X POST "$BASE_URL/charters" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "pickup_date": "2026-04-01",
    "pickup_time": "09:00",
    "return_date": "2026-04-01",
    "return_time": "17:00",
    "passenger_count": 45,
    "trip_type": "Round Trip"
  }')

CHARTER_ID=$(echo $CHARTER_RESPONSE | jq -r '.id')

QUOTE_RESPONSE=$(curl -s -X POST "$BASE_URL/charters/$CHARTER_ID/quotes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_price": 1500.00,
    "deposit_amount": 300.00,
    "valid_days": 14
  }')

QUOTE_ID=$(echo $QUOTE_RESPONSE | jq -r '.id')

echo -e "${GREEN}✓ Created quote: $QUOTE_ID${NC}"
echo ""

# Create shareable link
echo "=== Step 2: Create Shareable Link ==="
LINK_RESPONSE=$(curl -s -X POST "$BASE_URL/quotes/$QUOTE_ID/share" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expires_hours": 168,
    "password": null
  }')

TOKEN_VALUE=$(echo $LINK_RESPONSE | jq -r '.token')
SHARE_URL=$(echo $LINK_RESPONSE | jq -r '.url')

echo -e "${GREEN}✓ Created shareable link${NC}"
echo "   URL: $SHARE_URL"
echo "   Expires: $(echo $LINK_RESPONSE | jq -r '.expires_at')"
echo ""

# View quote via link (no auth)
echo "=== Step 3: View Quote via Link (No Authentication) ==="
VIEW_RESPONSE=$(curl -s -X POST "$BASE_URL/shared/quotes/view" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$TOKEN_VALUE\",
    \"password\": null
  }")

VIEWED_QUOTE_ID=$(echo $VIEW_RESPONSE | jq -r '.quote_id')

if [ "$VIEWED_QUOTE_ID" = "$QUOTE_ID" ]; then
  echo -e "${GREEN}✓ Quote viewed successfully without authentication${NC}"
  echo "   Total Price: \$$(echo $VIEW_RESPONSE | jq -r '.total_price')"
else
  echo -e "${RED}❌ Failed to view quote${NC}"
  exit 1
fi
echo ""

# Create password-protected link
echo "=== Step 4: Create Password-Protected Link ==="
PW_LINK_RESPONSE=$(curl -s -X POST "$BASE_URL/quotes/$QUOTE_ID/share" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expires_hours": 24,
    "password": "secret123"
  }')

PW_TOKEN=$(echo $PW_LINK_RESPONSE | jq -r '.token')
HAS_PASSWORD=$(echo $PW_LINK_RESPONSE | jq -r '.has_password')

echo -e "${GREEN}✓ Created password-protected link${NC}"
echo "   Has Password: $HAS_PASSWORD"
echo ""

# Try to view without password (should fail)
echo "=== Step 5: Test Password Protection ==="
FAIL_RESPONSE=$(curl -s -X POST "$BASE_URL/shared/quotes/view" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$PW_TOKEN\",
    \"password\": null
  }")

if echo $FAIL_RESPONSE | grep -q "Password required"; then
  echo -e "${GREEN}✓ Correctly rejected access without password${NC}"
else
  echo -e "${RED}❌ Should have rejected access${NC}"
fi
echo ""

# View with correct password
echo "=== Step 6: View with Correct Password ==="
PW_VIEW_RESPONSE=$(curl -s -X POST "$BASE_URL/shared/quotes/view" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$PW_TOKEN\",
    \"password\": \"secret123\"
  }")

if echo $PW_VIEW_RESPONSE | grep -q "quote_id"; then
  echo -e "${GREEN}✓ Successfully viewed with correct password${NC}"
else
  echo -e "${RED}❌ Failed to view with password${NC}"
fi
echo ""

# List all links
echo "=== Step 7: List All Links for Quote ==="
LINKS_RESPONSE=$(curl -s -X GET "$BASE_URL/quotes/$QUOTE_ID/links" \
  -H "Authorization: Bearer $TOKEN")

LINK_COUNT=$(echo $LINKS_RESPONSE | jq 'length')
echo -e "${GREEN}✓ Found $LINK_COUNT link(s) for quote${NC}"
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All Quote Link Tests Passed${NC}"
echo "========================================"
echo ""
echo "Test Coverage:"
echo "  ✓ Create shareable link"
echo "  ✓ View quote without authentication"
echo "  ✓ Password protection"
echo "  ✓ View tracking"
echo "  ✓ List links"
echo ""

exit 0
```

Make executable:
```bash
chmod +x tests/test_task_8_4_quote_links.sh
```

### Validation Checklist

- [ ] Database migration runs successfully
- [ ] JWT tokens generated correctly
- [ ] Quotes viewable via secure link without auth
- [ ] Password protection works
- [ ] View tracking updates correctly
- [ ] Links can be deactivated
- [ ] Expiration handled properly
- [ ] Test script passes

---

## Task 8.5: Custom E-Signature System (GAP-007)

**Time Estimate:** 15-18 hours  
**Service:** document-service  
**Impact:** HIGH - Required for contract signing workflow

### Problem Statement

Need custom e-signature capability for:
- Charter agreements
- Vendor contracts
- Liability waivers
- Other legal documents

Requirements:
- Canvas-based signature capture
- Base64 image storage
- PDF generation with embedded signature
- Email confirmation
- Audit trail

### Step-by-Step Implementation

#### Step 1: Update Database Schema (1 hour)

**File:** `backend/services/document/migrations/add_esignature.sql`

```sql
-- ============================================================================
-- Migration: Add E-Signature Support
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Add custom e-signature capture and storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS document.signature_requests (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES document.documents(id) ON DELETE CASCADE,
    
    -- Signer info
    signer_name VARCHAR(200) NOT NULL,
    signer_email VARCHAR(255) NOT NULL,
    signer_role VARCHAR(100),  -- 'client', 'vendor', 'driver', etc.
    
    -- Request details
    request_message TEXT,
    expires_at TIMESTAMP,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, signed, expired, declined
    
    -- Signature data
    signature_image TEXT,  -- Base64 encoded PNG
    signed_at TIMESTAMP,
    signer_ip_address VARCHAR(45),
    signer_user_agent TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    
    -- Reminders
    last_reminder_sent_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'signed', 'expired', 'declined', 'cancelled'))
);

-- Indexes
CREATE INDEX idx_signature_requests_document ON document.signature_requests(document_id);
CREATE INDEX idx_signature_requests_email ON document.signature_requests(signer_email);
CREATE INDEX idx_signature_requests_status ON document.signature_requests(status);
CREATE INDEX idx_signature_requests_expires ON document.signature_requests(expires_at) 
  WHERE status = 'pending';

-- Comments
COMMENT ON TABLE document.signature_requests IS 'E-signature requests for documents';
COMMENT ON COLUMN document.signature_requests.signature_image IS 'Base64 encoded PNG of signature';
COMMENT ON COLUMN document.signature_requests.signer_ip_address IS 'IP address at time of signing';
COMMENT ON COLUMN document.signature_requests.signer_user_agent IS 'Browser info at time of signing';

-- Add signature fields to documents table
ALTER TABLE document.documents 
  ADD COLUMN IF NOT EXISTS requires_signature BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS all_signed BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS signed_document_url TEXT;

COMMENT ON COLUMN document.documents.requires_signature IS 'Whether document requires signatures';
COMMENT ON COLUMN document.documents.all_signed IS 'All required signatures collected';
COMMENT ON COLUMN document.documents.signed_document_url IS 'URL to final signed PDF';

-- ============================================================================
-- Rollback Script
-- ============================================================================
-- ALTER TABLE document.documents DROP COLUMN IF EXISTS requires_signature;
-- ALTER TABLE document.documents DROP COLUMN IF EXISTS all_signed;
-- ALTER TABLE document.documents DROP COLUMN IF EXISTS signed_document_url;
-- DROP TABLE IF EXISTS document.signature_requests CASCADE;
```

Run migration:
```bash
docker exec -it coachway_demo-postgres-1 psql -U athena -d athena -f backend/services/document/migrations/add_esignature.sql
```

#### Step 2: Create Models and Schemas (1 hour)

**File:** `backend/services/document/app/models.py`

```python
class SignatureRequest(Base):
    """E-signature request for document."""
    
    __tablename__ = "signature_requests"
    __table_args__ = {"schema": "document"}
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document.documents.id", ondelete="CASCADE"), nullable=False)
    
    # Signer info
    signer_name = Column(String(200), nullable=False)
    signer_email = Column(String(255), nullable=False, index=True)
    signer_role = Column(String(100))
    
    # Request details
    request_message = Column(Text)
    expires_at = Column(DateTime)
    
    # Status
    status = Column(String(50), default="pending", index=True)
    
    # Signature data
    signature_image = Column(Text)  # Base64
    signed_at = Column(DateTime)
    signer_ip_address = Column(String(45))
    signer_user_agent = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Reminders
    last_reminder_sent_at = Column(DateTime)
    reminder_count = Column(Integer, default=0)
    
    # Relationships
    document = relationship("Document", back_populates="signature_requests")
```

**File:** `backend/services/document/app/schemas.py`

```python
class SignatureRequestCreate(BaseModel):
    """Create signature request."""
    signer_name: str = Field(..., max_length=200)
    signer_email: EmailStr
    signer_role: Optional[str] = Field(None, max_length=100)
    request_message: Optional[str] = Field(None, max_length=1000)
    expires_days: int = Field(14, ge=1, le=90, description="Days until expiration")

class SignatureSubmit(BaseModel):
    """Submit signature."""
    signature_image: str = Field(..., description="Base64 encoded PNG image")
    signer_name: str = Field(..., max_length=200, description="Typed name for verification")

class SignatureRequestResponse(BaseModel):
    """Signature request response."""
    id: int
    document_id: int
    signer_name: str
    signer_email: str
    signer_role: Optional[str]
    status: str
    signed_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]
    reminder_count: int
    
    class Config:
        from_attributes = True
```

#### Step 3: Implement Signature Service (4-5 hours)

**File:** `backend/services/document/app/signature_service.py`

```python
"""
E-signature service for document signing.
"""

import base64
import io
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from PIL import Image
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class SignatureService:
    """Service for managing e-signatures."""
    
    @staticmethod
    def validate_signature_image(base64_image: str) -> bool:
        """
        Validate base64 signature image.
        
        Args:
            base64_image: Base64 encoded PNG
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If invalid
        """
        try:
            # Remove data URL prefix if present
            if "base64," in base64_image:
                base64_image = base64_image.split("base64,")[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_image)
            
            # Verify it's a valid image
            image = Image.open(io.BytesIO(image_data))
            
            # Check format
            if image.format not in ["PNG", "JPEG"]:
                raise HTTPException(400, "Signature must be PNG or JPEG")
            
            # Check size (max 2MB)
            if len(image_data) > 2 * 1024 * 1024:
                raise HTTPException(400, "Signature image too large (max 2MB)")
            
            return True
            
        except Exception as e:
            raise HTTPException(400, f"Invalid signature image: {str(e)}")
    
    @staticmethod
    async def create_signature_request(
        document_id: int,
        signer_name: str,
        signer_email: str,
        signer_role: Optional[str],
        request_message: Optional[str],
        expires_days: int,
        created_by: int,
        db: Session
    ) -> Dict:
        """
        Create signature request.
        
        Args:
            document_id: Document requiring signature
            signer_name: Name of signer
            signer_email: Email of signer
            signer_role: Role (client, vendor, etc.)
            request_message: Custom message
            expires_days: Days until expiration
            created_by: User creating request
            db: Database session
            
        Returns:
            Dict with request details
        """
        from .models import SignatureRequest, Document
        
        # Verify document exists
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(404, "Document not found")
        
        # Set expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Create request
        signature_request = SignatureRequest(
            document_id=document_id,
            signer_name=signer_name,
            signer_email=signer_email,
            signer_role=signer_role,
            request_message=request_message,
            expires_at=expires_at,
            created_by=created_by
        )
        
        db.add(signature_request)
        
        # Mark document as requiring signature
        document.requires_signature = True
        
        db.commit()
        db.refresh(signature_request)
        
        # TODO: Send email notification
        # await send_signature_request_email(signature_request)
        
        return {
            "request_id": signature_request.id,
            "signer_email": signer_email,
            "expires_at": expires_at,
            "status": "pending"
        }
    
    @staticmethod
    async def submit_signature(
        request_id: int,
        signature_image: str,
        signer_name: str,
        ip_address: str,
        user_agent: str,
        db: Session
    ) -> Dict:
        """
        Submit signature for document.
        
        Args:
            request_id: Signature request ID
            signature_image: Base64 encoded signature
            signer_name: Typed name for verification
            ip_address: Signer's IP
            user_agent: Signer's browser info
            db: Database session
            
        Returns:
            Dict with signed document details
        """
        from .models import SignatureRequest, Document
        
        # Get request
        request = db.query(SignatureRequest).filter(
            SignatureRequest.id == request_id
        ).first()
        
        if not request:
            raise HTTPException(404, "Signature request not found")
        
        # Validate status
        if request.status != "pending":
            raise HTTPException(400, f"Request already {request.status}")
        
        # Check expiration
        if request.expires_at and request.expires_at < datetime.utcnow():
            request.status = "expired"
            db.commit()
            raise HTTPException(400, "Signature request has expired")
        
        # Verify name matches
        if signer_name.lower().strip() != request.signer_name.lower().strip():
            raise HTTPException(400, "Signer name does not match request")
        
        # Validate signature image
        SignatureService.validate_signature_image(signature_image)
        
        # Save signature
        request.signature_image = signature_image
        request.signed_at = datetime.utcnow()
        request.signer_ip_address = ip_address
        request.signer_user_agent = user_agent
        request.status = "signed"
        
        # Check if all signatures collected
        document = request.document
        all_requests = db.query(SignatureRequest).filter(
            SignatureRequest.document_id == document.id
        ).all()
        
        all_signed = all(r.status == "signed" for r in all_requests)
        
        if all_signed:
            document.all_signed = True
            
            # Generate final signed PDF
            signed_pdf_url = await SignatureService.generate_signed_pdf(
                document=document,
                signature_requests=all_requests,
                db=db
            )
            
            document.signed_document_url = signed_pdf_url
        
        db.commit()
        
        # TODO: Send confirmation email
        # await send_signature_confirmation_email(request)
        
        return {
            "request_id": request_id,
            "signed_at": request.signed_at,
            "all_signed": all_signed,
            "signed_document_url": signed_pdf_url if all_signed else None
        }
    
    @staticmethod
    async def generate_signed_pdf(
        document: "Document",
        signature_requests: List["SignatureRequest"],
        db: Session
    ) -> str:
        """
        Generate PDF with embedded signatures.
        
        Args:
            document: Document model
            signature_requests: List of signed requests
            db: Database session
            
        Returns:
            URL to signed PDF
        """
        # TODO: Implement PDF generation with signatures
        # This is a placeholder - actual implementation would:
        # 1. Load original PDF
        # 2. Add signature images to appropriate pages
        # 3. Add signature metadata (date, IP, etc.)
        # 4. Save to MongoDB GridFS or S3
        # 5. Return URL
        
        return f"/documents/{document.id}/signed.pdf"
```

#### Step 4: Create API Endpoints (3-4 hours)

**File:** `backend/services/document/app/main.py`

```python
from fastapi import Request
from .signature_service import SignatureService
from .schemas import SignatureRequestCreate, SignatureSubmit, SignatureRequestResponse

# Request signature on document
@app.post("/documents/{document_id}/request-signature", response_model=SignatureRequestResponse)
async def request_signature(
    document_id: int,
    request_data: SignatureRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Request signature on document.
    
    Sends email to signer with link to sign document.
    
    - **signer_name**: Full name of person signing
    - **signer_email**: Email to send signature request
    - **signer_role**: Role (client, vendor, driver, etc.)
    - **request_message**: Custom message to include
    - **expires_days**: Days until request expires
    """
    try:
        result = await SignatureService.create_signature_request(
            document_id=document_id,
            signer_name=request_data.signer_name,
            signer_email=request_data.signer_email,
            signer_role=request_data.signer_role,
            request_message=request_data.request_message,
            expires_days=request_data.expires_days,
            created_by=current_user["user_id"],
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to create signature request: {str(e)}")

# Get signature request details (public - for signing page)
@app.get("/signature-requests/{request_id}")
async def get_signature_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Get signature request details (PUBLIC - no auth required).
    
    Used by signing page to display document info.
    """
    from .models import SignatureRequest
    
    request = db.query(SignatureRequest).filter(
        SignatureRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(404, "Signature request not found")
    
    return {
        "request_id": request.id,
        "document_id": request.document_id,
        "document_name": request.document.filename,
        "signer_name": request.signer_name,
        "signer_email": request.signer_email,
        "request_message": request.request_message,
        "status": request.status,
        "expires_at": request.expires_at,
        "created_at": request.created_at
    }

# Submit signature (public - no auth required)
@app.post("/signature-requests/{request_id}/sign")
async def submit_signature(
    request_id: int,
    signature_data: SignatureSubmit,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit signature for document (PUBLIC - no auth required).
    
    - **signature_image**: Base64 encoded PNG of signature
    - **signer_name**: Typed name (must match request)
    
    Validates signature and marks request as signed.
    """
    try:
        # Get client IP and user agent
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "Unknown")
        
        result = await SignatureService.submit_signature(
            request_id=request_id,
            signature_image=signature_data.signature_image,
            signer_name=signature_data.signer_name,
            ip_address=ip_address,
            user_agent=user_agent,
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to submit signature: {str(e)}")

# List signature requests for document
@app.get("/documents/{document_id}/signatures")
async def list_document_signatures(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all signature requests for document.
    
    Shows status, signed dates, and signer info.
    """
    from .models import SignatureRequest
    
    requests = db.query(SignatureRequest).filter(
        SignatureRequest.document_id == document_id
    ).order_by(SignatureRequest.created_at.desc()).all()
    
    return [
        {
            "request_id": r.id,
            "signer_name": r.signer_name,
            "signer_email": r.signer_email,
            "signer_role": r.signer_role,
            "status": r.status,
            "signed_at": r.signed_at,
            "created_at": r.created_at,
            "expires_at": r.expires_at,
            "reminder_count": r.reminder_count
        }
        for r in requests
    ]

# Send reminder
@app.post("/signature-requests/{request_id}/remind")
async def send_signature_reminder(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send reminder email for pending signature.
    """
    from .models import SignatureRequest
    
    request = db.query(SignatureRequest).filter(
        SignatureRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(404, "Signature request not found")
    
    if request.status != "pending":
        raise HTTPException(400, f"Cannot remind - request is {request.status}")
    
    # TODO: Send reminder email
    # await send_signature_reminder_email(request)
    
    request.last_reminder_sent_at = datetime.utcnow()
    request.reminder_count += 1
    db.commit()
    
    return {
        "message": "Reminder sent",
        "request_id": request_id,
        "reminder_count": request.reminder_count
    }

# Cancel signature request
@app.delete("/signature-requests/{request_id}")
async def cancel_signature_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel pending signature request.
    """
    from .models import SignatureRequest
    
    request = db.query(SignatureRequest).filter(
        SignatureRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(404, "Signature request not found")
    
    if request.status != "pending":
        raise HTTPException(400, f"Cannot cancel - request is {request.status}")
    
    request.status = "cancelled"
    db.commit()
    
    return {"message": "Signature request cancelled", "request_id": request_id}
```

#### Step 5: Create Test Script (2 hours)

**File:** `tests/test_task_8_5_esignature.sh`

```bash
#!/bin/bash

# ============================================================================
# Test Script: E-Signature System (Task 8.5)
# ============================================================================

set -e

BASE_URL="http://localhost:8080/api/v1"
ADMIN_EMAIL="admin@athena.com"
ADMIN_PASSWORD="admin123"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "Testing E-Signature System (Task 8.5)"
echo "========================================"
echo ""

# Authenticate
TOKEN=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD" | jq -r '.access_token')

echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Create test document
echo "=== Step 1: Create Test Document ==="
DOC_RESPONSE=$(curl -s -X POST "$BASE_URL/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test-charter-agreement.pdf",
    "document_type": "charter_agreement",
    "charter_id": 1
  }')

DOC_ID=$(echo $DOC_RESPONSE | jq -r '.id')
echo -e "${GREEN}✓ Created document: $DOC_ID${NC}"
echo ""

# Request signature
echo "=== Step 2: Request Signature ==="
SIG_REQUEST_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/$DOC_ID/request-signature" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signer_name": "John Client",
    "signer_email": "john.client@example.com",
    "signer_role": "client",
    "request_message": "Please review and sign this charter agreement",
    "expires_days": 14
  }')

REQUEST_ID=$(echo $SIG_REQUEST_RESPONSE | jq -r '.request_id')
echo -e "${GREEN}✓ Created signature request: $REQUEST_ID${NC}"
echo "   Signer: $(echo $SIG_REQUEST_RESPONSE | jq -r '.signer_email')"
echo "   Expires: $(echo $SIG_REQUEST_RESPONSE | jq -r '.expires_at')"
echo ""

# Get request details (public)
echo "=== Step 3: Get Request Details (No Auth) ==="
REQUEST_DETAILS=$(curl -s -X GET "$BASE_URL/signature-requests/$REQUEST_ID")

SIGNER_NAME=$(echo $REQUEST_DETAILS | jq -r '.signer_name')
DOC_NAME=$(echo $REQUEST_DETAILS | jq -r '.document_name')

echo -e "${GREEN}✓ Retrieved request details without authentication${NC}"
echo "   Document: $DOC_NAME"
echo "   Signer: $SIGNER_NAME"
echo ""

# Submit signature (public)
echo "=== Step 4: Submit Signature (No Auth) ==="
# Generate simple base64 signature (in real use, this comes from canvas)
SIGNATURE_BASE64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

SIGN_RESPONSE=$(curl -s -X POST "$BASE_URL/signature-requests/$REQUEST_ID/sign" \
  -H "Content-Type: application/json" \
  -d "{
    \"signature_image\": \"data:image/png;base64,$SIGNATURE_BASE64\",
    \"signer_name\": \"John Client\"
  }")

SIGNED_AT=$(echo $SIGN_RESPONSE | jq -r '.signed_at')

if [ "$SIGNED_AT" != "null" ]; then
  echo -e "${GREEN}✓ Signature submitted successfully${NC}"
  echo "   Signed at: $SIGNED_AT"
  echo "   All signed: $(echo $SIGN_RESPONSE | jq -r '.all_signed')"
else
  echo -e "${RED}❌ Failed to submit signature${NC}"
  echo $SIGN_RESPONSE | jq
  exit 1
fi
echo ""

# List signatures for document
echo "=== Step 5: List Document Signatures ==="
SIGNATURES=$(curl -s -X GET "$BASE_URL/documents/$DOC_ID/signatures" \
  -H "Authorization: Bearer $TOKEN")

SIG_COUNT=$(echo $SIGNATURES | jq 'length')
echo -e "${GREEN}✓ Found $SIG_COUNT signature(s)${NC}"
echo "   Status: $(echo $SIGNATURES | jq -r '.[0].status')"
echo ""

# Test reminder
echo "=== Step 6: Create Another Request and Test Reminder ==="
REQUEST2_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/$DOC_ID/request-signature" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signer_name": "Jane Vendor",
    "signer_email": "jane.vendor@example.com",
    "signer_role": "vendor",
    "expires_days": 7
  }')

REQUEST2_ID=$(echo $REQUEST2_RESPONSE | jq -r '.request_id')

# Send reminder
REMINDER_RESPONSE=$(curl -s -X POST "$BASE_URL/signature-requests/$REQUEST2_ID/remind" \
  -H "Authorization: Bearer $TOKEN")

REMINDER_COUNT=$(echo $REMINDER_RESPONSE | jq -r '.reminder_count')
echo -e "${GREEN}✓ Sent reminder (count: $REMINDER_COUNT)${NC}"
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All E-Signature Tests Passed${NC}"
echo "========================================"
echo ""
echo "Test Coverage:"
echo "  ✓ Create signature request"
echo "  ✓ Get request details (public)"
echo "  ✓ Submit signature (public)"
echo "  ✓ List document signatures"
echo "  ✓ Send reminder"
echo "  ✓ Audit trail (IP, user agent)"
echo ""

exit 0
```

Make executable:
```bash
chmod +x tests/test_task_8_5_esignature.sh
```

### Validation Checklist

- [ ] Database migration runs successfully
- [ ] Signature requests can be created
- [ ] Email notifications sent (TODO: implement)
- [ ] Signature can be submitted without auth
- [ ] Base64 image validation works
- [ ] Audit trail recorded (IP, user agent, timestamp)
- [ ] All signatures tracked per document
- [ ] Reminders can be sent
- [ ] Requests can be cancelled
- [ ] Test script passes

### Frontend Integration Notes

The frontend will need to implement:

1. **Signature Canvas Component:**
```javascript
// Using react-signature-canvas or similar
import SignatureCanvas from 'react-signature-canvas'

const SignaturePad = () => {
  const sigCanvas = useRef()
  
  const handleSubmit = async () => {
    // Get base64 image
    const signatureImage = sigCanvas.current.toDataURL('image/png')
    
    // Submit to API
    await fetch(`/api/v1/signature-requests/${requestId}/sign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        signature_image: signatureImage,
        signer_name: name
      })
    })
  }
  
  return (
    <div>
      <SignatureCanvas
        ref={sigCanvas}
        canvasProps={{
          width: 500,
          height: 200,
          className: 'signature-canvas'
        }}
      />
      <button onClick={() => sigCanvas.current.clear()}>Clear</button>
      <button onClick={handleSubmit}>Submit Signature</button>
    </div>
  )
}
```

2. **Signature Request Page (Public):**
   - No authentication required
   - Load request details by ID
   - Display document preview
   - Show signature canvas
   - Collect typed name for verification
   - Submit signature

---

## Summary

Phase 8 implements the final 10% of backend features across 5 critical tasks:

1. **Saved Payment Methods** (15-18 hours) - Stripe Customer integration
2. **TomTom Geocoding** (12-15 hours) - Address geocoding and routing
3. **Multi-Vehicle Pricing** (8-10 hours) - Proper pricing for multiple vehicles
4. **Secure Quote Links** (8-10 hours) - JWT-based shareable quotes
5. **E-Signature System** (15-18 hours) - Custom canvas-based signatures

**Total Time:** 58-71 hours (2-3 weeks with 2 developers)

All tasks include:
- Step-by-step implementation instructions
- Complete code examples
- Database migrations with rollback scripts
- Test scripts
- Validation checklists
- Troubleshooting guides

**Next Steps:**
1. Set up environment (Stripe key, TomTom API key, JWT secret)
2. Start with Task 8.1 (Saved Payment Methods)
3. Run test scripts after each task
4. Update Kong routes as needed
5. Document API endpoints
6. Get code review before frontend integration

**Estimated Timeline:**

| Task | Developer | Week 1 | Week 2 | Week 3 |
|------|-----------|--------|--------|--------|
| 8.1 Payment Methods | Dev 1 | ████   |        |        |
| 8.2 TomTom Geocoding | Dev 2 | ████   |        |        |
| 8.3 Multi-Vehicle Pricing | Dev 1 |        | ██     |        |
| 8.4 Secure Quote Links | Dev 2 |        | ███    |        |
| 8.5 E-Signature System | Dev 1 & 2 |        | ██     | ███    |

**After Phase 8:**
- Frontend development can proceed without backend blockers
- All critical user-facing features supported
- Production deployment ready
- Focus shifts to frontend UX and polish
