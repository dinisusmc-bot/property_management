from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_API_KEY", "sk_test_...")  # Use STRIPE_API_KEY from docker-compose
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_..."
    STRIPE_WEBHOOK_SECRET: str = ""
    RABBITMQ_URL: str = "amqp://athena:athena_dev_password@rabbitmq:5672/"
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    
    class Config:
        env_file = ".env"

settings = Settings()
