"""
Configuration for Client Service
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
