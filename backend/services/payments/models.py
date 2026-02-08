from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    payment_type = Column(String(20), nullable=False)  # deposit, balance, refund
    payment_method = Column(String(20), nullable=False)  # card, ach, check, cash
    status = Column(String(20), default="pending")  # pending, processing, succeeded, failed, refunded
    
    # Stripe fields
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_customer_id = Column(String(255), index=True)
    stripe_charge_id = Column(String(255))
    
    # Card details (last 4, brand)
    card_last4 = Column(String(4))
    card_brand = Column(String(20))
    
    # Transaction details
    transaction_id = Column(String(255))
    failure_reason = Column(Text)
    failure_code = Column(String(50))
    
    # Additional info
    description = Column(Text)
    payment_metadata = Column(Text)  # JSON string - renamed from metadata to avoid SQLAlchemy conflict
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_by = Column(Integer)  # user_id who initiated payment
    
class PaymentSchedule(Base):
    __tablename__ = "payment_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, index=True, nullable=False)
    payment_type = Column(String(20), nullable=False)  # deposit, balance
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="pending")  # pending, scheduled, processing, paid, overdue, cancelled
    
    # Reminders
    reminder_sent_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime(timezone=True))
    
    # Payment reference
    payment_id = Column(Integer, ForeignKey('payments.id'))
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PaymentRefund(Base):
    __tablename__ = "payment_refunds"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String(50))  # requested_by_customer, fraudulent, duplicate, etc.
    status = Column(String(20), default="pending")
    
    # Stripe
    stripe_refund_id = Column(String(255), unique=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer)
    processed_at = Column(DateTime(timezone=True))

class VendorBill(Base):
    __tablename__ = "vendor_bills"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, nullable=False, index=True)
    charter_id = Column(Integer)  # FK exists in DB but not in SQLAlchemy
    bill_number = Column(String(100), unique=True, nullable=False)
    bill_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default="pending")
    approval_status = Column(String(20), default="pending")
    approved_by = Column(Integer)
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    description = Column(Text)
    notes = Column(Text)
    
    # Aging (auto-calculated by trigger)
    aging_days = Column(Integer)
    aging_bucket = Column(String(20))
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer)


class PaymentAllocation(Base):
    """Payment allocation to multiple charters"""
    __tablename__ = "payment_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, nullable=False, index=True)
    charter_id = Column(Integer, nullable=False, index=True)
    allocated_amount = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SavedPaymentMethod(Base):
    """Saved payment method for client (linked to Stripe Customer)."""
    __tablename__ = "saved_payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    stripe_payment_method_id = Column(String(100), unique=True, nullable=False)
    
    # Card details (for display)
    card_brand = Column(String(50))  # visa, mastercard, amex, etc.
    card_last4 = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    
    # Metadata
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    nickname = Column(String(100))
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    last_used_at = Column(DateTime)
    
    def __repr__(self):
        return f"<SavedPaymentMethod {self.card_brand} ****{self.card_last4}>"

