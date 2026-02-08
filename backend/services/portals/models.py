"""
Database Models for Portals Service

Stores portal-specific data:
- User preferences and settings
- Portal session tracking
- Cached dashboard data
- Activity logs
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey, Index, Numeric
from sqlalchemy.sql import func
from datetime import datetime

from database import Base


class PortalUserPreference(Base):
    """
    User preferences for portal customization.
    Stores user-specific settings for dashboard layouts, notifications, etc.
    """
    __tablename__ = "portal_user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # From auth service
    user_type = Column(String(50), nullable=False)  # 'client', 'vendor', 'admin'
    
    # Notification preferences
    email_notifications_enabled = Column(Boolean, default=True)
    sms_notifications_enabled = Column(Boolean, default=False)
    push_notifications_enabled = Column(Boolean, default=True)
    notification_frequency = Column(String(20), default="realtime")  # realtime, daily, weekly
    
    # Dashboard preferences
    dashboard_layout = Column(JSON, nullable=True)  # Custom widget layout
    default_view = Column(String(50), default="dashboard")  # Default landing page
    items_per_page = Column(Integer, default=20)
    
    # Display preferences
    timezone = Column(String(50), default="America/Los_Angeles")
    date_format = Column(String(20), default="MM/DD/YYYY")
    currency = Column(String(3), default="USD")
    language = Column(String(5), default="en-US")
    
    # Theme
    theme = Column(String(20), default="light")  # light, dark, auto
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PortalSession(Base):
    """
    Track active portal sessions for security and analytics.
    """
    __tablename__ = "portal_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_type = Column(String(50), nullable=False)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timing
    login_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    logout_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    terminated_reason = Column(String(100), nullable=True)  # timeout, logout, security
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PortalActivityLog(Base):
    """
    Log significant portal activities for audit and analytics.
    """
    __tablename__ = "portal_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_type = Column(String(50), nullable=False)
    session_id = Column(Integer, ForeignKey("portal_sessions.id"), nullable=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)  # login, view_dashboard, accept_quote, etc.
    activity_category = Column(String(50), nullable=False)  # authentication, charter, payment, etc.
    description = Column(Text, nullable=True)
    
    # Context
    entity_type = Column(String(50), nullable=True)  # charter, quote, payment, etc.
    entity_id = Column(Integer, nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_url = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    
    # Response
    response_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Additional context (renamed from 'metadata' to avoid SQLAlchemy conflict)
    extra_data = Column(JSON, nullable=True)  # Additional context
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class DashboardCache(Base):
    """
    Cache expensive dashboard aggregations to improve performance.
    """
    __tablename__ = "dashboard_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_type = Column(String(50), nullable=False)
    
    # Cache details
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    cache_type = Column(String(100), nullable=False)  # dashboard_summary, recent_charters, etc.
    
    # Cached data
    data = Column(JSON, nullable=False)
    
    # Cache management
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)


# Indexes for performance
Index('idx_portal_preferences_user', PortalUserPreference.user_id, PortalUserPreference.user_type)
Index('idx_portal_sessions_user_active', PortalSession.user_id, PortalSession.is_active)
Index('idx_portal_activity_user_date', PortalActivityLog.user_id, PortalActivityLog.created_at.desc())
Index('idx_dashboard_cache_expires', DashboardCache.expires_at)
