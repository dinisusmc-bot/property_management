"""
Client Service - Customer Relationship Management
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import engine, SessionLocal, Base
from models import Client, Contact
from schemas import (
    ClientCreate, ClientUpdate, ClientResponse,
    ContactCreate, ContactUpdate, ContactResponse
)
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Athena Client Service",
    description="Customer relationship management service",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    servers=[
        {"url": "/api/v1/clients", "description": "API Gateway"}
    ]
)

# Custom Swagger UI with correct openapi URL
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    from fastapi.responses import HTMLResponse
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
                url: '/api/v1/clients/openapi.json',
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
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize database with sample clients"""
    db = SessionLocal()
    try:
        # Check if clients exist
        client_count = db.query(Client).count()
        if client_count == 0:
            # Create sample clients
            clients = [
                Client(
                    name="ABC Corporation",
                    type="corporate",
                    email="contact@abccorp.com",
                    phone="212-555-0100",
                    address="123 Business Ave",
                    city="New York",
                    state="NY",
                    zip_code="10001",
                    is_active=True
                ),
                Client(
                    name="Smith Family Tours",
                    type="personal",
                    email="john@smithtours.com",
                    phone="310-555-0150",
                    address="456 Tour Lane",
                    city="Los Angeles",
                    state="CA",
                    zip_code="90001",
                    is_active=True
                ),
                Client(
                    name="City School District",
                    type="government",
                    email="transport@cityschool.edu",
                    phone="312-555-0200",
                    address="789 Education Blvd",
                    city="Chicago",
                    state="IL",
                    zip_code="60601",
                    is_active=True
                ),
            ]
            db.add_all(clients)
            db.commit()
            logger.info("Created sample clients")
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "clients", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Client endpoints
@app.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db)
):
    """Create a new client"""
    # Check if client with same email exists
    existing = db.query(Client).filter(Client.email == client.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client with this email already exists"
        )
    
    # Create client
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    logger.info(f"Created client {db_client.id}: {db_client.name}")
    return db_client

@app.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    active_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all clients with optional filtering"""
    query = db.query(Client)
    
    if active_only:
        query = query.filter(Client.is_active == True)
    
    if type:
        query = query.filter(Client.type == type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(search_term)) |
            (Client.email.ilike(search_term)) |
            (Client.phone.ilike(search_term))
        )
    
    clients = query.order_by(Client.name).offset(skip).limit(limit).all()
    return clients

@app.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """Get client by ID"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@app.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: Session = Depends(get_db)
):
    """Update a client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Update fields
    update_data = client_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    logger.info(f"Updated client {client_id}")
    return client

@app.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Delete a client (soft delete)"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Soft delete
    client.is_active = False
    db.commit()
    
    logger.info(f"Deactivated client {client_id}")
    return None

# Contact endpoints
@app.post("/clients/{client_id}/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    client_id: int,
    contact: ContactCreate,
    db: Session = Depends(get_db)
):
    """Create a new contact for a client"""
    # Verify client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Create contact
    db_contact = Contact(client_id=client_id, **contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    
    logger.info(f"Created contact {db_contact.id} for client {client_id}")
    return db_contact

@app.get("/clients/{client_id}/contacts", response_model=List[ContactResponse])
async def list_client_contacts(
    client_id: int,
    db: Session = Depends(get_db)
):
    """List all contacts for a client"""
    # Verify client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    contacts = db.query(Contact).filter(Contact.client_id == client_id).all()
    return contacts

@app.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get contact by ID"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact

@app.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    db: Session = Depends(get_db)
):
    """Update a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Update fields
    update_data = contact_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Updated contact {contact_id}")
    return contact

@app.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    db.delete(contact)
    db.commit()
    
    logger.info(f"Deleted contact {contact_id}")
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
