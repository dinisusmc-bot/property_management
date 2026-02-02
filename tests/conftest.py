import pytest
import os
from typing import Generator
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://athena:athena_dev_password@localhost:5432/athena"
)

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api/v1")
AUTH_SERVICE = "http://localhost:8000"


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for test session"""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a new database session for a test, rollback after test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def admin_token():
    """Get admin JWT token for API tests"""
    response = requests.post(
        f"{AUTH_SERVICE}/token",
        data={"username": "admin@athena.com", "password": "admin123"}
    )
    assert response.status_code == 200, "Admin login failed"
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def manager_token():
    """Get manager JWT token for API tests"""
    response = requests.post(
        f"{AUTH_SERVICE}/token",
        data={"username": "manager@athena.com", "password": "admin123"}
    )
    assert response.status_code == 200, "Manager login failed"
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def vendor_token():
    """Get vendor JWT token for API tests"""
    response = requests.post(
        f"{AUTH_SERVICE}/token",
        data={"username": "vendor1@athena.com", "password": "admin123"}
    )
    assert response.status_code == 200, "Vendor login failed"
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def driver_token():
    """Get driver JWT token for API tests"""
    response = requests.post(
        f"{AUTH_SERVICE}/token",
        data={"username": "driver1@athena.com", "password": "admin123"}
    )
    assert response.status_code == 200, "Driver login failed"
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    """Get authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_headers(manager_token):
    """Get authorization headers with manager token"""
    return {"Authorization": f"Bearer {manager_token}"}


@pytest.fixture
def vendor_headers(vendor_token):
    """Get authorization headers with vendor token"""
    return {"Authorization": f"Bearer {vendor_token}"}


@pytest.fixture
def driver_headers(driver_token):
    """Get authorization headers with driver token"""
    return {"Authorization": f"Bearer {driver_token}"}


@pytest.fixture
def test_charter_data():
    """Sample charter data for testing"""
    return {
        "client_id": 5,
        "vehicle_id": 4,
        "trip_date": "2025-12-25",
        "passengers": 30,
        "trip_hours": 6.0,
        "base_cost": 450.0,
        "mileage_cost": 100.0,
        "additional_fees": 50.0,
        "total_cost": 600.0,
        "is_overnight": False,
        "is_weekend": True,
        "notes": "Test charter from automated tests",
        "stops": [
            {
                "location": "123 Test St, Philadelphia, PA 19101",
                "arrival_time": "2025-12-25T10:00:00Z",
                "departure_time": "2025-12-25T10:30:00Z",
                "notes": "Pickup location",
                "sequence": 1
            },
            {
                "location": "456 Test Ave, Philadelphia, PA 19102",
                "arrival_time": "2025-12-25T16:00:00Z",
                "departure_time": None,
                "notes": "Drop-off location",
                "sequence": 2
            }
        ]
    }



@pytest.fixture
def test_client_data():
    """Sample client data for testing"""
    return {
        "name": "Test Client Inc",
        "email": "testclient@example.com",
        "phone": "555-0123",
        "address": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345",
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test (quick validation)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
