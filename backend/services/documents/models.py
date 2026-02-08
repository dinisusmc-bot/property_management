from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class CharterDocument(Base):
    __tablename__ = "charter_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, nullable=False, index=True)
    
    # Document details
    document_type = Column(String(50), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # MongoDB reference
    mongodb_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Metadata
    description = Column(Text)
    uploaded_by = Column(Integer)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Document model for e-signature system."""
    __tablename__ = "documents"
    __table_args__ = {"schema": "document"}
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    charter_id = Column(Integer)
    uploaded_by = Column(Integer)
    
    # E-signature fields (Task 8.5)
    requires_signature = Column(Boolean, default=False)
    all_signed = Column(Boolean, default=False)
    signed_document_url = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    signature_requests = relationship("SignatureRequest", back_populates="document", cascade="all, delete-orphan")


class SignatureRequest(Base):
    """E-signature request for document - Task 8.5."""
    __tablename__ = "signature_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'signed', 'expired', 'declined', 'cancelled')",
            name="valid_signature_status"
        ),
        {"schema": "document"}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document.documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Signer info
    signer_name = Column(String(200), nullable=False)
    signer_email = Column(String(255), nullable=False, index=True)
    signer_role = Column(String(100))  # client, vendor, driver, etc.
    
    # Request details
    request_message = Column(Text)
    expires_at = Column(DateTime)
    
    # Status
    status = Column(String(50), default="pending", index=True)
    
    # Signature data
    signature_image = Column(Text)  # Base64 encoded PNG
    signed_at = Column(DateTime)
    signer_ip_address = Column(String(45))
    signer_user_agent = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer)
    
    # Reminders
    last_reminder_sent_at = Column(DateTime)
    reminder_count = Column(Integer, default=0)
    
    # Relationships
    document = relationship("Document", back_populates="signature_requests")
