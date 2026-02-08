"""
Database connection and session management for Dispatch Service
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import config
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency for getting database session.
    Use with FastAPI Depends().
    """
    db = SessionLocal()
    # Set schema search path
    db.execute(text(f"SET search_path TO {config.SCHEMA_NAME},public"))
    try:
        yield db
    finally:
        db.close()


def init_schema():
    """Initialize database schema"""
    with engine.connect() as conn:
        # Create schema if it doesn't exist
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {config.SCHEMA_NAME}"))
        conn.commit()
        logger.info(f"Schema '{config.SCHEMA_NAME}' created or already exists")
