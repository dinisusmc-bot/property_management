from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentUpload(BaseModel):
    charter_id: int
    document_type: str  # approval, booking, confirmation, contract, invoice, receipt, insurance, other
    description: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    charter_id: int
    document_type: str
    file_name: str
    file_size: int
    mime_type: str
    mongodb_id: str
    description: Optional[str]
    uploaded_by: Optional[int]
    uploaded_at: datetime
    download_url: str
    
    class Config:
        from_attributes = True
