"""
Load and Performance Testing with Locust
Tests API performance under concurrent load
"""
from locust import HttpUser, task, between, events
import random
from datetime import datetime, timedelta


class CharterSystemUser(HttpUser):
    """Simulates a user interacting with the Charter Management System"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login and get JWT token before starting tasks"""
        response = self.client.post(
            "/token",
            data={
                "username": "admin@athena.com",
                "password": "admin123"
            },
            name="POST /token (login)"
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Login failed with status {response.status_code}")
            self.headers = {}
    
    @task(10)
    def list_charters(self):
        """Most common operation - list all charters"""
        self.client.get(
            "/api/v1/charters/charters",
            headers=self.headers,
            name="GET /charters (list)"
        )
    
    @task(5)
    def view_charter_detail(self):
        """View specific charter details"""
        # Use random charter ID from 1-100
        charter_id = random.randint(1, 100)
        self.client.get(
            f"/api/v1/charters/charters/{charter_id}",
            headers=self.headers,
            name="GET /charters/{id} (detail)"
        )
    
    @task(3)
    def list_clients(self):
        """List clients"""
        self.client.get(
            "/api/v1/clients/clients",
            headers=self.headers,
            name="GET /clients (list)"
        )
    
    @task(2)
    def list_vehicles(self):
        """List available vehicles"""
        self.client.get(
            "/api/v1/charters/vehicles",
            headers=self.headers,
            name="GET /vehicles (list)"
        )
    
    @task(2)
    def filter_charters_by_status(self):
        """Filter charters by status"""
        statuses = ["quote", "approved", "booked", "confirmed", "in_progress", "completed"]
        status = random.choice(statuses)
        self.client.get(
            f"/api/v1/charters/charters?status={status}",
            headers=self.headers,
            name="GET /charters?status= (filter)"
        )
    
    @task(1)
    def create_charter(self):
        """Create a new charter (less frequent)"""
        tomorrow = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        
        payload = {
            "client_id": random.randint(4, 9),  # Use valid client IDs from seed data
            "vehicle_id": random.randint(4, 8),  # Use valid vehicle IDs from seed data
            "trip_date": tomorrow,
            "passengers": random.randint(10, 50),
            "trip_hours": random.uniform(2.0, 12.0),
            "pickup_location": f"{random.randint(100, 999)} Main St",
            "dropoff_location": f"{random.randint(100, 999)} Oak Ave",
            "base_cost": random.uniform(500, 2000),
            "mileage_cost": random.uniform(100, 500),
            "total_cost": random.uniform(600, 2500)
        }
        
        self.client.post(
            "/api/v1/charters/charters",
            json=payload,
            headers=self.headers,
            name="POST /charters (create)"
        )
    
    @task(1)
    def update_charter_status(self):
        """Update charter status"""
        charter_id = random.randint(1, 100)
        statuses = ["approved", "booked", "confirmed"]
        status = random.choice(statuses)
        
        self.client.put(
            f"/api/v1/charters/charters/{charter_id}",
            json={"status": status},
            headers=self.headers,
            name="PUT /charters/{id} (update status)"
        )
    
    @task(2)
    def list_documents(self):
        """List documents for a charter"""
        charter_id = random.randint(1, 50)
        self.client.get(
            f"/api/v1/documents/charter/{charter_id}",
            headers=self.headers,
            name="GET /documents/charter/{id} (list)"
        )
    
    @task(1)
    def get_document_detail(self):
        """Get document metadata"""
        doc_id = random.randint(1, 20)
        self.client.get(
            f"/api/v1/documents/{doc_id}",
            headers=self.headers,
            name="GET /documents/{id} (metadata)"
        )
    
    @task(1)
    def check_service_health(self):
        """Check service health endpoints"""
        services = ["charters", "clients", "documents", "notifications"]
        service = random.choice(services)
        self.client.get(
            f"/api/v1/{service}/health",
            headers=self.headers,
            name=f"GET /{service}/health"
        )


class AdminUser(HttpUser):
    """Simulates admin user with heavier operations"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as admin"""
        response = self.client.post(
            "/token",
            data={
                "username": "admin@athena.com",
                "password": "admin123"
            },
            name="POST /token (admin login)"
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(5)
    def list_all_charters(self):
        """Admin frequently views all charters"""
        self.client.get(
            "/api/v1/charters/charters",
            headers=self.headers,
            name="GET /charters (admin)"
        )
    
    @task(3)
    def manage_clients(self):
        """Admin manages client accounts"""
        self.client.get(
            "/api/v1/clients/clients",
            headers=self.headers,
            name="GET /clients (admin)"
        )
    
    @task(2)
    def create_charter_quote(self):
        """Admin creates charter quotes"""
        tomorrow = (datetime.now() + timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d")
        
        payload = {
            "client_id": random.randint(4, 9),
            "vehicle_id": random.randint(4, 8),
            "trip_date": tomorrow,
            "passengers": random.randint(20, 56),
            "trip_hours": random.uniform(4.0, 10.0),
            "pickup_location": "Conference Center",
            "dropoff_location": "Hotel",
            "base_cost": random.uniform(800, 2500),
            "mileage_cost": random.uniform(150, 600),
            "total_cost": random.uniform(950, 3100)
        }
        
        self.client.post(
            "/api/v1/charters/charters",
            json=payload,
            headers=self.headers,
            name="POST /charters (admin create)"
        )
    
    @task(2)
    def update_charter_workflow(self):
        """Admin progresses charter through workflow"""
        charter_id = random.randint(1, 100)
        statuses = ["approved", "booked", "confirmed", "in_progress", "completed"]
        status = random.choice(statuses)
        
        self.client.put(
            f"/api/v1/charters/charters/{charter_id}",
            json={"status": status},
            headers=self.headers,
            name="PUT /charters (admin workflow)"
        )
    
    @task(1)
    def assign_driver(self):
        """Admin assigns driver to charter"""
        charter_id = random.randint(1, 100)
        driver_id = random.randint(1, 5)
        
        self.client.put(
            f"/api/v1/charters/charters/{charter_id}",
            json={"driver_id": driver_id},
            headers=self.headers,
            name="PUT /charters (assign driver)"
        )


class DriverUser(HttpUser):
    """Simulates driver accessing their dashboard"""
    
    wait_time = between(5, 15)  # Drivers check less frequently
    
    def on_start(self):
        """Login as driver"""
        # Use one of the driver accounts
        driver_emails = ["driver1@athena.com", "driver2@athena.com"]
        email = random.choice(driver_emails)
        
        response = self.client.post(
            "/token",
            data={
                "username": email,
                "password": "admin123"
            },
            name="POST /token (driver login)"
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(10)
    def view_my_charters(self):
        """Driver views their assigned charters"""
        self.client.get(
            "/api/v1/charters/charters",
            headers=self.headers,
            name="GET /charters (driver)"
        )
    
    @task(3)
    def view_charter_detail(self):
        """Driver views charter details"""
        charter_id = random.randint(1, 50)
        self.client.get(
            f"/api/v1/charters/charters/{charter_id}",
            headers=self.headers,
            name="GET /charters/{id} (driver)"
        )
    
    @task(1)
    def update_location(self):
        """Driver updates their location (simulated)"""
        charter_id = random.randint(1, 50)
        lat = random.uniform(39.0, 41.0)
        lon = random.uniform(-75.0, -73.0)
        
        self.client.put(
            f"/api/v1/charters/charters/{charter_id}",
            json={
                "last_checkin_location": f"{lat},{lon}",
                "last_checkin_time": datetime.now().isoformat()
            },
            headers=self.headers,
            name="PUT /charters (driver location)"
        )


# Event listeners for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start message"""
    print("\n" + "="*80)
    print("Starting Load Test for Athena Charter Management System")
    print(f"Target: {environment.host}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary"""
    print("\n" + "="*80)
    print("Load Test Completed")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")
    print("="*80 + "\n")
