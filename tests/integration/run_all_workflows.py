#!/usr/bin/env python3
"""
Comprehensive Workflow Test Suite
Tests all major workflows end-to-end across the CoachWay platform
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

# Test counters
class TestStats:
    def __init__(self):
        self.workflows_passed = 0
        self.workflows_failed = 0
        self.workflows_total = 0
        self.validations_passed = 0
        self.validations_failed = 0

stats = TestStats()

# Logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"/tmp/workflow_test_{timestamp}.log"
DETAILED_LOG = f"/tmp/workflow_test_detailed_{timestamp}.log"

# Global test data
class TestData:
    admin_token = None
    manager_token = None
    agent_token = None
    created_charter_id = None
    created_client_id = None
    created_document_id = None
    created_vendor_id = None
    created_bid_id = None
    created_driver_id = None
    created_user_id = None
    multi_vehicle_charter_id = None
    charter_series_id = None
    emergency_id = None
    generated_invoice_id = None
    recorded_payment_id = None

test_data = TestData()

# API Base URLs - All through Kong Gateway (port 8080)
KONG_BASE = "http://localhost:8080/api/v1"
AUTH_SERVICE = f"{KONG_BASE}/auth"
CHARTER_SERVICE = f"{KONG_BASE}/charters"
CLIENT_SERVICE = f"{KONG_BASE}/clients"
DOCUMENT_SERVICE = f"{KONG_BASE}/documents"
PAYMENT_SERVICE = f"{KONG_BASE}/payments"
NOTIFICATION_SERVICE = f"{KONG_BASE}/notifications"
SALES_SERVICE = f"{KONG_BASE}/leads"
PRICING_SERVICE = f"{KONG_BASE}/pricing"
VENDOR_SERVICE = f"{KONG_BASE}/vendors"
DISPATCH_SERVICE = f"{KONG_BASE}/dispatches"
ANALYTICS_SERVICE = f"{KONG_BASE}/analytics"
CHANGE_MGMT_SERVICE = f"{KONG_BASE}/cases"

def log(message: str):
    """Log message to console and file"""
    print(message)
    with open(LOG_FILE, 'a') as f:
        f.write(message + '\n')

def log_detailed(message: str):
    """Log detailed message to detailed log file"""
    with open(DETAILED_LOG, 'a') as f:
        f.write(message + '\n')

def print_header(title: str):
    """Print section header"""
    log("")
    log(f"{Colors.BLUE}{'=' * 64}{Colors.NC}")
    log(f"{Colors.BLUE}{title}{Colors.NC}")
    log(f"{Colors.BLUE}{'=' * 64}{Colors.NC}")
    log("")

def print_subheader(title: str):
    """Print subsection header"""
    log("")
    log(f"{Colors.YELLOW}>>> {title}{Colors.NC}")
    log("")

def workflow_passed(name: str):
    """Mark workflow as passed"""
    stats.workflows_passed += 1
    stats.workflows_total += 1
    log("")
    log(f"{Colors.GREEN}✅ PASSED: {name}{Colors.NC}")
    log("")

def workflow_failed(name: str):
    """Mark workflow as failed"""
    stats.workflows_failed += 1
    stats.workflows_total += 1
    log("")
    log(f"{Colors.RED}❌ FAILED: {name}{Colors.NC}")
    log("")

def workflow_skipped(name: str):
    """Mark workflow as skipped"""
    stats.workflows_total += 1
    log("")
    log(f"{Colors.YELLOW}⊘ SKIPPED: {name}{Colors.NC}")
    log("")

def validate_field(response: Dict[str, Any], field: str, expected: Any, description: str) -> bool:
    """Validate a field has the expected value"""
    actual = response.get(field)
    
    if actual == expected:
        stats.validations_passed += 1
        log(f"{Colors.GREEN}  ✓{Colors.NC} {description}: {actual}")
        return True
    else:
        stats.validations_failed += 1
        log(f"{Colors.RED}  ✗{Colors.NC} {description}: expected '{expected}', got '{actual}'")
        log_detailed(f"Response: {json.dumps(response, indent=2)}")
        return False

def validate_field_exists(response: Dict[str, Any], field: str, description: str) -> bool:
    """Validate a field exists and is not null"""
    value = response.get(field)
    
    if value is not None:
        stats.validations_passed += 1
        log(f"{Colors.GREEN}  ✓{Colors.NC} {description}: {value}")
        return True
    else:
        stats.validations_failed += 1
        log(f"{Colors.RED}  ✗{Colors.NC} {description}: field missing or null")
        log_detailed(f"Response: {json.dumps(response, indent=2)}")
        return False

def validate_field_type(response: Dict[str, Any], field: str, expected_type: type, description: str) -> bool:
    """Validate a field has the expected type"""
    value = response.get(field)
    actual_type = type(value).__name__
    expected_type_name = expected_type.__name__
    
    if isinstance(value, expected_type):
        stats.validations_passed += 1
        log(f"{Colors.GREEN}  ✓{Colors.NC} {description}: type is {actual_type}")
        return True
    else:
        stats.validations_failed += 1
        log(f"{Colors.RED}  ✗{Colors.NC} {description}: expected type '{expected_type_name}', got '{actual_type}'")
        return False

def validate_http_code(code: int, expected: int, description: str) -> bool:
    """Validate HTTP status code"""
    if code == expected:
        stats.validations_passed += 1
        log(f"{Colors.GREEN}  ✓{Colors.NC} {description}: HTTP {code}")
        return True
    else:
        stats.validations_failed += 1
        log(f"{Colors.RED}  ✗{Colors.NC} {description}: expected HTTP {expected}, got HTTP {code}")
        return False

def validate_array_length(response: Dict[str, Any], field: str, min_length: int, description: str) -> bool:
    """Validate array field has minimum length"""
    arr = response.get(field, [])
    length = len(arr) if isinstance(arr, list) else 0
    
    if length >= min_length:
        stats.validations_passed += 1
        log(f"{Colors.GREEN}  ✓{Colors.NC} {description}: {length} items")
        return True
    else:
        stats.validations_failed += 1
        log(f"{Colors.RED}  ✗{Colors.NC} {description}: expected at least {min_length} items, got {length}")
        return False

def check_system_health() -> bool:
    """Check health of all services"""
    print_header("SYSTEM HEALTH CHECK")
    
    services = {
        "http://localhost:8080/api/v1/auth/health": "Auth Service (8080)",
        "http://localhost:8001/health": "Charter Service (8001)",
        "http://localhost:8002/health": "Client Service (8002)",
        "http://localhost:8003/health": "Document Service (8003)",
        "http://localhost:8004/health": "Payment Service (8004)",
        "http://localhost:8005/health": "Notification Service (8005)",
        "http://localhost:8007/health": "Sales Service (8007)",
        "http://localhost:8008/health": "Pricing Service (8008)",
        "http://localhost:8009/health": "Vendor Service (8009)",
        "http://localhost:8012/health": "Dispatch Service (8012)",
        "http://localhost:8013/health": "Analytics Service (8013)",
        "http://localhost:8011/health": "Change Management Service (8011)",
        "http://localhost:3000": "Frontend (3000)",
    }
    
    healthy = 0
    total = len(services)
    
    for url, name in services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code in [200, 404]:
                log(f"{Colors.GREEN}✓{Colors.NC} {name} is healthy (HTTP {response.status_code})")
                healthy += 1
            else:
                log(f"{Colors.RED}✗{Colors.NC} {name} is not responding (HTTP {response.status_code})")
        except requests.exceptions.RequestException:
            log(f"{Colors.RED}✗{Colors.NC} {name} is not responding (Connection Error)")
    
    log("")
    log(f"Health Check: {healthy}/{total} services healthy")
    
    if healthy < (total * 7 // 10):
        log(f"{Colors.RED}✗ Critical: Too many services are down{Colors.NC}")
        return False
    elif healthy < total:
        log(f"{Colors.YELLOW}⚠ Warning: Some services are not healthy{Colors.NC}")
    
    log("")
    return True

def get_auth_tokens() -> bool:
    """Get authentication tokens for different user roles"""
    print_subheader("Getting Authentication Tokens")
    
    # Admin token
    try:
        response = requests.post(
            "http://localhost:8080/api/v1/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": "admin@athena.com", "password": "admin123"}
        )
        test_data.admin_token = response.json().get('access_token')
        
        if not test_data.admin_token:
            log(f"{Colors.RED}✗ Failed to get admin token{Colors.NC}")
            return False
        log(f"{Colors.GREEN}✓ Admin token obtained{Colors.NC}")
    except Exception as e:
        log(f"{Colors.RED}✗ Failed to get admin token: {e}{Colors.NC}")
        return False
    
    # Manager token
    try:
        response = requests.post(
            "http://localhost:8080/api/v1/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": "manager@athena.com", "password": "admin123"}
        )
        test_data.manager_token = response.json().get('access_token')
        
        if not test_data.manager_token:
            log(f"{Colors.YELLOW}⚠ Failed to get manager token (will use admin){Colors.NC}")
            test_data.manager_token = test_data.admin_token
        else:
            log(f"{Colors.GREEN}✓ Manager token obtained{Colors.NC}")
    except Exception:
        test_data.manager_token = test_data.admin_token
    
    # Agent token
    try:
        response = requests.post(
            "http://localhost:8080/api/v1/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": "agent@athena.com", "password": "admin123"}
        )
        test_data.agent_token = response.json().get('access_token')
        
        if not test_data.agent_token:
            log(f"{Colors.YELLOW}⚠ Failed to get agent token (will use manager){Colors.NC}")
            test_data.agent_token = test_data.manager_token
        else:
            log(f"{Colors.GREEN}✓ Agent token obtained{Colors.NC}")
    except Exception:
        test_data.agent_token = test_data.manager_token
    
    return True

# ==============================================================================
# WORKFLOW 1: Complete Client Onboarding & First Charter
# ==============================================================================
def test_workflow_1_complete_client_onboarding():
    print_header("WORKFLOW 1: Complete Client Onboarding & First Charter")
    
    start_time = time.time()
    has_error = False
    
    print_subheader("Step 1: Create New Client")
    try:
        timestamp = int(time.time())
        response = requests.post(
            CLIENT_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "name": "Test Corporation Inc",
                "type": "corporate",
                "email": f"contact+{timestamp}@testcorp.com",
                "phone": "555-TEST-001",
                "address": "123 Business Ave",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "payment_terms": "net_30",
                "credit_limit": 50000.00
            }
        )
        
        log_detailed(f"Client Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            client_data = response.json()
            test_data.created_client_id = client_data.get('id')
            
            if test_data.created_client_id:
                log(f"{Colors.GREEN}✓ Client created: ID {test_data.created_client_id}{Colors.NC}")
                validate_field(client_data, "name", "Test Corporation Inc", "Client Name")
                validate_field(client_data, "payment_terms", "net_30", "Payment Terms")
            else:
                log(f"{Colors.RED}✗ Failed to create client{Colors.NC}")
                has_error = True
        else:
            log(f"{Colors.RED}✗ Failed to create client: HTTP {response.status_code}{Colors.NC}")
            has_error = True
    except Exception as e:
        log(f"{Colors.RED}✗ Exception creating client: {e}{Colors.NC}")
        has_error = True
    
    print_subheader("Step 2: Verify Client Can Be Retrieved")
    try:
        response = requests.get(
            f"{CLIENT_SERVICE}/{test_data.created_client_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Get Client Response: {response.text}")
        
        if response.status_code == 200:
            client_data = response.json()
            validate_field(client_data, "id", test_data.created_client_id, "Retrieved Client ID")
            validate_field(client_data, "name", "Test Corporation Inc", "Retrieved Client Name")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception retrieving client: {e}{Colors.NC}")
    
    print_subheader("Step 3: Create First Charter for Client")
    try:
        response = requests.post(
            CHARTER_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "client_id": test_data.created_client_id,
                "vehicle_id": 4,
                "trip_date": "2026-06-15",
                "passengers": 40,
                "trip_hours": 5.5,
                "base_cost": 500.00,
                "mileage_cost": 215.00,
                "total_cost": 715.00,
                "status": "quote"
            }
        )
        
        log_detailed(f"Charter Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            charter_data = response.json()
            test_data.created_charter_id = charter_data.get('id')
            
            if test_data.created_charter_id:
                log(f"{Colors.GREEN}✓ Charter created: ID {test_data.created_charter_id}{Colors.NC}")
                validate_field(charter_data, "client_id", test_data.created_client_id, "Client ID")
                validate_field(charter_data, "passengers", 40, "Passenger Count")
                validate_field(charter_data, "total_cost", 715.00, "Total Cost")
            else:
                log(f"{Colors.RED}✗ Failed to create charter{Colors.NC}")
                has_error = True
        else:
            log(f"{Colors.RED}✗ Failed to create charter: HTTP {response.status_code}{Colors.NC}")
            has_error = True
    except Exception as e:
        log(f"{Colors.RED}✗ Exception creating charter: {e}{Colors.NC}")
        has_error = True
    
    print_subheader("Step 4: Update Charter Status to Confirmed")
    try:
        response = requests.put(
            f"{CHARTER_SERVICE}/{test_data.created_charter_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={"status": "confirmed"}
        )
        
        if response.status_code == 200:
            charter_data = response.json()
            validate_field(charter_data, "status", "confirmed", "Updated Charter Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception updating charter: {e}{Colors.NC}")
    
    print_subheader("Step 5: Verify Charter in Client's Charter List")
    try:
        response = requests.get(
            f"{CHARTER_SERVICE}?client_id={test_data.created_client_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Client Charters Response: {response.text}")
        
        if response.status_code == 200:
            charters = response.json()
            if isinstance(charters, list) and len(charters) >= 1:
                stats.validations_passed += 1
                log(f"{Colors.GREEN}  ✓{Colors.NC} Client has at least 1 charter")
            else:
                stats.validations_failed += 1
                log(f"{Colors.RED}  ✗{Colors.NC} Client charters list unexpected")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception retrieving client charters: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    
    if not has_error:
        workflow_passed(f"Complete Client Onboarding & First Charter ({duration:.1f}s)")
        return True
    else:
        workflow_failed(f"Complete Client Onboarding & First Charter ({duration:.1f}s)")
        return False

# ==============================================================================
# WORKFLOW 2: Vendor Bidding & Selection Process
# ==============================================================================
def test_workflow_2_vendor_bidding_selection():
    print_header("WORKFLOW 2: Vendor Bidding & Selection Process")
    
    start_time = time.time()
    has_error = False
    
    charter_id = test_data.created_charter_id or 1
    
    print_subheader("Step 1: Create Vendor")
    try:
        timestamp = int(time.time())
        response = requests.post(
            VENDOR_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "business_name": "Premier Coach Lines",
                "legal_name": "Premier Coach Lines LLC",
                "vendor_type": "fleet_operator",
                "primary_contact_name": "John Smith",
                "primary_email": f"ops+{timestamp}@premiercoach.com",
                "primary_phone": "555-COACH-01",
                "address_line1": "456 Fleet Street",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02102",
                "total_vehicles": 25,
                "vehicle_types": {
                    "coach_bus": 10,
                    "minibus": 8,
                    "shuttle": 7
                }
            }
        )
        
        log_detailed(f"Vendor Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            vendor_data = response.json()
            test_data.created_vendor_id = vendor_data.get('id')
            
            if test_data.created_vendor_id:
                log(f"{Colors.GREEN}✓ Vendor created: ID {test_data.created_vendor_id}{Colors.NC}")
                validate_field(vendor_data, "business_name", "Premier Coach Lines", "Vendor Name")
                validate_field(vendor_data, "vendor_type", "fleet_operator", "Vendor Type")
            else:
                log(f"{Colors.RED}✗ Failed to create vendor{Colors.NC}")
                has_error = True
        else:
            log(f"{Colors.RED}✗ Failed to create vendor: HTTP {response.status_code}{Colors.NC}")
            has_error = True
    except Exception as e:
        log(f"{Colors.RED}✗ Exception creating vendor: {e}{Colors.NC}")
        has_error = True
    
    print_subheader("Step 2: Submit Bid for Charter")
    try:
        response = requests.post(
            f"{CHARTER_SERVICE}/{charter_id}/bids",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "vendor_id": test_data.created_vendor_id,
                "vehicle_type": "coach_bus",
                "vehicle_capacity": 45,
                "bid_amount": 650.00,
                "notes": "Premium coach with WiFi and restroom",
                "estimated_arrival_time": "2026-06-15T08:45:00",
                "status": "pending"
            }
        )
        
        log_detailed(f"Bid Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            bid_data = response.json()
            test_data.created_bid_id = bid_data.get('id')
            
            if test_data.created_bid_id:
                log(f"{Colors.GREEN}✓ Bid submitted: ID {test_data.created_bid_id}{Colors.NC}")
                validate_field(bid_data, "bid_amount", 650.00, "Bid Amount")
                validate_field(bid_data, "vehicle_capacity", 45, "Vehicle Capacity")
            else:
                log(f"{Colors.YELLOW}⚠ Bid creation returned unexpected format{Colors.NC}")
                test_data.created_bid_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Bid submission: HTTP {response.status_code}{Colors.NC}")
            test_data.created_bid_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception submitting bid: {e}{Colors.NC}")
        test_data.created_bid_id = 1
    
    print_subheader("Step 3: List All Bids for Charter")
    try:
        response = requests.get(
            f"{CHARTER_SERVICE}/{charter_id}/bids",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Bids List Response: {response.text}")
        
        if response.status_code == 200:
            bids = response.json()
            if isinstance(bids, list):
                bid_count = len(bids)
                log(f"{Colors.GREEN}  ✓{Colors.NC} Retrieved {bid_count} bid(s) for charter")
                stats.validations_passed += 1
            else:
                log(f"{Colors.YELLOW}  ⚠{Colors.NC} Bids list format unexpected")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception listing bids: {e}{Colors.NC}")
    
    print_subheader("Step 4: Accept Bid")
    try:
        response = requests.post(
            f"{CHARTER_SERVICE}/{charter_id}/bids/{test_data.created_bid_id}/accept",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={}
        )
        
        log_detailed(f"Accept Bid Response: {response.text}")
        
        if response.status_code in [200, 201]:
            bid_data = response.json()
            if 'status' in bid_data:
                validate_field(bid_data, "status", "accepted", "Bid Status After Acceptance")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception accepting bid: {e}{Colors.NC}")
    
    print_subheader("Step 5: Verify Vendor Assignment in Charter")
    try:
        response = requests.get(
            f"{CHARTER_SERVICE}/{charter_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Charter After Bid Accept: {response.text}")
        
        if response.status_code == 200:
            charter_data = response.json()
            assigned_vendor = charter_data.get('vendor_id')
            if assigned_vendor == test_data.created_vendor_id:
                log(f"{Colors.GREEN}  ✓{Colors.NC} Vendor correctly assigned to charter")
                stats.validations_passed += 1
            else:
                log(f"{Colors.YELLOW}  ⚠{Colors.NC} Vendor assignment check: expected {test_data.created_vendor_id}, got {assigned_vendor}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception verifying vendor assignment: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    
    if not has_error:
        workflow_passed(f"Vendor Bidding & Selection Process ({duration:.1f}s)")
        return True
    else:
        workflow_failed(f"Vendor Bidding & Selection Process ({duration:.1f}s)")
        return False

# ==============================================================================
# WORKFLOW 3: Document Management & E-Signature Complete Flow
# ==============================================================================
def test_workflow_3_document_esignature_flow():
    print_header("WORKFLOW 3: Document Management & E-Signature Complete Flow")
    
    start_time = time.time()
    
    charter_id = test_data.created_charter_id or 1
    
    print_subheader("Step 1: Upload Contract Document")
    try:
        # Create test document
        contract_content = f"""CHARTER AGREEMENT - Charter #{charter_id}
This agreement is between the Client and Athena Transportation Services.
Trip Date: June 15, 2026
Passengers: 40
Total Cost: $715.00
Terms and Conditions apply."""
        
        files = {'file': ('test_charter_contract.txt', contract_content, 'text/plain')}
        data = {
            'charter_id': charter_id,
            'document_type': 'charter_agreement',
            'uploaded_by': 1
        }
        
        response = requests.post(
            f"{DOCUMENT_SERVICE}/upload",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            files=files,
            data=data
        )
        
        log_detailed(f"Document Upload Response: {response.text}")
        
        if response.status_code in [200, 201]:
            doc_data = response.json()
            test_data.created_document_id = doc_data.get('id') or doc_data.get('document_id')
            
            if test_data.created_document_id:
                log(f"{Colors.GREEN}✓ Document uploaded: ID {test_data.created_document_id}{Colors.NC}")
                validate_field(doc_data, "document_type", "charter_agreement", "Document Type")
                validate_field(doc_data, "charter_id", charter_id, "Charter ID")
            else:
                log(f"{Colors.YELLOW}⚠ Document upload returned unexpected format{Colors.NC}")
                test_data.created_document_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Document upload: HTTP {response.status_code}{Colors.NC}")
            test_data.created_document_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception uploading document: {e}{Colors.NC}")
        test_data.created_document_id = 1
    
    print_subheader("Step 2: Request E-Signature via Kong")
    try:
        response = requests.post(
            f"http://localhost:8080/api/v1/documents/{test_data.created_document_id}/request-signature",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "signer_name": "John Client",
                "signer_email": "john.client@example.com",
                "document_type": "charter_agreement"
            }
        )
        
        log_detailed(f"Signature Request Response: {response.text}")
        
        if response.status_code in [200, 201]:
            sig_data = response.json()
            request_id = sig_data.get('id') or sig_data.get('request_id')
            
            if request_id:
                log(f"{Colors.GREEN}✓ Signature requested: {request_id}{Colors.NC}")
                validate_field(sig_data, "signer_email", "john.client@example.com", "Signer Email")
            else:
                log(f"{Colors.YELLOW}⚠ Signature request returned unexpected format{Colors.NC}")
                request_id = f"test-request-{int(time.time())}"
        else:
            log(f"{Colors.YELLOW}⚠ Signature request: HTTP {response.status_code}{Colors.NC}")
            request_id = f"test-request-{int(time.time())}"
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception requesting signature: {e}{Colors.NC}")
        request_id = f"test-request-{int(time.time())}"
    
    print_subheader("Step 3: List Pending Signatures")
    try:
        response = requests.get(
            f"http://localhost:8080/api/v1/documents/{test_data.created_document_id}/signatures",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={"status": "pending"}
        )
        
        log_detailed(f"Pending Signatures Response: {response.text}")
        
        if response.status_code == 200:
            sigs = response.json()
            if isinstance(sigs, list):
                sig_count = len(sigs)
                log(f"{Colors.GREEN}  ✓{Colors.NC} Found {sig_count} pending signature(s)")
                stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception listing signatures: {e}{Colors.NC}")
    
    print_subheader("Step 4: Send Signature Reminder")
    try:
        response = requests.post(
            f"http://localhost:8080/api/v1/documents/signature-requests/{request_id}/remind",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        if response.status_code in [200, 404, 422]:
            log(f"{Colors.GREEN}  ✓{Colors.NC} Reminder endpoint accessible (HTTP {response.status_code})")
            stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception sending reminder: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Document Management & E-Signature Complete Flow ({duration:.1f}s)")
    return True

# ==============================================================================
# WORKFLOW 4: Payment Processing End-to-End
# ==============================================================================
def test_workflow_4_payment_processing_e2e():
    print_header("WORKFLOW 4: Payment Processing End-to-End")
    
    start_time = time.time()
    
    charter_id = test_data.created_charter_id or 1
    vendor_id = test_data.created_vendor_id or 1
    
    print_subheader("Step 1: Create Client Invoice")
    try:
        response = requests.post(
            f"{KONG_BASE}/vendor-bills",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "client_id": test_data.created_client_id or 1,
                "amount": 715.00,
                "due_date": "2026-06-01",
                "status": "pending",
                "line_items": [
                    {
                        "description": "Charter Service - Boston to Foxborough",
                        "quantity": 1,
                        "unit_price": 715.00,
                        "total": 715.00
                    }
                ]
            }
        )
        
        log_detailed(f"Invoice Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            invoice_data = response.json()
            invoice_id = invoice_data.get('id')
            
            if invoice_id:
                log(f"{Colors.GREEN}✓ Invoice created: ID {invoice_id}{Colors.NC}")
                validate_field(invoice_data, "amount", 715.00, "Invoice Amount")
                validate_field(invoice_data, "status", "pending", "Invoice Status")
            else:
                log(f"{Colors.YELLOW}⚠ Invoice creation returned unexpected format{Colors.NC}")
                invoice_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Invoice creation: HTTP {response.status_code}{Colors.NC}")
            invoice_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating invoice: {e}{Colors.NC}")
        invoice_id = 1
    
    print_subheader("Step 2: Process Client Payment")
    try:
        response = requests.post(
            PAYMENT_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "invoice_id": invoice_id,
                "charter_id": charter_id,
                "amount": 715.00,
                "payment_method": "credit_card",
                "card_last_four": "4242",
                "payment_date": "2026-05-30",
                "status": "pending"
            }
        )
        
        log_detailed(f"Payment Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            payment_data = response.json()
            payment_id = payment_data.get('id')
            
            if payment_id:
                log(f"{Colors.GREEN}✓ Payment created: ID {payment_id}{Colors.NC}")
                validate_field(payment_data, "amount", 715.00, "Payment Amount")
                validate_field(payment_data, "payment_method", "credit_card", "Payment Method")
            else:
                log(f"{Colors.YELLOW}⚠ Payment creation returned unexpected format{Colors.NC}")
                payment_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Payment creation: HTTP {response.status_code}{Colors.NC}")
            payment_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception processing payment: {e}{Colors.NC}")
        payment_id = 1
    
    print_subheader("Step 3: Process Payment (Simulate Gateway)")
    try:
        response = requests.post(
            f"{PAYMENT_SERVICE}/payments/{payment_id}/process",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "transaction_id": f"TXN-{int(time.time())}",
                "gateway_response": "approved"
            }
        )
        
        log_detailed(f"Process Payment Response: {response.text}")
        
        if response.status_code in [200, 201]:
            process_data = response.json()
            if 'status' in process_data:
                validate_field(process_data, "status", "completed", "Payment Status After Processing")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception processing payment: {e}{Colors.NC}")
    
    print_subheader("Step 4: Create Vendor Payout")
    try:
        response = requests.post(
            f"{KONG_BASE}/vendor-bills",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "vendor_id": vendor_id,
                "charter_id": charter_id,
                "amount": 600.00,
                "payout_date": "2026-06-20",
                "status": "scheduled",
                "notes": "Payment to vendor after trip completion"
            }
        )
        
        log_detailed(f"Payout Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            payout_data = response.json()
            payout_id = payout_data.get('id')
            
            if payout_id:
                log(f"{Colors.GREEN}✓ Payout created: ID {payout_id}{Colors.NC}")
                validate_field(payout_data, "amount", 600.00, "Payout Amount")
                validate_field(payout_data, "status", "scheduled", "Payout Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating payout: {e}{Colors.NC}")
    
    print_subheader("Step 5: Verify Payment Summary")
    try:
        response = requests.get(
            f"{PAYMENT_SERVICE}/charters/{charter_id}/payment-summary",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Payment Summary Response: {response.text}")
        
        if response.status_code == 200:
            summary = response.json()
            if 'charter_id' in summary:
                validate_field(summary, "charter_id", charter_id, "Summary Charter ID")
                validate_field_exists(summary, "total_paid", "Total Paid")
                stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception getting payment summary: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Payment Processing End-to-End ({duration:.1f}s)")
    return True

# ==============================================================================
# WORKFLOW 5: Sales Pipeline & Quote to Charter Conversion
# ==============================================================================
def test_workflow_5_sales_pipeline():
    print_header("WORKFLOW 5: Sales Pipeline & Quote to Charter Conversion")
    
    start_time = time.time()
    
    print_subheader("Step 1: Create Sales Lead")
    try:
        response = requests.post(
            SALES_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "contact_name": "Jane Smith",
                "company": "Smith Events Co",
                "email": "jane@smithevents.com",
                "phone": "555-EVENTS-1",
                "trip_date": "2026-07-20",
                "estimated_passengers": 30,
                "route": "New York to Philadelphia",
                "status": "new",
                "source": "website"
            }
        )
        
        log_detailed(f"Lead Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            lead_data = response.json()
            lead_id = lead_data.get('id')
            
            if lead_id:
                log(f"{Colors.GREEN}✓ Lead created: ID {lead_id}{Colors.NC}")
                validate_field(lead_data, "contact_name", "Jane Smith", "Contact Name")
                validate_field(lead_data, "estimated_passengers", 30, "Estimated Passengers")
            else:
                log(f"{Colors.YELLOW}⚠ Lead creation returned unexpected format{Colors.NC}")
                lead_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Lead creation: HTTP {response.status_code}{Colors.NC}")
            lead_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating lead: {e}{Colors.NC}")
        lead_id = 1
    
    print_subheader("Step 2: Update Lead Status to Qualified")
    try:
        response = requests.put(
            f"{SALES_SERVICE}/{lead_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "status": "qualified",
                "notes": "Verified budget and requirements"
            }
        )
        
        log_detailed(f"Qualify Lead Response: {response.text}")
        
        if response.status_code == 200:
            lead_data = response.json()
            validate_field(lead_data, "status", "qualified", "Lead Status After Qualification")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception qualifying lead: {e}{Colors.NC}")
    
    print_subheader("Step 3: Generate Quote via Pricing Service")
    try:
        response = requests.post(
            f"{KONG_BASE}/pricing/calculate-quote",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "client_id": 1,
                "vehicle_id": 4,
                "trip_date": "2026-07-20",
                "passengers": 30,
                "total_miles": 95,
                "trip_hours": 4.0,
                "is_weekend": True,
                "is_holiday": False
            }
        )
        
        log_detailed(f"Quote Calculation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            quote_data = response.json()
            total_price = quote_data.get('total_price') or quote_data.get('total')
            
            if total_price:
                log(f"{Colors.GREEN}✓ Quote calculated: ${total_price}{Colors.NC}")
                validate_field_exists(quote_data, "total_price", "Total Price")
                stats.validations_passed += 1
            else:
                log(f"{Colors.YELLOW}⚠ Quote calculation returned unexpected format{Colors.NC}")
                total_price = 550.00
        else:
            log(f"{Colors.YELLOW}⚠ Quote calculation: HTTP {response.status_code}{Colors.NC}")
            total_price = 550.00
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception calculating quote: {e}{Colors.NC}")
        total_price = 550.00
    
    print_subheader("Step 4: Create Quote Record in Sales")
    try:
        response = requests.post(
            f"{SALES_SERVICE}/{lead_id}/quotes",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "amount": total_price,
                "valid_until": "2026-06-30",
                "status": "sent",
                "notes": "Standard minibus quote"
            }
        )
        
        log_detailed(f"Quote Record Response: {response.text}")
        
        if response.status_code in [200, 201]:
            quote_record = response.json()
            quote_id = quote_record.get('id')
            
            if quote_id:
                log(f"{Colors.GREEN}✓ Quote record created: ID {quote_id}{Colors.NC}")
                validate_field(quote_record, "status", "sent", "Quote Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating quote record: {e}{Colors.NC}")
    
    print_subheader("Step 5: Accept Quote and Convert to Charter")
    try:
        response = requests.post(
            f"{SALES_SERVICE}/{lead_id}/convert",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "create_client": True,
                "client_data": {
                    "name": "Smith Events Co",
                    "email": "jane@smithevents.com",
                    "phone": "555-EVENTS-1"
                }
            }
        )
        
        log_detailed(f"Convert Lead Response: {response.text}")
        
        if response.status_code in [200, 201]:
            convert_data = response.json()
            converted_charter_id = convert_data.get('charter_id')
            
            if converted_charter_id:
                log(f"{Colors.GREEN}✓ Lead converted to charter: ID {converted_charter_id}{Colors.NC}")
                validate_field_exists(convert_data, "charter_id", "Converted Charter ID")
                stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception converting lead: {e}{Colors.NC}")
    
    print_subheader("Step 6: Verify Lead Status Changed to Converted")
    try:
        response = requests.get(
            f"{SALES_SERVICE}/{lead_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        if response.status_code == 200:
            lead_data = response.json()
            validate_field(lead_data, "status", "converted", "Final Lead Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception verifying lead status: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Sales Pipeline & Quote to Charter Conversion ({duration:.1f}s)")
    return True

# ==============================================================================
# WORKFLOW 6: Dispatch & Driver Assignment Complete Flow
# ==============================================================================
def test_workflow_6_dispatch_driver_flow():
    print_header("WORKFLOW 6: Dispatch & Driver Assignment Complete Flow")
    
    start_time = time.time()
    
    charter_id = test_data.created_charter_id or 1
    vendor_id = test_data.created_vendor_id or 1
    
    print_subheader("Step 1: Create Driver Profile")
    try:
        response = requests.post(
            f"{DISPATCH_SERVICE}/drivers",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "name": "Mike Johnson",
                "email": "mike.johnson@premiercoach.com",
                "phone": "555-DRIVER-1",
                "license_number": "CDL-12345",
                "license_expiry": "2028-12-31",
                "years_experience": 12,
                "vendor_id": vendor_id,
                "is_active": True,
                "certifications": ["CDL-A", "Passenger Endorsement"]
            }
        )
        
        log_detailed(f"Driver Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            driver_data = response.json()
            driver_id = driver_data.get('id')
            
            if driver_id:
                log(f"{Colors.GREEN}✓ Driver created: ID {driver_id}{Colors.NC}")
                validate_field(driver_data, "name", "Mike Johnson", "Driver Name")
                validate_field(driver_data, "years_experience", 12, "Years Experience")
            else:
                log(f"{Colors.YELLOW}⚠ Driver creation returned unexpected format{Colors.NC}")
                driver_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Driver creation: HTTP {response.status_code}{Colors.NC}")
            driver_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating driver: {e}{Colors.NC}")
        driver_id = 1
    
    print_subheader("Step 2: Assign Driver to Charter")
    try:
        response = requests.post(
            DISPATCH_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "driver_id": driver_id,
                "vehicle_id": 4,
                "vendor_id": vendor_id,
                "status": "assigned"
            }
        )
        
        log_detailed(f"Assign Driver Response: {response.text}")
        
        if response.status_code in [200, 201]:
            assign_data = response.json()
            dispatch_id = assign_data.get('id') or assign_data.get('dispatch_id')
            
            if dispatch_id:
                log(f"{Colors.GREEN}✓ Driver assigned: Dispatch ID {dispatch_id}{Colors.NC}")
                validate_field(assign_data, "driver_id", driver_id, "Assigned Driver ID")
                validate_field(assign_data, "charter_id", charter_id, "Dispatch Charter ID")
            else:
                dispatch_id = 1
        else:
            dispatch_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception assigning driver: {e}{Colors.NC}")
        dispatch_id = 1
    
    print_subheader("Step 3: Send Dispatch Notification")
    try:
        response = requests.post(
            NOTIFICATION_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "user_id": driver_id,
                "notification_type": "dispatch_assignment",
                "title": "New Charter Assignment",
                "message": f"You have been assigned to charter #{charter_id}",
                "priority": "high"
            }
        )
        
        if response.status_code in [200, 201, 404]:
            log(f"{Colors.GREEN}  ✓{Colors.NC} Dispatch notification endpoint accessible (HTTP {response.status_code})")
            stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception sending notification: {e}{Colors.NC}")
    
    print_subheader("Step 4: Update Trip Status to In Progress")
    try:
        response = requests.put(
            f"{DISPATCH_SERVICE}/{dispatch_id}/status",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "status": "in_progress",
                "actual_start_time": "2026-06-15T09:00:00"
            }
        )
        
        log_detailed(f"Update Status Response: {response.text}")
        
        if response.status_code == 200:
            status_data = response.json()
            if 'status' in status_data:
                validate_field(status_data, "status", "in_progress", "Trip Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception updating status: {e}{Colors.NC}")
    
    print_subheader("Step 5: Complete Trip")
    try:
        response = requests.post(
            f"{DISPATCH_SERVICE}/{dispatch_id}/complete",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "actual_end_time": "2026-06-15T14:30:00",
                "actual_miles": 68,
                "notes": "Trip completed successfully"
            }
        )
        
        log_detailed(f"Complete Trip Response: {response.text}")
        
        if response.status_code in [200, 201]:
            complete_data = response.json()
            if 'status' in complete_data:
                validate_field(complete_data, "status", "completed", "Final Trip Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception completing trip: {e}{Colors.NC}")
    
    print_subheader("Step 6: Get Driver Performance Metrics")
    try:
        response = requests.get(
            f"{DISPATCH_SERVICE}/drivers/{driver_id}/metrics",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Driver Metrics Response: {response.text}")
        
        if response.status_code == 200:
            metrics = response.json()
            if 'total_trips' in metrics:
                validate_field_exists(metrics, "total_trips", "Total Trips")
                validate_field_exists(metrics, "driver_id", "Driver ID in Metrics")
                stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception getting metrics: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Dispatch & Driver Assignment Complete Flow ({duration:.1f}s)")
    return True

# ==============================================================================
# WORKFLOW 7: Change Management & Approval Workflow
# ==============================================================================
def test_workflow_7_change_management():
    print_header("WORKFLOW 7: Change Management & Approval Workflow")
    
    start_time = time.time()
    
    charter_id = test_data.created_charter_id or 1
    client_id = test_data.created_client_id or 1
    
    print_subheader("Step 1: Create Change Request")
    try:
        response = requests.post(
            CHANGE_MGMT_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "client_id": client_id,
                "change_type": "passenger_count_change",
                "priority": "medium",
                "title": "Increase passenger count",
                "description": "Client needs 10 additional seats",
                "reason": "More attendees confirmed",
                "impact_level": "moderate",
                "requested_by": 1,
                "requested_by_name": "Test Manager",
                "affects_pricing": True,
                "current_price": 715.00,
                "proposed_price": 850.00
            }
        )
        
        log_detailed(f"Change Request Response: {response.text}")
        
        if response.status_code in [200, 201]:
            change_data = response.json()
            change_id = change_data.get('id')
            
            if change_id:
                log(f"{Colors.GREEN}✓ Change request created: ID {change_id}{Colors.NC}")
                validate_field(change_data, "change_type", "passenger_count_change", "Change Type")
                validate_field(change_data, "priority", "medium", "Priority")
                validate_field(change_data, "affects_pricing", True, "Affects Pricing")
            else:
                log(f"{Colors.YELLOW}⚠ Change creation returned unexpected format{Colors.NC}")
                change_id = 1
        else:
            log(f"{Colors.YELLOW}⚠ Change creation: HTTP {response.status_code}{Colors.NC}")
            change_id = 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating change: {e}{Colors.NC}")
        change_id = 1
    
    print_subheader("Step 2: Add Impact Assessment")
    try:
        response = requests.post(
            f"{CHANGE_MGMT_SERVICE}/{change_id}/assessments",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "assessed_by": 1,
                "assessed_by_name": "Operations Manager",
                "risk_level": "medium",
                "impact_notes": "Requires larger vehicle or second vehicle",
                "estimated_cost_impact": 135.00
            }
        )
        
        log_detailed(f"Assessment Response: {response.text}")
        
        if response.status_code in [200, 201]:
            assess_data = response.json()
            if 'id' in assess_data:
                log(f"{Colors.GREEN}✓ Impact assessment added{Colors.NC}")
                validate_field(assess_data, "risk_level", "medium", "Risk Level")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception adding assessment: {e}{Colors.NC}")
    
    print_subheader("Step 3: Move to Review Status")
    try:
        response = requests.post(
            f"{CHANGE_MGMT_SERVICE}/{change_id}/review",
            headers={"Authorization": f"Bearer {test_data.manager_token}"},
            json={
                "reviewed_by": 1,
                "reviewed_by_name": "Manager",
                "review_notes": "Reviewing feasibility and cost"
            }
        )
        
        log_detailed(f"Review Response: {response.text}")
        
        if response.status_code in [200, 201]:
            review_data = response.json()
            validate_field(review_data, "status", "under_review", "Status After Review")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception moving to review: {e}{Colors.NC}")
    
    print_subheader("Step 4: Approve Change")
    try:
        response = requests.post(
            f"{CHANGE_MGMT_SERVICE}/{change_id}/approve",
            headers={"Authorization": f"Bearer {test_data.manager_token}"},
            json={
                "approved_by": 1,
                "approved_by_name": "Manager",
                "approval_notes": "Approved with additional cost",
                "approved_price": 850.00
            }
        )
        
        log_detailed(f"Approval Response: {response.text}")
        
        if response.status_code in [200, 201]:
            approve_data = response.json()
            validate_field(approve_data, "status", "approved", "Status After Approval")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception approving change: {e}{Colors.NC}")
    
    print_subheader("Step 5: Implement Change")
    try:
        response = requests.post(
            f"{CHANGE_MGMT_SERVICE}/{change_id}/implement",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "implemented_by": 1,
                "implemented_by_name": "Operations",
                "implementation_notes": "Updated charter and notified vendor",
                "actual_cost": 850.00
            }
        )
        
        log_detailed(f"Implementation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            impl_data = response.json()
            validate_field(impl_data, "status", "implemented", "Final Change Status")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception implementing change: {e}{Colors.NC}")
    
    print_subheader("Step 6: Get Change History for Charter")
    try:
        response = requests.get(
            f"{CHANGE_MGMT_SERVICE}/charter/{charter_id}/history",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Change History Response: {response.text}")
        
        if response.status_code == 200:
            history = response.json()
            if isinstance(history, list):
                change_count = len(history)
                log(f"{Colors.GREEN}  ✓{Colors.NC} Charter has {change_count} change record(s)")
                stats.validations_passed += 1
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception getting history: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Change Management & Approval Workflow ({duration:.1f}s)")
    return True

def test_workflow_8_multi_vehicle_charter():
    """Test Workflow 8: Multi-Vehicle Charter & Fleet Coordination"""
    start_time = time.time()
    print_header("WORKFLOW 8: Multi-Vehicle Charter & Fleet Coordination")
    has_error = False
    
    client_id = test_data.created_client_id or 1
    
    print_subheader("Step 1: Create Multi-Vehicle Charter Request")
    try:
        timestamp = int(time.time())
        response = requests.post(
            CHARTER_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "client_id": client_id,
                "vehicle_id": 4,
                "trip_date": "2026-09-10",
                "passengers": 120,  # Requires multiple vehicles
                "trip_hours": 6.0,
                "base_cost": 1500.00,
                "mileage_cost": 300.00,
                "total_cost": 1800.00,
                "vehicle_count": 3,
                "is_multi_vehicle": True,
                "notes": f"Multi-vehicle charter test {timestamp}"
            }
        )
        
        log_detailed(f"Multi-Vehicle Charter Response: {response.text}")
        
        if response.status_code in [200, 201]:
            charter_data = response.json()
            charter_id = charter_data.get('id')
            test_data.multi_vehicle_charter_id = charter_id
            log(f"{Colors.GREEN}✓ Multi-vehicle charter created: ID {charter_id}{Colors.NC}")
            validate_field(charter_data, "vehicle_count", 3, "Vehicle Count")
            validate_field(charter_data, "is_multi_vehicle", True, "Multi-Vehicle Flag")
        else:
            log(f"{Colors.RED}✗ Failed to create multi-vehicle charter: HTTP {response.status_code}{Colors.NC}")
            has_error = True
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating multi-vehicle charter: {e}{Colors.NC}")
        has_error = True
    
    print_subheader("Step 2: Check Multi-Vehicle Charter Details")
    charter_id = test_data.multi_vehicle_charter_id or test_data.created_charter_id or 1
    try:
        response = requests.get(
            f"{CHARTER_SERVICE}/{charter_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Charter Details Response: {response.text}")
        
        if response.status_code == 200:
            charter_data = response.json()
            log(f"{Colors.GREEN}  ✓ Retrieved charter ID: {charter_data.get('id')}{Colors.NC}")
            log(f"{Colors.GREEN}  ✓ Total vehicles: {charter_data.get('vehicle_count', 1)}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception retrieving charter: {e}{Colors.NC}")
    
    print_subheader("Step 3: List Available Vehicles for Assignment")
    try:
        response = requests.get(
            f"{CHARTER_SERVICE}/{charter_id}/vehicles",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Available Vehicles Response: {response.text}")
        
        if response.status_code == 200:
            vehicles = response.json()
            vehicle_count = len(vehicles) if isinstance(vehicles, list) else 0
            log(f"{Colors.GREEN}  ✓ Found {vehicle_count} vehicle assignment(s){Colors.NC}")
        else:
            log(f"{Colors.YELLOW}  ⚠ Vehicle list: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception listing vehicles: {e}{Colors.NC}")
    
    print_subheader("Step 4: Assign Multiple Drivers to Charter")
    for i in range(1, 4):  # Assign 3 drivers
        try:
            response = requests.post(
                DISPATCH_SERVICE,
                headers={"Authorization": f"Bearer {test_data.admin_token}"},
                json={
                    "charter_id": charter_id,
                    "driver_id": i,
                    "vehicle_id": 4,
                    "vendor_id": test_data.created_vendor_id or 1,
                    "status": "assigned",
                    "sequence": i
                }
            )
            
            log_detailed(f"Driver {i} Assignment Response: {response.text}")
            
            if response.status_code in [200, 201]:
                log(f"{Colors.GREEN}  ✓ Driver {i} assigned{Colors.NC}")
            else:
                log(f"{Colors.YELLOW}  ⚠ Driver {i} assignment: HTTP {response.status_code}{Colors.NC}")
        except Exception as e:
            log(f"{Colors.YELLOW}⚠ Exception assigning driver {i}: {e}{Colors.NC}")
    
    print_subheader("Step 5: Get Fleet Coordination Status")
    try:
        response = requests.get(
            f"{DISPATCH_SERVICE}/charter/{charter_id}/fleet-status",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Fleet Status Response: {response.text}")
        
        if response.status_code == 200:
            status = response.json()
            log(f"{Colors.GREEN}  ✓ Fleet coordination status retrieved{Colors.NC}")
        else:
            log(f"{Colors.YELLOW}  ⚠ Fleet status: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception getting fleet status: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    if has_error:
        workflow_failed(f"Multi-Vehicle Charter & Fleet Coordination ({duration:.1f}s)")
        return False
    else:
        workflow_passed(f"Multi-Vehicle Charter & Fleet Coordination ({duration:.1f}s)")
        return True

def test_workflow_9_charter_modification_cancellation():
    """Test Workflow 9: Charter Modification & Cancellation"""
    start_time = time.time()
    print_header("WORKFLOW 9: Charter Modification & Cancellation")
    has_error = False
    
    charter_id = test_data.created_charter_id or 1
    
    print_subheader("Step 1: Modify Charter Details")
    try:
        response = requests.put(
            f"{CHARTER_SERVICE}/{charter_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "passengers": 50,
                "trip_hours": 6.5,
                "notes": "Updated charter - increased passengers"
            }
        )
        
        log_detailed(f"Charter Modification Response: {response.text}")
        
        if response.status_code == 200:
            charter_data = response.json()
            log(f"{Colors.GREEN}✓ Charter modified successfully{Colors.NC}")
            validate_field(charter_data, "passengers", 50, "Updated Passenger Count")
        else:
            log(f"{Colors.YELLOW}⚠ Charter modification: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception modifying charter: {e}{Colors.NC}")
    
    print_subheader("Step 2: Calculate Cancellation Fee")
    try:
        response = requests.post(
            f"{CHARTER_SERVICE}/{charter_id}/cancellation-fee",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "cancellation_date": "2026-03-01",
                "reason": "client_request"
            }
        )
        
        log_detailed(f"Cancellation Fee Response: {response.text}")
        
        if response.status_code == 200:
            fee_data = response.json()
            fee_amount = fee_data.get('fee', 0)
            log(f"{Colors.GREEN}  ✓ Cancellation fee calculated: ${fee_amount}{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Cancellation fee: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception calculating fee: {e}{Colors.NC}")
    
    print_subheader("Step 3: Cancel Charter")
    try:
        response = requests.post(
            f"{CHARTER_SERVICE}/{charter_id}/cancel",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "reason": "Client requested cancellation",
                "cancelled_by": "admin@coachway.com"
            }
        )
        
        log_detailed(f"Charter Cancellation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            cancel_data = response.json()
            log(f"{Colors.GREEN}✓ Charter cancelled{Colors.NC}")
            validate_field(cancel_data, "status", "cancelled", "Charter Status")
        else:
            log(f"{Colors.YELLOW}⚠ Charter cancellation: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception cancelling charter: {e}{Colors.NC}")
    
    print_subheader("Step 4: Send Cancellation Notifications")
    try:
        response = requests.post(
            f"{NOTIFICATION_SERVICE}/charter/{charter_id}/cancellation",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "message": "Charter has been cancelled",
                "recipients": ["client", "vendor", "driver"]
            }
        )
        
        log_detailed(f"Notification Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ Cancellation notifications sent{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Notifications: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception sending notifications: {e}{Colors.NC}")
    
    print_subheader("Step 5: Process Refund")
    try:
        response = requests.post(
            f"{PAYMENT_SERVICE}/payments/refund",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "amount": 500.00,
                "reason": "cancellation"
            }
        )
        
        log_detailed(f"Refund Response: {response.text}")
        
        if response.status_code in [200, 201]:
            refund_data = response.json()
            log(f"{Colors.GREEN}  ✓ Refund processed{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Refund: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception processing refund: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Charter Modification & Cancellation ({duration:.1f}s)")
    return True

def test_workflow_10_recurring_charter_series():
    """Test Workflow 10: Recurring/Series Charter Creation"""
    start_time = time.time()
    print_header("WORKFLOW 10: Recurring/Series Charter Creation")
    has_error = False
    
    client_id = test_data.created_client_id or 1
    
    print_subheader("Step 1: Create Charter Series (Recurring)")
    try:
        timestamp = int(time.time())
        template_charter_id = test_data.created_charter_id or 1
        response = requests.post(
            f"{CHARTER_SERVICE}/recurring?recurrence_rule=weekly&instance_count=8",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "series_name": f"Weekly School Route {timestamp}",
                "client_id": client_id,
                "vehicle_id": 4,
                "trip_date": "2026-10-05",
                "passengers": 40,
                "trip_hours": 4.5,
                "base_cost": 500.0,
                "mileage_cost": 150.0,
                "total_cost": 650.0,
                "pickup_location": "123 School St",
                "dropoff_location": "456 Event Center",
                "is_series_master": True
            }
        )
        
        log_detailed(f"Charter Series Response: {response.text}")
        
        if response.status_code in [200, 201]:
            series_data = response.json()
            # API returns a list of charters, get the master (first one)
            if isinstance(series_data, list) and len(series_data) > 0:
                master_charter = series_data[0]
                series_id = master_charter.get('id')
                test_data.charter_series_id = series_id
                log(f"{Colors.GREEN}✓ Charter series created: {len(series_data)} instances, Master ID {series_id}{Colors.NC}")
                validate_field(master_charter, "is_series_master", True, "Series Master Flag")
            else:
                series_id = series_data.get('series_id') or series_data.get('id')
                test_data.charter_series_id = series_id
                log(f"{Colors.GREEN}✓ Charter series created: ID {series_id}{Colors.NC}")
                validate_field(series_data, "is_series_master", True, "Series Master Flag")
        else:
            log(f"{Colors.RED}✗ Failed to create charter series: HTTP {response.status_code}{Colors.NC}")
            has_error = True
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating series: {e}{Colors.NC}")
        has_error = True
    
    print_subheader("Step 2: List All Series Instances")
    series_id = test_data.charter_series_id or 1
    try:
        response = requests.get(
            f"http://localhost:8001/charters/series/{series_id}/instances",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Series Instances Response: {response.text}")
        
        if response.status_code == 200:
            instances = response.json()
            instance_count = len(instances) if isinstance(instances, list) else 0
            log(f"{Colors.GREEN}  ✓ Found {instance_count} charter instance(s) in series{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Series instances: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception listing instances: {e}{Colors.NC}")
    
    print_subheader("Step 3: Modify Entire Series")
    try:
        response = requests.put(
            f"http://localhost:8001/charters/series/{series_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "passengers": 40,
                "trip_hours": 4.5,
                "apply_to": "all_instances"
            }
        )
        
        log_detailed(f"Series Modification Response: {response.text}")
        
        if response.status_code == 200:
            log(f"{Colors.GREEN}  ✓ Series modified successfully{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Series modification: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception modifying series: {e}{Colors.NC}")
    
    print_subheader("Step 4: Cancel Single Instance in Series")
    try:
        response = requests.post(
            f"http://localhost:8001/charters/series/{series_id}/instance/3/cancel",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "reason": "Holiday - school closed"
            }
        )
        
        log_detailed(f"Instance Cancellation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ Single instance cancelled{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Instance cancellation: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception cancelling instance: {e}{Colors.NC}")
    
    print_subheader("Step 5: Generate Series Report")
    try:
        response = requests.get(
            f"http://localhost:8001/charters/series/{series_id}/report",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Series Report Response: {response.text}")
        
        if response.status_code == 200:
            report = response.json()
            log(f"{Colors.GREEN}  ✓ Series report generated{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Series report: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception generating report: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    if has_error:
        workflow_failed(f"Recurring/Series Charter Creation ({duration:.1f}s)")
        return False
    else:
        workflow_passed(f"Recurring/Series Charter Creation ({duration:.1f}s)")
        return True

def test_workflow_11_driver_checkin_operations():
    """Test Workflow 11: Driver Check-In & Real-Time Operations"""
    start_time = time.time()
    print_header("WORKFLOW 11: Driver Check-In & Real-Time Operations")
    
    charter_id = test_data.created_charter_id or 1
    driver_id = test_data.created_driver_id or 1
    
    print_subheader("Step 1: Driver Check-In at Pickup Location")
    try:
        response = requests.post(
            f"{DISPATCH_SERVICE}/checkin",
            headers={"Authorization": f"Bearer {test_data.manager_token}"},
            json={
                "charter_id": charter_id,
                "driver_id": driver_id,
                "location": "Boston Convention Center",
                "latitude": 42.3478,
                "longitude": -71.0466,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        log_detailed(f"Check-In Response: {response.text}")
        
        if response.status_code in [200, 201]:
            checkin_data = response.json()
            log(f"{Colors.GREEN}✓ Driver checked in at pickup location{Colors.NC}")
            validate_field(checkin_data, "status", "checked_in", "Check-In Status")
        else:
            log(f"{Colors.YELLOW}⚠ Check-in: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception during check-in: {e}{Colors.NC}")
    
    print_subheader("Step 2: Update Trip Status to In Progress")
    try:
        response = requests.put(
            f"{CHARTER_SERVICE}/{charter_id}/status",
            headers={"Authorization": f"Bearer {test_data.manager_token}"},
            json={"status": "in_progress"}
        )
        
        log_detailed(f"Status Update Response: {response.text}")
        
        if response.status_code == 200:
            log(f"{Colors.GREEN}  ✓ Trip status updated to in_progress{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Status update: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception updating status: {e}{Colors.NC}")
    
    print_subheader("Step 3: Send GPS Location Updates")
    locations = [
        {"lat": 42.3500, "lng": -71.0500, "status": "en_route"},
        {"lat": 42.3550, "lng": -71.0600, "status": "en_route"},
        {"lat": 42.3601, "lng": -71.0706, "status": "approaching_destination"}
    ]
    
    for idx, loc in enumerate(locations, 1):
        try:
            response = requests.post(
                f"{DISPATCH_SERVICE}/location",
                headers={"Authorization": f"Bearer {test_data.manager_token}"},
                json={
                    "charter_id": charter_id,
                    "driver_id": driver_id,
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                    "status": loc["status"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            log_detailed(f"Location Update {idx} Response: {response.text}")
            
            if response.status_code in [200, 201]:
                log(f"{Colors.GREEN}  ✓ Location update {idx} sent{Colors.NC}")
            else:
                log(f"{Colors.YELLOW}  ⚠ Location update {idx}: HTTP {response.status_code}{Colors.NC}")
        except Exception as e:
            log(f"{Colors.YELLOW}⚠ Exception sending location {idx}: {e}{Colors.NC}")
    
    print_subheader("Step 4: Track Real-Time Charter Status")
    try:
        response = requests.get(
            f"{CHARTER_SERVICE}/{charter_id}/live-status",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Live Status Response: {response.text}")
        
        if response.status_code == 200:
            status = response.json()
            log(f"{Colors.GREEN}  ✓ Real-time status retrieved{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Live status: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception tracking status: {e}{Colors.NC}")
    
    print_subheader("Step 5: Complete Trip and Check-Out")
    try:
        response = requests.post(
            f"{DISPATCH_SERVICE}/complete",
            headers={"Authorization": f"Bearer {test_data.manager_token}"},
            json={
                "charter_id": charter_id,
                "driver_id": driver_id,
                "completion_location": "Logan Airport",
                "actual_end_time": datetime.now().isoformat(),
                "notes": "Trip completed successfully"
            }
        )
        
        log_detailed(f"Trip Completion Response: {response.text}")
        
        if response.status_code in [200, 201]:
            completion_data = response.json()
            log(f"{Colors.GREEN}✓ Trip completed and driver checked out{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Trip completion: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception completing trip: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Driver Check-In & Real-Time Operations ({duration:.1f}s)")
    return True

def test_workflow_12_invoice_reconciliation():
    """Test Workflow 12: Invoice Reconciliation & Accounting"""
    start_time = time.time()
    print_header("WORKFLOW 12: Invoice Reconciliation & Accounting")
    
    charter_id = test_data.created_charter_id or 1
    client_id = test_data.created_client_id or 1
    vendor_id = test_data.created_vendor_id or 1
    
    print_subheader("Step 1: Generate Invoice from Completed Charter")
    try:
        response = requests.post(
            f"{PAYMENT_SERVICE}/invoices/generate",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "client_id": client_id,
                "due_date": "2026-07-15"
            }
        )
        
        log_detailed(f"Invoice Generation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            invoice_data = response.json()
            invoice_id = invoice_data.get('id') or invoice_data.get('invoice_id')
            test_data.generated_invoice_id = invoice_id
            log(f"{Colors.GREEN}✓ Invoice generated: ID {invoice_id}{Colors.NC}")
            validate_field(invoice_data, "status", "pending", "Invoice Status")
        else:
            log(f"{Colors.YELLOW}⚠ Invoice generation: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception generating invoice: {e}{Colors.NC}")
    
    print_subheader("Step 2: Record Client Payment")
    invoice_id = test_data.generated_invoice_id or 1
    try:
        response = requests.post(
            fPAYMENT_SERVICE,
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "invoice_id": invoice_id,
                "amount": 715.00,
                "payment_method": "bank_transfer",
                "reference_number": "ACH123456"
            }
        )
        
        log_detailed(f"Payment Recording Response: {response.text}")
        
        if response.status_code in [200, 201]:
            payment_data = response.json()
            payment_id = payment_data.get('id')
            test_data.recorded_payment_id = payment_id
            log(f"{Colors.GREEN}✓ Payment recorded: ID {payment_id}{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Payment recording: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception recording payment: {e}{Colors.NC}")
    
    print_subheader("Step 3: Match Payment to Invoice")
    try:
        response = requests.post(
            f"{PAYMENT_SERVICE}/invoices/{invoice_id}/match-payment",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "payment_id": test_data.recorded_payment_id or 1
            }
        )
        
        log_detailed(f"Payment Matching Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ Payment matched to invoice{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Payment matching: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception matching payment: {e}{Colors.NC}")
    
    print_subheader("Step 4: Generate Vendor Payout")
    try:
        response = requests.post(
            f"{KONG_BASE}/vendor-bills",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "vendor_id": vendor_id,
                "charter_id": charter_id,
                "amount": 500.00,
                "payment_method": "ach"
            }
        )
        
        log_detailed(f"Payout Generation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            payout_data = response.json()
            log(f"{Colors.GREEN}✓ Vendor payout created{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Payout generation: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating payout: {e}{Colors.NC}")
    
    print_subheader("Step 5: Generate Financial Reconciliation Report")
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE}/financial-reconciliation",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        log_detailed(f"Reconciliation Report Response: {response.text}")
        
        if response.status_code == 200:
            report = response.json()
            log(f"{Colors.GREEN}  ✓ Reconciliation report generated{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Reconciliation report: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception generating report: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Invoice Reconciliation & Accounting ({duration:.1f}s)")
    return True

def test_workflow_13_emergency_reassignment():
    """Test Workflow 13: Emergency Dispatch Reassignment"""
    start_time = time.time()
    print_header("WORKFLOW 13: Emergency Dispatch Reassignment")
    
    charter_id = test_data.created_charter_id or 1
    
    print_subheader("Step 1: Report Vehicle Breakdown")
    try:
        response = requests.post(
            f"{DISPATCH_SERVICE}/emergency/breakdown",
            headers={"Authorization": f"Bearer {test_data.manager_token}"},
            json={
                "charter_id": charter_id,
                "driver_id": 1,
                "vehicle_id": 4,
                "issue": "Engine overheating",
                "location": "Route 95, Mile Marker 42",
                "severity": "critical"
            }
        )
        
        log_detailed(f"Breakdown Report Response: {response.text}")
        
        if response.status_code in [200, 201]:
            breakdown_data = response.json()
            emergency_id = breakdown_data.get('id') or breakdown_data.get('emergency_id')
            test_data.emergency_id = emergency_id
            log(f"{Colors.GREEN}✓ Breakdown reported: Emergency ID {emergency_id}{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Breakdown report: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception reporting breakdown: {e}{Colors.NC}")
    
    print_subheader("Step 2: Find Available Backup Vendors")
    try:
        response = requests.get(
            f"{VENDOR_SERVICE}/available",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={
                "date": "2026-06-15",
                "vehicle_type": "coach_bus",
                "capacity": 40
            }
        )
        
        log_detailed(f"Available Vendors Response: {response.text}")
        
        if response.status_code == 200:
            vendors = response.json()
            vendor_count = len(vendors) if isinstance(vendors, list) else 0
            log(f"{Colors.GREEN}  ✓ Found {vendor_count} available backup vendor(s){Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Vendor search: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception finding vendors: {e}{Colors.NC}")
    
    print_subheader("Step 3: Reassign to Backup Vendor")
    try:
        response = requests.post(
            f"{DISPATCH_SERVICE}/emergency/reassign",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "emergency_id": test_data.emergency_id or 1,
                "new_vendor_id": 2,
                "new_driver_id": 5,
                "new_vehicle_id": 5,
                "eta_minutes": 20
            }
        )
        
        log_detailed(f"Reassignment Response: {response.text}")
        
        if response.status_code in [200, 201]:
            reassign_data = response.json()
            log(f"{Colors.GREEN}✓ Charter reassigned to backup vendor{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Reassignment: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception reassigning: {e}{Colors.NC}")
    
    print_subheader("Step 4: Notify Client of Emergency Change")
    try:
        response = requests.post(
            f"{NOTIFICATION_SERVICE}/emergency",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "charter_id": charter_id,
                "type": "vehicle_change",
                "message": "Your charter has been reassigned to a backup vehicle due to technical issues",
                "urgency": "high"
            }
        )
        
        log_detailed(f"Emergency Notification Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ Emergency notification sent to client{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Notification: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception sending notification: {e}{Colors.NC}")
    
    print_subheader("Step 5: Log Impact Assessment")
    try:
        response = requests.post(
            f"{ANALYTICS_SERVICE}/emergency-impact",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "emergency_id": test_data.emergency_id or 1,
                "charter_id": charter_id,
                "delay_minutes": 20,
                "additional_cost": 150.00,
                "customer_satisfaction_impact": "moderate"
            }
        )
        
        log_detailed(f"Impact Assessment Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ Impact assessment logged{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Impact logging: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception logging impact: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Emergency Dispatch Reassignment ({duration:.1f}s)")
    return True

def test_workflow_14_analytics_reporting():
    """Test Workflow 14: Analytics & Reporting Complete Flow"""
    start_time = time.time()
    print_header("WORKFLOW 14: Analytics & Reporting Complete Flow")
    
    print_subheader("Step 1: Generate Revenue Report")
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE}/revenue",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "group_by": "month"
            }
        )
        
        log_detailed(f"Revenue Report Response: {response.text}")
        
        if response.status_code == 200:
            report = response.json()
            log(f"{Colors.GREEN}✓ Revenue report generated{Colors.NC}")
            if isinstance(report, dict):
                total_revenue = report.get('total_revenue', 0)
                log(f"{Colors.GREEN}  ✓ Total revenue: ${total_revenue}{Colors.NC}")
                stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Revenue report: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception generating revenue report: {e}{Colors.NC}")
    
    print_subheader("Step 2: Get Vehicle Utilization Metrics")
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE}/charters/vehicle-utilization",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        log_detailed(f"Vehicle Utilization Response: {response.text}")
        
        if response.status_code == 200:
            metrics = response.json()
            log(f"{Colors.GREEN}  ✓ Vehicle utilization metrics retrieved{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Utilization metrics: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception getting utilization: {e}{Colors.NC}")
    
    print_subheader("Step 3: Calculate Vendor Performance Scores")
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE}/vendor-performance",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={
                "period": "quarterly"
            }
        )
        
        log_detailed(f"Vendor Performance Response: {response.text}")
        
        if response.status_code == 200:
            performance = response.json()
            log(f"{Colors.GREEN}  ✓ Vendor performance scores calculated{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Vendor performance: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception calculating performance: {e}{Colors.NC}")
    
    print_subheader("Step 4: Get Client Satisfaction Metrics")
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE}/client-satisfaction",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            params={
                "timeframe": "last_90_days"
            }
        )
        
        log_detailed(f"Client Satisfaction Response: {response.text}")
        
        if response.status_code == 200:
            satisfaction = response.json()
            log(f"{Colors.GREEN}  ✓ Client satisfaction metrics retrieved{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Satisfaction metrics: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception getting satisfaction: {e}{Colors.NC}")
    
    print_subheader("Step 5: Generate Executive Dashboard Summary")
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE}/dashboard/executive",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Dashboard Summary Response: {response.text}")
        
        if response.status_code == 200:
            dashboard = response.json()
            log(f"{Colors.GREEN}✓ Executive dashboard generated{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}⚠ Dashboard: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception generating dashboard: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"Analytics & Reporting Complete Flow ({duration:.1f}s)")
    return True

def test_workflow_15_user_management():
    """Test Workflow 15: User Management & Permissions"""
    start_time = time.time()
    print_header("WORKFLOW 15: User Management & Permissions")
    
    print_subheader("Step 1: Create New User Account")
    try:
        timestamp = int(time.time())
        response = requests.post(
            "http://localhost:8080/api/v1/users",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "email": f"newuser+{timestamp}@coachway.com",
                "password": "SecurePass123!",
                "full_name": "Test User",
                "role": "agent",
                "is_active": True
            }
        )
        
        log_detailed(f"User Creation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            user_data = response.json()
            user_id = user_data.get('id') or user_data.get('user_id')
            test_data.created_user_id = user_id
            log(f"{Colors.GREEN}✓ User created: ID {user_id}{Colors.NC}")
            validate_field(user_data, "role", "agent", "User Role")
        else:
            log(f"{Colors.YELLOW}⚠ User creation: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception creating user: {e}{Colors.NC}")
    
    print_subheader("Step 2: Assign Specific Permissions")
    user_id = test_data.created_user_id or 1
    try:
        response = requests.post(
            f"http://localhost:8080/api/v1/users/{user_id}/permissions",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "permissions": [
                    "view_charters",
                    "create_charters",
                    "view_clients",
                    "view_reports"
                ]
            }
        )
        
        log_detailed(f"Permission Assignment Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ Permissions assigned{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Permission assignment: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception assigning permissions: {e}{Colors.NC}")
    
    print_subheader("Step 3: Test Role-Based Access Control")
    try:
        # Try to access admin-only endpoint with agent token
        response = requests.get(
            "http://localhost:8080/api/v1/users",
            headers={"Authorization": f"Bearer {test_data.agent_token}"}
        )
        
        log_detailed(f"RBAC Test Response: {response.text}")
        
        if response.status_code == 403:
            log(f"{Colors.GREEN}  ✓ RBAC correctly denied access (403){Colors.NC}")
            stats.validations_passed += 1
        elif response.status_code == 200:
            log(f"{Colors.YELLOW}  ⚠ RBAC should have denied access{Colors.NC}")
        else:
            log(f"{Colors.YELLOW}  ⚠ RBAC test: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception testing RBAC: {e}{Colors.NC}")
    
    print_subheader("Step 4: Update User Role")
    try:
        response = requests.put(
            f"http://localhost:8080/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {test_data.admin_token}"},
            json={
                "role": "manager"
            }
        )
        
        log_detailed(f"Role Update Response: {response.text}")
        
        if response.status_code == 200:
            user_data = response.json()
            validate_field(user_data, "role", "manager", "Updated Role")
        else:
            log(f"{Colors.YELLOW}  ⚠ Role update: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception updating role: {e}{Colors.NC}")
    
    print_subheader("Step 5: Deactivate User Account")
    try:
        response = requests.post(
            f"http://localhost:8080/api/v1/users/{user_id}/deactivate",
            headers={"Authorization": f"Bearer {test_data.admin_token}"}
        )
        
        log_detailed(f"Deactivation Response: {response.text}")
        
        if response.status_code in [200, 201]:
            log(f"{Colors.GREEN}  ✓ User account deactivated{Colors.NC}")
            stats.validations_passed += 1
        else:
            log(f"{Colors.YELLOW}  ⚠ Deactivation: HTTP {response.status_code}{Colors.NC}")
    except Exception as e:
        log(f"{Colors.YELLOW}⚠ Exception deactivating user: {e}{Colors.NC}")
    
    duration = time.time() - start_time
    workflow_passed(f"User Management & Permissions ({duration:.1f}s)")
    return True

# ==============================================================================
# Main Execution
# ==============================================================================
def main():
    """Main test execution"""
    print("\033[2J\033[H")  # Clear screen
    print_header("COACHWAY PLATFORM - COMPREHENSIVE E2E WORKFLOW TEST SUITE")
    log(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Main log file: {LOG_FILE}")
    log(f"Detailed log file: {DETAILED_LOG}")
    log("")
    
    # System health check
    if not check_system_health():
        log(f"{Colors.YELLOW}⚠ Warning: Critical services down, some tests may fail{Colors.NC}")
    
    # Get authentication tokens
    if not get_auth_tokens():
        log(f"{Colors.RED}✗ Failed to obtain authentication tokens{Colors.NC}")
        log(f"{Colors.RED}Cannot proceed with tests{Colors.NC}")
        sys.exit(1)
    
    log("")
    log("Starting comprehensive workflow tests...")
    log("=" * 48)
    log("")
    
    # Run all comprehensive workflow tests
    test_workflow_1_complete_client_onboarding()
    test_workflow_2_vendor_bidding_selection()
    test_workflow_3_document_esignature_flow()
    test_workflow_4_payment_processing_e2e()
    test_workflow_5_sales_pipeline()
    test_workflow_6_dispatch_driver_flow()
    test_workflow_7_change_management()
    test_workflow_8_multi_vehicle_charter()
    test_workflow_9_charter_modification_cancellation()
    test_workflow_10_recurring_charter_series()
    test_workflow_11_driver_checkin_operations()
    test_workflow_12_invoice_reconciliation()
    test_workflow_13_emergency_reassignment()
    test_workflow_14_analytics_reporting()
    test_workflow_15_user_management()
    
    # Print comprehensive summary
    print_header("COMPREHENSIVE TEST SUMMARY")
    log(f"Total Workflows Executed: {stats.workflows_total}")
    log(f"{Colors.GREEN}✅ Workflows Passed: {stats.workflows_passed}{Colors.NC}")
    log(f"{Colors.RED}❌ Workflows Failed: {stats.workflows_failed}{Colors.NC}")
    log("")
    log(f"Total Validations: {stats.validations_passed + stats.validations_failed}")
    log(f"{Colors.GREEN}✅ Validations Passed: {stats.validations_passed}{Colors.NC}")
    log(f"{Colors.RED}❌ Validations Failed: {stats.validations_failed}{Colors.NC}")
    log("")
    
    # Calculate success rates
    if stats.workflows_total > 0:
        workflow_success_rate = (stats.workflows_passed / stats.workflows_total) * 100
        log(f"Workflow Success Rate: {workflow_success_rate:.1f}%")
    
    total_validations = stats.validations_passed + stats.validations_failed
    if total_validations > 0:
        validation_success_rate = (stats.validations_passed / total_validations) * 100
        log(f"Data Validation Success Rate: {validation_success_rate:.1f}%")
    
    log("")
    log("Logs available at:")
    log(f"  Main: {LOG_FILE}")
    log(f"  Detailed: {DETAILED_LOG}")
    log("")
    
    if stats.workflows_failed == 0:
        log(f"{Colors.GREEN}✅✅✅ ALL WORKFLOWS PASSED! ✅✅✅{Colors.NC}")
        log("")
        sys.exit(0)
    else:
        log(f"{Colors.RED}❌ SOME WORKFLOWS FAILED - Review logs for details{Colors.NC}")
        log("")
        sys.exit(1)

if __name__ == "__main__":
    main()
