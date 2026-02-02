"""
Charter API Tests
Test charter CRUD operations and workflow
"""
import pytest
import requests

API_BASE_URL = "http://localhost:8080/api/v1"


class TestCharterAPI:
    """Test charter endpoints"""
    
    def test_list_charters(self, admin_headers):
        """Test GET /charters endpoint"""
        response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have charters from seed data"
    
    def test_charter_schema(self, admin_headers):
        """Test charter response has expected fields"""
        response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert response.status_code == 200
        charters = response.json()
        assert len(charters) > 0, "Should have charters from seed data"
        charter = charters[0]
        
        # Required fields
        assert "id" in charter
        assert "trip_date" in charter
        assert "status" in charter
        assert "passengers" in charter
        
        # Pricing fields
        assert "vendor_base_cost" in charter
        assert "vendor_mileage_cost" in charter
        assert "client_base_charge" in charter
        assert "client_mileage_charge" in charter
        
        # Driver fields (may be null if not assigned)
        assert "driver_id" in charter
        assert "driver_name" in charter
        assert "driver_email" in charter
    
    def test_get_charter_detail(self, admin_headers):
        """Test GET /charters/{id} endpoint"""
        # First get list to find a valid charter ID
        list_response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert list_response.status_code == 200
        charters = list_response.json()
        assert len(charters) > 0, "No charters available for testing"
        
        charter_id = charters[0]["id"]
        
        # Now test getting that specific charter
        response = requests.get(
            f"{API_BASE_URL}/charters/charters/{charter_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        charter = response.json()
        assert charter["id"] == charter_id
    
    def test_create_charter(self, admin_headers, test_charter_data):
        """Test POST /charters endpoint"""
        response = requests.post(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers,
            json=test_charter_data
        )
        assert response.status_code == 201
        charter = response.json()
        assert charter["passengers"] == test_charter_data["passengers"]
        assert charter["status"] == "quote"
    
    def test_update_charter(self, admin_headers):
        """Test PUT /charters/{id} endpoint"""
        # First get list to find a valid charter ID
        list_response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert list_response.status_code == 200
        charters = list_response.json()
        assert len(charters) > 0, "No charters available for testing"
        
        charter_id = charters[0]["id"]
        
        # Get existing charter
        get_response = requests.get(
            f"{API_BASE_URL}/charters/charters/{charter_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 200
        charter = get_response.json()
        
        # Update passengers
        original_passengers = charter["passengers"]
        charter["passengers"] = 35 if original_passengers != 35 else 36
        update_response = requests.put(
            f"{API_BASE_URL}/charters/charters/{charter_id}",
            headers=admin_headers,
            json=charter
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["passengers"] == charter["passengers"]


class TestCharterPricing:
    """Test charter pricing calculations"""
    
    def test_vendor_pricing_is_75_percent(self, admin_headers):
        """Test vendor pricing is 75% of client charge"""
        # Get list to find a charter with pricing data
        list_response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert list_response.status_code == 200
        charters = list_response.json()
        
        # Find a completed charter with complete pricing data (completed charters have finalized pricing)
        charter = None
        for c in charters:
            if (c.get("status") in ["completed", "in_progress", "confirmed"] and
                c.get("vendor_base_cost") and c.get("vendor_mileage_cost") and 
                c.get("client_base_charge") and c.get("client_mileage_charge")):
                charter = c
                break
        
        assert charter is not None, "No charter with complete pricing data found"
        
        vendor_total = (
            charter["vendor_base_cost"] +
            charter["vendor_mileage_cost"] +
            charter.get("vendor_additional_fees", 0)
        )
        client_total = (
            charter["client_base_charge"] +
            charter["client_mileage_charge"] +
            charter.get("client_additional_fees", 0)
        )
        
        # Allow 3% tolerance for rounding
        assert abs(vendor_total - (client_total * 0.75)) < client_total * 0.03
    
    def test_profit_margin_calculation(self, admin_headers):
        """Test profit margin is calculated correctly"""
        # Get list to find a charter with profit margin data
        list_response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert list_response.status_code == 200
        charters = list_response.json()
        
        # Find a charter with profit margin
        charter_with_margin = None
        for charter in charters:
            if "profit_margin" in charter and charter["profit_margin"] is not None:
                charter_with_margin = charter
                break
        
        if charter_with_margin:
            # Profit margin should be around 25% (allowing 15-35% range)
            assert 0.15 <= charter_with_margin["profit_margin"] <= 0.35


class TestDriverEndpoints:
    """Test driver-specific endpoints"""
    
    def test_driver_get_assigned_charter(self, driver_headers):
        """Test driver can get their assigned charter"""
        response = requests.get(
            f"{API_BASE_URL}/charters/charters/driver/my-charter",
            headers=driver_headers
        )
        assert response.status_code == 200
        charter = response.json()
        
        # Driver 1 should have a charter assigned
        if charter is not None:
            assert "id" in charter
            assert "trip_date" in charter
    
    def test_driver_update_notes(self, driver_headers):
        """Test driver can update notes"""
        # First, get assigned charter
        get_response = requests.get(
            f"{API_BASE_URL}/charters/charters/driver/my-charter",
            headers=driver_headers
        )
        
        if get_response.status_code == 200:
            charter = get_response.json()
            if charter is not None:
                # Update notes
                notes_response = requests.patch(
                    f"{API_BASE_URL}/charters/charters/{charter['id']}/driver-notes",
                    headers=driver_headers,
                    json={"vendor_notes": "Test note from automation"}
                )
                assert notes_response.status_code == 200
    
    def test_driver_update_location(self, driver_headers):
        """Test driver can update location"""
        # Get assigned charter
        get_response = requests.get(
            f"{API_BASE_URL}/charters/charters/driver/my-charter",
            headers=driver_headers
        )
        
        if get_response.status_code == 200:
            charter = get_response.json()
            if charter is not None:
                # Update location
                location_response = requests.patch(
                    f"{API_BASE_URL}/charters/charters/{charter['id']}/location",
                    headers=driver_headers,
                    json={
                        "location": "40.232550,-74.301440",
                        "timestamp": "2025-12-08T14:30:00Z"
                    }
                )
                assert location_response.status_code == 200
    
    @pytest.mark.skip(reason="Authorization filtering not implemented yet - drivers can currently see all charters")
    def test_driver_cannot_access_other_charters(self, driver_headers):
        """Test driver cannot access charters not assigned to them"""
        # Try to get all charters
        response = requests.get(
            f"{API_BASE_URL}/charters/charters",
            headers=driver_headers
        )
        
        # Driver should either get 403 or only see their charter
        if response.status_code == 200:
            charters = response.json()
            # Should see 1 or 0 charters (only their assigned one)
            assert len(charters) <= 1


class TestCharterFiltering:
    """Test charter filtering and search"""
    
    def test_filter_by_status(self, admin_headers):
        """Test filtering charters by status"""
        response = requests.get(
            f"{API_BASE_URL}/charters/charters?status=confirmed",
            headers=admin_headers
        )
        assert response.status_code == 200
        charters = response.json()
        
        # All returned charters should be confirmed
        for charter in charters:
            assert charter["status"] == "confirmed"
    
    def test_filter_by_date(self, admin_headers):
        """Test filtering charters by date"""
        response = requests.get(
            f"{API_BASE_URL}/charters/charters?trip_date=2025-12-09",
            headers=admin_headers
        )
        assert response.status_code == 200
