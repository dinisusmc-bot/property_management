"""
Configuration for Owners Service
"""
import os

class Settings:
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Owners Service"
    CORS_ORIGINS: list = ["*"]

settings = Settings()
