"""
API Health Check Tests
Quick smoke tests to verify all microservices are running
"""
import pytest
import requests

API_BASE_URL = "http://localhost:8080/api/v1"
AUTH_SERVICE = "http://localhost:8000"


@pytest.mark.smoke
class TestAPIHealth:
    """Test health endpoints for all microservices"""
    
    def test_auth_service_health(self):
        """Test auth service is running"""
        response = requests.get(f"{AUTH_SERVICE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_charter_service_health(self):
        """Test charter service is running"""
        response = requests.get(f"{API_BASE_URL}/charters/health")
        assert response.status_code == 200
    
    def test_client_service_health(self):
        """Test client service is running"""
        response = requests.get(f"{API_BASE_URL}/clients/health")
        assert response.status_code == 200
    
    def test_document_service_health(self):
        """Test document service is running"""
        response = requests.get(f"{API_BASE_URL}/documents/health")
        assert response.status_code == 200


@pytest.mark.smoke
class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        # Auth service uses OAuth2 form data at /token endpoint
        response = requests.post(
            f"{AUTH_SERVICE}/token",
            data={"username": "admin@athena.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert len(data["access_token"]) > 0
    
    def test_invalid_login(self):
        """Test invalid credentials return error"""
        response = requests.post(
            f"{AUTH_SERVICE}/token",
            data={"username": "invalid@example.com", "password": "wrong"}
        )
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test getting current user info with valid token"""
        # First login to get token
        login_response = requests.post(
            f"{AUTH_SERVICE}/token",
            data={"username": "admin@athena.com", "password": "admin123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Then get user info
        response = requests.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@athena.com"
        assert data["role"] == "admin"

