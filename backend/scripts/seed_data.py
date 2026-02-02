"""
Seed database with sample data for testing.
Run with: python seed_data.py
"""
import asyncio
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://athena:athena_dev_password@localhost:5432/athena')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def seed_users(session):
    """Create default users including vendors."""
    print("Seeding users...")
    
    # Don't skip if admin exists - create other users individually
    # Password for all users: admin123
    import bcrypt
    password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
    
    users = [
        ("admin@athena.com", "Admin User", password_hash, "admin", True),
        ("manager@athena.com", "Sarah Johnson", password_hash, "manager", False),
        ("dispatcher@athena.com", "Mike Rodriguez", password_hash, "user", False),
        # Vendor accounts
        ("vendor1@athena.com", "John Anderson", password_hash, "vendor", False),
        ("vendor2@athena.com", "Maria Garcia", password_hash, "vendor", False),
        ("vendor3@athena.com", "David Chen", password_hash, "vendor", False),
        ("vendor4@athena.com", "Jennifer Williams", password_hash, "vendor", False),
        ("vendor5@athena.com", "Robert Taylor", password_hash, "vendor", False),
        # Driver accounts - temporary users assigned to specific charters
        ("driver1@athena.com", "Tom Mitchell", password_hash, "driver", False),
        ("driver2@athena.com", "Lisa Brown", password_hash, "driver", False),
        ("driver3@athena.com", "Carlos Rodriguez", password_hash, "driver", False),
        ("driver4@athena.com", "Amy Wilson", password_hash, "driver", False),
    ]
    
    created_count = 0
    for email, name, password, role, is_superuser in users:
        # Check if user already exists
        result = session.execute(text("SELECT COUNT(*) FROM users WHERE email = :email"), {"email": email})
        if result.scalar() == 0:
            session.execute(text("""
                INSERT INTO users (email, full_name, hashed_password, role, is_active, is_superuser)
                VALUES (:email, :name, :password, :role, true, :is_superuser)
            """), {"email": email, "name": name, "password": password, "role": role, "is_superuser": is_superuser})
            created_count += 1
    
    if created_count > 0:
        print(f"  Created {created_count} users")
    else:
        print("  Users already exist")
    
    # Count total vendors
    result = session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'vendor'"))
    vendor_count = result.scalar()
    print(f"  Total vendors in system: {vendor_count}")

def seed_vehicles(session):
    """Create vehicle fleet."""
    print("Seeding vehicles...")
    
    result = session.execute(text("SELECT COUNT(*) FROM vehicles"))
    if result.scalar() > 0:
        print("  Vehicles already exist")
        return
    
    vehicles = [
        ("Mini Bus (25 passenger)", 25, 75.00, 3.50),
        ("Coach Bus (47 passenger)", 47, 95.00, 4.00),
        ("Luxury Motor Coach (56 passenger)", 56, 125.00, 4.50),
        ("Shuttle Van (14 passenger)", 14, 55.00, 2.50),
        ("Executive Sprinter (12 passenger)", 12, 85.00, 3.00),
    ]
    
    for name, capacity, base_rate, per_mile in vehicles:
        session.execute(text("""
            INSERT INTO vehicles (name, capacity, base_rate, per_mile_rate, is_active)
            VALUES (:name, :capacity, :base_rate, :per_mile, true)
        """), {
            "name": name, "capacity": capacity, "base_rate": base_rate, "per_mile": per_mile
        })
    
    print(f"  Created {len(vehicles)} vehicles")

def seed_clients(session):
    """Create sample clients."""
    print("Seeding clients...")
    
    result = session.execute(text("SELECT COUNT(*) FROM clients"))
    if result.scalar() > 0:
        print("  Clients already exist")
        return
    
    clients = [
        ("ABC Corporation", "corporate", "contact@abc-corp.com", "555-0101", "123 Business Ave", "New York", "NY", "10001", 10000.00),
        ("XYZ Events", "corporate", "events@xyz.com", "555-0102", "456 Event St", "Boston", "MA", "02101", 15000.00),
        ("Smith Wedding Party", "individual", "john.smith@email.com", "555-0103", "789 Main St", "Philadelphia", "PA", "19101", 0),
        ("City School District", "corporate", "transport@cityschools.edu", "555-0104", "321 Education Ln", "Newark", "NJ", "07101", 25000.00),
        ("Johnson Family", "individual", "mjohnson@email.com", "555-0105", "654 Oak Dr", "Baltimore", "MD", "21201", 0),
        ("Tech Startup Inc", "corporate", "admin@techstartup.com", "555-0106", "987 Innovation Blvd", "Washington", "DC", "20001", 5000.00),
    ]
    
    for name, type_, email, phone, address, city, state, zip_code, credit in clients:
        result = session.execute(text("""
            INSERT INTO clients (name, type, email, phone, address, city, state, zip_code, credit_limit, balance_owed, is_active)
            VALUES (:name, :type, :email, :phone, :address, :city, :state, :zip, :credit, 0.0, true)
            RETURNING id
        """), {
            "name": name, "type": type_, "email": email, "phone": phone,
            "address": address, "city": city, "state": state, "zip": zip_code, "credit": credit
        })
        client_id = result.scalar()
        
        # Add primary contact for each client
        first, last = name.split()[0], name.split()[-1]
        session.execute(text("""
            INSERT INTO contacts (client_id, first_name, last_name, email, phone, is_primary)
            VALUES (:client_id, :first, :last, :email, :phone, true)
        """), {
            "client_id": client_id, "first": first, "last": last,
            "email": email, "phone": phone
        })
    
    print(f"  Created {len(clients)} clients with contacts")

def seed_charters(session):
    """Create sample charters with vendor assignments and proper pricing."""
    print("Seeding charters...")
    
    result = session.execute(text("SELECT COUNT(*) FROM charters"))
    if result.scalar() > 0:
        print("  Charters already exist")
        return
    
    # Get client, vehicle, vendor, and driver IDs
    clients = session.execute(text("SELECT id FROM clients ORDER BY id")).fetchall()
    vehicles = session.execute(text("SELECT id FROM vehicles ORDER BY id")).fetchall()
    vendors = session.execute(text("SELECT id FROM users WHERE role = 'vendor' ORDER BY id")).fetchall()
    drivers = session.execute(text("SELECT id FROM users WHERE role = 'driver' ORDER BY id")).fetchall()
    
    today = datetime.now().date()
    now = datetime.now()
    
    # Helper function to calculate pricing with proper vendor/client split
    def calc_pricing(base, mileage, add_fees=0):
        """Calculate vendor and client pricing with 25% margin"""
        vendor_base = round(base * 0.75, 2)
        vendor_mileage = round(mileage * 0.75, 2)
        vendor_add = round(add_fees, 2)
        
        client_base = round(base * 1.0, 2)
        client_mileage = round(mileage * 1.0, 2) 
        client_add = round(add_fees, 2)
        
        vendor_total = vendor_base + vendor_mileage + vendor_add
        client_total = client_base + client_mileage + client_add
        profit_margin = (client_total - vendor_total) / client_total if client_total > 0 else 0
        
        return {
            'base': base, 'mileage': mileage, 'add_fees': add_fees,
            'vendor_base': vendor_base, 'vendor_mileage': vendor_mileage, 'vendor_add': vendor_add,
            'client_base': client_base, 'client_mileage': client_mileage, 'client_add': client_add,
            'profit_margin': profit_margin
        }
    
    # Charters with complete pricing details
    charters_data = [
        # Past completed charter with vendor and driver
        {
            'client_idx': 0, 'vehicle_idx': 1, 'vendor_idx': 0, 'driver_idx': 0, 'status': 'completed',
            'trip_date': today - timedelta(days=10), 'passengers': 45, 'hours': 8.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(760, 215, 0),
            'deposit': 400.00, 'notes': 'Corporate team building event - confirmed amenities',
            'vendor_notes': 'Trip completed smoothly. Client very satisfied with service.',
            'location': '40.232550,-74.301440', 'checkin': now - timedelta(days=10, hours=2)
        },
        # Past completed with additional fees
        {
            'client_idx': 1, 'vehicle_idx': 0, 'vendor_idx': 1, 'driver_idx': 1, 'status': 'completed',
            'trip_date': today - timedelta(days=5), 'passengers': 20, 'hours': 6.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(450, 100, 100),
            'deposit': 200.00, 'notes': 'Wedding party transport',
            'vendor_notes': 'Beautiful event, guests were very happy.',
            'location': '40.232550,-74.301440', 'checkin': now - timedelta(days=5, hours=1)
        },
        # Upcoming charter (tomorrow) - driver assigned
        {
            'client_idx': 2, 'vehicle_idx': 2, 'vendor_idx': 2, 'driver_idx': 2, 'status': 'confirmed',
            'trip_date': today + timedelta(days=1), 'passengers': 12, 'hours': 4.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(220, 50, 0),
            'deposit': 100.00, 'notes': 'Airport transfer for business group',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
        # School field trip - driver assigned
        {
            'client_idx': 3, 'vehicle_idx': 1, 'vendor_idx': 3, 'driver_idx': 3, 'status': 'confirmed',
            'trip_date': today + timedelta(days=7), 'passengers': 50, 'hours': 10.0,
            'overnight': True, 'weekend': False, 'pricing': calc_pricing(1250, 450, 200),
            'deposit': 700.00, 'notes': 'School field trip to museum - requires parking pass',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
        # Quote/pending - no vendor or driver yet
        {
            'client_idx': 4, 'vehicle_idx': 0, 'vendor_idx': None, 'driver_idx': None, 'status': 'quote',
            'trip_date': today + timedelta(days=14), 'passengers': 18, 'hours': 5.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(375, 75, 0),
            'deposit': 0.00, 'notes': 'Tech conference shuttle service',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
        # In progress today - active driver
        {
            'client_idx': 5, 'vehicle_idx': 2, 'vendor_idx': 4, 'driver_idx': 0, 'status': 'in_progress',
            'trip_date': today, 'passengers': 10, 'hours': 6.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(510, 80, 0),
            'deposit': 200.00, 'notes': 'University athletics team transport',
            'vendor_notes': 'En route. Traffic moderate. ETA on schedule.',
            'location': '40.232550,-74.301440', 'checkin': now - timedelta(minutes=15)
        },
        # Executive transfer
        {
            'client_idx': 0, 'vehicle_idx': 3, 'vendor_idx': 0, 'driver_idx': 1, 'status': 'confirmed',
            'trip_date': today + timedelta(days=2), 'passengers': 14, 'hours': 3.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(165, 35, 0),
            'deposit': 75.00, 'notes': 'Executive airport transfer',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
        # Corporate meeting with fees
        {
            'client_idx': 1, 'vehicle_idx': 4, 'vendor_idx': 1, 'driver_idx': 2, 'status': 'confirmed',
            'trip_date': today + timedelta(days=3), 'passengers': 12, 'hours': 5.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(425, 90, 0),
            'deposit': 150.00, 'notes': 'Corporate client meeting transport',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
        # Past athletic event
        {
            'client_idx': 3, 'vehicle_idx': 2, 'vendor_idx': 2, 'driver_idx': 3, 'status': 'completed',
            'trip_date': today - timedelta(days=3), 'passengers': 35, 'hours': 7.0,
            'overnight': False, 'weekend': False, 'pricing': calc_pricing(875, 157.5, 0),
            'deposit': 300.00, 'notes': 'Athletic team championship game',
            'vendor_notes': 'Great group. Everything went perfectly.',
            'location': '40.232550,-74.301440', 'checkin': now - timedelta(days=3, hours=3)
        },
        # Weekend retreat with fees
        {
            'client_idx': 4, 'vehicle_idx': 1, 'vendor_idx': 3, 'driver_idx': None, 'status': 'confirmed',
            'trip_date': today + timedelta(days=5), 'passengers': 47, 'hours': 12.0,
            'overnight': False, 'weekend': True, 'pricing': calc_pricing(1140, 480, 150),
            'deposit': 600.00, 'notes': 'Weekend company retreat - requires WiFi',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
        # High-value charter with vendor fees
        {
            'client_idx': 0, 'vehicle_idx': 2, 'vendor_idx': 4, 'driver_idx': 1, 'status': 'confirmed',
            'trip_date': today + timedelta(days=4), 'passengers': 25, 'hours': 15.0,
            'overnight': True, 'weekend': False, 'pricing': calc_pricing(165.03, 500, 100),
            'deposit': 300.00, 'notes': 'Multi-day corporate event',
            'vendor_notes': None, 'location': None, 'checkin': None
        },
    ]
    
    charter_ids = []
    for data in charters_data:
        if data['vendor_idx'] is not None and data['vendor_idx'] < len(vendors):
            vendor_id = vendors[data['vendor_idx']][0]
        else:
            vendor_id = None
        
        if data['driver_idx'] is not None and data['driver_idx'] < len(drivers):
            driver_id = drivers[data['driver_idx']][0]
        else:
            driver_id = None
            
        p = data['pricing']
        
        result = session.execute(text("""
            INSERT INTO charters (
                client_id, vehicle_id, vendor_id, driver_id, status, trip_date, passengers, trip_hours,
                is_overnight, is_weekend, 
                base_cost, mileage_cost, additional_fees, total_cost, deposit_amount,
                vendor_base_cost, vendor_mileage_cost, vendor_additional_fees,
                client_base_charge, client_mileage_charge, client_additional_fees,
                profit_margin,
                notes, vendor_notes, last_checkin_location, last_checkin_time
            ) VALUES (
                :client_id, :vehicle_id, :vendor_id, :driver_id, :status, :trip_date, :passengers, :hours,
                :overnight, :weekend,
                :base, :mileage, :fees, :total, :deposit,
                :vendor_base, :vendor_mileage, :vendor_add,
                :client_base, :client_mileage, :client_add,
                :profit_margin,
                :notes, :vendor_notes, :location, :checkin
            ) RETURNING id
        """), {
            "client_id": clients[data['client_idx']][0],
            "vehicle_id": vehicles[data['vehicle_idx']][0],
            "vendor_id": vendor_id,
            "driver_id": driver_id,
            "status": data['status'],
            "trip_date": data['trip_date'],
            "passengers": data['passengers'],
            "hours": data['hours'],
            "overnight": data['overnight'],
            "weekend": data['weekend'],
            "base": p['base'],
            "mileage": p['mileage'],
            "fees": p['add_fees'],
            "total": p['client_base'] + p['client_mileage'] + p['client_add'],
            "deposit": data['deposit'],
            "vendor_base": p['vendor_base'],
            "vendor_mileage": p['vendor_mileage'],
            "vendor_add": p['vendor_add'],
            "client_base": p['client_base'],
            "client_mileage": p['client_mileage'],
            "client_add": p['client_add'],
            "profit_margin": p['profit_margin'],
            "notes": data['notes'],
            "vendor_notes": data['vendor_notes'],
            "location": data['location'],
            "checkin": data['checkin']
        })
        charter_ids.append(result.scalar())
    
    print(f"  Created {len(charters_data)} charters with vendor pricing")
    return charter_ids

def seed_stops(session):
    """Create itinerary stops for charters."""
    print("Seeding charter itineraries (stops)...")
    
    result = session.execute(text("SELECT COUNT(*) FROM stops"))
    if result.scalar() > 0:
        print("  Stops already exist")
        return
    
    # Get charter IDs
    charters = session.execute(text("SELECT id, trip_date, status FROM charters ORDER BY id")).fetchall()
    
    if not charters:
        print("  No charters found, skipping stops")
        return
    
    stops_created = 0
    
    # Charter 1: Corporate team building - NYC to Boston with lunch stop
    if len(charters) > 0:
        charter_id = charters[0][0]
        trip_date = charters[0][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=8, minute=0)
        
        charter_stops = [
            (charter_id, 1, "123 Business Ave, New York, NY 10001", base_time, base_time + timedelta(minutes=30), "Pickup - Corporate headquarters"),
            (charter_id, 2, "Rest Area, I-95 Connecticut", base_time + timedelta(hours=2), base_time + timedelta(hours=2, minutes=30), "Lunch break - catered meal"),
            (charter_id, 3, "456 Resort Dr, Boston, MA 02101", base_time + timedelta(hours=4), None, "Destination - Team building venue"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    # Charter 2: Wedding party - multiple pickup locations
    if len(charters) > 1:
        charter_id = charters[1][0]
        trip_date = charters[1][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=14, minute=0)
        
        charter_stops = [
            (charter_id, 1, "789 Main St, Philadelphia, PA 19101", base_time, base_time + timedelta(minutes=20), "Pickup - Bride's family"),
            (charter_id, 2, "321 Oak Ave, Philadelphia, PA 19102", base_time + timedelta(minutes=30), base_time + timedelta(minutes=50), "Pickup - Groom's family"),
            (charter_id, 3, "Grand Hotel, 555 Wedding Blvd, Philadelphia, PA 19103", base_time + timedelta(hours=1), base_time + timedelta(hours=5), "Wedding venue - ceremony and reception"),
            (charter_id, 4, "789 Main St, Philadelphia, PA 19101", base_time + timedelta(hours=5, minutes=30), None, "Drop-off - return to origin"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    # Charter 3: Airport transfer - simple round trip
    if len(charters) > 2:
        charter_id = charters[2][0]
        trip_date = charters[2][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=6, minute=0)
        
        charter_stops = [
            (charter_id, 1, "Downtown Hotel, Philadelphia, PA", base_time, base_time + timedelta(minutes=15), "Hotel pickup - business travelers"),
            (charter_id, 2, "Philadelphia International Airport, Terminal B", base_time + timedelta(minutes=45), None, "Airport drop-off"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    # Charter 4: School field trip - multiple stops
    if len(charters) > 3:
        charter_id = charters[3][0]
        trip_date = charters[3][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=7, minute=30)
        
        charter_stops = [
            (charter_id, 1, "321 Education Ln, Newark, NJ 07101", base_time, base_time + timedelta(minutes=30), "School pickup"),
            (charter_id, 2, "Natural History Museum, New York, NY", base_time + timedelta(hours=2), base_time + timedelta(hours=4), "Museum visit - guided tour"),
            (charter_id, 3, "Central Park Picnic Area, New York, NY", base_time + timedelta(hours=4, minutes=15), base_time + timedelta(hours=5), "Lunch break"),
            (charter_id, 4, "Science Center, 123 Discovery Ave, New York, NY", base_time + timedelta(hours=5, minutes=30), base_time + timedelta(hours=7), "Science exhibit"),
            (charter_id, 5, "321 Education Ln, Newark, NJ 07101", base_time + timedelta(hours=9), None, "Return to school"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    # Charter 6: In-progress trip with current location
    if len(charters) > 5:
        charter_id = charters[5][0]
        trip_date = charters[5][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=9, minute=0)
        now = datetime.now()
        
        charter_stops = [
            (charter_id, 1, "100 Campus Way, Ann Arbor, MI 48109", base_time, base_time + timedelta(minutes=30), "University pickup - completed"),
            (charter_id, 2, "Rest Stop, I-80 Pennsylvania", base_time + timedelta(hours=3), base_time + timedelta(hours=3, minutes=20), "Currently here - comfort break"),
            (charter_id, 3, "Championship Arena, Philadelphia, PA", base_time + timedelta(hours=6), None, "Game venue - estimated arrival"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    # Charter 7: Executive airport transfer
    if len(charters) > 6:
        charter_id = charters[6][0]
        trip_date = charters[6][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=5, minute=30)
        
        charter_stops = [
            (charter_id, 1, "Executive Suites Hotel, New York, NY", base_time, base_time + timedelta(minutes=10), "VIP pickup"),
            (charter_id, 2, "JFK International Airport, Terminal 4", base_time + timedelta(hours=1), None, "International flight departure"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    # Charter 10: Weekend retreat - multi-day itinerary
    if len(charters) > 9:
        charter_id = charters[9][0]
        trip_date = charters[9][1]
        base_time = datetime.combine(trip_date, datetime.min.time()).replace(hour=8, minute=0)
        
        charter_stops = [
            (charter_id, 1, "500 Innovation Dr, San Francisco, CA", base_time, base_time + timedelta(minutes=45), "Company headquarters pickup"),
            (charter_id, 2, "Scenic Overlook, Highway 1", base_time + timedelta(hours=2), base_time + timedelta(hours=2, minutes=30), "Photo opportunity"),
            (charter_id, 3, "Lunch Bistro, Monterey, CA", base_time + timedelta(hours=4), base_time + timedelta(hours=5), "Lunch stop"),
            (charter_id, 4, "Mountain Retreat Center, Big Sur, CA", base_time + timedelta(hours=6, minutes=30), base_time + timedelta(days=2, hours=6), "Retreat venue - 2 night stay"),
            (charter_id, 5, "500 Innovation Dr, San Francisco, CA", base_time + timedelta(days=2, hours=12), None, "Return to origin"),
        ]
        
        for stop in charter_stops:
            session.execute(text("""
                INSERT INTO stops (charter_id, sequence, location, arrival_time, departure_time, notes)
                VALUES (:charter_id, :seq, :location, :arrival, :departure, :notes)
            """), {"charter_id": stop[0], "seq": stop[1], "location": stop[2], 
                   "arrival": stop[3], "departure": stop[4], "notes": stop[5]})
            stops_created += 1
    
    print(f"  Created {stops_created} itinerary stops for charters")

def seed_payments(session, charter_ids):
    """Create vendor and client payment records for completed charters."""
    print("Seeding payment records...")
    
    result = session.execute(text("SELECT COUNT(*) FROM vendor_payments"))
    if result.scalar() > 0:
        print("  Payments already exist")
        return
    
    # Get charters with their pricing and client info
    charters = session.execute(text("""
        SELECT id, status, vendor_id, client_id,
               vendor_base_cost, vendor_mileage_cost, vendor_additional_fees,
               client_base_charge, client_mileage_charge, client_additional_fees,
               deposit_amount
        FROM charters 
        ORDER BY id
    """)).fetchall()
    
    vendor_payments_count = 0
    client_payments_count = 0
    
    for charter in charters:
        charter_id, status, vendor_id, client_id, v_base, v_mile, v_add, c_base, c_mile, c_add, deposit = charter
        
        # Calculate totals
        vendor_total = (v_base or 0) + (v_mile or 0) + (v_add or 0)
        client_total = (c_base or 0) + (c_mile or 0) + (c_add or 0)
        
        # For completed charters, create payment records
        if status == 'completed':
            # Vendor payment - mark as paid for completed trips
            if vendor_id and vendor_total > 0:
                session.execute(text("""
                    INSERT INTO vendor_payments (charter_id, vendor_id, amount, payment_status, payment_date, notes)
                    VALUES (:charter_id, :vendor_id, :amount, 'paid', CURRENT_TIMESTAMP - INTERVAL '2 days', 'Payment processed via ACH')
                """), {"charter_id": charter_id, "vendor_id": vendor_id, "amount": vendor_total})
                vendor_payments_count += 1
            
            # Client payment - deposit + remaining balance
            if client_total > 0:
                # Deposit payment (if any)
                if deposit and deposit > 0:
                    session.execute(text("""
                        INSERT INTO client_payments (charter_id, client_id, amount, payment_status, payment_method, payment_date, notes)
                        VALUES (:charter_id, :client_id, :amount, 'paid', 'credit_card', CURRENT_TIMESTAMP - INTERVAL '10 days', 'Deposit payment')
                    """), {"charter_id": charter_id, "client_id": client_id, "amount": deposit})
                    client_payments_count += 1
                
                # Final payment
                remaining = client_total - (deposit or 0)
                if remaining > 0:
                    session.execute(text("""
                        INSERT INTO client_payments (charter_id, client_id, amount, payment_status, payment_method, payment_date, notes)
                        VALUES (:charter_id, :client_id, :amount, 'paid', 'check', CURRENT_TIMESTAMP - INTERVAL '1 day', 'Final payment')
                    """), {"charter_id": charter_id, "client_id": client_id, "amount": remaining})
                    client_payments_count += 1
        
        # For confirmed future charters, create deposit records
        elif status == 'confirmed':
            # Vendor payment - pending
            if vendor_id and vendor_total > 0:
                session.execute(text("""
                    INSERT INTO vendor_payments (charter_id, vendor_id, amount, payment_status, payment_date, notes)
                    VALUES (:charter_id, :vendor_id, :amount, 'pending', NULL, 'Payment scheduled after trip completion')
                """), {"charter_id": charter_id, "vendor_id": vendor_id, "amount": vendor_total})
                vendor_payments_count += 1
            
            # Client deposit payment (if any)
            if deposit and deposit > 0:
                session.execute(text("""
                    INSERT INTO client_payments (charter_id, client_id, amount, payment_status, payment_method, payment_date, notes)
                    VALUES (:charter_id, :client_id, :amount, 'paid', 'credit_card', CURRENT_TIMESTAMP, 'Deposit payment')
                """), {"charter_id": charter_id, "client_id": client_id, "amount": deposit})
                client_payments_count += 1
            
            # Remaining balance - pending
            remaining = client_total - (deposit or 0)
            if remaining > 0:
                session.execute(text("""
                    INSERT INTO client_payments (charter_id, client_id, amount, payment_status, payment_method, payment_date, notes)
                    VALUES (:charter_id, :client_id, :amount, 'pending', NULL, NULL, 'Balance due upon trip completion')
                """), {"charter_id": charter_id, "client_id": client_id, "amount": remaining})
                client_payments_count += 1
    
    print(f"  Created {vendor_payments_count} vendor payments and {client_payments_count} client payments")

def main():
    """Run all seed functions."""
    session = SessionLocal()
    
    try:
        print("\nSeeding Athena database...\n")
        
        seed_users(session)
        seed_vehicles(session)
        seed_clients(session)
        charter_ids = seed_charters(session)
        seed_stops(session)
        seed_payments(session, charter_ids)
        
        session.commit()
        print("\n✅ Database seeded successfully!")
        print("\nDefault logins:")
        print("  Admin:    admin@athena.com / admin123")
        print("  Manager:  manager@athena.com / admin123")
        print("  Vendor:   vendor1@athena.com / admin123")
        print("\n📊 Summary:")
        result = session.execute(text("SELECT COUNT(*) FROM users WHERE role='vendor'"))
        vendor_count = result.scalar()
        result = session.execute(text("SELECT COUNT(*) FROM charters"))
        charter_count = result.scalar()
        result = session.execute(text("SELECT COUNT(*) FROM stops"))
        stop_count = result.scalar()
        result = session.execute(text("SELECT COUNT(*) FROM vendor_payments"))
        vendor_payment_count = result.scalar()
        result = session.execute(text("SELECT COUNT(*) FROM client_payments"))
        client_payment_count = result.scalar()
        print(f"  {vendor_count} vendors")
        print(f"  {charter_count} charters")
        print(f"  {stop_count} itinerary stops")
        print(f"  {vendor_payment_count} vendor payment records")
        print(f"  {client_payment_count} client payment records\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
