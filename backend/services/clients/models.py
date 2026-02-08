"""
Database models for Client Service
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Client(Base):
    """Client model"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)  # corporate, personal, government, nonprofit
    
    # Contact information
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    
    # Address
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    
    # Business details
    credit_limit = Column(Float, default=0.0)
    balance_owed = Column(Float, default=0.0)
    payment_terms = Column(String, default="net_30")  # net_30, net_60, due_on_receipt, etc.
    
    # Stripe integration
    stripe_customer_id = Column(String(100), unique=True, index=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contacts = relationship("Contact", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.name}>"

class Contact(Base):
    """Contact person for a client"""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Personal information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    
    # Contact details
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    
    # Status
    is_primary = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="contacts")

    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name}>"


class ClientInsurance(Base):
    """Certificate of Insurance (COI) for clients - Phase 4 Task 4.2"""
    __tablename__ = "client_insurance"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Policy information
    policy_type = Column(String(100), nullable=False)  # general_liability, auto, workers_comp, umbrella, other
    insurance_company = Column(String(255), nullable=False)
    policy_number = Column(String(100), nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=False)
    
    # Dates
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False, index=True)
    
    # Additional information
    certificate_holder = Column(String(255), nullable=True)
    document_url = Column(String(500), nullable=True)
    status = Column(String(20), default='active', index=True)  # active, expired, pending_renewal, cancelled
    
    # Verification
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ClientInsurance {self.policy_number} - {self.policy_type}>"


class InsuranceVerificationLog(Base):
    """Audit trail for insurance verifications - Phase 4 Task 4.2"""
    __tablename__ = "insurance_verification_log"

    id = Column(Integer, primary_key=True, index=True)
    insurance_id = Column(Integer, ForeignKey("client_insurance.id"), nullable=False)
    
    verified_by = Column(Integer, nullable=False)
    verification_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False)  # approved, rejected, needs_update
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<InsuranceVerification {self.insurance_id} - {self.status}>"
