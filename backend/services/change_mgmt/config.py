"""
Change Management Service Configuration

Tracks and manages post-booking changes with approval workflows.
Provides audit logging, version control, and approval processes.
"""
import os

# Service Configuration
SERVICE_NAME = "change-mgmt-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8011))

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_dev_password@postgres:5432/athena"
)
SCHEMA_NAME = "change_mgmt"

# Redis Configuration (for caching and locks)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Backend Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://charter-service:8000")
CLIENT_SERVICE_URL = os.getenv("CLIENT_SERVICE_URL", "http://client-service:8002")
VENDOR_SERVICE_URL = os.getenv("VENDOR_SERVICE_URL", "http://vendor-service:8000")
PRICING_SERVICE_URL = os.getenv("PRICING_SERVICE_URL", "http://pricing-service:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8005")

# Workflow Configuration
AUTO_APPROVE_MINOR_CHANGES = os.getenv("AUTO_APPROVE_MINOR_CHANGES", "false").lower() == "true"
REQUIRE_MANAGER_APPROVAL_THRESHOLD = float(os.getenv("REQUIRE_MANAGER_APPROVAL_THRESHOLD", "500.0"))
CHANGE_NOTIFICATION_ENABLED = os.getenv("CHANGE_NOTIFICATION_ENABLED", "true").lower() == "true"

# Change Types
CHANGE_TYPES = [
    "itinerary_modification",
    "passenger_count_change",
    "vehicle_change",
    "date_time_change",
    "pickup_location_change",
    "destination_change",
    "amenity_addition",
    "amenity_removal",
    "cancellation",
    "pricing_adjustment",
    "other"
]

# Change Priorities
PRIORITY_LEVELS = ["low", "medium", "high", "urgent"]

# Workflow States
WORKFLOW_STATES = [
    "pending",
    "under_review",
    "approved",
    "rejected",
    "implemented",
    "cancelled"
]

# Impact Assessment Levels
IMPACT_LEVELS = ["minimal", "moderate", "significant", "major"]
