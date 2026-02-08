"""
Stripe Customer management for saved payment methods.
"""

import stripe
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from config import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeCustomerService:
    """Service for managing Stripe Customers and payment methods."""
    
    @staticmethod
    async def create_or_get_customer(
        client_id: int,
        email: str,
        name: str,
        db: Session,
        existing_stripe_customer_id: Optional[str] = None
    ) -> str:
        """
        Create Stripe Customer if doesn't exist, or return existing customer_id.
        
        Args:
            client_id: Client database ID
            email: Client email
            name: Client name
            db: Database session
            existing_stripe_customer_id: Existing Stripe Customer ID if known
            
        Returns:
            Stripe Customer ID (cus_xxx)
            
        Note:
            In a microservices architecture, this should update the client via API call.
            For now, we accept the stripe_customer_id if it exists.
        """
        if existing_stripe_customer_id:
            return existing_stripe_customer_id
        
        try:
            # Create new Stripe Customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"client_id": str(client_id)}
            )
            
            # Note: In production, update client.stripe_customer_id via API call to clients service
            # For now, return the customer ID and caller must handle storage
            
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
