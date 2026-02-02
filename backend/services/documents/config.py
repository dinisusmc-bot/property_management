from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_URL: str = "postgresql://athena:athena_dev_password@postgres:5432/athena"
    
    # MongoDB
    MONGODB_URL: str = "mongodb://athena:athena_dev_password@mongodb:27017/"
    MONGODB_DATABASE: str = "athena_documents"
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 
        'jpg', 'jpeg', 'png', 'gif', 'bmp',
        'txt', 'csv'
    }
    
    class Config:
        env_file = ".env"

settings = Settings()
