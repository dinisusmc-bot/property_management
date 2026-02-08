"""
Configuration for Pricing Service
"""
import os

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_dev_password@postgres:5432/athena"
)
SCHEMA_NAME = "pricing"

# Service Configuration
SERVICE_NAME = "pricing"
SERVICE_PORT = int(os.getenv("PRICING_SERVICE_PORT", "8008"))

# External Service URLs
CHARTER_SERVICE_URL = os.getenv("CHARTER_SERVICE_URL", "http://charter-service:8000")

# TomTom API Configuration
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
TOMTOM_BASE_URL = "https://api.tomtom.com"

# TomTom API endpoints
TOMTOM_GEOCODE_URL = f"{TOMTOM_BASE_URL}/search/2/geocode"
TOMTOM_REVERSE_GEOCODE_URL = f"{TOMTOM_BASE_URL}/search/2/reverseGeocode"
TOMTOM_AUTOCOMPLETE_URL = f"{TOMTOM_BASE_URL}/search/2/search"
TOMTOM_ROUTING_URL = f"{TOMTOM_BASE_URL}/routing/1/calculateRoute"

# TomTom Settings
TOMTOM_TIMEOUT = 30  # seconds
TOMTOM_MAX_RESULTS = 10  # for autocomplete

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")

# Business Rules
DEFAULT_BASE_RATE = 500.0  # Base rate if no rules match
DEFAULT_PER_MILE_RATE = 2.50  # Per mile if no rules match
BASE_RATE_PER_MILE = 2.50  # Standard rate per mile
BASE_RATE_PER_HOUR = 75.0  # Standard rate per hour
WEEKEND_MULTIPLIER = 1.2  # 20% increase for weekends
OVERNIGHT_MULTIPLIER = 1.15  # 15% increase for overnight trips
HOLIDAY_MULTIPLIER = 1.5  # 50% increase for holidays
PEAK_SEASON_MULTIPLIER = 1.3  # 30% increase for peak season
