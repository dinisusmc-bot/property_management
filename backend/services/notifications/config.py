from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://athena_user:athena_secure_password@postgres:5432/athena"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://athena:athena_dev_password@rabbitmq:5672/"
    
    # SendGrid (Email)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@athenacoach.com"
    SENDGRID_FROM_NAME: str = "Athena Coach Services"
    
    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_PHONE: str = ""
    
    # Notification Settings
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
