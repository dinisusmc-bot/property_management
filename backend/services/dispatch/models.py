"""
Database models for Dispatch Service
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class Dispatch(Base):
    """Main dispatch record for a charter"""
    __tablename__ = "dispatches"

    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, nullable=False, index=True)
    vehicle_id = Column(Integer)
    driver_id = Column(Integer, index=True)
    
    # Status tracking
    status = Column(String(50), default="pending", nullable=False)
    # pending, assigned, en_route, arrived, in_service, completed, cancelled
    
    # Timing
    dispatch_time = Column(DateTime, index=True)  # When dispatched
    pickup_time = Column(DateTime)  # Actual pickup time
    dropoff_time = Column(DateTime)  # Actual dropoff time
    
    # Additional info
    notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    
    # Relationships
    locations = relationship("DispatchLocation", back_populates="dispatch", cascade="all, delete-orphan")
    events = relationship("DispatchEvent", back_populates="dispatch", cascade="all, delete-orphan")


class DispatchLocation(Base):
    """GPS location tracking for dispatches"""
    __tablename__ = "dispatch_locations"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(Integer, ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # GPS coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Additional tracking info
    speed = Column(Float)  # mph
    heading = Column(Float)  # degrees (0-360)
    altitude = Column(Float)  # feet
    accuracy = Column(Float)  # meters
    
    # Timestamp
    recorded_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Relationship
    dispatch = relationship("Dispatch", back_populates="locations")


class DispatchEvent(Base):
    """Event timeline for dispatch operations"""
    __tablename__ = "dispatch_events"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(Integer, ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)
    # Types: assigned, dispatched, departed, arrived, delayed, breakdown, completed, cancelled
    description = Column(Text)
    
    # Location at time of event
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Timing
    occurred_at = Column(DateTime, nullable=False, server_default=func.now())
    recorded_by = Column(Integer)
    
    # Relationship
    dispatch = relationship("Dispatch", back_populates="events")


class Recovery(Base):
    """Recovery/breakdown tracking"""
    __tablename__ = "recoveries"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(Integer, nullable=False, index=True)
    
    # Issue details
    issue_type = Column(String(50), nullable=False)  # breakdown, accident, emergency
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    description = Column(Text, nullable=False)
    
    # Status
    status = Column(String(50), default="reported")
    # reported, acknowledged, en_route, resolved, cancelled
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(500))
    
    # Resolution
    resolution_notes = Column(Text)
    replacement_vehicle_id = Column(Integer)
    replacement_driver_id = Column(Integer)
    
    # Timing
    reported_at = Column(DateTime, nullable=False, server_default=func.now())
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Audit
    reported_by = Column(Integer)
    assigned_to = Column(Integer)
    
    # Phase 7: Enhanced Recovery Workflow
    recovery_priority = Column(String(20), default="normal")  # low, normal, high, critical
    estimated_recovery_time = Column(DateTime)
    recovery_attempts = Column(Integer, default=0)
    last_contact_at = Column(DateTime)
    last_contact_method = Column(String(50))  # phone, sms, email
    escalated = Column(Boolean, default=False)
    escalated_to = Column(Integer)  # FK to users
    escalated_at = Column(DateTime)
    recovery_notes = Column(Text)
