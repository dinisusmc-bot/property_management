"""
Charter Service - Charter Management and Quote Calculation
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import Field
import logging
import httpx

from database import engine, SessionLocal, Base
from models import Charter, Stop, Vehicle, VendorPayment, ClientPayment
from schemas import (
    CharterCreate, CharterUpdate, CharterResponse,
    StopCreate, StopUpdate, StopResponse, VehicleResponse,
    QuoteRequest, QuoteResponse, CheckInRequest,
    VendorPaymentCreate, VendorPaymentUpdate, VendorPaymentResponse,
    ClientPaymentCreate, ClientPaymentUpdate, ClientPaymentResponse
)
from business_logic import QuoteCalculator
from distance_service import DistanceService
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Athena Charter Service",
    description="Charter management and quote calculation service",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    servers=[
        {"url": "/api/v1/charters", "description": "API Gateway"}
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
                url: '/api/v1/charters/openapi.json',
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

# Helper function to fetch driver details from auth service
async def get_vendor_info(vendor_id: int) -> Optional[dict]:
    """Fetch vendor information from database"""
    try:
        # Query the database directly to get vendor info
        from sqlalchemy import create_engine, text
        import os
        
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT email, full_name FROM users WHERE id = :id AND role = 'vendor'"),
                {"id": vendor_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "vendor_name": row[1],  # full_name
                    "vendor_email": row[0]   # email
                }
    except Exception as e:
        logger.error(f"Failed to fetch vendor info for ID {vendor_id}: {e}")
    return None

async def get_driver_info(driver_id: int) -> Optional[dict]:
    """Fetch driver information from database"""
    try:
        # Query the database directly to get driver info
        from sqlalchemy import create_engine, text
        import os
        
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT email, full_name FROM users WHERE id = :id AND role = 'driver'"),
                {"id": driver_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "driver_name": row[1],  # full_name
                    "driver_email": row[0]   # email
                }
    except Exception as e:
        logger.error(f"Failed to fetch driver info for ID {driver_id}: {e}")
    return None

async def get_driver_info(driver_id: int) -> Optional[dict]:
    """Fetch driver information from database"""
    try:
        # Query the database directly to get driver info
        from sqlalchemy import create_engine, text
        import os
        
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT email, full_name FROM users WHERE id = :id AND role = 'driver'"),
                {"id": driver_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "driver_name": row[1],  # full_name
                    "driver_email": row[0]   # email
                }
    except Exception as e:
        logger.error(f"Failed to fetch driver info for ID {driver_id}: {e}")
    return None

@app.on_event("startup")
async def startup_event():
    """Initialize database with sample vehicles"""
    db = SessionLocal()
    try:
        # Check if vehicles exist
        vehicle_count = db.query(Vehicle).count()
        if vehicle_count == 0:
            # Create sample vehicles
            vehicles = [
                Vehicle(
                    name="Mini Bus",
                    capacity=25,
                    base_rate=150.0,
                    per_mile_rate=2.50,
                    is_active=True
                ),
                Vehicle(
                    name="Motor Coach",
                    capacity=56,
                    base_rate=250.0,
                    per_mile_rate=3.50,
                    is_active=True
                ),
                Vehicle(
                    name="Executive Shuttle",
                    capacity=14,
                    base_rate=120.0,
                    per_mile_rate=2.00,
                    is_active=True
                ),
            ]
            db.add_all(vehicles)
            db.commit()
            logger.info("Created sample vehicles")
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "charters", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Vehicle endpoints
@app.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all vehicles"""
    query = db.query(Vehicle)
    if active_only:
        query = query.filter(Vehicle.is_active == True)
    vehicles = query.offset(skip).limit(limit).all()
    return vehicles

@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get vehicle by ID"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    return vehicle

# Quote calculation
@app.post("/quotes/calculate", response_model=QuoteResponse)
async def calculate_quote(
    quote_request: QuoteRequest,
    db: Session = Depends(get_db)
):
    """Calculate quote for a charter"""
    # Get vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == quote_request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Calculate distance
    distance_service = DistanceService()
    total_distance = 0.0
    
    for i in range(len(quote_request.stops) - 1):
        origin = quote_request.stops[i]
        destination = quote_request.stops[i + 1]
        distance = await distance_service.calculate_distance(origin, destination)
        total_distance += distance
    
    # Calculate quote
    calculator = QuoteCalculator()
    quote = calculator.calculate_quote(
        vehicle=vehicle,
        distance_miles=total_distance,
        trip_hours=quote_request.trip_hours,
        passengers=quote_request.passengers,
        is_overnight=quote_request.is_overnight,
        is_weekend=quote_request.is_weekend
    )
    
    return quote

# Charter endpoints
@app.post("/quotes/submit", response_model=CharterResponse, status_code=status.HTTP_201_CREATED)
async def submit_quote(
    charter: CharterCreate,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for submitting quote requests (no authentication required)
    Creates a charter with 'quote' status
    """
    # Force status to 'quote' for public submissions
    db_charter = Charter(
        client_id=charter.client_id,
        vehicle_id=charter.vehicle_id,
        status="quote",
        trip_date=charter.trip_date,
        passengers=charter.passengers,
        trip_hours=charter.trip_hours,
        is_overnight=charter.is_overnight,
        is_weekend=charter.is_weekend,
        base_cost=charter.base_cost,
        mileage_cost=charter.mileage_cost,
        additional_fees=charter.additional_fees,
        total_cost=charter.total_cost,
        deposit_amount=charter.deposit_amount,
        notes=charter.notes
    )
    db.add(db_charter)
    db.flush()
    
    # Create itinerary stops
    if charter.stops:
        for idx, stop_data in enumerate(charter.stops):
            stop = Stop(
                charter_id=db_charter.id,
                sequence=idx,
                location=stop_data.location,
                arrival_time=stop_data.arrival_time,
                departure_time=stop_data.departure_time,
                notes=stop_data.notes
            )
            db.add(stop)
    
    db.commit()
    db.refresh(db_charter)
    
    logger.info(f"Created quote request {db_charter.id} via public form")
    return db_charter

@app.post("/charters", response_model=CharterResponse, status_code=status.HTTP_201_CREATED)
async def create_charter(
    charter: CharterCreate,
    db: Session = Depends(get_db)
):
    """Create a new charter"""
    # Create charter
    db_charter = Charter(
        client_id=charter.client_id,
        vehicle_id=charter.vehicle_id,
        status=charter.status or "quote",
        trip_date=charter.trip_date,
        passengers=charter.passengers,
        trip_hours=charter.trip_hours,
        is_overnight=charter.is_overnight,
        is_weekend=charter.is_weekend,
        base_cost=charter.base_cost,
        mileage_cost=charter.mileage_cost,
        additional_fees=charter.additional_fees,
        total_cost=charter.total_cost,
        deposit_amount=charter.deposit_amount,
        notes=charter.notes
    )
    db.add(db_charter)
    db.flush()
    
    # Create itinerary stops
    if charter.stops:
        for idx, stop_data in enumerate(charter.stops):
            stop = Stop(
                charter_id=db_charter.id,
                sequence=idx,
                location=stop_data.location,
                arrival_time=stop_data.arrival_time,
                departure_time=stop_data.departure_time,
                notes=stop_data.notes
            )
            db.add(stop)
    
    db.commit()
    db.refresh(db_charter)
    
    logger.info(f"Created charter {db_charter.id} for client {charter.client_id}")
    return db_charter

@app.get("/charters", response_model=List[CharterResponse])
async def list_charters(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all charters with optional filtering"""
    query = db.query(Charter)
    
    if status:
        query = query.filter(Charter.status == status)
    if client_id:
        query = query.filter(Charter.client_id == client_id)
    if vendor_id:
        query = query.filter(Charter.vendor_id == vendor_id)
    
    charters = query.order_by(Charter.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich charters with driver info
    result = []
    for charter in charters:
        charter_dict = {
            "id": charter.id,
            "client_id": charter.client_id,
            "vehicle_id": charter.vehicle_id,
            "vendor_id": charter.vendor_id,
            "driver_id": charter.driver_id,
            "trip_date": charter.trip_date,
            "passengers": charter.passengers,
            "trip_hours": charter.trip_hours,
            "is_overnight": charter.is_overnight,
            "is_weekend": charter.is_weekend,
            "notes": charter.notes,
            "vendor_notes": charter.vendor_notes,
            "last_checkin_location": charter.last_checkin_location,
            "last_checkin_time": charter.last_checkin_time,
            "status": charter.status,
            "base_cost": charter.base_cost,
            "mileage_cost": charter.mileage_cost,
            "additional_fees": charter.additional_fees,
            "total_cost": charter.total_cost,
            "deposit_amount": charter.deposit_amount,
            "vendor_base_cost": charter.vendor_base_cost,
            "vendor_mileage_cost": charter.vendor_mileage_cost,
            "vendor_additional_fees": charter.vendor_additional_fees,
            "client_base_charge": charter.client_base_charge,
            "client_mileage_charge": charter.client_mileage_charge,
            "client_additional_fees": charter.client_additional_fees,
            "profit_margin": charter.profit_margin,
            "created_at": charter.created_at,
            "updated_at": charter.updated_at,
            "vehicle": charter.vehicle,
            "stops": charter.stops,
            "vendor_name": None,
            "vendor_email": None,
            "driver_name": None,
            "driver_email": None
        }
        
        if charter.vendor_id:
            vendor_info = await get_vendor_info(charter.vendor_id)
            if vendor_info:
                charter_dict["vendor_name"] = vendor_info["vendor_name"]
                charter_dict["vendor_email"] = vendor_info["vendor_email"]
        
        if charter.driver_id:
            driver_info = await get_driver_info(charter.driver_id)
            if driver_info:
                charter_dict["driver_name"] = driver_info["driver_name"]
                charter_dict["driver_email"] = driver_info["driver_email"]
        
        result.append(charter_dict)
    
    return result

@app.get("/charters/{charter_id}", response_model=CharterResponse)
async def get_charter(charter_id: int, db: Session = Depends(get_db)):
    """Get charter by ID"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    # Convert to dict and add vendor info if vendor is assigned
    charter_dict = {
        "id": charter.id,
        "client_id": charter.client_id,
        "vehicle_id": charter.vehicle_id,
        "vendor_id": charter.vendor_id,
        "driver_id": charter.driver_id,
        "trip_date": charter.trip_date,
        "passengers": charter.passengers,
        "trip_hours": charter.trip_hours,
        "is_overnight": charter.is_overnight,
        "is_weekend": charter.is_weekend,
        "notes": charter.notes,
        "vendor_notes": charter.vendor_notes,
        "last_checkin_location": charter.last_checkin_location,
        "last_checkin_time": charter.last_checkin_time,
        "status": charter.status,
        "base_cost": charter.base_cost,
        "mileage_cost": charter.mileage_cost,
        "additional_fees": charter.additional_fees,
        "total_cost": charter.total_cost,
        "deposit_amount": charter.deposit_amount,
        # Vendor pricing
        "vendor_base_cost": charter.vendor_base_cost,
        "vendor_mileage_cost": charter.vendor_mileage_cost,
        "vendor_additional_fees": charter.vendor_additional_fees,
        "vendor_total_cost": charter.vendor_total_cost,
        # Client pricing
        "client_base_charge": charter.client_base_charge,
        "client_mileage_charge": charter.client_mileage_charge,
        "client_additional_fees": charter.client_additional_fees,
        "client_total_charge": charter.client_total_charge,
        "profit_margin": charter.profit_margin,
        # Tax tracking
        "tax_rate": charter.tax_rate,
        "tax_amount": charter.tax_amount,
        "tax_status": charter.tax_status,
        "tax_category": charter.tax_category,
        # Other fields
        "approval_sent_date": charter.approval_sent_date,
        "approval_amount": charter.approval_amount,
        "approval_status": charter.approval_status,
        "booking_status": charter.booking_status,
        "booked_at": charter.booked_at,
        "booking_cost": charter.booking_cost,
        "confirmation_status": charter.confirmation_status,
        "confirmed_at": charter.confirmed_at,
        "created_at": charter.created_at,
        "updated_at": charter.updated_at,
        "vehicle": charter.vehicle,
        "stops": charter.stops,
        "vendor_name": None,
        "vendor_email": None,
        "driver_name": None,
        "driver_email": None
    }
    
    if charter.vendor_id:
        vendor_info = await get_vendor_info(charter.vendor_id)
        if vendor_info:
            charter_dict["vendor_name"] = vendor_info["vendor_name"]
            charter_dict["vendor_email"] = vendor_info["vendor_email"]
    
    if charter.driver_id:
        driver_info = await get_driver_info(charter.driver_id)
        if driver_info:
            charter_dict["driver_name"] = driver_info["driver_name"]
            charter_dict["driver_email"] = driver_info["driver_email"]
    
    return charter_dict

@app.put("/charters/{charter_id}", response_model=CharterResponse)
async def update_charter(
    charter_id: int,
    charter_update: CharterUpdate,
    db: Session = Depends(get_db)
):
    """Update a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    # Update fields
    update_data = charter_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(charter, field, value)
    
    db.commit()
    db.refresh(charter)
    
    logger.info(f"Updated charter {charter_id}")
    return charter

@app.delete("/charters/{charter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_charter(charter_id: int, db: Session = Depends(get_db)):
    """Delete a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    db.delete(charter)
    db.commit()
    
    logger.info(f"Deleted charter {charter_id}")
    return None

@app.post("/charters/{charter_id}/convert-to-booking")
async def convert_to_booking(charter_id: int, db: Session = Depends(get_db)):
    """Convert a quote to a booking"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    if charter.status != "quote":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only quotes can be converted to bookings"
        )
    
    charter.status = "booked"
    db.commit()
    db.refresh(charter)
    
    logger.info(f"Converted charter {charter_id} to booking")
    return charter

@app.post("/charters/{charter_id}/checkin")
async def checkin_charter(
    charter_id: int,
    checkin_data: CheckInRequest,
    db: Session = Depends(get_db)
):
    """Record a check-in for a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    from datetime import datetime as dt
    charter.last_checkin_location = checkin_data.location
    charter.last_checkin_time = checkin_data.checkin_time or dt.utcnow()
    
    db.commit()
    db.refresh(charter)
    
    logger.info(f"Charter {charter_id} checked in at {checkin_data.location}")
    return {
        "message": "Check-in recorded successfully",
        "charter_id": charter_id,
        "location": charter.last_checkin_location,
        "checkin_time": charter.last_checkin_time
    }

# Stop endpoints

@app.get("/charters/{charter_id}/stops", response_model=List[StopResponse])
async def list_stops(charter_id: int, db: Session = Depends(get_db)):
    """List all stops for a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    stops = db.query(Stop).filter(Stop.charter_id == charter_id).order_by(Stop.sequence).all()
    return stops

@app.post("/charters/{charter_id}/stops", response_model=StopResponse, status_code=status.HTTP_201_CREATED)
async def create_stop(
    charter_id: int,
    stop: StopCreate,
    db: Session = Depends(get_db)
):
    """Create a new stop for a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charter not found"
        )
    
    # Use provided sequence or get the next one
    if not hasattr(stop, 'sequence') or stop.sequence is None:
        max_sequence = db.query(Stop).filter(Stop.charter_id == charter_id).count()
        sequence = max_sequence
    else:
        sequence = stop.sequence
    
    db_stop = Stop(
        charter_id=charter_id,
        sequence=sequence,
        location=stop.location,
        arrival_time=stop.arrival_time,
        departure_time=stop.departure_time,
        notes=stop.notes
    )
    db.add(db_stop)
    db.commit()
    db.refresh(db_stop)
    
    logger.info(f"Created stop {db_stop.id} for charter {charter_id}")
    return db_stop

@app.put("/stops/{stop_id}", response_model=StopResponse)
async def update_stop(
    stop_id: int,
    stop_update: StopUpdate,
    db: Session = Depends(get_db)
):
    """Update a stop"""
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found"
        )
    
    # Update fields
    update_data = stop_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stop, field, value)
    
    db.commit()
    db.refresh(stop)
    
    logger.info(f"Updated stop {stop_id}")
    return stop

@app.delete("/stops/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stop(stop_id: int, db: Session = Depends(get_db)):
    """Delete a stop"""
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found"
        )
    
    db.delete(stop)
    db.commit()
    
    logger.info(f"Deleted stop {stop_id}")
    return None

# ============= Vendor Payment Endpoints =============

@app.post("/vendor-payments", response_model=VendorPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor_payment(payment: VendorPaymentCreate, db: Session = Depends(get_db)):
    """Create a new vendor payment record"""
    db_payment = VendorPayment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    logger.info(f"Created vendor payment {db_payment.id} for charter {payment.charter_id}")
    return db_payment

@app.get("/vendor-payments", response_model=List[VendorPaymentResponse])
async def list_vendor_payments(
    vendor_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List vendor payments with optional filters"""
    query = db.query(VendorPayment)
    
    if vendor_id:
        query = query.filter(VendorPayment.vendor_id == vendor_id)
    if charter_id:
        query = query.filter(VendorPayment.charter_id == charter_id)
    if payment_status:
        query = query.filter(VendorPayment.payment_status == payment_status)
    
    return query.order_by(VendorPayment.created_at.desc()).all()

@app.get("/vendor-payments/{payment_id}", response_model=VendorPaymentResponse)
async def get_vendor_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get vendor payment by ID"""
    payment = db.query(VendorPayment).filter(VendorPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@app.put("/vendor-payments/{payment_id}", response_model=VendorPaymentResponse)
async def update_vendor_payment(payment_id: int, payment_update: VendorPaymentUpdate, db: Session = Depends(get_db)):
    """Update a vendor payment"""
    payment = db.query(VendorPayment).filter(VendorPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    for field, value in payment_update.dict(exclude_unset=True).items():
        setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    logger.info(f"Updated vendor payment {payment_id}")
    return payment

@app.delete("/vendor-payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor_payment(payment_id: int, db: Session = Depends(get_db)):
    """Delete a vendor payment"""
    payment = db.query(VendorPayment).filter(VendorPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    db.delete(payment)
    db.commit()
    logger.info(f"Deleted vendor payment {payment_id}")
    return None

# ============= Client Payment Endpoints =============

@app.post("/client-payments", response_model=ClientPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_client_payment(payment: ClientPaymentCreate, db: Session = Depends(get_db)):
    """Create a new client payment record"""
    db_payment = ClientPayment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    logger.info(f"Created client payment {db_payment.id} for charter {payment.charter_id}")
    return db_payment

@app.get("/client-payments", response_model=List[ClientPaymentResponse])
async def list_client_payments(
    client_id: Optional[int] = None,
    charter_id: Optional[int] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List client payments with optional filters"""
    query = db.query(ClientPayment)
    
    if client_id:
        query = query.filter(ClientPayment.client_id == client_id)
    if charter_id:
        query = query.filter(ClientPayment.charter_id == charter_id)
    if payment_status:
        query = query.filter(ClientPayment.payment_status == payment_status)
    
    return query.order_by(ClientPayment.created_at.desc()).all()

@app.get("/client-payments/{payment_id}", response_model=ClientPaymentResponse)
async def get_client_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get client payment by ID"""
    payment = db.query(ClientPayment).filter(ClientPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment

@app.put("/client-payments/{payment_id}", response_model=ClientPaymentResponse)
async def update_client_payment(payment_id: int, payment_update: ClientPaymentUpdate, db: Session = Depends(get_db)):
    """Update a client payment"""
    payment = db.query(ClientPayment).filter(ClientPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    for field, value in payment_update.dict(exclude_unset=True).items():
        setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    logger.info(f"Updated client payment {payment_id}")
    return payment

@app.delete("/client-payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_payment(payment_id: int, db: Session = Depends(get_db)):
    """Delete a client payment"""
    payment = db.query(ClientPayment).filter(ClientPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    db.delete(payment)
    db.commit()
    logger.info(f"Deleted client payment {payment_id}")
    return None

# =====================
# Driver Endpoints
# =====================

@app.get("/charters/driver/my-charter")
async def get_driver_charter(request: Request, db: Session = Depends(get_db)):
    """Get the charter assigned to the current driver"""
    # Try to get user_id from Kong header, or decode JWT token
    user_id = request.headers.get("X-User-Id")
    
    # If no header, try to decode JWT from Authorization header
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                import jwt
                # Decode without verification for now (Kong already validated)
                payload = jwt.decode(token, options={"verify_signature": False})
                user_email = payload.get("sub")
                
                # Look up user by email to get user_id
                if user_email:
                    from sqlalchemy import create_engine, text
                    import os
                    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
                    engine = create_engine(DATABASE_URL)
                    with engine.connect() as conn:
                        result = conn.execute(
                            text("SELECT id FROM users WHERE email = :email"),
                            {"email": user_email}
                        )
                        row = result.fetchone()
                        if row:
                            user_id = row[0]
            except Exception as e:
                logger.error(f"Failed to decode token: {e}")
    
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")
    
    # Find charter assigned to this driver
    charter = db.query(Charter).filter(Charter.driver_id == user_id).first()
    if not charter:
        return None
    
    # Fetch related data
    stops = db.query(Stop).filter(Stop.charter_id == charter.id).order_by(Stop.sequence).all()
    vehicle = db.query(Vehicle).filter(Vehicle.id == charter.vehicle_id).first()
    
    return {
        "id": charter.id,
        "client_id": charter.client_id,
        "trip_date": charter.trip_date.isoformat() if charter.trip_date else None,
        "passengers": charter.passengers,
        "status": charter.status,
        "notes": charter.notes,
        "vendor_notes": charter.vendor_notes,
        "last_checkin_location": charter.last_checkin_location,
        "last_checkin_time": charter.last_checkin_time.isoformat() if charter.last_checkin_time else None,
        "stops": [
            {
                "id": stop.id,
                "sequence": stop.sequence,
                "location": stop.location,
                "arrival_time": stop.arrival_time.isoformat() if stop.arrival_time else None,
                "departure_time": stop.departure_time.isoformat() if stop.departure_time else None,
                "notes": stop.notes
            } for stop in stops
        ],
        "vehicle": {
            "id": vehicle.id,
            "name": vehicle.name,
            "capacity": vehicle.capacity
        } if vehicle else None
    }

@app.patch("/charters/{charter_id}/driver-notes")
async def update_driver_notes(charter_id: int, request: Request, db: Session = Depends(get_db), vendor_notes: str = None):
    """Allow driver to update vendor notes on their assigned charter"""
    from pydantic import BaseModel
    
    class NotesUpdate(BaseModel):
        vendor_notes: str
    
    # Try to get user_id from Kong header, or decode JWT token
    user_id = request.headers.get("X-User-Id")
    
    # If no header, try to decode JWT from Authorization header
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                user_email = payload.get("sub")
                
                # Look up user by email to get user_id
                if user_email:
                    from sqlalchemy import create_engine, text
                    import os
                    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
                    engine = create_engine(DATABASE_URL)
                    with engine.connect() as conn:
                        result = conn.execute(
                            text("SELECT id FROM users WHERE email = :email"),
                            {"email": user_email}
                        )
                        row = result.fetchone()
                        if row:
                            user_id = row[0]
            except Exception as e:
                logger.error(f"Failed to decode token: {e}")
    
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")
    
    # Get charter
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Verify driver owns this charter
    if charter.driver_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this charter")
    
    # Parse request body
    body = await request.json()
    vendor_notes = body.get("vendor_notes", "")
    
    # Update notes
    charter.vendor_notes = vendor_notes
    db.commit()
    db.refresh(charter)
    logger.info(f"Driver {user_id} updated notes for charter {charter_id}")
    
    return {"message": "Notes updated successfully"}

@app.patch("/charters/{charter_id}/location")
async def update_driver_location(charter_id: int, request: Request, db: Session = Depends(get_db)):
    """Update driver's current location for the charter"""
    from datetime import datetime
    
    # Try to get user_id from Kong header, or decode JWT token
    user_id = request.headers.get("X-User-Id")
    
    # If no header, try to decode JWT from Authorization header
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                user_email = payload.get("sub")
                
                # Look up user by email to get user_id
                if user_email:
                    from sqlalchemy import create_engine, text
                    import os
                    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@postgres:5432/athena')
                    engine = create_engine(DATABASE_URL)
                    with engine.connect() as conn:
                        result = conn.execute(
                            text("SELECT id FROM users WHERE email = :email"),
                            {"email": user_email}
                        )
                        row = result.fetchone()
                        if row:
                            user_id = row[0]
            except Exception as e:
                logger.error(f"Failed to decode token: {e}")
    
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")
    
    # Get charter
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Verify driver owns this charter
    if charter.driver_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this charter")
    
    # Parse request body
    body = await request.json()
    location = body.get("location")
    timestamp = body.get("timestamp")
    
    # Update location
    charter.last_checkin_location = location
    charter.last_checkin_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    db.commit()
    db.refresh(charter)
    logger.info(f"Driver {user_id} updated location for charter {charter_id}: {location}")
    
    return {"message": "Location updated successfully"}

# =====================
# Phase 2: Charter Enhancements
# =====================

@app.post("/charters/{charter_id}/clone", response_model=CharterResponse, status_code=status.HTTP_201_CREATED)
async def clone_charter(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """
    Clone an existing charter with all its details and stops.
    Creates a new charter in 'quote' status.
    """
    # Get the original charter
    original = db.query(Charter).filter(Charter.id == charter_id).first()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Create new charter with cloned data
    cloned = Charter(
        client_id=original.client_id,
        vehicle_id=original.vehicle_id,
        vendor_id=original.vendor_id,
        driver_id=None,  # Reset driver
        status="quote",  # Always start as quote
        trip_date=original.trip_date,
        passengers=original.passengers,
        trip_hours=original.trip_hours,
        is_overnight=original.is_overnight,
        is_weekend=original.is_weekend,
        trip_type=original.trip_type,
        requires_second_driver=original.requires_second_driver,
        vehicle_count=original.vehicle_count,
        base_cost=original.base_cost,
        mileage_cost=original.mileage_cost,
        additional_fees=original.additional_fees,
        total_cost=original.total_cost,
        vendor_base_cost=original.vendor_base_cost,
        vendor_mileage_cost=original.vendor_mileage_cost,
        vendor_additional_fees=original.vendor_additional_fees,
        vendor_total_cost=original.vendor_total_cost,
        client_base_charge=original.client_base_charge,
        client_mileage_charge=original.client_mileage_charge,
        client_additional_fees=original.client_additional_fees,
        client_total_charge=original.client_total_charge,
        profit_margin=original.profit_margin,
        notes=original.notes,
        vendor_notes=original.vendor_notes,
        cloned_from_charter_id=charter_id
    )
    
    db.add(cloned)
    db.flush()  # Get the ID
    
    # Clone stops
    for stop in original.stops:
        cloned_stop = Stop(
            charter_id=cloned.id,
            sequence=stop.sequence,
            location=stop.location,
            arrival_time=stop.arrival_time,
            departure_time=stop.departure_time,
            notes=stop.notes,
            latitude=stop.latitude,
            longitude=stop.longitude,
            geocoded_address=stop.geocoded_address,
            stop_type=stop.stop_type,
            estimated_arrival=stop.estimated_arrival,
            estimated_departure=stop.estimated_departure
        )
        db.add(cloned_stop)
    
    db.commit()
    db.refresh(cloned)
    
    logger.info(f"Cloned charter {charter_id} to new charter {cloned.id}")
    return cloned


@app.post("/charters/recurring", response_model=List[CharterResponse], status_code=status.HTTP_201_CREATED)
async def create_recurring_charters(
    charter_data: CharterCreate,
    recurrence_rule: str = Query(..., description="Recurrence pattern: daily, weekly, biweekly, monthly"),
    instance_count: int = Query(..., ge=1, le=52, description="Number of instances (max 52)"),
    db: Session = Depends(get_db)
):
    """
    Create a series of recurring charters based on a recurrence rule.
    
    Args:
        charter_data: Base charter data
        recurrence_rule: Simple recurrence pattern (e.g., "weekly", "biweekly", "monthly")
        instance_count: Number of instances to create
    
    Returns:
        List of created charters
    """
    from datetime import timedelta
    
    # Determine date increment based on recurrence rule
    if recurrence_rule.lower() == "weekly":
        increment = timedelta(days=7)
    elif recurrence_rule.lower() == "biweekly":
        increment = timedelta(days=14)
    elif recurrence_rule.lower() == "monthly":
        increment = timedelta(days=30)  # Simplified monthly
    elif recurrence_rule.lower() == "daily":
        increment = timedelta(days=1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported recurrence rule: {recurrence_rule}. Use: daily, weekly, biweekly, or monthly"
        )
    
    created_charters = []
    base_trip_date = charter_data.trip_date
    
    for i in range(instance_count):
        # Calculate trip date for this instance
        trip_date = base_trip_date + (increment * i)
        
        # Create charter
        charter = Charter(
            client_id=charter_data.client_id,
            vehicle_id=charter_data.vehicle_id,
            vendor_id=charter_data.vendor_id,
            status=charter_data.status or "quote",
            trip_date=trip_date,
            passengers=charter_data.passengers,
            trip_hours=charter_data.trip_hours,
            is_overnight=charter_data.is_overnight,
            is_weekend=charter_data.is_weekend,
            trip_type=charter_data.trip_type,
            requires_second_driver=charter_data.requires_second_driver,
            vehicle_count=charter_data.vehicle_count,
            base_cost=charter_data.base_cost,
            mileage_cost=charter_data.mileage_cost,
            additional_fees=charter_data.additional_fees,
            total_cost=charter_data.total_cost,
            deposit_amount=charter_data.deposit_amount,
            vendor_base_cost=charter_data.vendor_base_cost,
            vendor_mileage_cost=charter_data.vendor_mileage_cost,
            vendor_additional_fees=charter_data.vendor_additional_fees,
            vendor_total_cost=charter_data.vendor_total_cost,
            client_base_charge=charter_data.client_base_charge,
            client_mileage_charge=charter_data.client_mileage_charge,
            client_additional_fees=charter_data.client_additional_fees,
            client_total_charge=charter_data.client_total_charge,
            profit_margin=charter_data.profit_margin,
            notes=charter_data.notes,
            vendor_notes=charter_data.vendor_notes,
            recurrence_rule=recurrence_rule,
            instance_number=i + 1,
            series_total=instance_count,
            is_series_master=(i == 0)  # First one is the master
        )
        
        db.add(charter)
        db.flush()  # Get the ID
        
        # Add stops
        if charter_data.stops:
            for stop_data in charter_data.stops:
                stop = Stop(
                    charter_id=charter.id,
                    sequence=stop_data.sequence or 0,
                    location=stop_data.location,
                    arrival_time=stop_data.arrival_time,
                    departure_time=stop_data.departure_time,
                    notes=stop_data.notes,
                    latitude=stop_data.latitude,
                    longitude=stop_data.longitude,
                    geocoded_address=stop_data.geocoded_address,
                    stop_type=stop_data.stop_type,
                    estimated_arrival=stop_data.estimated_arrival,
                    estimated_departure=stop_data.estimated_departure
                )
                db.add(stop)
        
        db.flush()
        db.refresh(charter)
        created_charters.append(charter)
    
    db.commit()
    
    logger.info(f"Created {instance_count} recurring charters with rule: {recurrence_rule}")
    return created_charters


@app.get("/charters/{charter_id}/series", response_model=List[CharterResponse])
async def get_charter_series(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all charters in a recurring series.
    If the charter is part of a series, returns all charters with the same recurrence_rule and series_total.
    """
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    if not charter.recurrence_rule:
        # Not part of a series, just return this charter
        return [charter]
    
    # Find master charter
    if charter.is_series_master:
        master_id = charter.id
    else:
        # Find the master (instance_number = 1)
        master = db.query(Charter).filter(
            Charter.client_id == charter.client_id,
            Charter.recurrence_rule == charter.recurrence_rule,
            Charter.is_series_master == True
        ).first()
        master_id = master.id if master else charter.id
    
    # Get all charters in the series
    series_charters = db.query(Charter).filter(
        Charter.client_id == charter.client_id,
        Charter.recurrence_rule == charter.recurrence_rule,
        Charter.series_total == charter.series_total
    ).order_by(Charter.instance_number).all()
    
    return series_charters


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
