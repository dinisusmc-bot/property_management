#!/usr/bin/env python3
"""
Backend API Tests for Phase 2 Features
Tests directly against backend services
"""
import requests
import os
from datetime import datetime, timedelta

# Test results storage
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test(name, passed, details=""):
    if passed:
        test_results["passed"] += 1
        print(f"✓ {name}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append({"name": name, "details": details})
        print(f"✗ {name}")
        if details:
            print(f"  {details}")

def test_qc_tasks():
    """Test QC Task System API - Direct to service"""
    print("\n=== QC Task System API Tests ===")
    
    QC_SERVICE = "http://localhost:8012"
    
    # Test 1: Get all QC tasks
    try:
        response = requests.get(f"{QC_SERVICE}/api/v1/qc/tasks", timeout=5)
        log_test(f"GET {QC_SERVICE}/api/v1/qc/tasks", response.status_code == 200)
        if response.status_code == 200:
            print(f"  Response: {len(response.json())} tasks")
    except Exception as e:
        log_test("GET /qc/tasks", False, str(e))
    
    # Test 2: Create a QC task
    try:
        payload = {
            "title": f"API Test Task {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Test description for API testing",
            "task_type": "document_review",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": "medium",
            "status": "pending"
        }
        response = requests.post(f"{QC_SERVICE}/api/v1/qc/tasks", json=payload, timeout=5)
        log_test(f"POST {QC_SERVICE}/api/v1/qc/tasks creates task", response.status_code in [200, 201])
        
        if response.status_code in [200, 201]:
            data = response.json()
            task_id = data.get("id")
            print(f"  Created task ID: {task_id}")
            
            # Test 3: Get specific task
            response = requests.get(f"{QC_SERVICE}/api/v1/qc/tasks/{task_id}", timeout=5)
            log_test(f"GET /qc/tasks/{{id}} returns task", response.status_code == 200)
            
            # Test 4: Filter by status
            response = requests.get(f"{QC_SERVICE}/api/v1/qc/tasks?status=pending", timeout=5)
            log_test("GET /qc/tasks?status=pending filters", response.status_code == 200)
            
    except Exception as e:
        log_test("Create and test QC task", False, str(e))

def test_manual_payment():
    """Test Manual Payment Application API - Direct to service"""
    print("\n=== Manual Payment Application API Tests ===")
    
    PAYMENT_SERVICE = "http://localhost:8003"  # accounting service
    
    # Test 1: Create payment override
    try:
        payload = {
            "charter_id": 1,
            "payment_type": "check",
            "amount": 250.00,
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "reference_number": f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "notes": "API test payment override"
        }
        response = requests.post(f"{PAYMENT_SERVICE}/api/v1/payments/override", json=payload, timeout=5)
        log_test(f"POST {PAYMENT_SERVICE}/api/v1/payments/override", response.status_code in [200, 201])
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            # Test 2: Validate amount is positive
            negative_payload = payload.copy()
            negative_payload["amount"] = -50.00
            response = requests.post(f"{PAYMENT_SERVICE}/api/v1/payments/override", json=negative_payload, timeout=5)
            log_test("POST /payments/override rejects negative amount", response.status_code != 200)
            
    except Exception as e:
        log_test("Create and test payment", False, str(e))
    
    # Test 3: Get payments
    try:
        response = requests.get(f"{PAYMENT_SERVICE}/api/v1/payments", timeout=5)
        log_test(f"GET {PAYMENT_SERVICE}/api/v1/payments", response.status_code == 200)
        if response.status_code == 200:
            print(f"  Response: {len(response.json())} payments")
    except Exception as e:
        log_test("GET /payments", False, str(e))

def test_change_requests():
    """Test Change Case System API - Direct to service"""
    print("\n=== Change Case System API Tests ===")
    
    CHANGE_SERVICE = "http://localhost:8012"  # Same as QC service
    
    # Test 1: Get all changes
    try:
        response = requests.get(f"{CHANGE_SERVICE}/api/v1/changes", timeout=5)
        log_test(f"GET {CHANGE_SERVICE}/api/v1/changes", response.status_code == 200)
        if response.status_code == 200:
            print(f"  Response: {len(response.json())} changes")
    except Exception as e:
        log_test("GET /changes", False, str(e))
    
    # Test 2: Create a change request
    try:
        payload = {
            "subject": f"API Test Change {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Test description for API change testing",
            "change_type": "scheduled",
            "priority": "normal",
            "status": "draft",
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "charter_id": 1
        }
        response = requests.post(f"{CHANGE_SERVICE}/api/v1/changes", json=payload, timeout=5)
        log_test(f"POST {CHANGE_SERVICE}/api/v1/changes creates change", response.status_code in [200, 201])
        
        if response.status_code in [200, 201]:
            data = response.json()
            change_id = data.get("id")
            print(f"  Created change ID: {change_id}")
            
            # Test 3: Get specific change
            response = requests.get(f"{CHANGE_SERVICE}/api/v1/changes/{change_id}", timeout=5)
            log_test(f"GET /changes/{{id}} returns change", response.status_code == 200)
            
            # Test 4: Filter by status
            response = requests.get(f"{CHANGE_SERVICE}/api/v1/changes?status=draft", timeout=5)
            log_test("GET /changes?status=draft filters", response.status_code == 200)
            
    except Exception as e:
        log_test("Create and test change request", False, str(e))

def main():
    print("=" * 60)
    print("Backend API Tests for Phase 2 Features")
    print("=" * 60)
    
    # Run all tests
    test_qc_tasks()
    test_manual_payment()
    test_change_requests()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    if test_results['errors']:
        print("\nFailed Tests:")
        for error in test_results['errors']:
            print(f"  - {error['name']}: {error['details']}")
    
    print("=" * 60)
    
    return 0 if test_results['failed'] == 0 else 1

if __name__ == "__main__":
    exit(main())
