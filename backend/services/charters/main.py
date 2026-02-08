"""
Charter Service - Charter Management and Quote Calculation
"""
from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import Field
from datetime import date, datetime, timedelta
import logging
import httpx

from database import engine, SessionLocal, Base
from models import Charter, Stop, Vehicle, VendorPayment, ClientPayment, CharterVehicle, CharterSeries, DOTCertification, CharterShareLink
from schemas import (
    CharterCreate, CharterUpdate, CharterResponse,
    StopCreate, StopUpdate, StopResponse, VehicleResponse,
    QuoteRequest, QuoteResponse, CheckInRequest,
    VendorPaymentCreate, VendorPaymentUpdate, VendorPaymentResponse,
    ClientPaymentCreate, ClientPaymentUpdate, ClientPaymentResponse,
    CharterVehicleCreate, CharterVehicleUpdate, CharterVehicleResponse,
    MultiVehicleCharterCreate, MultiVehicleCharterResponse,
    SaveAsTemplateRequest, CloneCharterRequest,
    CharterSeriesCreate, CharterSeriesResponse,
    DOTCertificationCreate, DOTCertificationResponse,
    CharterSplitRequest, CharterSplitResponse, CharterSplitListResponse, CharterLegResponse,
    CharterShareLinkCreate, CharterShareLinkResponse, CharterShareLinkVerify
)
import schemas
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
        vendor_id=charter.vendor_id,
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
        notes=charter.notes,
        vehicle_count=charter.vehicle_count,
        is_multi_vehicle=charter.is_multi_vehicle
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

# ============================================================================
# Specific Routes (must come before /charters/{charter_id})
# ============================================================================

@app.get("/charters/templates")
async def list_charter_templates(db: Session = Depends(get_db)):
    """List all charter templates"""
    templates = db.query(Charter).filter(
        Charter.is_template == True
    ).order_by(Charter.template_name).all()
    
    return [
        {
            "id": t.id,
            "template_name": t.template_name,
            "is_multi_vehicle": t.is_multi_vehicle,
            "total_vehicles": t.total_vehicles,
            "passengers": t.passengers,
            "trip_hours": t.trip_hours,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in templates
    ]


@app.post("/charters/multi-vehicle", response_model=MultiVehicleCharterResponse, status_code=status.HTTP_201_CREATED)
async def create_multi_vehicle_charter(
    charter_data: MultiVehicleCharterCreate,
    db: Session = Depends(get_db)
):
    """
    Create a multi-vehicle charter for large events (weddings, conferences, etc.)
    Requires at least 2 vehicles.
    """
    if len(charter_data.vehicles) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multi-vehicle charter requires at least 2 vehicles"
        )
    
    # Get the first vehicle for the main charter record (for compatibility)
    first_vehicle_type = charter_data.vehicles[0].vehicle_type_id
    vehicle = db.query(Vehicle).filter(Vehicle.id == first_vehicle_type).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle type {first_vehicle_type} not found")
    
    # Calculate totals
    total_capacity = sum(v.capacity for v in charter_data.vehicles)
    total_cost = sum(float(v.cost) for v in charter_data.vehicles)
    
    # Create main charter record
    charter = Charter(
        client_id=charter_data.client_id,
        vehicle_id=first_vehicle_type,
        trip_date=charter_data.trip_date,
        passengers=charter_data.passengers,
        trip_hours=charter_data.trip_hours,
        is_overnight=False,
        is_weekend=False,
        base_cost=total_cost,
        mileage_cost=0.0,
        additional_fees=0.0,
        total_cost=total_cost,
        notes=charter_data.notes,
        status='quote',
        is_multi_vehicle=True,
        total_vehicles=len(charter_data.vehicles)
    )
    db.add(charter)
    db.flush()  # Get charter.id
    
    # Create vehicle records
    vehicles_created = []
    for vehicle_data in charter_data.vehicles:
        vehicle_record = CharterVehicle(
            charter_id=charter.id,
            vehicle_type_id=vehicle_data.vehicle_type_id,
            vehicle_id=vehicle_data.vehicle_id,
            vendor_id=vehicle_data.vendor_id,
            capacity=vehicle_data.capacity,
            cost=vehicle_data.cost,
            pickup_location=vehicle_data.pickup_location or charter_data.pickup_location,
            dropoff_location=vehicle_data.dropoff_location or charter_data.dropoff_location,
            special_requirements=vehicle_data.special_requirements,
            status=vehicle_data.status
        )
        db.add(vehicle_record)
        vehicles_created.append(vehicle_record)
    
    db.commit()
    db.refresh(charter)
    
    # Refresh all vehicle records to get IDs
    for v in vehicles_created:
        db.refresh(v)
    
    logger.info(f"Created multi-vehicle charter {charter.id} with {len(vehicles_created)} vehicles")
    
    return MultiVehicleCharterResponse(
        charter_id=charter.id,
        is_multi_vehicle=True,
        total_vehicles=len(vehicles_created),
        total_capacity=total_capacity,
        total_cost=total_cost,
        vehicles=[CharterVehicleResponse.from_orm(v) for v in vehicles_created]
    )


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


@app.post("/charters/series")
async def create_charter_series(
    series_data: CharterSeriesCreate,
    db: Session = Depends(get_db)
):
    """Create a charter series for recurring trips"""
    # Create series
    series = CharterSeries(
        series_name=series_data.series_name,
        client_id=series_data.client_id,
        description=series_data.description,
        recurrence_pattern=series_data.recurrence_pattern,
        recurrence_days=series_data.recurrence_days,
        start_date=series_data.start_date,
        end_date=series_data.end_date,
        template_charter_id=series_data.template_charter_id,
        created_by=1  # Default user for now
    )
    db.add(series)
    db.flush()
    
    # Optionally generate charters for series
    charters_created = []
    if series_data.generate_charters:
        template = db.query(Charter).filter(
            Charter.id == series_data.template_charter_id
        ).first()
        
        if template:
            charters_created = generate_series_charters(
                db, series.id, template, series_data.start_date, series_data.end_date,
                series_data.recurrence_pattern, series_data.recurrence_days
            )
    
    db.commit()
    
    logger.info(f"Created series {series.id} with {len(charters_created)} charters")
    
    return {
        "series_id": series.id,
        "series_name": series.series_name,
        "charters_created": len(charters_created),
        "charter_ids": [c.id for c in charters_created]
    }


@app.get("/charters/series")
async def list_charter_series(
    client_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List charter series with optional filters"""
    query = db.query(CharterSeries)
    
    if client_id:
        query = query.filter(CharterSeries.client_id == client_id)
    if is_active is not None:
        query = query.filter(CharterSeries.is_active == is_active)
    
    series_list = query.order_by(CharterSeries.start_date.desc()).all()
    
    return [
        {
            "id": s.id,
            "series_name": s.series_name,
            "client_id": s.client_id,
            "recurrence_pattern": s.recurrence_pattern,
            "start_date": s.start_date.isoformat(),
            "end_date": s.end_date.isoformat() if s.end_date else None,
            "is_active": s.is_active,
            "charter_count": db.query(func.count(Charter.id)).filter(Charter.series_id == s.id).scalar()
        }
        for s in series_list
    ]


@app.post("/charters/clone/{template_id}")
async def clone_charter_from_template(
    template_id: int,
    request: CloneCharterRequest,
    db: Session = Depends(get_db)
):
    """Create new charter from template"""
    template = db.query(Charter).filter(
        Charter.id == template_id,
        Charter.is_template == True
    ).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    # Clone charter from template
    charter_data = {
        column.name: getattr(template, column.name)
        for column in Charter.__table__.columns
        if column.name not in ['id', 'created_at', 'updated_at', 'is_template', 'template_name', 'cloned_from_charter_id']
    }
    
    # Apply new values
    charter_data.update({
        'trip_date': request.trip_date,
        'status': 'quote',
        'cloned_from_charter_id': template_id
    })
    
    if request.client_id:
        charter_data['client_id'] = request.client_id
    
    # Apply overrides
    if request.overrides:
        charter_data.update(request.overrides)
    
    new_charter = Charter(**charter_data)
    db.add(new_charter)
    db.flush()
    
    # Clone vehicles if multi-vehicle
    if template.is_multi_vehicle and template.charter_vehicles:
        for vehicle in template.charter_vehicles:
            new_vehicle = CharterVehicle(
                charter_id=new_charter.id,
                vehicle_type_id=vehicle.vehicle_type_id,
                capacity=vehicle.capacity,
                cost=vehicle.cost,
                pickup_location=vehicle.pickup_location,
                dropoff_location=vehicle.dropoff_location,
                special_requirements=vehicle.special_requirements
            )
            db.add(new_vehicle)
    
    db.commit()
    db.refresh(new_charter)
    
    logger.info(f"Created charter {new_charter.id} from template {template_id}")
    
    return {
        "charter_id": new_charter.id,
        "cloned_from_template": template.template_name,
        "trip_date": request.trip_date.isoformat(),
        "message": "Charter created from template"
    }


# ============================================================================
# Parametrized Routes (must come after specific routes)
# ============================================================================

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
        # Phase 2 Enhancement fields
        "trip_type": charter.trip_type,
        "requires_second_driver": charter.requires_second_driver,
        "vehicle_count": charter.vehicle_count,
        # Phase 2.1: Multi-vehicle fields
        "is_multi_vehicle": charter.is_multi_vehicle,
        "total_vehicles": charter.total_vehicles,
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


# Phase 2.1: Multi-Vehicle Charter Endpoints
@app.get("/charters/{charter_id}/vehicles", response_model=List[CharterVehicleResponse])
async def get_charter_vehicles(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """Get all vehicles for a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    if not charter.is_multi_vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Charter is not a multi-vehicle charter"
        )
    
    return charter.charter_vehicles


@app.post("/charters/{charter_id}/vehicles", response_model=CharterVehicleResponse, status_code=status.HTTP_201_CREATED)
async def add_vehicle_to_charter(
    charter_id: int,
    vehicle: CharterVehicleCreate,
    db: Session = Depends(get_db)
):
    """Add an additional vehicle to existing charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Convert to multi-vehicle if not already
    if not charter.is_multi_vehicle:
        charter.is_multi_vehicle = True
    
    db_vehicle = CharterVehicle(
        charter_id=charter_id,
        vehicle_type_id=vehicle.vehicle_type_id,
        vehicle_id=vehicle.vehicle_id,
        vendor_id=vehicle.vendor_id,
        capacity=vehicle.capacity,
        cost=vehicle.cost,
        pickup_location=vehicle.pickup_location,
        dropoff_location=vehicle.dropoff_location,
        special_requirements=vehicle.special_requirements,
        status=vehicle.status
    )
    db.add(db_vehicle)
    
    charter.total_vehicles += 1
    
    db.commit()
    db.refresh(db_vehicle)
    
    logger.info(f"Added vehicle to charter {charter_id}, now has {charter.total_vehicles} vehicles")
    return db_vehicle


@app.patch("/charters/charter-vehicles/{vehicle_id}", response_model=CharterVehicleResponse)
async def update_charter_vehicle(
    vehicle_id: int,
    updates: CharterVehicleUpdate,
    db: Session = Depends(get_db)
):
    """Update vehicle details (assign vendor, update status, etc.)"""
    vehicle = db.query(CharterVehicle).filter(CharterVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    # Update fields that are provided
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vehicle, key, value)
    
    from datetime import datetime
    vehicle.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(vehicle)
    
    logger.info(f"Updated charter vehicle {vehicle_id}")
    return vehicle


@app.delete("/charters/charter-vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_charter_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    """Remove a vehicle from charter"""
    vehicle = db.query(CharterVehicle).filter(CharterVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    charter_id = vehicle.charter_id
    db.delete(vehicle)
    
    # Update charter vehicle count
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if charter:
        charter.total_vehicles -= 1
        
        # If only 1 vehicle left, convert back to single vehicle
        if charter.total_vehicles <= 1:
            charter.is_multi_vehicle = False
    
    db.commit()
    
    logger.info(f"Removed vehicle {vehicle_id} from charter {charter_id}")
    return None


# ============================================================================
# Phase 2.2: Charter Cloning & Templates
# ============================================================================

@app.post("/charters/{charter_id}/save-as-template")
async def save_charter_as_template(
    charter_id: int,
    request: SaveAsTemplateRequest,
    db: Session = Depends(get_db)
):
    """Save existing charter as reusable template"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Clone charter as template
    template_data = {
        column.name: getattr(charter, column.name)
        for column in Charter.__table__.columns
        if column.name not in ['id', 'created_at', 'updated_at', 'status', 'trip_date', 'is_template', 'template_name', 'series_id', 'cloned_from_charter_id']
    }
    
    template = Charter(
        **template_data,
        is_template=True,
        template_name=request.template_name,
        status='template',
        trip_date=None  # Templates don't have actual dates
    )
    db.add(template)
    db.flush()
    
    # Copy vehicles if multi-vehicle
    if charter.is_multi_vehicle and charter.charter_vehicles:
        for vehicle in charter.charter_vehicles:
            template_vehicle = CharterVehicle(
                charter_id=template.id,
                vehicle_type_id=vehicle.vehicle_type_id,
                capacity=vehicle.capacity,
                cost=vehicle.cost,
                pickup_location=vehicle.pickup_location,
                dropoff_location=vehicle.dropoff_location,
                special_requirements=vehicle.special_requirements
            )
            db.add(template_vehicle)
    
    db.commit()
    db.refresh(template)
    
    logger.info(f"Saved charter {charter_id} as template '{request.template_name}'")
    
    return {
        "template_id": template.id,
        "template_name": request.template_name,
        "message": "Template created successfully"
    }


@app.post("/charters/{charter_id}/clone")
async def clone_existing_charter(
    charter_id: int,
    request: CloneCharterRequest,
    db: Session = Depends(get_db)
):
    """Clone an existing charter (one-off copy)"""
    source_charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not source_charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Similar logic to template cloning
    charter_data = {
        column.name: getattr(source_charter, column.name)
        for column in Charter.__table__.columns
        if column.name not in ['id', 'created_at', 'updated_at', 'status']
    }
    
    charter_data.update({
        'trip_date': request.trip_date,
        'status': 'quote',
        'cloned_from_charter_id': charter_id
    })
    
    if request.client_id:
        charter_data['client_id'] = request.client_id
    
    if request.overrides:
        charter_data.update(request.overrides)
    
    new_charter = Charter(**charter_data)
    db.add(new_charter)
    db.flush()
    
    # Clone vehicles
    if source_charter.is_multi_vehicle and source_charter.charter_vehicles:
        for vehicle in source_charter.charter_vehicles:
            new_vehicle = CharterVehicle(
                charter_id=new_charter.id,
                vehicle_type_id=vehicle.vehicle_type_id,
                capacity=vehicle.capacity,
                cost=vehicle.cost,
                pickup_location=vehicle.pickup_location,
                dropoff_location=vehicle.dropoff_location,
                special_requirements=vehicle.special_requirements
            )
            db.add(new_vehicle)
    
    db.commit()
    db.refresh(new_charter)
    
    logger.info(f"Cloned charter {charter_id} to new charter {new_charter.id}")
    
    return {
        "charter_id": new_charter.id,
        "cloned_from": charter_id,
        "trip_date": request.trip_date.isoformat()
    }


@app.delete("/charters/templates/{template_id}")
async def delete_charter_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Delete a charter template"""
    template = db.query(Charter).filter(
        Charter.id == template_id,
        Charter.is_template == True
    ).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    # Clear foreign key references from charters cloned from this template
    db.query(Charter).filter(
        Charter.cloned_from_charter_id == template_id
    ).update({"cloned_from_charter_id": None})
    
    db.delete(template)
    db.commit()
    
    logger.info(f"Deleted template {template_id}")
    return {"message": "Template deleted", "template_id": template_id}


# ============================================================================
# Phase 2.3: Charter Series Management  
# ============================================================================

def generate_series_charters(
    db: Session,
    series_id: int,
    template: Charter,
    start_date: date,
    end_date: Optional[date],
    pattern: str,
    recurrence_days: Optional[str]
) -> List[Charter]:
    """Generate individual charters based on series pattern"""
    charters = []
    current_date = start_date
    max_iterations = 365  # Limit to 1 year
    iterations = 0
    
    # Parse recurrence days for weekly pattern
    days_of_week = []
    if pattern == 'weekly' and recurrence_days:
        day_map = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
        days_of_week = [day_map[d.strip().lower()] for d in recurrence_days.split(',')]
    
    while iterations < max_iterations:
        # Check end date
        if end_date and current_date > end_date:
            break
        
        # Check if current date matches pattern
        should_create = False
        if pattern == 'daily':
            should_create = True
        elif pattern == 'weekly' and current_date.weekday() in days_of_week:
            should_create = True
        elif pattern == 'monthly' and current_date.day == start_date.day:
            should_create = True
        
        if should_create:
            # Clone template for this date
            charter_data = {
                column.name: getattr(template, column.name)
                for column in Charter.__table__.columns
                if column.name not in ['id', 'created_at', 'updated_at', 'status', 'trip_date', 'series_id', 'cloned_from_charter_id', 'is_template', 'template_name']
            }
            
            charter = Charter(
                **charter_data,
                trip_date=current_date,
                series_id=series_id,
                status='quote',
                cloned_from_charter_id=template.id
            )
            db.add(charter)
            db.flush()
            
            # Clone vehicles if multi-vehicle
            if template.is_multi_vehicle and template.charter_vehicles:
                for vehicle in template.charter_vehicles:
                    new_vehicle = CharterVehicle(
                        charter_id=charter.id,
                        vehicle_type_id=vehicle.vehicle_type_id,
                        capacity=vehicle.capacity,
                        cost=vehicle.cost,
                        pickup_location=vehicle.pickup_location,
                        dropoff_location=vehicle.dropoff_location,
                        special_requirements=vehicle.special_requirements
                    )
                    db.add(new_vehicle)
            
            charters.append(charter)
        
        # Increment date
        if pattern == 'daily':
            current_date += timedelta(days=1)
        elif pattern == 'weekly':
            current_date += timedelta(days=1)
        elif pattern == 'monthly':
            # Move to same day next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        iterations += 1
    
    return charters


@app.get("/charters/series/{series_id}/charters")
async def get_series_charters(
    series_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all charters in a series"""
    query = db.query(Charter).filter(Charter.series_id == series_id)
    
    if status:
        query = query.filter(Charter.status == status)
    
    charters = query.order_by(Charter.trip_date).all()
    
    return [
        {
            "id": c.id,
            "trip_date": c.trip_date.isoformat() if c.trip_date else None,
            "status": c.status,
            "total_cost": float(c.total_cost) if c.total_cost else 0
        }
        for c in charters
    ]


@app.post("/charters/series/{series_id}/deactivate")
async def deactivate_charter_series(
    series_id: int,
    cancel_future_charters: bool = False,
    db: Session = Depends(get_db)
):
    """Deactivate a charter series"""
    series = db.query(CharterSeries).filter(CharterSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    
    series.is_active = False
    
    # Optionally cancel future charters in series
    cancelled_count = 0
    if cancel_future_charters:
        today = date.today()
        future_charters = db.query(Charter).filter(
            Charter.series_id == series_id,
            Charter.trip_date >= today,
            Charter.status.in_(['quote', 'pending', 'confirmed'])
        ).all()
        
        for charter in future_charters:
            charter.status = 'cancelled'
            cancelled_count += 1
    
    db.commit()
    
    logger.info(f"Deactivated series {series_id}, cancelled {cancelled_count} charters")
    
    return {
        "series_id": series_id,
        "deactivated": True,
        "charters_cancelled": cancelled_count
    }


# ============================================================================
# Phase 2.4: DOT Compliance Certifications
# ============================================================================

@app.post("/charters/vendors/{vendor_id}/certifications")
async def add_vendor_certification(
    vendor_id: int,
    cert_data: DOTCertificationCreate,
    db: Session = Depends(get_db)
):
    """Add DOT or other certification to vendor"""
    certification = DOTCertification(
        vendor_id=vendor_id,
        certification_type=cert_data.certification_type,
        certification_number=cert_data.certification_number,
        issue_date=cert_data.issue_date,
        expiration_date=cert_data.expiration_date,
        document_id=cert_data.document_id,
        notes=cert_data.notes
    )
    db.add(certification)
    db.commit()
    db.refresh(certification)
    
    logger.info(f"Added {cert_data.certification_type} certification to vendor {vendor_id}")
    
    return {
        "certification_id": certification.id,
        "vendor_id": vendor_id,
        "certification_type": certification.certification_type,
        "expiration_date": certification.expiration_date.isoformat(),
        "status": certification.status
    }


@app.get("/charters/vendors/{vendor_id}/certifications")
async def get_vendor_certifications(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """Get all certifications for a vendor"""
    certs = db.query(DOTCertification).filter(
        DOTCertification.vendor_id == vendor_id
    ).order_by(DOTCertification.expiration_date).all()
    
    today = date.today()
    
    return [
        {
            "id": c.id,
            "certification_type": c.certification_type,
            "certification_number": c.certification_number,
            "issue_date": c.issue_date.isoformat(),
            "expiration_date": c.expiration_date.isoformat(),
            "status": c.status,
            "days_until_expiration": (c.expiration_date - today).days,
            "verified_at": c.verified_at.isoformat() if c.verified_at else None
        }
        for c in certs
    ]


@app.get("/charters/certifications/expiring")
async def get_expiring_certifications(
    days_ahead: int = 30,
    db: Session = Depends(get_db)
):
    """Get certifications expiring within specified days"""
    today = date.today()
    expiring_date = today + timedelta(days=days_ahead)
    
    certs = db.query(DOTCertification).filter(
        DOTCertification.status == 'active',
        DOTCertification.expiration_date <= expiring_date,
        DOTCertification.expiration_date >= today
    ).order_by(DOTCertification.expiration_date).all()
    
    return [
        {
            "certification_id": cert.id,
            "vendor_id": cert.vendor_id,
            "certification_type": cert.certification_type,
            "certification_number": cert.certification_number,
            "expiration_date": cert.expiration_date.isoformat(),
            "days_until_expiration": (cert.expiration_date - today).days
        }
        for cert in certs
    ]


@app.post("/charters/certifications/{cert_id}/verify")
async def verify_certification(
    cert_id: int,
    db: Session = Depends(get_db)
):
    """Mark certification as verified"""
    cert = db.query(DOTCertification).filter(DOTCertification.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
    
    cert.verified_by = 1  # Default user for now
    cert.verified_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Verified certification {cert_id}")
    return {"certification_id": cert_id, "verified": True}


@app.get("/charters/{charter_id}/vendor-compliance")
async def check_charter_vendor_compliance(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """Check if assigned vendors have valid certifications"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charter not found")
    
    # Get all vendors for this charter
    vendor_ids = []
    if charter.is_multi_vehicle and charter.charter_vehicles:
        vendor_ids = [v.vendor_id for v in charter.charter_vehicles if v.vendor_id]
    elif charter.vendor_id:
        vendor_ids = [charter.vendor_id]
    
    compliance_status = []
    all_compliant = True
    today = date.today()
    
    for vendor_id in vendor_ids:
        # Check required certifications
        required_certs = ['DOT', 'MC Number', 'Insurance']
        certs = db.query(DOTCertification).filter(
            DOTCertification.vendor_id == vendor_id,
            DOTCertification.certification_type.in_(required_certs),
            DOTCertification.status == 'active',
            DOTCertification.expiration_date >= today
        ).all()
        
        found_cert_types = [c.certification_type for c in certs]
        missing = [ct for ct in required_certs if ct not in found_cert_types]
        
        is_compliant = len(missing) == 0
        if not is_compliant:
            all_compliant = False
        
        compliance_status.append({
            "vendor_id": vendor_id,
            "is_compliant": is_compliant,
            "missing_certifications": missing,
            "certifications": [
                {
                    "type": c.certification_type,
                    "number": c.certification_number,
                    "expires": c.expiration_date.isoformat()
                }
                for c in certs
            ]
        })
    
    return {
        "charter_id": charter_id,
        "all_vendors_compliant": all_compliant,
        "vendor_compliance": compliance_status
    }


# ============================================================================
# Phase 7: Charter Splitting Endpoints
# ============================================================================

@app.post("/charters/{charter_id}/split", response_model=CharterSplitResponse)
async def split_charter(
    charter_id: int,
    split_request: CharterSplitRequest,
    db: Session = Depends(get_db)
):
    """
    Split charter into multiple legs
    """
    parent_charter = db.query(Charter).filter(Charter.id == charter_id).first()
    
    if not parent_charter:
        raise HTTPException(status_code=404, detail="Charter not found")
    
    if parent_charter.is_split_charter:
        raise HTTPException(status_code=400, detail="Cannot split an already-split charter")
    
    if len(split_request.legs) < 2:
        raise HTTPException(status_code=400, detail="Must have at least 2 legs to split")
    
    # Mark parent as split
    parent_charter.is_split_charter = True
    
    # Create child charters for each leg
    split_charters = []
    for idx, leg_data in enumerate(split_request.legs, start=1):
        # Clone parent charter data
        child_charter = Charter(
            client_id=parent_charter.client_id,
            vehicle_id=parent_charter.vehicle_id,
            vendor_id=parent_charter.vendor_id,
            driver_id=parent_charter.driver_id,
            status=parent_charter.status,
            trip_date=leg_data.trip_date,
            passengers=leg_data.passengers,
            trip_hours=parent_charter.trip_hours,
            is_overnight=parent_charter.is_overnight,
            is_weekend=parent_charter.is_weekend,
            base_cost=parent_charter.base_cost,
            mileage_cost=parent_charter.mileage_cost,
            additional_fees=parent_charter.additional_fees,
            total_cost=parent_charter.total_cost,
            deposit_amount=parent_charter.deposit_amount,
            vendor_base_cost=parent_charter.vendor_base_cost,
            vendor_mileage_cost=parent_charter.vendor_mileage_cost,
            vendor_total_cost=parent_charter.vendor_total_cost,
            client_base_charge=parent_charter.client_base_charge,
            client_mileage_charge=parent_charter.client_mileage_charge,
            client_total_charge=parent_charter.client_total_charge,
            profit_margin=parent_charter.profit_margin,
            notes=leg_data.notes or parent_charter.notes,
            trip_type=parent_charter.trip_type,
            requires_second_driver=parent_charter.requires_second_driver,
            parent_charter_id=charter_id,
            is_split_charter=True,
            split_sequence=idx
        )
        
        db.add(child_charter)
        split_charters.append(child_charter)
    
    db.commit()
    
    # Refresh to get IDs
    for charter in split_charters:
        db.refresh(charter)
    
    logger.info(f"Charter {charter_id} split into {len(split_charters)} legs")
    
    return CharterSplitResponse(
        parent_charter_id=charter_id,
        split_count=len(split_charters),
        split_charters=[
            CharterLegResponse(
                id=c.id,
                sequence=c.split_sequence,
                trip_date=c.trip_date.isoformat(),
                passengers=c.passengers,
                status=c.status,
                total_cost=float(c.total_cost) if c.total_cost else 0.0
            )
            for c in split_charters
        ]
    )


@app.get("/charters/{charter_id}/split-charters", response_model=CharterSplitListResponse)
async def get_split_charters(
    charter_id: int,
    db: Session = Depends(get_db)
):
    """Get all split charters for a parent charter"""
    parent_charter = db.query(Charter).filter(Charter.id == charter_id).first()
    
    if not parent_charter:
        raise HTTPException(status_code=404, detail="Charter not found")
    
    if not parent_charter.is_split_charter:
        return CharterSplitListResponse(
            parent_charter_id=charter_id,
            is_split=False,
            split_count=0,
            split_charters=[]
        )
    
    # Get child charters
    children = db.query(Charter).filter(
        Charter.parent_charter_id == charter_id
    ).order_by(Charter.split_sequence).all()
    
    logger.info(f"Retrieved {len(children)} split charters for parent {charter_id}")
    
    return CharterSplitListResponse(
        parent_charter_id=charter_id,
        is_split=True,
        split_count=len(children),
        split_charters=[
            CharterLegResponse(
                id=c.id,
                sequence=c.split_sequence,
                trip_date=c.trip_date.isoformat(),
                passengers=c.passengers,
                status=c.status,
                total_cost=float(c.total_cost) if c.total_cost else 0.0
            )
            for c in children
        ]
    )


# ============================================================================
# Task 8.4: Secure Charter Share Links
# ============================================================================

@app.post("/charters/{charter_id}/share", response_model=schemas.CharterShareLinkResponse, tags=["Charters"])
async def create_charter_share_link(
    charter_id: int,
    link_request: schemas.CharterShareLinkCreate,
    db: Session = Depends(get_db)
):
    """
    Create secure shareable link for charter quote.
    
    - **expires_hours**: Hours until link expires (default 7 days, max 30 days)
    - **password**: Optional password protection
    
    Returns JWT token and full URL.
    Link can be shared with anyone, no login required.
    """
    try:
        from charter_share_service import CharterShareLinkService
        
        result = CharterShareLinkService.create_share_link(
            charter_id=charter_id,
            expires_hours=link_request.expires_hours,
            password=link_request.password,
            created_by=None,  # No auth required for MVP
            db=db
        )
        
        # Build full URL
        base_url = config.FRONTEND_URL if hasattr(config, 'FRONTEND_URL') else "http://localhost:3000"
        result["url"] = f"{base_url}/shared/charter/{result['token']}"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create share link: {str(e)}")
        raise HTTPException(500, f"Failed to create share link: {str(e)}")


@app.post("/shared/charters/view", tags=["Public"])
async def view_shared_charter(
    verify_request: schemas.CharterShareLinkVerify,
    db: Session = Depends(get_db)
):
    """
    View charter via secure link (PUBLIC - no authentication required).
    
    - **token**: JWT token from shared link
    - **password**: Password if link is password protected
    
    Returns full charter details including:
    - Charter information
    - Vehicle details
    - Stops/itinerary
    - Pricing breakdown
    """
    try:
        from charter_share_service import CharterShareLinkService
        
        # Verify link and get charter_id
        charter_id = CharterShareLinkService.verify_share_link(
            token=verify_request.token,
            password=verify_request.password,
            db=db
        )
        
        # Get charter with all details
        charter = db.query(Charter).filter(Charter.id == charter_id).first()
        
        if not charter:
            raise HTTPException(404, "Charter not found")
        
        # Get stops
        stops = db.query(Stop).filter(Stop.charter_id == charter_id).order_by(Stop.sequence).all()
        
        # Return full charter details (public view)
        return {
            "charter_id": charter.id,
            "status": charter.status,
            "trip_date": charter.trip_date.isoformat() if charter.trip_date else None,
            "passengers": charter.passengers,
            "trip_hours": charter.trip_hours,
            "is_overnight": charter.is_overnight,
            "is_weekend": charter.is_weekend,
            
            # Pricing (what we charge the client)
            "client_total_charge": charter.client_total_charge,
            "client_base_charge": charter.client_base_charge,
            "client_mileage_charge": charter.client_mileage_charge,
            "client_additional_fees": charter.client_additional_fees,
            "deposit_amount": charter.deposit_amount,
            
            # Vehicle info
            "vehicle": {
                "name": charter.vehicle.name,
                "capacity": charter.vehicle.capacity
            } if charter.vehicle else None,
            
            # Stops
            "stops": [
                {
                    "sequence": stop.sequence,
                    "address": stop.address,
                    "city": stop.city,
                    "state": stop.state,
                    "stop_type": stop.stop_type
                }
                for stop in stops
            ],
            
            # Additional info
            "notes": charter.notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to view shared charter: {str(e)}")
        raise HTTPException(500, f"Failed to load charter details: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
