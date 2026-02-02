from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class CharterDocument(Base):
    __tablename__ = "charter_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    charter_id = Column(Integer, nullable=False, index=True)
    
    # Document details
    document_type = Column(String(50), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # MongoDB reference
    mongodb_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Metadata
    description = Column(Text)
    uploaded_by = Column(Integer)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
