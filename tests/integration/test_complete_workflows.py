"""
Comprehensive integration tests for CoachWay platform
Tests complete workflows across all 6 microservices
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any


# Base URLs - Kong strips the prefix, so services define their own paths
KONG_BASE = "http://localhost:8080"
SALES_BASE = f"{KONG_BASE}/api/v1/sales"  # Sales service has /api/v1/leads internally
PRICING_BASE = f"{KONG_BASE}/api/v1/pricing"
VENDOR_BASE = f"{KONG_BASE}/api/v1/vendor"
PORTAL_BASE = f"{KONG_BASE}/api/v1/portal"
CHANGES_BASE = f"{KONG_BASE}/api/v1/changes"
TIMEOUT = 10


class TestCompleteWorkflows:
    """Test end-to-end workflows across all services"""
    
    def __init__(self):
        """Setup test data"""
        self.test_data = {
            "lead": None,
            "client": None,
            "charter": None,
            "quote": None,
            "pricing": None,
            "vendor_bid": None,
            "change_case": None
        }
    
    def test_health_checks_all_services(self):
        """Test that all services are healthy"""
        services = [
            ("sales", f"{SALES_BASE}/health"),
            ("pricing", f"{PRICING_BASE}/health"),
            ("vendor", f"{VENDOR_BASE}/health"),
            ("portal", f"{PORTAL_BASE}/health"),
            ("changes", f"{CHANGES_BASE}/health")
        ]
        
        for service_name, endpoint in services:
            response = requests.get(endpoint, timeout=TIMEOUT)
            assert response.status_code == 200, f"{service_name} service is not healthy"
            data = response.json()
            assert data["status"] in ["healthy", "ok"], f"{service_name} status: {data['status']}"
            print(f"✅ {service_name.capitalize()} Service: {data['status']}")
    
    def test_workflow_1_lead_to_charter_conversion(self):
        """
        Test complete workflow: Lead → Client → Charter
        Covers: Sales Service → Client Service → Charter Service
        """
        print("\n=== Testing Lead to Charter Conversion Workflow ===")
        
        # Step 1: Create a lead in Sales Service
        lead_data = {
            "first_name": "Integration",
            "last_name": "Test",
            "email": f"integration.test.{int(time.time())}@example.com",
            "phone": "555-0100",
            "company_name": "Test Corp",
            "trip_details": "Corporate event transportation",
            "estimated_passengers": 45,
            "estimated_trip_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "pickup_location": "Downtown Convention Center",
            "dropoff_location": "Airport Terminal 1",
            "source": "web"
        }
        
        response = requests.post(
            f"{SALES_BASE}/api/v1/leads",
            json=lead_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Failed to create lead: {response.text}"
        lead = response.json()
        self.test_data["lead"] = lead
        print(f"✅ Step 1: Lead created (ID: {lead['id']}, Status: {lead['status']})")
        
        # Step 2: Convert lead to client and charter
        conversion_data = {
            "lead_id": lead["id"],
            "converted_by": 1,
            "conversion_notes": "Integration test conversion"
        }
        
        response = requests.post(
            f"{SALES_BASE}/api/v1/leads/{lead['id']}/convert",
            json=conversion_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to convert lead: {response.text}"
        conversion_result = response.json()
        print(f"✅ Step 2: Lead converted to Client (ID: {conversion_result['client_id']}) and Charter (ID: {conversion_result['charter_id']})")
        
        self.test_data["client"] = {"id": conversion_result["client_id"]}
        self.test_data["charter"] = {"id": conversion_result["charter_id"]}
        
        # Step 3: Verify lead status changed to CONVERTED
        response = requests.get(
            f"{SALES_BASE}/api/v1/leads/{lead['id']}",
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        updated_lead = response.json()
        assert updated_lead["status"] == "converted", f"Lead status is {updated_lead['status']}, expected 'converted'"
        print(f"✅ Step 3: Lead status verified as CONVERTED")
        
        print("✅ Workflow 1 Complete: Lead → Client → Charter")
        return conversion_result
    
    def test_workflow_2_pricing_calculation(self):
        """
        Test pricing workflow: Charter → Pricing Calculation
        Covers: Pricing Service with dynamic pricing rules
        """
        print("\n=== Testing Pricing Calculation Workflow ===")
        
        # Create a charter first (using charter service directly)
        charter_id = 1  # Using existing charter or create one
        
        # Step 1: Create pricing calculation
        pricing_data = {
            "charter_id": charter_id,
            "base_price": 2500.00,
            "distance_miles": 150.0,
            "duration_hours": 4.0,
            "passenger_count": 45,
            "vehicle_type": "motor_coach",
            "pricing_rules_applied": {
                "weekend_surcharge": 1.15,
                "distance_multiplier": 1.5,
                "peak_season": False
            }
        }
        
        response = requests.post(
            f"{PRICING_BASE}/calculations",
            json=pricing_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Failed to create pricing: {response.text}"
        pricing = response.json()
        self.test_data["pricing"] = pricing
        print(f"✅ Step 1: Pricing calculated (ID: {pricing['id']}, Final: ${pricing['final_price']})")
        
        # Step 2: Retrieve pricing with history
        response = requests.get(
            f"{PRICING_BASE}/calculations/{pricing['id']}",
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        pricing_detail = response.json()
        print(f"✅ Step 2: Pricing retrieved with breakdown")
        
        # Step 3: Get pricing history for charter
        response = requests.get(
            f"{PRICING_BASE}/calculations/charter/{charter_id}",
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        history = response.json()
        assert len(history) > 0, "No pricing history found"
        print(f"✅ Step 3: Pricing history retrieved ({len(history)} calculations)")
        
        print("✅ Workflow 2 Complete: Pricing Calculation")
        return pricing
    
    def test_workflow_3_vendor_bidding_process(self):
        """
        Test vendor workflow: Opportunity → Bid → Award
        Covers: Vendor Service with bidding and ratings
        """
        print("\n=== Testing Vendor Bidding Workflow ===")
        
        charter_id = 1
        vendor_id = 1
        
        # Step 1: Create vendor opportunity
        opportunity_data = {
            "charter_id": charter_id,
            "title": "Integration Test - Corporate Event Transportation",
            "description": "Need 45-passenger motor coach for corporate event",
            "pickup_location": "Downtown Convention Center",
            "dropoff_location": "Airport Terminal 1",
            "trip_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "passenger_count": 45,
            "vehicle_type_required": "motor_coach",
            "estimated_budget": 3000.00,
            "deadline": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = requests.post(
            f"{VENDOR_BASE}/opportunities",
            json=opportunity_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Failed to create opportunity: {response.text}"
        opportunity = response.json()
        print(f"✅ Step 1: Vendor opportunity created (ID: {opportunity['id']})")
        
        # Step 2: Submit bid
        bid_data = {
            "opportunity_id": opportunity["id"],
            "vendor_id": vendor_id,
            "bid_amount": 2800.00,
            "proposal": "We can provide a modern 45-passenger motor coach with WiFi and refreshments",
            "vehicle_id": 1,
            "estimated_response_time": "24 hours",
            "additional_services": ["WiFi", "Refreshments", "Professional Driver"]
        }
        
        response = requests.post(
            f"{VENDOR_BASE}/bids",
            json=bid_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Failed to submit bid: {response.text}"
        bid = response.json()
        self.test_data["vendor_bid"] = bid
        print(f"✅ Step 2: Bid submitted (ID: {bid['id']}, Amount: ${bid['bid_amount']})")
        
        # Step 3: Get all bids for opportunity
        response = requests.get(
            f"{VENDOR_BASE}/opportunities/{opportunity['id']}/bids",
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        bids = response.json()
        assert len(bids) > 0, "No bids found for opportunity"
        print(f"✅ Step 3: Retrieved bids for opportunity ({len(bids)} bids)")
        
        # Step 4: Award bid
        award_data = {
            "awarded_by": 1,
            "award_notes": "Best price and good reputation"
        }
        
        response = requests.post(
            f"{VENDOR_BASE}/bids/{bid['id']}/award",
            json=award_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to award bid: {response.text}"
        awarded_bid = response.json()
        assert awarded_bid["status"] == "awarded", f"Bid status is {awarded_bid['status']}"
        print(f"✅ Step 4: Bid awarded (Status: {awarded_bid['status']})")
        
        print("✅ Workflow 3 Complete: Vendor Bidding Process")
        return awarded_bid
    
    def test_workflow_4_portal_aggregation(self):
        """
        Test portal aggregation: Client Dashboard with aggregated data
        Covers: Portals Service BFF pattern
        """
        print("\n=== Testing Portal Aggregation Workflow ===")
        
        client_id = 1
        
        # Step 1: Get client portal dashboard
        response = requests.get(
            f"{PORTAL_BASE}/client/dashboard?client_id={client_id}",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to get client dashboard: {response.text}"
        dashboard = response.json()
        print(f"✅ Step 1: Client dashboard retrieved")
        print(f"   - Active Charters: {dashboard.get('active_charters_count', 0)}")
        print(f"   - Pending Quotes: {dashboard.get('pending_quotes_count', 0)}")
        
        # Step 2: Get user preferences
        preference_data = {
            "user_id": 1,
            "portal_type": "client",
            "notification_email": True,
            "notification_sms": False,
            "dashboard_layout": "compact",
            "theme": "light"
        }
        
        response = requests.post(
            f"{PORTAL_BASE}/preferences",
            json=preference_data,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 201], f"Failed to set preferences: {response.text}"
        preferences = response.json()
        print(f"✅ Step 2: User preferences set (Theme: {preferences.get('theme')})")
        
        # Step 3: Log activity
        activity_data = {
            "user_id": 1,
            "activity_type": "view_dashboard",
            "description": "Integration test - viewed client dashboard",
            "ip_address": "127.0.0.1"
        }
        
        response = requests.post(
            f"{PORTAL_BASE}/activity",
            json=activity_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Failed to log activity: {response.text}"
        print(f"✅ Step 3: Activity logged")
        
        print("✅ Workflow 4 Complete: Portal Aggregation")
        return dashboard
    
    def test_workflow_5_change_management_approval(self):
        """
        Test change management: Create → Review → Approve → Implement
        Covers: Change Management Service with state machine
        """
        print("\n=== Testing Change Management Workflow ===")
        
        charter_id = 1
        
        # Step 1: Create change case
        change_data = {
            "charter_id": charter_id,
            "client_id": 1,
            "vendor_id": 1,
            "change_type": "passenger_count_change",
            "priority": "high",
            "title": "Integration Test - Increase Passenger Count",
            "description": "Need to accommodate 10 additional passengers",
            "reason": "More attendees confirmed",
            "impact_level": "moderate",
            "impact_assessment": "Requires larger vehicle or additional vehicle",
            "affects_vendor": True,
            "affects_pricing": True,
            "affects_schedule": False,
            "current_price": 2500.00,
            "proposed_price": 2900.00,
            "requested_by": 1,
            "requested_by_name": "Integration Test User",
            "proposed_changes": {
                "passenger_count": {
                    "before": 45,
                    "after": 55
                }
            },
            "tags": ["integration_test", "passenger_increase"]
        }
        
        response = requests.post(
            f"{CHANGES_BASE}/cases",
            json=change_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Failed to create change case: {response.text}"
        change_case = response.json()
        self.test_data["change_case"] = change_case
        print(f"✅ Step 1: Change case created (Number: {change_case['case_number']}, Status: {change_case['status']})")
        assert change_case["requires_approval"] == True, "Change should require approval"
        
        # Step 2: Move to review
        response = requests.post(
            f"{CHANGES_BASE}/cases/{change_case['id']}/review?reviewed_by=2&reviewed_by_name=Reviewer",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to move to review: {response.text}"
        reviewed_case = response.json()
        assert reviewed_case["status"] == "under_review", f"Status is {reviewed_case['status']}"
        print(f"✅ Step 2: Change moved to review (Status: {reviewed_case['status']})")
        
        # Step 3: Approve change
        approval_data = {
            "approved_by": 3,
            "approved_by_name": "Manager",
            "approval_notes": "Approved - additional revenue justifies vehicle upgrade"
        }
        
        response = requests.post(
            f"{CHANGES_BASE}/cases/{change_case['id']}/approve",
            json=approval_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to approve change: {response.text}"
        approved_case = response.json()
        assert approved_case["status"] == "approved", f"Status is {approved_case['status']}"
        print(f"✅ Step 3: Change approved (Status: {approved_case['status']})")
        
        # Step 4: Get audit trail
        response = requests.get(
            f"{CHANGES_BASE}/cases/{change_case['id']}/history",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to get history: {response.text}"
        history = response.json()
        assert len(history) >= 3, f"Expected at least 3 history entries, got {len(history)}"
        print(f"✅ Step 4: Audit trail retrieved ({len(history)} entries)")
        
        # Verify state transitions in history
        actions = [entry["action"] for entry in history]
        assert "created" in actions, "Missing 'created' action in history"
        assert "moved_to_review" in actions, "Missing 'moved_to_review' action in history"
        assert "approved" in actions, "Missing 'approved' action in history"
        print(f"   - Actions logged: {', '.join(actions)}")
        
        # Step 5: Implement change
        implementation_data = {
            "implemented_by": 4,
            "implemented_by_name": "Operations",
            "implementation_notes": "Vehicle upgraded and pricing adjusted"
        }
        
        response = requests.post(
            f"{CHANGES_BASE}/cases/{change_case['id']}/implement",
            json=implementation_data,
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Failed to implement change: {response.text}"
        implemented_case = response.json()
        assert implemented_case["status"] == "implemented", f"Status is {implemented_case['status']}"
        print(f"✅ Step 5: Change implemented (Status: {implemented_case['status']})")
        
        print("✅ Workflow 5 Complete: Change Management with Full Approval")
        return implemented_case
    
    def test_workflow_6_cross_service_integration(self):
        """
        Test complete end-to-end workflow across all services
        """
        print("\n=== Testing Complete Cross-Service Integration ===")
        
        # This would test:
        # Lead (Sales) → Client (Client Service) → Charter (Charter) → 
        # Pricing (Pricing) → Vendor Opportunity (Vendor) → Bid → Award → 
        # Change Request (Change Mgmt) → Portal Dashboard (Portals)
        
        print("Running sub-workflows...")
        
        # Run all workflows in sequence
        conversion = self.test_workflow_1_lead_to_charter_conversion()
        pricing = self.test_workflow_2_pricing_calculation()
        bid = self.test_workflow_3_vendor_bidding_process()
        dashboard = self.test_workflow_4_portal_aggregation()
        change = self.test_workflow_5_change_management_approval()
        
        print("\n✅ Complete Cross-Service Integration Test Passed!")
        print(f"   - Lead converted to Charter ID: {conversion['charter_id']}")
        print(f"   - Pricing calculated: ${pricing['final_price']}")
        print(f"   - Vendor bid awarded: ${bid['bid_amount']}")
        print(f"   - Portal dashboard loaded successfully")
        print(f"   - Change case {change['case_number']} implemented")
        
        return {
            "conversion": conversion,
            "pricing": pricing,
            "bid": bid,
            "dashboard": dashboard,
            "change": change
        }


class TestServicePerformance:
    """Test performance and reliability"""
    
    def test_concurrent_requests(self):
        """Test multiple concurrent requests"""
        print("\n=== Testing Concurrent Request Handling ===")
        
        import concurrent.futures
        
        def make_request(i):
            response = requests.get(f"{SALES_BASE}/health", timeout=TIMEOUT)
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(20)))
        
        success_rate = sum(results) / len(results) * 100
        print(f"✅ Concurrent requests: {sum(results)}/{len(results)} successful ({success_rate:.1f}%)")
        assert success_rate >= 95, f"Success rate too low: {success_rate}%"
    
    def test_response_times(self):
        """Test response times for all services"""
        print("\n=== Testing Response Times ===")
        
        endpoints = [
            ("sales", f"{SALES_BASE}/health"),
            ("pricing", f"{PRICING_BASE}/health"),
            ("vendor", f"{VENDOR_BASE}/health"),
            ("portal", f"{PORTAL_BASE}/health"),
            ("changes", f"{CHANGES_BASE}/health")
        ]
        
        for service_name, endpoint in endpoints:
            start = time.time()
            response = requests.get(endpoint, timeout=TIMEOUT)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            assert response.status_code == 200
            assert elapsed < 500, f"{service_name} response time too high: {elapsed:.0f}ms"
            print(f"✅ {service_name}: {elapsed:.0f}ms")


if __name__ == "__main__":
    # Run tests
    print("Starting CoachWay Integration Tests...")
    print("=" * 60)
    
    tester = TestCompleteWorkflows()
    
    try:
        # Health checks
        tester.test_health_checks_all_services()
        
        # Complete workflow test
        tester.test_workflow_6_cross_service_integration()
        
        # Performance tests
        perf_tester = TestServicePerformance()
        perf_tester.test_concurrent_requests()
        perf_tester.test_response_times()
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
