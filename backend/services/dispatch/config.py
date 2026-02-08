"""
Configuration for Dispatch Service
"""
import os

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena123@postgres:5432/athena"
)

# Schema name
SCHEMA_NAME = "dispatch"

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Service info
SERVICE_NAME = "dispatch-service"
SERVICE_VERSION = "1.0.0"
