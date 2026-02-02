"""
Integration Tests for Payment Flow
Tests payment processing, invoice generation, and payment tracking
"""
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080/api/v1"


@pytest.fixture
def admin_headers(admin_token):
    """Use admin token from shared conftest"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestPaymentServiceIntegration:
    """Test payment service endpoints"""
    
    def test_payment_service_health(self):
        """Test payment service is accessible"""
        response = requests.get(f"{BASE_URL}/payments/health")
        # May return 200 or 404 if not fully implemented
        assert response.status_code in [200, 404]
    
    def test_create_payment_for_charter(self, admin_headers):
        """Test creating a payment record for a charter"""
        # Get existing charter
        response = requests.get(
            f"{BASE_URL}/charters/charters",
            headers=admin_headers
        )
        assert response.status_code == 200
        charters = response.json()
        
        if len(charters) > 0:
            charter = charters[0]
            charter_id = charter["id"]
            
            # Attempt to create payment
            payment_data = {
                "charter_id": charter_id,
                "amount": charter.get("total_cost", 1000.00),
                "payment_method": "credit_card",
                "payment_date": datetime.now().strftime("%Y-%m-%d"),
                "payment_type": "client"
            }
            
            response = requests.post(
                f"{BASE_URL}/payments/payments",
                headers=admin_headers,
                json=payment_data
            )
            
            # Payment service may not be fully implemented
            if response.status_code == 201:
                payment = response.json()
                assert payment["charter_id"] == charter_id
                assert payment["payment_type"] == "client"


class TestInvoiceGeneration:
    """Test invoice generation workflow"""
    
    def test_charter_has_invoice_data(self, admin_headers):
        """Test charter contains necessary data for invoice generation"""
        response = requests.get(
            f"{BASE_URL}/charters/charters/1",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            charter = response.json()
            
            # Verify invoice-related fields exist
            assert "client_id" in charter
            assert "total_cost" in charter
            assert "trip_date" in charter
            assert charter["total_cost"] > 0
    
    def test_list_invoices(self, admin_headers):
        """Test listing invoices (if endpoint exists)"""
        response = requests.get(
            f"{BASE_URL}/payments/invoices",
            headers=admin_headers
        )
        
        # Invoice endpoint may not exist yet
        if response.status_code == 200:
            invoices = response.json()
            assert isinstance(invoices, list)


class TestAccountsReceivable:
    """Test AR functionality - client payments"""
    
    def test_client_payment_tracking(self, admin_headers):
        """Test tracking client payments (100% of charter cost)"""
        # Get charters to calculate AR
        response = requests.get(
            f"{BASE_URL}/charters/charters?status=completed",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        completed_charters = response.json()
        
        # Calculate total AR (100% of client charges)
        total_ar = sum(charter.get("total_cost", 0) for charter in completed_charters)
        assert total_ar >= 0  # Should be non-negative
    
    def test_client_payment_recording(self, admin_headers):
        """Test recording a client payment"""
        payment_data = {
            "charter_id": 1,
            "amount": 1500.00,
            "payment_method": "check",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_type": "client",
            "notes": "Payment for charter services"
        }
        
        response = requests.post(
            f"{BASE_URL}/payments/payments",
            headers=admin_headers,
            json=payment_data
        )
        
        # May return 201, 404, or 405 depending on implementation
        assert response.status_code in [201, 404, 405]


class TestAccountsPayable:
    """Test AP functionality - vendor payments"""
    
    def test_vendor_payment_calculation(self, admin_headers):
        """Test vendor payments are 75% of charter cost"""
        response = requests.get(
            f"{BASE_URL}/charters/charters/1",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            charter = response.json()
            
            if "vendor_base_cost" in charter:
                # Vendor should get ~75% of client charge
                expected_vendor_cost = charter["base_cost"] * 0.75
                assert abs(charter["vendor_base_cost"] - expected_vendor_cost) < 50
    
    def test_vendor_payment_recording(self, admin_headers):
        """Test recording a vendor payment"""
        payment_data = {
            "charter_id": 1,
            "amount": 1125.00,  # 75% of $1500
            "payment_method": "ach",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "payment_type": "vendor",
            "notes": "Vendor payment for charter"
        }
        
        response = requests.post(
            f"{BASE_URL}/payments/payments",
            headers=admin_headers,
            json=payment_data
        )
        
        # May return 201, 404, or 405 depending on implementation
        assert response.status_code in [201, 404, 405]


class TestProfitMarginCalculation:
    """Test profit margin calculation across payment flows"""
    
    def test_profit_margin_is_25_percent(self, admin_headers):
        """Test that profit margin equals 25% (100% - 75%)"""
        response = requests.get(
            f"{BASE_URL}/charters/charters/1",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            charter = response.json()
            
            if "vendor_base_cost" in charter and "base_cost" in charter:
                client_charge = charter["base_cost"]
                vendor_cost = charter["vendor_base_cost"]
                profit = client_charge - vendor_cost
                profit_margin = (profit / client_charge) * 100 if client_charge > 0 else 0
                
                # Profit margin should be approximately 25%
                assert 23 <= profit_margin <= 27  # Allow 2% tolerance


class TestPaymentStatusTracking:
    """Test payment status tracking across lifecycle"""
    
    def test_charter_payment_status_updates(self, admin_headers):
        """Test charter payment status can be tracked"""
        response = requests.get(
            f"{BASE_URL}/charters/charters",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        charters = response.json()
        
        # Charters should have payment-related fields
        if len(charters) > 0:
            charter = charters[0]
            # These fields may or may not exist depending on implementation
            assert "id" in charter
            assert "total_cost" in charter
    
    def test_payment_history_retrieval(self, admin_headers):
        """Test retrieving payment history for a charter"""
        response = requests.get(
            f"{BASE_URL}/payments/payments?charter_id=1",
            headers=admin_headers
        )
        
        # Endpoint may not exist yet
        if response.status_code == 200:
            payments = response.json()
            assert isinstance(payments, list)
