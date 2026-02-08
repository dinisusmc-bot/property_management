"""
Configuration for Vendor Service
"""
import os

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_dev_password@postgres:5432/athena"
)
SCHEMA_NAME = "vendor"

# Service Configuration
SERVICE_NAME = "vendor-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8009"))

# External Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://charter-service:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# RabbitMQ Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://athena:athena_dev_password@rabbitmq:5672/")

# JWT Secret
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")

# Bid Configuration
BID_EXPIRATION_HOURS = 72  # Bids expire after 72 hours
MIN_BID_RESPONSE_TIME_HOURS = 2  # Minimum time to respond to bid requests
AUTO_AWARD_THRESHOLD_PERCENT = 10  # Auto-award if bid is 10% below next best

# Vendor Rating Configuration
MIN_RATING = 1.0
MAX_RATING = 5.0
MIN_TRIPS_FOR_RATING = 3  # Minimum completed trips before vendor can be rated

# Compliance Document Types
REQUIRED_COMPLIANCE_DOCS = [
    "business_license",
    "insurance_certificate",
    "vehicle_registration",
    "driver_background_check",
    "safety_inspection"
]
