from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
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
    
    # Metadata
    description = Column(Text)
    metadata = Column(Text)  # JSON string
    
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
