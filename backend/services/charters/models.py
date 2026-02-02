"""
Database models for Charter Service
"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Vehicle(Base):
    """Vehicle model"""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    base_rate = Column(Float, nullable=False)
    per_mile_rate = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    charters = relationship("Charter", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.name}>"

class Charter(Base):
    """Charter model"""
    __tablename__ = "charters"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False, index=True)  # Foreign key to client service
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    vendor_id = Column(Integer, nullable=True, index=True)  # Foreign key to auth service (vendor user)
    driver_id = Column(Integer, nullable=True, index=True)  # Foreign key to auth service (driver user)
    status = Column(String, nullable=False, default="quote")  # quote, booked, in_progress, completed, cancelled
    
    # Trip details
    trip_date = Column(Date, nullable=False)
    passengers = Column(Integer, nullable=False)
    trip_hours = Column(Float, nullable=False)
    is_overnight = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)
    
    # Pricing - Legacy fields (kept for backwards compatibility)
    base_cost = Column(Float, nullable=False)
    mileage_cost = Column(Float, nullable=False)
    additional_fees = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)
    deposit_amount = Column(Float, nullable=True)
    
    # Vendor Pricing - What we pay to the vendor
    vendor_base_cost = Column(Float, nullable=True)
    vendor_mileage_cost = Column(Float, nullable=True)
    vendor_additional_fees = Column(Float, default=0.0)
    vendor_total_cost = Column(Float, nullable=True)
    
    # Client Pricing - What we charge to the client
    client_base_charge = Column(Float, nullable=True)
    client_mileage_charge = Column(Float, nullable=True)
    client_additional_fees = Column(Float, default=0.0)
    client_total_charge = Column(Float, nullable=True)
    
    # Profit calculation
    profit_margin = Column(Float, nullable=True)  # As decimal (e.g., 0.25 = 25%)
    
    # Tax tracking - for future tax reporting and expense tracking
    tax_rate = Column(Float, nullable=True)  # Tax rate as decimal (e.g., 0.08 = 8%)
    tax_amount = Column(Float, nullable=True)  # Calculated tax amount
    tax_status = Column(String, nullable=True)  # pending, filed, paid
    tax_category = Column(String, nullable=True)  # business_travel, charter_service, other
    
    # Additional info
    notes = Column(Text, nullable=True)
    vendor_notes = Column(Text, nullable=True)
    last_checkin_location = Column(String, nullable=True)
    last_checkin_time = Column(DateTime(timezone=True), nullable=True)
    
    # Workflow fields
    approval_sent_date = Column(DateTime(timezone=True), nullable=True)
    approval_amount = Column(Float, nullable=True)
    approval_status = Column(String, nullable=True)  # pending, approved, rejected
    booking_status = Column(String, nullable=True)  # confirmed, pending
    booked_at = Column(DateTime(timezone=True), nullable=True)
    booking_cost = Column(Float, nullable=True)
    confirmation_status = Column(String, nullable=True)  # sent, pending
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    vehicle = relationship("Vehicle", back_populates="charters")
    stops = relationship("Stop", back_populates="charter", cascade="all, delete-orphan")
    vendor_payments = relationship("VendorPayment", back_populates="charter", cascade="all, delete-orphan")
    client_payments = relationship("ClientPayment", back_populates="charter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Charter {self.id} - {self.status}>"

class VendorPayment(Base):
    """Vendor payment model - tracks payments to vendors (debits/money out)"""
    __tablename__ = "vendor_payments"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, ForeignKey("charters.id"), nullable=False)
    vendor_id = Column(Integer, nullable=False, index=True)  # FK to auth service
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(String, nullable=True)  # check, wire_transfer, ach, credit_card, cash, other
    payment_status = Column(String, nullable=False, default="pending")  # pending, paid, cancelled
    reference_number = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # FK to auth service

    # Relationships
    charter = relationship("Charter", back_populates="vendor_payments")

    def __repr__(self):
        return f"<VendorPayment {self.id} - ${self.amount} - {self.payment_status}>"

class ClientPayment(Base):
    """Client payment model - tracks payments from clients (credits/money in)"""
    __tablename__ = "client_payments"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, ForeignKey("charters.id"), nullable=False)
    client_id = Column(Integer, nullable=False, index=True)  # FK to client service
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(String, nullable=True)  # check, wire_transfer, ach, credit_card, cash, invoice, other
    payment_status = Column(String, nullable=False, default="pending")  # pending, paid, partial, cancelled
    payment_type = Column(String, nullable=True)  # deposit, full_payment, partial_payment, final_payment
    reference_number = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # FK to auth service

    # Relationships
    charter = relationship("Charter", back_populates="client_payments")

    def __repr__(self):
        return f"<ClientPayment {self.id} - ${self.amount} - {self.payment_status}>"

class Stop(Base):
    """Itinerary stop model"""
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, ForeignKey("charters.id"), nullable=False)
    sequence = Column(Integer, nullable=False)  # Order of stops
    location = Column(String, nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    departure_time = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    charter = relationship("Charter", back_populates="stops")

    def __repr__(self):
        return f"<Stop {self.sequence}: {self.location}>"
