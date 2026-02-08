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
    
    # Charter Enhancement Fields (Phase 2)
    trip_type = Column(String(50), nullable=True)  # one-way, round-trip, multi-day, etc.
    requires_second_driver = Column(Boolean, default=False)
    vehicle_count = Column(Integer, default=1)
    parent_charter_id = Column(Integer, ForeignKey("charters.id"), nullable=True)
    is_split_charter = Column(Boolean, default=False)  # Phase 7: Charter splitting
    split_sequence = Column(Integer, nullable=True)  # Phase 7: Leg number in split charter
    quote_secure_token = Column(String(255), unique=True, nullable=True)
    revision_number = Column(Integer, default=1)
    recurrence_rule = Column(Text, nullable=True)  # iCal-style recurrence rule
    instance_number = Column(Integer, nullable=True)  # Instance in series (1, 2, 3...)
    series_total = Column(Integer, nullable=True)  # Total instances in series
    is_series_master = Column(Boolean, default=False)  # Master record for recurring series
    cloned_from_charter_id = Column(Integer, ForeignKey("charters.id"), nullable=True)
    
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

    # Phase 2.1: Multi-vehicle support
    is_multi_vehicle = Column(Boolean, default=False)
    total_vehicles = Column(Integer, default=1)
    
    # Phase 2.2: Charter Cloning & Templates
    is_template = Column(Boolean, default=False)
    template_name = Column(String(255), nullable=True)
    
    # Phase 2.3: Charter Series
    series_id = Column(Integer, ForeignKey("charter_series.id"), nullable=True)
    
    # Task 8.4: Secure share links tracking
    last_shared_at = Column(DateTime(timezone=True), nullable=True)
    share_count = Column(Integer, default=0)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="charters")
    stops = relationship("Stop", back_populates="charter", cascade="all, delete-orphan")
    vendor_payments = relationship("VendorPayment", back_populates="charter", cascade="all, delete-orphan")
    client_payments = relationship("ClientPayment", back_populates="charter", cascade="all, delete-orphan")
    charter_vehicles = relationship("CharterVehicle", back_populates="charter", cascade="all, delete-orphan")
    share_links = relationship("CharterShareLink", back_populates="charter", cascade="all, delete-orphan")  # Task 8.4

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
    
    # Phase 2 Enhancement Fields
    latitude = Column(Float, nullable=True)  # GPS latitude
    longitude = Column(Float, nullable=True)  # GPS longitude
    geocoded_address = Column(Text, nullable=True)  # Standardized address from geocoding
    stop_type = Column(String(20), default="waypoint")  # pickup, dropoff, waypoint
    estimated_arrival = Column(DateTime(timezone=True), nullable=True)
    estimated_departure = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    charter = relationship("Charter", back_populates="stops")

    def __repr__(self):
        return f"<Stop {self.sequence}: {self.location}>"

class CharterVehicle(Base):
    """Charter Vehicle model - for multi-vehicle charters (Phase 2.1)"""
    __tablename__ = "charter_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, ForeignKey("charters.id"), nullable=False)
    vehicle_type_id = Column(Integer, nullable=False)  # FK to vehicles table
    vehicle_id = Column(Integer, nullable=True)  # Specific vehicle assigned (if any)
    vendor_id = Column(Integer, nullable=True, index=True)  # FK to auth service
    capacity = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    pickup_location = Column(String, nullable=True)
    dropoff_location = Column(String, nullable=True)
    special_requirements = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, assigned, confirmed, en_route, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    charter = relationship("Charter", back_populates="charter_vehicles")

    def __repr__(self):
        return f"<CharterVehicle {self.id} - Charter {self.charter_id} - {self.status}>"

class CharterSeries(Base):
    """Charter Series model - for recurring charters (Phase 2.3)"""
    __tablename__ = "charter_series"

    id = Column(Integer, primary_key=True, index=True)
    series_name = Column(String(255), nullable=False)
    client_id = Column(Integer, nullable=False, index=True)
    description = Column(Text, nullable=True)
    recurrence_pattern = Column(String(50), nullable=False)  # daily, weekly, monthly
    recurrence_days = Column(String(50), nullable=True)  # For weekly: 'mon,wed,fri'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    template_charter_id = Column(Integer, ForeignKey("charters.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CharterSeries {self.id} - {self.series_name}>"

class DOTCertification(Base):
    """DOT Certification model - for vendor compliance (Phase 2.4)"""
    __tablename__ = "dot_certifications"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, nullable=False, index=True)
    certification_type = Column(String(100), nullable=False)  # DOT, MC Number, Insurance
    certification_number = Column(String(100), nullable=False)
    issue_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    status = Column(String(20), default='active')  # active, expired, suspended, revoked
    document_id = Column(Integer, nullable=True)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DOTCertification {self.id} - {self.certification_type} - {self.vendor_id}>"


class CharterShareLink(Base):
    """Secure shareable link for charter quotes - Task 8.4"""
    __tablename__ = "charter_share_links"
    __table_args__ = {'schema': 'charter'}
    
    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, ForeignKey("charters.id", ondelete="CASCADE"), nullable=False)
    
    # Security
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Tracking
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer)
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)
    
    # Optional password
    password_hash = Column(String(255))
    
    # Relationships
    charter = relationship("Charter", back_populates="share_links")
    
    def __repr__(self):
        return f"<CharterShareLink {self.id} - Charter {self.charter_id}>"
