from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class DocumentUpload(BaseModel):
    charter_id: int
    document_type: str  # approval, booking, confirmation, contract, invoice, receipt, insurance, other
    description: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    charter_id: int
    document_type: str
    file_name: str
    file_size: int
    mime_type: str
    mongodb_id: str
    description: Optional[str]
    uploaded_by: Optional[int]
    uploaded_at: datetime
    download_url: str
    
    class Config:
        from_attributes = True


# Task 8.5: E-Signature Schemas

class SignatureRequestCreate(BaseModel):
    """Create signature request."""
    signer_name: str = Field(..., max_length=200, description="Full name of person signing")
    signer_email: EmailStr = Field(..., description="Email to send signature request")
    signer_role: Optional[str] = Field(None, max_length=100, description="Role: client, vendor, driver, etc.")
    request_message: Optional[str] = Field(None, max_length=1000, description="Custom message to signer")
    expires_days: int = Field(14, ge=1, le=90, description="Days until request expires (max 90)")


class SignatureSubmit(BaseModel):
    """Submit signature for document."""
    signature_image: str = Field(..., description="Base64 encoded PNG image of signature")
    signer_name: str = Field(..., max_length=200, description="Typed name for verification (must match request)")


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


class SignatureRequestDetail(BaseModel):
    """Detailed signature request info (for public signing page)."""
    request_id: int
    document_id: int
    document_name: str
    signer_name: str
    signer_email: str
    request_message: Optional[str]
    status: str
    expires_at: Optional[datetime]
    created_at: datetime
