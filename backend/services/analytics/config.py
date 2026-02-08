import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Analytics Service Configuration"""
    
    # Service Info
    SERVICE_NAME: str = "analytics-service"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://athena:athena123@localhost:5432/athena"
    )
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    
    # Auth Service
    AUTH_SERVICE_URL: str = os.getenv(
        "AUTH_SERVICE_URL",
        "http://auth-service:8000"
    )
    
    # Charter Service
    CHARTER_SERVICE_URL: str = os.getenv(
        "CHARTER_SERVICE_URL", 
        "http://charter-service:8000"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
