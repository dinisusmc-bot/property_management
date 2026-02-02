from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import io
from bson import ObjectId

from database import get_db, Base, engine
from mongodb import get_gridfs
from models import CharterDocument
from schemas import DocumentResponse
from config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Service", 
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,
    openapi_url="/openapi.json"
)

# Custom Swagger UI with correct openapi URL
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <title>{app.title} - Swagger UI</title>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/api/v1/documents/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true
            }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "documents"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    charter_id: int = Form(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a document to MongoDB GridFS"""
    
    # Validate file extension
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Store file in MongoDB GridFS
    fs = get_gridfs()
    mongodb_id = fs.put(
        file_content,
        filename=file.filename,
        content_type=file.content_type,
        charter_id=charter_id,
        document_type=document_type
    )
    
    # Create document record in PostgreSQL
    document = CharterDocument(
        charter_id=charter_id,
        document_type=document_type,
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        mongodb_id=str(mongodb_id),
        description=description
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return DocumentResponse(
        **document.__dict__,
        download_url=f"/{document.id}/download"
    )

@app.get("/charter/{charter_id}", response_model=List[DocumentResponse])
def list_charter_documents(
    charter_id: int,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all documents for a charter"""
    query = db.query(CharterDocument).filter(CharterDocument.charter_id == charter_id)
    
    if document_type:
        query = query.filter(CharterDocument.document_type == document_type)
    
    documents = query.order_by(CharterDocument.uploaded_at.desc()).all()
    
    return [
        DocumentResponse(
            **doc.__dict__,
            download_url=f"/{doc.id}/download"
        )
        for doc in documents
    ]

@app.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document metadata"""
    document = db.query(CharterDocument).filter(CharterDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        **document.__dict__,
        download_url=f"/api/v1/documents/{document.id}/download"
    )

@app.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    """Download a document from MongoDB GridFS"""
    
    # Get document metadata
    document = db.query(CharterDocument).filter(CharterDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get file from GridFS
    fs = get_gridfs()
    try:
        file_data = fs.get(ObjectId(document.mongodb_id))
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found in storage")
    
    # Stream file content
    return StreamingResponse(
        io.BytesIO(file_data.read()),
        media_type=document.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={document.file_name}"
        }
    )

@app.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    document = db.query(CharterDocument).filter(CharterDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from GridFS
    fs = get_gridfs()
    try:
        fs.delete(ObjectId(document.mongodb_id))
    except Exception as e:
        print(f"Warning: Could not delete file from GridFS: {e}")
    
    # Delete from PostgreSQL
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
