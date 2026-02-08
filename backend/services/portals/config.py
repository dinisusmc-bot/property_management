"""
Portals Service Configuration

Backend-for-Frontend aggregator for client, vendor, and admin portals.
This service aggregates data from multiple backend services and provides
tailored APIs for different user interfaces.
"""
import os

# Service Configuration
SERVICE_NAME = "portals-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8010))

# Database Configuration (for portal-specific caching and preferences)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_dev_password@postgres:5432/athena"
)
SCHEMA_NAME = "portals"

# Redis Configuration (for caching aggregated data)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 300))  # 5 minutes default

# Backend Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://charter-service:8000")
CLIENT_SERVICE_URL = os.getenv("CLIENT_SERVICE_URL", "http://client-service:8002")
SALES_SERVICE_URL = os.getenv("SALES_SERVICE_URL", "http://sales-service:8000")
PRICING_SERVICE_URL = os.getenv("PRICING_SERVICE_URL", "http://pricing-service:8000")
VENDOR_SERVICE_URL = os.getenv("VENDOR_SERVICE_URL", "http://vendor-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8004")
DOCUMENT_SERVICE_URL = os.getenv("DOCUMENT_SERVICE_URL", "http://document-service:8003")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8005")

# Portal Settings
CLIENT_PORTAL_ENABLED = os.getenv("CLIENT_PORTAL_ENABLED", "true").lower() == "true"
VENDOR_PORTAL_ENABLED = os.getenv("VENDOR_PORTAL_ENABLED", "true").lower() == "true"
ADMIN_DASHBOARD_ENABLED = os.getenv("ADMIN_DASHBOARD_ENABLED", "true").lower() == "true"

# Session Configuration
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))
MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", 5))

# Dashboard Refresh Settings
DASHBOARD_REFRESH_INTERVAL_SECONDS = int(os.getenv("DASHBOARD_REFRESH_INTERVAL_SECONDS", 60))
RECENT_ACTIVITY_DAYS = int(os.getenv("RECENT_ACTIVITY_DAYS", 30))

# Pagination Defaults
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 20))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", 100))
