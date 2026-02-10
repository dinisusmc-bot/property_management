"""
Database models for Owners Service
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Owner(Base):
    """Property owner"""
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    company_name = Column(String)  # For corporate owners
    address = Column(Text)
    tax_id = Column(String)  # EIN or SSN (encrypted in production)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")


class OwnerNote(Base):
    """Internal notes about owners (audit trail)"""
    __tablename__ = "owner_notes"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('owners.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Who added the note
    note = Column(Text, nullable=False)
    is_private = Column(Boolean, default=True)  # Private = only managers see it
    created_at = Column(DateTime(timezone=True), server_default=func.now())
