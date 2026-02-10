"""
FastAPI application for Owners Service
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine
import models
import schemas

app = FastAPI(
    title="Owners Service",
    description="Property owner management for property management platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/owners", response_model=schemas.OwnerResponse, status_code=status.HTTP_201_CREATED)
def create_owner(owner: schemas.OwnerCreate, db: Session = Depends(get_db)):
    """Create a new property owner"""
    # Check for duplicate email
    existing = db.query(models.Owner).filter(models.Owner.email == owner.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_owner = models.Owner(**owner.model_dump(exclude_none=True))
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner


@app.get("/owners", response_model=List[schemas.OwnerResponse])
def list_owners(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """List owners with pagination and filters"""
    owners = db.query(models.Owner)\
        .filter(models.Owner.is_active == is_active)\
        .offset(skip).limit(limit)\
        .all()
    return owners


@app.get("/owners/{owner_id}", response_model=schemas.OwnerResponse)
def get_owner(owner_id: int, db: Session = Depends(get_db)):
    """Get a specific owner by ID"""
    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )
    return owner


@app.put("/owners/{owner_id}", response_model=schemas.OwnerResponse)
def update_owner(
    owner_id: int,
    owner: schemas.OwnerUpdate,
    db: Session = Depends(get_db)
):
    """Update an owner"""
    db_owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not db_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )
    
    update_data = owner.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_owner, key, value)
    
    db.commit()
    db.refresh(db_owner)
    return db_owner


@app.post("/owners/{owner_id}/notes", response_model=schemas.OwnerNoteResponse, status_code=status.HTTP_201_CREATED)
def create_owner_note(
    owner_id: int,
    note: schemas.OwnerNoteCreate,
    db: Session = Depends(get_db)
):
    """Add a note to an owner"""
    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )
    
    db_note = models.OwnerNote(owner_id=owner_id, **note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note
