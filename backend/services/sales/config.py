"""
Configuration for Sales Service
"""
import os
from typing import Optional

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_dev_password@postgres:5432/athena"
)
SCHEMA_NAME = "sales"

# Service Configuration
SERVICE_NAME = "sales"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))

# Auth Service Configuration
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

# Client Service Configuration
CLIENT_SERVICE_URL = os.getenv("CLIENT_SERVICE_URL", "http://client-service:8000")

# Charter Service Configuration
CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://charter-service:8000")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Lead Assignment Configuration
ENABLE_ROUND_ROBIN = os.getenv("ENABLE_ROUND_ROBIN", "true").lower() == "true"
DEFAULT_MAX_LEADS_PER_DAY = int(os.getenv("DEFAULT_MAX_LEADS_PER_DAY", "10"))

# Email Configuration
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://frontend:3000",
]
