"""
Configuration for Auth Service
"""
import os
from typing import List

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://athena:athena_secure_password_123@postgres:5432/athena"
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-min-32-characters-long")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# CORS
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://frontend:3000",
]
