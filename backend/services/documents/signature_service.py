"""
E-signature service for document signing - Task 8.5
Handles signature requests, validation, and submission
"""

import base64
import io
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class SignatureService:
    """Service for managing e-signatures."""
    
    @staticmethod
    def validate_signature_image(base64_image: str) -> bool:
        """
        Validate base64 signature image.
        
        Args:
            base64_image: Base64 encoded PNG/JPEG
            
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
            
            # Check size (max 2MB)
            if len(image_data) > 2 * 1024 * 1024:
                raise HTTPException(400, "Signature image too large (max 2MB)")
            
            # If PIL is available, verify it's a valid image
            if PILLOW_AVAILABLE:
                image = Image.open(io.BytesIO(image_data))
                
                # Check format
                if image.format not in ["PNG", "JPEG", "JPG"]:
                    raise HTTPException(400, "Signature must be PNG or JPEG")
                
                # Verify image has content (not blank)
                if image.size[0] < 50 or image.size[1] < 20:
                    raise HTTPException(400, "Signature image too small")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Invalid signature image: {str(e)}")
    
    @staticmethod
    def create_signature_request(
        document_id: int,
        signer_name: str,
        signer_email: str,
        signer_role: Optional[str],
        request_message: Optional[str],
        expires_days: int,
        created_by: Optional[int],
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
        from models import SignatureRequest, Document
        
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
        
        return {
            "request_id": signature_request.id,
            "signer_email": signer_email,
            "expires_at": expires_at.isoformat(),
            "status": "pending",
            "message": "Signature request created successfully"
        }
    
    @staticmethod
    def submit_signature(
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
        from models import SignatureRequest, Document
        
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
        
        # Verify name matches (case-insensitive, whitespace-trimmed)
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
        
        signed_document_url = None
        if all_signed:
            document.all_signed = True
            # In production, this would generate a PDF with embedded signatures
            signed_document_url = f"/documents/{document.id}/signed.pdf"
            document.signed_document_url = signed_document_url
        
        db.commit()
        
        return {
            "request_id": request_id,
            "signed_at": request.signed_at.isoformat(),
            "all_signed": all_signed,
            "signed_document_url": signed_document_url,
            "message": "Signature submitted successfully"
        }
    
    @staticmethod
    def get_signature_request(request_id: int, db: Session) -> Dict:
        """
        Get signature request details (for public signing page).
        
        Args:
            request_id: Request ID
            db: Database session
            
        Returns:
            Dict with request details
        """
        from models import SignatureRequest
        
        request = db.query(SignatureRequest).filter(
            SignatureRequest.id == request_id
        ).first()
        
        if not request:
            raise HTTPException(404, "Signature request not found")
        
        return {
            "request_id": request.id,
            "document_id": request.document_id,
            "document_name": request.document.filename if request.document else "Unknown",
            "signer_name": request.signer_name,
            "signer_email": request.signer_email,
            "request_message": request.request_message,
            "status": request.status,
            "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            "created_at": request.created_at.isoformat()
        }
    
    @staticmethod
    def list_document_signatures(document_id: int, db: Session) -> List[Dict]:
        """
        List all signature requests for document.
        
        Args:
            document_id: Document ID
            db: Database session
            
        Returns:
            List of signature requests
        """
        from models import SignatureRequest
        
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
                "signed_at": r.signed_at.isoformat() if r.signed_at else None,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "reminder_count": r.reminder_count
            }
            for r in requests
        ]
    
    @staticmethod
    def send_reminder(request_id: int, db: Session) -> Dict:
        """
        Send reminder for pending signature.
        
        Args:
            request_id: Request ID
            db: Database session
            
        Returns:
            Dict with reminder status
        """
        from models import SignatureRequest
        
        request = db.query(SignatureRequest).filter(
            SignatureRequest.id == request_id
        ).first()
        
        if not request:
            raise HTTPException(404, "Signature request not found")
        
        if request.status != "pending":
            raise HTTPException(400, f"Cannot remind - request is {request.status}")
        
        # Update reminder tracking
        request.last_reminder_sent_at = datetime.utcnow()
        request.reminder_count += 1
        db.commit()
        
        return {
            "message": "Reminder sent",
            "request_id": request_id,
            "reminder_count": request.reminder_count
        }
    
    @staticmethod
    def cancel_signature_request(request_id: int, db: Session) -> Dict:
        """
        Cancel pending signature request.
        
        Args:
            request_id: Request ID
            db: Database session
            
        Returns:
            Dict with cancellation status
        """
        from models import SignatureRequest
        
        request = db.query(SignatureRequest).filter(
            SignatureRequest.id == request_id
        ).first()
        
        if not request:
            raise HTTPException(404, "Signature request not found")
        
        if request.status != "pending":
            raise HTTPException(400, f"Cannot cancel - request is {request.status}")
        
        request.status = "cancelled"
        db.commit()
        
        return {
            "message": "Signature request cancelled",
            "request_id": request_id
        }
