import hashlib
import hmac
import json
from fastapi import Request, HTTPException
from config import settings

class StripeWebhookHandler:
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise Exception("Webhook secret not configured")
        
        try:
            # Extract timestamp and signature from header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                key, value = element.split('=')
                if key == 't':
                    timestamp = value
                elif key.startswith('v'):
                    signatures.append(value)
            
            if not timestamp or not signatures:
                return False
            
            # Create expected signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                settings.STRIPE_WEBHOOK_SECRET.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return any(
                hmac.compare_digest(expected_sig, sig) 
                for sig in signatures
            )
            
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    @staticmethod
    async def construct_event(request: Request):
        """Construct and verify webhook event"""
        payload = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        if not StripeWebhookHandler.verify_signature(payload, signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        try:
            event = json.loads(payload)
            return event
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid payload")
