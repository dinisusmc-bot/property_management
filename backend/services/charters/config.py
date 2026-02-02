"""
Configuration for Charter Service
"""
import os
from typing import List

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_secure_password_123@postgres:5432/athena"
)

# CORS
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://frontend:3000",
]

# Business Rules
MINIMUM_DEPOSIT_PERCENTAGE = float(os.getenv("MINIMUM_DEPOSIT_PERCENTAGE", "25.0"))  # 25%
TAX_RATE = float(os.getenv("TAX_RATE", "0.0"))  # 0% (configure based on state)
OVERNIGHT_FEE = float(os.getenv("OVERNIGHT_FEE", "200.0"))  # $200 per overnight
WEEKEND_FEE_PERCENTAGE = float(os.getenv("WEEKEND_FEE_PERCENTAGE", "10.0"))  # 10% surcharge
GRATUITY_PERCENTAGE = float(os.getenv("GRATUITY_PERCENTAGE", "15.0"))  # 15% suggested gratuity

# External Services
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
