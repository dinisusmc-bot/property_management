import stripe
import json
import pika
from datetime import datetime
from sqlalchemy.orm import Session
from config import settings
from models import Payment, PaymentRefund
from schemas import PaymentCreate, RefundCreate

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    
    @staticmethod
    def create_payment_intent(db: Session, charter_id: int, amount: float, payment_type: str, description: str = None):
        """Create a Stripe PaymentIntent"""
        try:
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe uses cents
                currency="usd",
                metadata={
                    "charter_id": charter_id,
                    "payment_type": payment_type
                },
                description=description or f"{payment_type} for Charter #{charter_id}"
            )
            
            # Create payment record
            payment = Payment(
                charter_id=charter_id,
                amount=amount,
                payment_type=payment_type,
                payment_method="card",
                status="pending",
                stripe_payment_intent_id=intent.id,
                description=description
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount,
                "currency": "usd",
                "payment_id": payment.id
            }
            
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def process_payment_succeeded(db: Session, payment_intent_id: str, charge_data: dict):
        """Handle successful payment"""
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()
        
        if payment:
            payment.status = "succeeded"
            payment.stripe_charge_id = charge_data.get('id')
            payment.processed_at = datetime.utcnow()
            
            # Extract card details
            if 'payment_method_details' in charge_data:
                card = charge_data['payment_method_details'].get('card', {})
                payment.card_last4 = card.get('last4')
                payment.card_brand = card.get('brand')
            
            db.commit()
            
            # Send notification
            PaymentService._send_payment_notification(
                charter_id=payment.charter_id,
                payment_type=payment.payment_type,
                amount=payment.amount,
                status="succeeded"
            )
            
            return payment
        return None
    
    @staticmethod
    def process_payment_failed(db: Session, payment_intent_id: str, failure_code: str, failure_message: str):
        """Handle failed payment"""
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()
        
        if payment:
            payment.status = "failed"
            payment.failure_code = failure_code
            payment.failure_reason = failure_message
            db.commit()
            
            # Send failure notification
            PaymentService._send_payment_notification(
                charter_id=payment.charter_id,
                payment_type=payment.payment_type,
                amount=payment.amount,
                status="failed",
                failure_reason=failure_message
            )
            
            return payment
        return None
    
    @staticmethod
    def create_refund(db: Session, refund_data: RefundCreate):
        """Process a refund"""
        payment = db.query(Payment).filter(Payment.id == refund_data.payment_id).first()
        if not payment or not payment.stripe_charge_id:
            raise Exception("Payment not found or not eligible for refund")
        
        try:
            # Create Stripe refund
            refund_amount = refund_data.amount or payment.amount
            stripe_refund = stripe.Refund.create(
                charge=payment.stripe_charge_id,
                amount=int(refund_amount * 100),
                reason=refund_data.reason
            )
            
            # Create refund record
            refund = PaymentRefund(
                payment_id=payment.id,
                amount=refund_amount,
                reason=refund_data.reason,
                status="processing",
                stripe_refund_id=stripe_refund.id,
                processed_at=datetime.utcnow()
            )
            db.add(refund)
            db.commit()
            db.refresh(refund)
            
            return refund
            
        except stripe.error.StripeError as e:
            raise Exception(f"Refund failed: {str(e)}")
    
    @staticmethod
    def charge_saved_card(db: Session, charter_id: int, customer_id: str, payment_method_id: str, amount: float, payment_type: str):
        """Charge a saved payment method"""
        try:
            # Create and confirm PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency="usd",
                customer=customer_id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
                metadata={
                    "charter_id": charter_id,
                    "payment_type": payment_type
                }
            )
            
            # Create payment record
            payment = Payment(
                charter_id=charter_id,
                amount=amount,
                payment_type=payment_type,
                payment_method="card",
                status="processing",
                stripe_payment_intent_id=intent.id,
                stripe_customer_id=customer_id
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            return payment
            
        except stripe.error.CardError as e:
            # Card was declined
            raise Exception(f"Card declined: {e.user_message}")
        except stripe.error.StripeError as e:
            raise Exception(f"Payment failed: {str(e)}")
    
    @staticmethod
    def _send_payment_notification(charter_id: int, payment_type: str, amount: float, status: str, failure_reason: str = None):
        """Send payment notification to RabbitMQ"""
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            channel = connection.channel()
            channel.queue_declare(queue='payment_notifications', durable=True)
            
            message = {
                "type": "payment_notification",
                "charter_id": charter_id,
                "payment_type": payment_type,
                "amount": amount,
                "status": status,
                "failure_reason": failure_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='payment_notifications',
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Persistent
            )
            
            connection.close()
        except Exception as e:
            print(f"Failed to send notification: {e}")
