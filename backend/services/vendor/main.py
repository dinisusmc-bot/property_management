"""
Vendor Service - FastAPI application
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Optional
import logging

import config
from database import get_db, engine
from models import Vendor, Bid, VendorRating, VendorCompliance, BidRequest, VendorStatus, BidStatus
from schemas import (
    VendorCreate, VendorUpdate, VendorResponse, VendorStatistics,
    BidCreate, BidUpdate, BidResponse, BidSubmitRequest, BidDecisionRequest, BidComparison,
    VendorRatingCreate, VendorRatingResponse, VendorResponseRequest,
    VendorComplianceCreate, VendorComplianceUpdate, VendorComplianceResponse,
    BidRequestCreate, BidRequestResponse, BidRequestResponseRequest,
    VendorStatusEnum, BidStatusEnum
)
from business_logic import VendorService, BidService, RatingService, ComplianceService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vendor Service", version="1.0.0")


# Startup: Create schema if it doesn't exist
@app.on_event("startup")
async def startup_event():
    """Create vendor schema and tables on startup"""
    logger.info("Starting Vendor Service...")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {config.SCHEMA_NAME}"))
        conn.commit()
    
    # Create tables
    from models import Base
    Base.metadata.create_all(bind=engine)
    logger.info(f"Schema '{config.SCHEMA_NAME}' and tables created successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vendor-service",
        "version": "1.0.0"
    }


# ============================================================================
# Vendor Endpoints
# ============================================================================

@app.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db)
):
    """Create a new vendor profile"""
    logger.info(f"Creating vendor: {vendor.business_name}")
    
    # Check for duplicate email
    existing = db.query(Vendor).filter(Vendor.primary_email == vendor.primary_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor with email {vendor.primary_email} already exists"
        )
    
    db_vendor = Vendor(**vendor.model_dump())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    logger.info(f"Vendor created with ID: {db_vendor.id}")
    return db_vendor


@app.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[VendorStatusEnum] = Query(None, alias="status"),
    vendor_type: Optional[str] = None,
    is_verified: Optional[bool] = None,
    is_preferred: Optional[bool] = None,
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0),
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all vendors with optional filters"""
    query = db.query(Vendor)
    
    if status_filter:
        query = query.filter(Vendor.status == status_filter.value)
    
    if vendor_type:
        query = query.filter(Vendor.vendor_type == vendor_type)
    
    if is_verified is not None:
        query = query.filter(Vendor.is_verified == is_verified)
    
    if is_preferred is not None:
        query = query.filter(Vendor.is_preferred == is_preferred)
    
    if min_rating:
        query = query.filter(Vendor.average_rating >= min_rating)
    
    if state:
        query = query.filter(Vendor.state == state)
    
    vendors = query.order_by(Vendor.created_at.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(vendors)} vendors")
    return vendors


@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific vendor by ID"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    return vendor


@app.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    vendor_update: VendorUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing vendor"""
    logger.info(f"Updating vendor {vendor_id}")
    
    db_vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    update_data = vendor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vendor, field, value)
    
    db.commit()
    db.refresh(db_vendor)
    
    logger.info(f"Vendor {vendor_id} updated")
    return db_vendor


@app.patch("/vendors/{vendor_id}/status")
async def update_vendor_status(
    vendor_id: int,
    new_status: VendorStatusEnum,
    db: Session = Depends(get_db)
):
    """Update vendor status (approve, suspend, reject, etc.)"""
    logger.info(f"Updating vendor {vendor_id} status to {new_status}")
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    old_status = vendor.status
    vendor.status = new_status.value
    
    # If approving, set verification
    if new_status == VendorStatusEnum.ACTIVE and old_status == VendorStatusEnum.PENDING:
        vendor.is_verified = True
        from datetime import datetime
        vendor.verification_date = datetime.now()
    
    db.commit()
    
    logger.info(f"Vendor {vendor_id} status changed from {old_status} to {new_status}")
    return {"message": "Status updated", "vendor_id": vendor_id, "new_status": new_status}


@app.get("/vendors/{vendor_id}/statistics", response_model=VendorStatistics)
async def get_vendor_statistics(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """Get performance statistics for a vendor"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    # Refresh stats
    vendor_service = VendorService(db)
    vendor_service.calculate_vendor_stats(vendor_id)
    
    db.refresh(vendor)
    
    return VendorStatistics(
        vendor_id=vendor.id,
        business_name=vendor.business_name,
        average_rating=vendor.average_rating,
        total_ratings=vendor.total_ratings,
        completed_trips=vendor.completed_trips,
        cancelled_trips=vendor.cancelled_trips,
        on_time_percentage=vendor.on_time_percentage,
        total_bids_submitted=vendor.total_bids_submitted,
        bids_won=vendor.bids_won,
        win_rate_percentage=vendor.win_rate_percentage,
        is_preferred=vendor.is_preferred
    )


@app.get("/vendors/top/rated", response_model=List[VendorResponse])
async def get_top_vendors(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top-rated vendors"""
    vendor_service = VendorService(db)
    vendors = vendor_service.get_top_vendors(limit)
    return vendors


# ============================================================================
# Bid Endpoints
# ============================================================================

@app.post("/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
async def create_bid(
    bid: BidCreate,
    db: Session = Depends(get_db)
):
    """Create a new bid (draft)"""
    logger.info(f"Creating bid for vendor {bid.vendor_id}, charter {bid.charter_id}")
    
    # Check vendor eligibility
    vendor_service = VendorService(db)
    eligible, message = vendor_service.check_vendor_eligibility(bid.vendor_id)
    
    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor not eligible to bid: {message}"
        )
    
    db_bid = Bid(**bid.model_dump())
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    
    logger.info(f"Bid created with ID: {db_bid.id}")
    return db_bid


@app.get("/bids", response_model=List[BidResponse])
async def get_bids(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    vendor_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    status_filter: Optional[BidStatusEnum] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Get all bids with optional filters"""
    query = db.query(Bid)
    
    if vendor_id:
        query = query.filter(Bid.vendor_id == vendor_id)
    
    if charter_id:
        query = query.filter(Bid.charter_id == charter_id)
    
    if status_filter:
        query = query.filter(Bid.status == status_filter.value)
    
    bids = query.order_by(Bid.created_at.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(bids)} bids")
    return bids


@app.get("/bids/{bid_id}", response_model=BidResponse)
async def get_bid(
    bid_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific bid by ID"""
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID {bid_id} not found"
        )
    
    return bid


@app.put("/bids/{bid_id}", response_model=BidResponse)
async def update_bid(
    bid_id: int,
    bid_update: BidUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing bid"""
    logger.info(f"Updating bid {bid_id}")
    
    db_bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not db_bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID {bid_id} not found"
        )
    
    # Can't update if already decided
    if db_bid.status in [BidStatus.ACCEPTED, BidStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update bid with status {db_bid.status}"
        )
    
    update_data = bid_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bid, field, value)
    
    db.commit()
    db.refresh(db_bid)
    
    logger.info(f"Bid {bid_id} updated")
    return db_bid


@app.post("/bids/{bid_id}/submit", response_model=BidResponse)
async def submit_bid(
    bid_id: int,
    db: Session = Depends(get_db)
):
    """Submit a bid (change from draft to submitted)"""
    logger.info(f"Submitting bid {bid_id}")
    
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID {bid_id} not found"
        )
    
    if bid.status != BidStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only submit bids in DRAFT status, current status: {bid.status}"
        )
    
    bid.status = BidStatus.SUBMITTED
    from datetime import datetime
    bid.submitted_at = datetime.now()
    
    db.commit()
    db.refresh(bid)
    
    # Rank bids for this charter
    bid_service = BidService(db)
    bid_service.rank_bids_for_charter(bid.charter_id)
    
    logger.info(f"Bid {bid_id} submitted")
    return bid


@app.post("/bids/{bid_id}/accept", response_model=BidResponse)
async def accept_bid(
    bid_id: int,
    decision: BidDecisionRequest,
    db: Session = Depends(get_db)
):
    """Accept a bid"""
    logger.info(f"Accepting bid {bid_id}")
    
    bid_service = BidService(db)
    
    try:
        bid = bid_service.accept_bid(bid_id, accepted_by=1, reason=decision.reason)
        return bid
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/bids/{bid_id}/reject", response_model=BidResponse)
async def reject_bid(
    bid_id: int,
    decision: BidDecisionRequest,
    db: Session = Depends(get_db)
):
    """Reject a bid"""
    logger.info(f"Rejecting bid {bid_id}")
    
    bid_service = BidService(db)
    
    try:
        bid = bid_service.reject_bid(bid_id, rejected_by=1, reason=decision.reason)
        return bid
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/charters/{charter_id}/bids/comparison", response_model=BidComparison)
async def get_charter_bid_comparison(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """Get comparison of all bids for a charter"""
    bid_service = BidService(db)
    comparison = bid_service.get_bid_comparison(charter_id)
    return comparison


# ============================================================================
# Rating Endpoints
# ============================================================================

@app.post("/ratings", response_model=VendorRatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating: VendorRatingCreate,
    db: Session = Depends(get_db)
):
    """Create a new vendor rating"""
    logger.info(f"Creating rating for vendor {rating.vendor_id}")
    
    rating_service = RatingService(db)
    
    try:
        db_rating = rating_service.create_rating(rating, rated_by=1)  # TODO: Get from auth
        return db_rating
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/ratings", response_model=List[VendorRatingResponse])
async def get_ratings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    vendor_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0),
    db: Session = Depends(get_db)
):
    """Get vendor ratings with optional filters"""
    query = db.query(VendorRating)
    
    if vendor_id:
        query = query.filter(VendorRating.vendor_id == vendor_id)
    
    if charter_id:
        query = query.filter(VendorRating.charter_id == charter_id)
    
    if min_rating:
        query = query.filter(VendorRating.overall_rating >= min_rating)
    
    ratings = query.order_by(VendorRating.created_at.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(ratings)} ratings")
    return ratings


@app.post("/ratings/{rating_id}/respond", response_model=VendorRatingResponse)
async def respond_to_rating(
    rating_id: int,
    response: VendorResponseRequest,
    db: Session = Depends(get_db)
):
    """Vendor responds to a rating"""
    logger.info(f"Vendor responding to rating {rating_id}")
    
    rating = db.query(VendorRating).filter(VendorRating.id == rating_id).first()
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with ID {rating_id} not found"
        )
    
    rating.vendor_response = response.response
    from datetime import datetime
    rating.vendor_responded_at = datetime.now()
    
    db.commit()
    db.refresh(rating)
    
    logger.info(f"Response added to rating {rating_id}")
    return rating


# ============================================================================
# Compliance Endpoints
# ============================================================================

@app.post("/compliance", response_model=VendorComplianceResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_document(
    doc: VendorComplianceCreate,
    db: Session = Depends(get_db)
):
    """Upload a new compliance document"""
    logger.info(f"Creating compliance document for vendor {doc.vendor_id}")
    
    db_doc = VendorCompliance(**doc.model_dump())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    logger.info(f"Compliance document created with ID: {db_doc.id}")
    return db_doc


@app.get("/compliance", response_model=List[VendorComplianceResponse])
async def get_compliance_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    vendor_id: Optional[int] = None,
    document_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Get compliance documents with optional filters"""
    query = db.query(VendorCompliance)
    
    if vendor_id:
        query = query.filter(VendorCompliance.vendor_id == vendor_id)
    
    if document_type:
        query = query.filter(VendorCompliance.document_type == document_type)
    
    if status_filter:
        query = query.filter(VendorCompliance.status == status_filter)
    
    docs = query.order_by(VendorCompliance.created_at.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(docs)} compliance documents")
    return docs


@app.put("/compliance/{doc_id}", response_model=VendorComplianceResponse)
async def update_compliance_document(
    doc_id: int,
    doc_update: VendorComplianceUpdate,
    db: Session = Depends(get_db)
):
    """Update compliance document (review/approve/reject)"""
    logger.info(f"Updating compliance document {doc_id}")
    
    db_doc = db.query(VendorCompliance).filter(VendorCompliance.id == doc_id).first()
    if not db_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance document with ID {doc_id} not found"
        )
    
    update_data = doc_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_doc, field, value)
    
    # If status is being changed, record review time
    if "status" in update_data:
        from datetime import datetime
        db_doc.reviewed_at = datetime.now()
        db_doc.reviewed_by = 1  # TODO: Get from auth
    
    db.commit()
    db.refresh(db_doc)
    
    logger.info(f"Compliance document {doc_id} updated")
    return db_doc


@app.get("/vendors/{vendor_id}/compliance/status")
async def get_vendor_compliance_status(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """Get overall compliance status for a vendor"""
    # Check vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    compliance_service = ComplianceService(db)
    status = compliance_service.get_vendor_compliance_status(vendor_id)
    
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
