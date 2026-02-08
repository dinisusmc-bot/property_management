# Phase 2: Charter Enhancements

**Duration:** 2-3 weeks  
**Priority:** 🔴 CRITICAL  
**Goal:** Complete charter management features for complex trip scenarios

---

## Overview

Charter service needs enhancements to handle:
- Multi-vehicle charters (weddings, large groups)
- Charter cloning/templates for recurring trips
- Series management for regular routes
- DOT compliance certification tracking

These features are frequently requested and will differentiate the platform.

---

## Task 2.1: Multi-Vehicle Charter Support

**Estimated Time:** 15-25 hours  
**Services:** Charter  
**Impact:** HIGH - Required for large events (weddings, conferences)

### Database Changes

```sql
\c athena
SET search_path TO charter, public;

-- Create charter vehicles table
CREATE TABLE IF NOT EXISTS charter_vehicles (
  id SERIAL PRIMARY KEY,
  charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
  vehicle_type_id INTEGER NOT NULL,
  vehicle_id INTEGER,  -- Specific vehicle if assigned
  vendor_id INTEGER,
  capacity INTEGER NOT NULL,
  cost DECIMAL(10,2) NOT NULL,
  pickup_location VARCHAR(255),
  dropoff_location VARCHAR(255),
  special_requirements TEXT,
  status VARCHAR(20) DEFAULT 'pending',  -- pending, assigned, confirmed, en_route, completed
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_vehicle_status CHECK (status IN ('pending', 'assigned', 'confirmed', 'en_route', 'completed'))
);

CREATE INDEX idx_charter_vehicles_charter ON charter_vehicles(charter_id);
CREATE INDEX idx_charter_vehicles_vendor ON charter_vehicles(vendor_id);
CREATE INDEX idx_charter_vehicles_status ON charter_vehicles(status);

-- Update charters table
ALTER TABLE charters ADD COLUMN IF NOT EXISTS is_multi_vehicle BOOLEAN DEFAULT FALSE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS total_vehicles INTEGER DEFAULT 1;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS total_capacity INTEGER GENERATED ALWAYS AS 
  (CASE WHEN is_multi_vehicle THEN 
    (SELECT COALESCE(SUM(capacity), 0) FROM charter.charter_vehicles WHERE charter_id = charters.id)
  ELSE passenger_count END) STORED;

-- Update charter cost calculation to include all vehicles
ALTER TABLE charters DROP COLUMN IF EXISTS total_cost;
ALTER TABLE charters ADD COLUMN total_cost DECIMAL(10,2) GENERATED ALWAYS AS
  (CASE WHEN is_multi_vehicle THEN
    (SELECT COALESCE(SUM(cost), 0) FROM charter.charter_vehicles WHERE charter_id = charters.id)
  ELSE base_price END) STORED;
```

### Implementation Steps

#### Step 1: Create Vehicle Models

**File:** `backend/services/charters/models.py`

```python
class CharterVehicle(Base):
    __tablename__ = "charter_vehicles"
    __table_args__ = {'schema': 'charter'}
    
    id = Column(Integer, primary_key=True)
    charter_id = Column(Integer, ForeignKey('charter.charters.id'), nullable=False)
    vehicle_type_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, nullable=True)
    vendor_id = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    pickup_location = Column(String(255))
    dropoff_location = Column(String(255))
    special_requirements = Column(Text)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    charter = relationship("Charter", back_populates="vehicles")

# Update Charter model
class Charter(Base):
    # ... existing fields ...
    
    is_multi_vehicle = Column(Boolean, default=False)
    total_vehicles = Column(Integer, default=1)
    
    # Relationship
    vehicles = relationship("CharterVehicle", back_populates="charter", cascade="all, delete-orphan")
```

#### Step 2: Create Vehicle Schemas

**File:** `backend/services/charters/schemas.py`

```python
class CharterVehicleCreate(BaseModel):
    vehicle_type_id: int
    vehicle_id: Optional[int] = None
    vendor_id: Optional[int] = None
    capacity: int
    cost: Decimal
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    special_requirements: Optional[str] = None

class CharterVehicleResponse(BaseModel):
    id: int
    charter_id: int
    vehicle_type_id: int
    vehicle_id: Optional[int]
    vendor_id: Optional[int]
    capacity: int
    cost: Decimal
    pickup_location: Optional[str]
    dropoff_location: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MultiVehicleCharterCreate(BaseModel):
    # Standard charter fields
    client_id: int
    pickup_date: date
    pickup_time: str
    event_type: str
    passenger_count: int
    
    # Multi-vehicle specific
    vehicles: List[CharterVehicleCreate]
    
    # Optional fields
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    special_instructions: Optional[str] = None
```

#### Step 3: Create Multi-Vehicle Endpoints

**File:** `backend/services/charters/main.py`

```python
@app.post("/charters/multi-vehicle", response_model=dict)
async def create_multi_vehicle_charter(
    charter_data: MultiVehicleCharterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a multi-vehicle charter for large events
    
    Body: {
        "client_id": 1,
        "pickup_date": "2026-03-15",
        "pickup_time": "14:00",
        "event_type": "wedding",
        "passenger_count": 150,
        "vehicles": [
            {"vehicle_type_id": 1, "capacity": 55, "cost": 1200.00},
            {"vehicle_type_id": 1, "capacity": 55, "cost": 1200.00},
            {"vehicle_type_id": 2, "capacity": 40, "cost": 900.00}
        ]
    }
    """
    if len(charter_data.vehicles) < 2:
        raise HTTPException(400, "Multi-vehicle charter must have at least 2 vehicles")
    
    # Create base charter
    charter = Charter(
        client_id=charter_data.client_id,
        pickup_date=charter_data.pickup_date,
        pickup_time=charter_data.pickup_time,
        event_type=charter_data.event_type,
        passenger_count=charter_data.passenger_count,
        pickup_location=charter_data.pickup_location,
        dropoff_location=charter_data.dropoff_location,
        special_instructions=charter_data.special_instructions,
        is_multi_vehicle=True,
        total_vehicles=len(charter_data.vehicles),
        status='pending',
        assigned_to=current_user["user_id"]
    )
    db.add(charter)
    db.flush()  # Get charter.id
    
    # Create vehicle records
    vehicles_created = []
    total_capacity = 0
    total_cost = 0
    
    for vehicle_data in charter_data.vehicles:
        vehicle = CharterVehicle(
            charter_id=charter.id,
            **vehicle_data.dict()
        )
        db.add(vehicle)
        vehicles_created.append(vehicle)
        total_capacity += vehicle.capacity
        total_cost += float(vehicle.cost)
    
    db.commit()
    db.refresh(charter)
    
    return {
        "charter_id": charter.id,
        "is_multi_vehicle": True,
        "total_vehicles": len(vehicles_created),
        "total_capacity": total_capacity,
        "total_cost": total_cost,
        "vehicles": [
            {
                "id": v.id,
                "vehicle_type_id": v.vehicle_type_id,
                "capacity": v.capacity,
                "cost": float(v.cost),
                "status": v.status
            }
            for v in vehicles_created
        ]
    }

@app.get("/charters/{charter_id}/vehicles", response_model=List[CharterVehicleResponse])
async def get_charter_vehicles(
    charter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all vehicles for a charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(404, "Charter not found")
    
    if not charter.is_multi_vehicle:
        raise HTTPException(400, "Charter is not multi-vehicle")
    
    return charter.vehicles

@app.post("/charters/{charter_id}/vehicles", response_model=CharterVehicleResponse)
async def add_vehicle_to_charter(
    charter_id: int,
    vehicle: CharterVehicleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add an additional vehicle to existing charter"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(404, "Charter not found")
    
    # Convert to multi-vehicle if not already
    if not charter.is_multi_vehicle:
        charter.is_multi_vehicle = True
    
    db_vehicle = CharterVehicle(
        charter_id=charter_id,
        **vehicle.dict()
    )
    db.add(db_vehicle)
    
    charter.total_vehicles += 1
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@app.patch("/charter-vehicles/{vehicle_id}", response_model=CharterVehicleResponse)
async def update_charter_vehicle(
    vehicle_id: int,
    updates: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update vehicle details (assign vendor, update status, etc.)"""
    vehicle = db.query(CharterVehicle).filter(CharterVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    
    for key, value in updates.items():
        if hasattr(vehicle, key):
            setattr(vehicle, key, value)
    
    vehicle.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(vehicle)
    return vehicle

@app.delete("/charter-vehicles/{vehicle_id}")
async def remove_charter_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove a vehicle from charter"""
    vehicle = db.query(CharterVehicle).filter(CharterVehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    
    charter_id = vehicle.charter_id
    db.delete(vehicle)
    
    # Update charter vehicle count
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    charter.total_vehicles -= 1
    
    # If only 1 vehicle left, convert back to single vehicle
    if charter.total_vehicles <= 1:
        charter.is_multi_vehicle = False
    
    db.commit()
    return {"message": "Vehicle removed", "vehicle_id": vehicle_id}
```

#### Step 4: Test Multi-Vehicle Charters

**Create:** `test_multi_vehicle.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create Multi-Vehicle Charter ==="
CHARTER_ID=$(curl -s -X POST "$BASE_URL/charters/charters/multi-vehicle" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "pickup_date": "2026-03-15",
    "pickup_time": "14:00",
    "event_type": "wedding",
    "passenger_count": 150,
    "pickup_location": "Downtown Hotel",
    "dropoff_location": "Vineyard Estate",
    "vehicles": [
      {"vehicle_type_id": 1, "capacity": 55, "cost": 1200.00, "special_requirements": "Wheelchair accessible"},
      {"vehicle_type_id": 1, "capacity": 55, "cost": 1200.00},
      {"vehicle_type_id": 2, "capacity": 40, "cost": 900.00}
    ]
  }' | jq -r '.charter_id')

echo "Charter ID: $CHARTER_ID"

echo -e "\n=== Get Charter Vehicles ==="
curl -s -X GET "$BASE_URL/charters/charters/$CHARTER_ID/vehicles" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Add Another Vehicle ==="
curl -s -X POST "$BASE_URL/charters/charters/$CHARTER_ID/vehicles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_type_id": 3,
    "capacity": 25,
    "cost": 600.00
  }' | jq

echo -e "\n=== Assign Vendor to Vehicle ==="
VEHICLE_ID=$(curl -s -X GET "$BASE_URL/charters/charters/$CHARTER_ID/vehicles" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

curl -s -X PATCH "$BASE_URL/charters/charter-vehicles/$VEHICLE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": 1,
    "vehicle_id": 101,
    "status": "confirmed"
  }' | jq
```

### Success Criteria

- [ ] `charter_vehicles` table created
- [ ] Can create multi-vehicle charters
- [ ] Can add/remove vehicles from charter
- [ ] Can assign vendors to specific vehicles
- [ ] Total capacity and cost calculated correctly
- [ ] Test script passes

---

## Task 2.2: Charter Cloning & Templates

**Estimated Time:** 12-18 hours  
**Services:** Charter  
**Impact:** HIGH - Saves time for recurring trips

### Database Changes

```sql
\c athena
SET search_path TO charter, public;

-- Add template fields to charters
ALTER TABLE charters ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS template_name VARCHAR(255);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS cloned_from_id INTEGER REFERENCES charters(id);

CREATE INDEX idx_charters_templates ON charters(is_template) WHERE is_template = TRUE;
CREATE INDEX idx_charters_cloned FROM idx_charters_cloned_from ON charters(cloned_from_id) WHERE cloned_from_id IS NOT NULL;
```

### Implementation Steps

#### Step 1: Update Charter Model

**File:** `backend/services/charters/models.py`

```python
class Charter(Base):
    # ... existing fields ...
    
    is_template = Column(Boolean, default=False)
    template_name = Column(String(255))
    cloned_from_id = Column(Integer, ForeignKey('charter.charters.id'))
```

#### Step 2: Create Template/Clone Endpoints

**File:** `backend/services/charters/main.py`

```python
@app.post("/charters/{charter_id}/save-as-template")
async def save_charter_as_template(
    charter_id: int,
    template_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Save existing charter as reusable template"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(404, "Charter not found")
    
    # Clone charter as template
    template_data = {
        column.name: getattr(charter, column.name)
        for column in Charter.__table__.columns
        if column.name not in ['id', 'created_at', 'updated_at', 'status', 'pickup_date']
    }
    
    template = Charter(
        **template_data,
        is_template=True,
        template_name=template_name,
        status='template',
        pickup_date=None  # Templates don't have actual dates
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Copy vehicles if multi-vehicle
    if charter.is_multi_vehicle:
        for vehicle in charter.vehicles:
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
    
    return {
        "template_id": template.id,
        "template_name": template_name,
        "message": "Template created successfully"
    }

@app.get("/charters/templates", response_model=List[dict])
async def list_charter_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all charter templates"""
    templates = db.query(Charter).filter(
        Charter.is_template == True
    ).order_by(Charter.template_name).all()
    
    return [
        {
            "id": t.id,
            "template_name": t.template_name,
            "event_type": t.event_type,
            "is_multi_vehicle": t.is_multi_vehicle,
            "total_vehicles": t.total_vehicles,
            "passenger_count": t.passenger_count,
            "pickup_location": t.pickup_location,
            "dropoff_location": t.dropoff_location,
            "created_at": t.created_at.isoformat()
        }
        for t in templates
    ]

@app.post("/charters/clone/{template_id}")
async def clone_charter_from_template(
    template_id: int,
    pickup_date: date,
    pickup_time: str,
    client_id: Optional[int] = None,
    overrides: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create new charter from template
    
    Body: {
        "pickup_date": "2026-04-10",
        "pickup_time": "09:00",
        "client_id": 5,
        "overrides": {
            "passenger_count": 45,
            "special_instructions": "Updated notes"
        }
    }
    """
    template = db.query(Charter).filter(
        Charter.id == template_id,
        Charter.is_template == True
    ).first()
    if not template:
        raise HTTPException(404, "Template not found")
    
    # Clone charter from template
    charter_data = {
        column.name: getattr(template, column.name)
        for column in Charter.__table__.columns
        if column.name not in ['id', 'created_at', 'updated_at', 'is_template', 'template_name', 'cloned_from_id']
    }
    
    # Apply new values
    charter_data.update({
        'pickup_date': pickup_date,
        'pickup_time': pickup_time,
        'status': 'pending',
        'cloned_from_id': template_id,
        'assigned_to': current_user["user_id"]
    })
    
    if client_id:
        charter_data['client_id'] = client_id
    
    # Apply overrides
    if overrides:
        charter_data.update(overrides)
    
    new_charter = Charter(**charter_data)
    db.add(new_charter)
    db.flush()
    
    # Clone vehicles if multi-vehicle
    if template.is_multi_vehicle:
        for vehicle in template.vehicles:
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
    
    return {
        "charter_id": new_charter.id,
        "cloned_from_template": template.template_name,
        "pickup_date": pickup_date.isoformat(),
        "message": "Charter created from template"
    }

@app.post("/charters/{charter_id}/clone")
async def clone_existing_charter(
    charter_id: int,
    pickup_date: date,
    pickup_time: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Clone an existing charter (one-off copy)"""
    source_charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not source_charter:
        raise HTTPException(404, "Charter not found")
    
    # Similar logic to template cloning
    charter_data = {
        column.name: getattr(source_charter, column.name)
        for column in Charter.__table__.columns
        if column.name not in ['id', 'created_at', 'updated_at', 'status']
    }
    
    charter_data.update({
        'pickup_date': pickup_date,
        'pickup_time': pickup_time,
        'status': 'pending',
        'cloned_from_id': charter_id,
        'assigned_to': current_user["user_id"]
    })
    
    new_charter = Charter(**charter_data)
    db.add(new_charter)
    db.flush()
    
    # Clone vehicles
    if source_charter.is_multi_vehicle:
        for vehicle in source_charter.vehicles:
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
    
    return {
        "charter_id": new_charter.id,
        "cloned_from": charter_id,
        "pickup_date": pickup_date.isoformat()
    }

@app.delete("/charters/templates/{template_id}")
async def delete_charter_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Delete a charter template"""
    template = db.query(Charter).filter(
        Charter.id == template_id,
        Charter.is_template == True
    ).first()
    if not template:
        raise HTTPException(404, "Template not found")
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted", "template_id": template_id}
```

#### Step 3: Test Charter Cloning

**Create:** `test_charter_cloning.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Save Charter as Template ==="
TEMPLATE_ID=$(curl -s -X POST "$BASE_URL/charters/charters/1/save-as-template?template_name=Airport%20Shuttle%20Standard" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.template_id')

echo "Template ID: $TEMPLATE_ID"

echo -e "\n=== List Templates ==="
curl -s -X GET "$BASE_URL/charters/charters/templates" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Clone from Template ==="
curl -s -X POST "$BASE_URL/charters/charters/clone/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_date": "2026-04-10",
    "pickup_time": "09:00",
    "client_id": 5,
    "overrides": {
      "passenger_count": 45
    }
  }' | jq

echo -e "\n=== Clone Existing Charter ==="
curl -s -X POST "$BASE_URL/charters/charters/2/clone" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_date": "2026-04-15",
    "pickup_time": "14:00"
  }' | jq
```

### Success Criteria

- [ ] Can save charter as template
- [ ] Can list templates
- [ ] Can clone from template
- [ ] Can clone existing charter
- [ ] Multi-vehicle charters clone correctly
- [ ] Test script passes

---

## Task 2.3: Charter Series Management

**Estimated Time:** 10-15 hours  
**Services:** Charter  
**Impact:** MEDIUM - For regular routes (daily airport shuttles, weekly school runs)

### Database Changes

```sql
\c athena
SET search_path TO charter, public;

CREATE TABLE IF NOT EXISTS charter_series (
  id SERIAL PRIMARY KEY,
  series_name VARCHAR(255) NOT NULL,
  client_id INTEGER NOT NULL,
  description TEXT,
  recurrence_pattern VARCHAR(50) NOT NULL,  -- daily, weekly, monthly
  recurrence_days VARCHAR(50),  -- For weekly: 'mon,wed,fri'
  start_date DATE NOT NULL,
  end_date DATE,
  template_charter_id INTEGER REFERENCES charters(id),
  is_active BOOLEAN DEFAULT TRUE,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_recurrence CHECK (recurrence_pattern IN ('daily', 'weekly', 'monthly'))
);

CREATE INDEX idx_charter_series_client ON charter_series(client_id);
CREATE INDEX idx_charter_series_active ON charter_series(is_active);

-- Link charters to series
ALTER TABLE charters ADD COLUMN IF NOT EXISTS series_id INTEGER REFERENCES charter_series(id);
CREATE INDEX idx_charters_series ON charters(series_id) WHERE series_id IS NOT NULL;
```

### Implementation Steps

#### Step 1: Create Series Models

**File:** `backend/services/charters/models.py`

```python
class CharterSeries(Base):
    __tablename__ = "charter_series"
    __table_args__ = {'schema': 'charter'}
    
    id = Column(Integer, primary_key=True)
    series_name = Column(String(255), nullable=False)
    client_id = Column(Integer, nullable=False)
    description = Column(Text)
    recurrence_pattern = Column(String(50), nullable=False)
    recurrence_days = Column(String(50))  # For weekly recurrence
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    template_charter_id = Column(Integer, ForeignKey('charter.charters.id'))
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Charter(Base):
    # ... existing fields ...
    series_id = Column(Integer, ForeignKey('charter.charter_series.id'))
```

#### Step 2: Create Series Endpoints

**File:** `backend/services/charters/main.py`

```python
from datetime import timedelta
from typing import List

@app.post("/charters/series", response_model=dict)
async def create_charter_series(
    series_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a charter series for recurring trips
    
    Body: {
        "series_name": "Daily Airport Shuttle",
        "client_id": 10,
        "description": "Mon-Fri airport runs",
        "recurrence_pattern": "weekly",
        "recurrence_days": "mon,tue,wed,thu,fri",
        "start_date": "2026-03-01",
        "end_date": "2026-06-30",
        "template_charter_id": 50,
        "generate_charters": true
    }
    """
    # Create series
    series = CharterSeries(
        series_name=series_data['series_name'],
        client_id=series_data['client_id'],
        description=series_data.get('description'),
        recurrence_pattern=series_data['recurrence_pattern'],
        recurrence_days=series_data.get('recurrence_days'),
        start_date=series_data['start_date'],
        end_date=series_data.get('end_date'),
        template_charter_id=series_data.get('template_charter_id'),
        created_by=current_user["user_id"]
    )
    db.add(series)
    db.flush()
    
    # Optionally generate charters for series
    charters_created = []
    if series_data.get('generate_charters', False):
        template = db.query(Charter).filter(
            Charter.id == series_data['template_charter_id']
        ).first()
        
        if template:
            charters_created = generate_series_charters(
                db, series.id, template, series_data['start_date'], series_data.get('end_date'),
                series_data['recurrence_pattern'], series_data.get('recurrence_days'),
                current_user["user_id"]
            )
    
    db.commit()
    
    return {
        "series_id": series.id,
        "series_name": series.series_name,
        "charters_created": len(charters_created),
        "charter_ids": [c.id for c in charters_created]
    }

def generate_series_charters(
    db: Session,
    series_id: int,
    template: Charter,
    start_date: date,
    end_date: Optional[date],
    pattern: str,
    recurrence_days: Optional[str],
    user_id: int
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
                if column.name not in ['id', 'created_at', 'updated_at', 'status', 'pickup_date', 'series_id']
            }
            
            charter = Charter(
                **charter_data,
                pickup_date=current_date,
                series_id=series_id,
                status='pending',
                assigned_to=user_id,
                cloned_from_id=template.id
            )
            db.add(charter)
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
    
    db.flush()
    return charters

@app.get("/charters/series", response_model=List[dict])
async def list_charter_series(
    client_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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

@app.get("/charters/series/{series_id}/charters", response_model=List[dict])
async def get_series_charters(
    series_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all charters in a series"""
    query = db.query(Charter).filter(Charter.series_id == series_id)
    
    if status:
        query = query.filter(Charter.status == status)
    
    charters = query.order_by(Charter.pickup_date).all()
    
    return [
        {
            "id": c.id,
            "pickup_date": c.pickup_date.isoformat(),
            "pickup_time": c.pickup_time,
            "status": c.status,
            "total_cost": float(c.total_cost) if c.total_cost else 0
        }
        for c in charters
    ]

@app.post("/charters/series/{series_id}/deactivate")
async def deactivate_charter_series(
    series_id: int,
    cancel_future_charters: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Deactivate a charter series"""
    series = db.query(CharterSeries).filter(CharterSeries.id == series_id).first()
    if not series:
        raise HTTPException(404, "Series not found")
    
    series.is_active = False
    
    # Optionally cancel future charters in series
    cancelled_count = 0
    if cancel_future_charters:
        future_charters = db.query(Charter).filter(
            Charter.series_id == series_id,
            Charter.pickup_date >= date.today(),
            Charter.status.in_(['pending', 'confirmed'])
        ).all()
        
        for charter in future_charters:
            charter.status = 'cancelled'
            charter.cancellation_reason = f"Series '{series.series_name}' deactivated"
            charter.cancellation_date = date.today()
            cancelled_count += 1
    
    db.commit()
    
    return {
        "series_id": series_id,
        "deactivated": True,
        "charters_cancelled": cancelled_count
    }
```

#### Step 3: Test Charter Series

**Create:** `test_charter_series.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Create Charter Series ==="
SERIES_ID=$(curl -s -X POST "$BASE_URL/charters/charters/series" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "series_name": "Weekly Airport Shuttle",
    "client_id": 10,
    "description": "Monday, Wednesday, Friday airport runs",
    "recurrence_pattern": "weekly",
    "recurrence_days": "mon,wed,fri",
    "start_date": "2026-03-01",
    "end_date": "2026-04-30",
    "template_charter_id": 50,
    "generate_charters": true
  }' | jq -r '.series_id')

echo "Series ID: $SERIES_ID"

echo -e "\n=== List Series ==="
curl -s -X GET "$BASE_URL/charters/charters/series?client_id=10" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Get Series Charters ==="
curl -s -X GET "$BASE_URL/charters/charters/series/$SERIES_ID/charters" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Deactivate Series ==="
curl -s -X POST "$BASE_URL/charters/charters/series/$SERIES_ID/deactivate?cancel_future_charters=true" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `charter_series` table created
- [ ] Can create series with recurrence patterns
- [ ] Automatic charter generation works
- [ ] Can list series and filter
- [ ] Can view all charters in series
- [ ] Can deactivate series
- [ ] Test script passes

---

## Task 2.4: DOT Compliance Certification

**Estimated Time:** 8-12 hours  
**Services:** Charter, Vendor  
**Impact:** MEDIUM - Required for commercial charters

### Database Changes

```sql
-- Vendor schema
\c athena
SET search_path TO vendor, public;

CREATE TABLE IF NOT EXISTS dot_certifications (
  id SERIAL PRIMARY KEY,
  vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  certification_type VARCHAR(100) NOT NULL,  -- DOT, MC, Insurance, etc.
  certification_number VARCHAR(100) NOT NULL,
  issue_date DATE NOT NULL,
  expiration_date DATE NOT NULL,
  status VARCHAR(20) DEFAULT 'active',  -- active, expired, suspended
  document_id INTEGER,  -- Reference to document service
  verified_by INTEGER,
  verified_at TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_cert_status CHECK (status IN ('active', 'expired', 'suspended', 'revoked'))
);

CREATE INDEX idx_dot_certs_vendor ON dot_certifications(vendor_id);
CREATE INDEX idx_dot_certs_expiration ON dot_certifications(expiration_date);
CREATE INDEX idx_dot_certs_status ON dot_certifications(status);

-- Alert for expiring certs
CREATE INDEX idx_dot_certs_expiring ON dot_certifications(expiration_date) 
  WHERE status = 'active' AND expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days';
```

### Implementation Steps

#### Step 1: Create Certification Models

**File:** `backend/services/vendors/models.py`

```python
class DOTCertification(Base):
    __tablename__ = "dot_certifications"
    __table_args__ = {'schema': 'vendor'}
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendor.vendors.id'), nullable=False)
    certification_type = Column(String(100), nullable=False)
    certification_number = Column(String(100), nullable=False)
    issue_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    status = Column(String(20), default='active')
    document_id = Column(Integer)
    verified_by = Column(Integer)
    verified_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Step 2: Create DOT Certification Endpoints

**File:** `backend/services/vendors/main.py`

```python
@app.post("/vendors/{vendor_id}/certifications", response_model=dict)
async def add_vendor_certification(
    vendor_id: int,
    cert_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Add DOT or other certification to vendor"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    
    certification = DOTCertification(
        vendor_id=vendor_id,
        certification_type=cert_data['certification_type'],
        certification_number=cert_data['certification_number'],
        issue_date=cert_data['issue_date'],
        expiration_date=cert_data['expiration_date'],
        document_id=cert_data.get('document_id'),
        notes=cert_data.get('notes')
    )
    db.add(certification)
    db.commit()
    db.refresh(certification)
    
    return {
        "certification_id": certification.id,
        "vendor_id": vendor_id,
        "certification_type": certification.certification_type,
        "expiration_date": certification.expiration_date.isoformat(),
        "status": certification.status
    }

@app.get("/vendors/{vendor_id}/certifications", response_model=List[dict])
async def get_vendor_certifications(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all certifications for a vendor"""
    certs = db.query(DOTCertification).filter(
        DOTCertification.vendor_id == vendor_id
    ).order_by(DOTCertification.expiration_date).all()
    
    return [
        {
            "id": c.id,
            "certification_type": c.certification_type,
            "certification_number": c.certification_number,
            "issue_date": c.issue_date.isoformat(),
            "expiration_date": c.expiration_date.isoformat(),
            "status": c.status,
            "days_until_expiration": (c.expiration_date - date.today()).days
        }
        for c in certs
    ]

@app.get("/certifications/expiring", response_model=List[dict])
async def get_expiring_certifications(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Get certifications expiring within specified days"""
    expiring_date = date.today() + timedelta(days=days_ahead)
    
    certs = db.query(DOTCertification, Vendor).join(
        Vendor, DOTCertification.vendor_id == Vendor.id
    ).filter(
        DOTCertification.status == 'active',
        DOTCertification.expiration_date <= expiring_date,
        DOTCertification.expiration_date >= date.today()
    ).order_by(DOTCertification.expiration_date).all()
    
    return [
        {
            "certification_id": cert.id,
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "certification_type": cert.certification_type,
            "certification_number": cert.certification_number,
            "expiration_date": cert.expiration_date.isoformat(),
            "days_until_expiration": (cert.expiration_date - date.today()).days
        }
        for cert, vendor in certs
    ]

@app.post("/certifications/{cert_id}/verify")
async def verify_certification(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("manager"))
):
    """Mark certification as verified"""
    cert = db.query(DOTCertification).filter(DOTCertification.id == cert_id).first()
    if not cert:
        raise HTTPException(404, "Certification not found")
    
    cert.verified_by = current_user["user_id"]
    cert.verified_at = datetime.utcnow()
    
    db.commit()
    return {"certification_id": cert_id, "verified": True}

@app.get("/charters/{charter_id}/vendor-compliance")
async def check_charter_vendor_compliance(
    charter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if assigned vendors have valid certifications"""
    charter = db.query(Charter).filter(Charter.id == charter_id).first()
    if not charter:
        raise HTTPException(404, "Charter not found")
    
    # Get all vendors for this charter
    vendor_ids = []
    if charter.is_multi_vehicle:
        vendor_ids = [v.vendor_id for v in charter.vehicles if v.vendor_id]
    elif charter.vendor_id:
        vendor_ids = [charter.vendor_id]
    
    compliance_status = []
    all_compliant = True
    
    for vendor_id in vendor_ids:
        # Check required certifications
        required_certs = ['DOT', 'MC Number', 'Insurance']
        certs = db.query(DOTCertification).filter(
            DOTCertification.vendor_id == vendor_id,
            DOTCertification.certification_type.in_(required_certs),
            DOTCertification.status == 'active',
            DOTCertification.expiration_date >= date.today()
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
```

#### Step 3: Test DOT Certifications

**Create:** `test_dot_certifications.sh`

```bash
#!/bin/bash

BASE_URL="http://localhost:8080/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "=== Add DOT Certification ==="
curl -s -X POST "$BASE_URL/vendors/vendors/1/certifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "certification_type": "DOT",
    "certification_number": "DOT-123456",
    "issue_date": "2025-01-01",
    "expiration_date": "2027-01-01",
    "notes": "Federal DOT certification"
  }' | jq

echo -e "\n=== Add MC Number ==="
curl -s -X POST "$BASE_URL/vendors/vendors/1/certifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "certification_type": "MC Number",
    "certification_number": "MC-987654",
    "issue_date": "2025-01-01",
    "expiration_date": "2026-03-15"
  }' | jq

echo -e "\n=== Add Insurance Cert ==="
curl -s -X POST "$BASE_URL/vendors/vendors/1/certifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "certification_type": "Insurance",
    "certification_number": "INS-555-2026",
    "issue_date": "2026-01-01",
    "expiration_date": "2027-01-01"
  }' | jq

echo -e "\n=== Get Vendor Certifications ==="
curl -s -X GET "$BASE_URL/vendors/vendors/1/certifications" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Get Expiring Certifications ==="
curl -s -X GET "$BASE_URL/vendors/certifications/expiring?days_ahead=90" \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n=== Check Charter Vendor Compliance ==="
curl -s -X GET "$BASE_URL/vendors/charters/1/vendor-compliance" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Success Criteria

- [ ] `dot_certifications` table created
- [ ] Can add certifications to vendors
- [ ] Can list vendor certifications
- [ ] Expiring certifications report works
- [ ] Charter compliance check works
- [ ] Test script passes

---

## Phase 2 Completion Checklist

### Database Migrations
- [ ] Charter vehicles table created
- [ ] Multi-vehicle charter fields added
- [ ] Charter template/cloning fields added
- [ ] Charter series table created
- [ ] DOT certifications table created

### API Endpoints
- [ ] Multi-vehicle charter CRUD
- [ ] Vehicle assignment to vendors
- [ ] Save charter as template
- [ ] Clone from template
- [ ] Clone existing charter
- [ ] Create charter series
- [ ] Generate series charters
- [ ] List series and charters
- [ ] Deactivate series
- [ ] Add DOT certifications
- [ ] List certifications
- [ ] Expiring certifications report
- [ ] Charter compliance check

### Testing
- [ ] Multi-vehicle charter creation tested
- [ ] Template/cloning tested
- [ ] Series generation tested
- [ ] DOT compliance tested
- [ ] All tests pass through Kong Gateway

### Documentation
- [ ] Multi-vehicle workflows documented
- [ ] Template usage documented
- [ ] Series management documented
- [ ] DOT compliance documented

---

## Next Steps

After Phase 2 completion:
1. Review and test all charter enhancements
2. Proceed to [Phase 3: Sales & Lead Management](phase_3.md)
3. Update progress tracking

---

**Estimated Total Time:** 45-70 hours (2-3 weeks)  
**Priority:** 🔴 CRITICAL - High business value features
