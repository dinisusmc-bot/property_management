"""
Database models for Vendor Service
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum, Date, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import date as date_type, datetime


# Enums
class VendorStatus(str, enum.Enum):
    """Vendor account status"""
    PENDING = "pending"           # Application submitted, awaiting approval
    ACTIVE = "active"             # Approved and can receive bids
    SUSPENDED = "suspended"       # Temporarily suspended
    INACTIVE = "inactive"         # Voluntarily inactive
    REJECTED = "rejected"         # Application rejected
    BANNED = "banned"             # Permanently banned


class VendorType(str, enum.Enum):
    """Type of vendor"""
    OWNER_OPERATOR = "owner_operator"  # Individual with own vehicle
    FLEET_OPERATOR = "fleet_operator"  # Company with multiple vehicles
    BROKER = "broker"                  # Middleman who subcontracts


class BidStatus(str, enum.Enum):
    """Bid lifecycle status"""
    DRAFT = "draft"               # Saved but not submitted
    SUBMITTED = "submitted"       # Submitted to client
    UNDER_REVIEW = "under_review" # Client is reviewing
    ACCEPTED = "accepted"         # Client accepted bid
    REJECTED = "rejected"         # Client rejected bid
    WITHDRAWN = "withdrawn"       # Vendor withdrew bid
    EXPIRED = "expired"           # Bid expired before decision


class ComplianceStatus(str, enum.Enum):
    """Document compliance status"""
    PENDING = "pending"           # Document uploaded, awaiting review
    APPROVED = "approved"         # Document approved
    REJECTED = "rejected"         # Document rejected
    EXPIRED = "expired"           # Document expired


class Vendor(Base):
    """Vendor profile - bus operators who can submit bids"""
    __tablename__ = "vendors"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Business Information
    business_name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(200), nullable=False)
    vendor_type = Column(Enum(VendorType), nullable=False, default=VendorType.OWNER_OPERATOR)
    tax_id = Column(String(50), nullable=True)  # EIN or SSN
    
    # Contact Information
    primary_contact_name = Column(String(100), nullable=False)
    primary_email = Column(String(100), nullable=False, unique=True, index=True)
    primary_phone = Column(String(20), nullable=False)
    secondary_phone = Column(String(20), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Address
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False, default="USA")
    
    # Fleet Information
    total_vehicles = Column(Integer, nullable=False, default=0)
    vehicle_types = Column(JSON, nullable=True)  # {"mini_bus": 2, "coach": 5}
    max_passenger_capacity = Column(Integer, nullable=True)
    
    # Service Areas
    service_radius_miles = Column(Integer, nullable=True)  # How far they'll travel
    service_states = Column(JSON, nullable=True)  # ["CA", "NV", "AZ"]
    
    # Financial
    bank_name = Column(String(100), nullable=True)
    bank_account_last4 = Column(String(4), nullable=True)
    payment_terms = Column(String(50), nullable=True)  # "net_30", "upon_completion"
    insurance_provider = Column(String(100), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    insurance_expiration = Column(Date, nullable=True)
    
    # Ratings & Performance
    average_rating = Column(Float, nullable=True, default=0.0)
    total_ratings = Column(Integer, nullable=False, default=0)
    completed_trips = Column(Integer, nullable=False, default=0)
    cancelled_trips = Column(Integer, nullable=False, default=0)
    on_time_percentage = Column(Float, nullable=True)  # % of trips that were on time
    
    # Bid Statistics
    total_bids_submitted = Column(Integer, nullable=False, default=0)
    bids_won = Column(Integer, nullable=False, default=0)
    bids_lost = Column(Integer, nullable=False, default=0)
    win_rate_percentage = Column(Float, nullable=True)
    
    # Status & Verification
    status = Column(Enum(VendorStatus), nullable=False, default=VendorStatus.PENDING)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_preferred = Column(Boolean, nullable=False, default=False)  # Preferred vendor status
    verification_date = Column(DateTime, nullable=True)
    
    # Notes & Tags
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["reliable", "luxury_fleet", "24_7_available"]
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # User ID who created
    approved_by = Column(Integer, nullable=True)  # User ID who approved
    approved_at = Column(DateTime, nullable=True)


class Bid(Base):
    """Vendor bid for a charter"""
    __tablename__ = "bids"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    vendor_id = Column(Integer, nullable=False, index=True)  # FK to vendors
    charter_id = Column(Integer, nullable=False, index=True)  # FK to charters (in public schema)
    
    # Bid Details
    quoted_price = Column(Float, nullable=False)
    vehicle_id = Column(Integer, nullable=True)  # Specific vehicle assigned (FK to vehicles)
    vehicle_type = Column(String(50), nullable=False)  # "coach", "mini_bus"
    passenger_capacity = Column(Integer, nullable=False)
    driver_name = Column(String(100), nullable=True)
    
    # Pricing Breakdown
    base_price = Column(Float, nullable=True)
    mileage_charge = Column(Float, nullable=True)
    driver_charge = Column(Float, nullable=True)
    fuel_surcharge = Column(Float, nullable=True)
    additional_fees = Column(Float, nullable=True)
    
    # Bid Terms
    valid_until = Column(DateTime, nullable=False)  # Bid expiration
    estimated_arrival_time = Column(DateTime, nullable=True)
    estimated_departure_time = Column(DateTime, nullable=True)
    payment_terms = Column(String(50), nullable=True)
    cancellation_policy = Column(Text, nullable=True)
    
    # Vehicle Features
    amenities = Column(JSON, nullable=True)  # ["wifi", "restroom", "reclining_seats"]
    is_ada_compliant = Column(Boolean, nullable=False, default=False)
    has_luggage_space = Column(Boolean, nullable=False, default=True)
    
    # Vendor Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Not visible to client
    
    # Status Tracking
    status = Column(Enum(BidStatus), nullable=False, default=BidStatus.DRAFT)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    # Rankings
    rank = Column(Integer, nullable=True)  # Rank among all bids for this charter
    is_lowest_bid = Column(Boolean, nullable=False, default=False)
    price_difference_from_lowest = Column(Float, nullable=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(Integer, nullable=True)


class VendorRating(Base):
    """Ratings and reviews for vendors"""
    __tablename__ = "vendor_ratings"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    vendor_id = Column(Integer, nullable=False, index=True)  # FK to vendors
    charter_id = Column(Integer, nullable=False, index=True)  # FK to charters
    rated_by = Column(Integer, nullable=False)  # User ID who left the rating
    
    # Rating Categories (1-5 scale)
    overall_rating = Column(Float, nullable=False)
    vehicle_condition_rating = Column(Float, nullable=True)
    driver_professionalism_rating = Column(Float, nullable=True)
    on_time_performance_rating = Column(Float, nullable=True)
    communication_rating = Column(Float, nullable=True)
    value_for_money_rating = Column(Float, nullable=True)
    
    # Review
    review_title = Column(String(200), nullable=True)
    review_text = Column(Text, nullable=True)
    
    # Issues
    had_issues = Column(Boolean, nullable=False, default=False)
    issue_description = Column(Text, nullable=True)
    
    # Would Recommend
    would_recommend = Column(Boolean, nullable=True)
    would_use_again = Column(Boolean, nullable=True)
    
    # Vendor Response
    vendor_response = Column(Text, nullable=True)
    vendor_responded_at = Column(DateTime, nullable=True)
    
    # Status
    is_verified = Column(Boolean, nullable=False, default=False)  # Verified actual trip
    is_public = Column(Boolean, nullable=False, default=True)
    is_flagged = Column(Boolean, nullable=False, default=False)
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class VendorCompliance(Base):
    """Vendor compliance documents and certifications"""
    __tablename__ = "vendor_compliance"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    vendor_id = Column(Integer, nullable=False, index=True)  # FK to vendors
    
    # Document Information
    document_type = Column(String(100), nullable=False)  # "insurance", "license", etc.
    document_name = Column(String(200), nullable=False)
    document_number = Column(String(100), nullable=True)
    
    # File Storage
    file_path = Column(String(500), nullable=True)  # S3 path or local path
    file_url = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)  # "pdf", "jpg", etc.
    
    # Validity
    issue_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    
    # Status
    status = Column(Enum(ComplianceStatus), nullable=False, default=ComplianceStatus.PENDING)
    reviewed_by = Column(Integer, nullable=True)  # User ID who reviewed
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Reminders
    reminder_sent = Column(Boolean, nullable=False, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    uploaded_by = Column(Integer, nullable=True)


class VendorDocument(Base):
    """Vendor documents for COI, licenses, and certifications tracking"""
    __tablename__ = "vendor_documents"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document Information
    document_type = Column(String(50), nullable=False)  # 'coi', 'license', 'dot_authority'
    document_id = Column(Integer, nullable=True)  # Link to document service
    
    # Validity
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # 'active', 'expired', 'expiring_soon'
    notes = Column(Text, nullable=True)
    uploaded_by = Column(Integer, nullable=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class VendorPerformance(Base):
    """Vendor performance tracking - on-time rate, cancellations, ratings"""
    __tablename__ = "vendor_performance"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    charter_id = Column(Integer, nullable=True)
    
    # Metric Information
    metric_type = Column(String(50), nullable=False)  # 'on_time', 'cancellation', 'rating'
    value = Column(Numeric(5, 2), nullable=False)  # Rating value or 1/0 for boolean metrics
    notes = Column(Text, nullable=True)
    
    # Audit
    recorded_at = Column(DateTime, nullable=False, server_default=func.now())
    recorded_by = Column(Integer, nullable=True)


class BidRequest(Base):
    """Invitation to vendors to submit bids for a charter"""
    __tablename__ = "bid_requests"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    charter_id = Column(Integer, nullable=False, index=True)  # FK to charters
    vendor_id = Column(Integer, nullable=False, index=True)  # FK to vendors
    
    # Request Details
    requested_by = Column(Integer, nullable=False)  # User ID
    message = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=False)
    
    # Response Tracking
    viewed_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    response_message = Column(Text, nullable=True)
    declined_reason = Column(Text, nullable=True)
    
    # Status
    is_accepted = Column(Boolean, nullable=True)  # True=will bid, False=declined, None=no response
    bid_id = Column(Integer, nullable=True)  # FK to bids if they submitted a bid
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
