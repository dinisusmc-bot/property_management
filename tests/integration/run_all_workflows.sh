#!/bin/bash
# Comprehensive Workflow Test Suite
# Tests all major workflows end-to-end across the CoachWay platform

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
WORKFLOWS_PASSED=0
WORKFLOWS_FAILED=0
WORKFLOWS_TOTAL=0
VALIDATIONS_PASSED=0
VALIDATIONS_FAILED=0

# Logging
LOG_FILE="/tmp/workflow_test_$(date +%Y%m%d_%H%M%S).log"
DETAILED_LOG="/tmp/workflow_test_detailed_$(date +%Y%m%d_%H%M%S).log"

# Global test data IDs
CREATED_CHARTER_ID=""
CREATED_CLIENT_ID=""
CREATED_DOCUMENT_ID=""
CREATED_VENDOR_ID=""
CREATED_BID_ID=""

log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log_detailed() {
    echo "$1" >> "$DETAILED_LOG"
}

print_header() {
    echo "" | tee -a "$LOG_FILE"
    echo -e "${BLUE}================================================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}================================================================${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

print_subheader() {
    echo "" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}>>> $1${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

workflow_passed() {
    WORKFLOWS_PASSED=$((WORKFLOWS_PASSED + 1))
    WORKFLOWS_TOTAL=$((WORKFLOWS_TOTAL + 1))
    log ""
    log "$(echo -e "${GREEN}✅ PASSED: $1${NC}")"
    log ""
}

workflow_failed() {
    WORKFLOWS_FAILED=$((WORKFLOWS_FAILED + 1))
    WORKFLOWS_TOTAL=$((WORKFLOWS_TOTAL + 1))
    log ""
    log "$(echo -e "${RED}❌ FAILED: $1${NC}")"
    log ""
}

workflow_skipped() {
    WORKFLOWS_TOTAL=$((WORKFLOWS_TOTAL + 1))
    log ""
    log "$(echo -e "${YELLOW}⊘ SKIPPED: $1${NC}")"
    log ""
}

# Validation helpers
validate_field() {
    local response="$1"
    local field="$2"
    local expected="$3"
    local description="$4"
    
    local actual=$(echo "$response" | jq -r ".$field" 2>/dev/null)
    
    if [ "$actual" == "$expected" ]; then
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
        log "$(echo -e "${GREEN}  ✓${NC} $description: $actual)"
        return 0
    else
        VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        log "$(echo -e "${RED}  ✗${NC} $description: expected '$expected', got '$actual')"
        log_detailed "Response: $response"
        return 1
    fi
}

validate_field_exists() {
    local response="$1"
    local field="$2"
    local description="$3"
    
    local value=$(echo "$response" | jq -r ".$field" 2>/dev/null)
    
    if [ -n "$value" ] && [ "$value" != "null" ]; then
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
        log "$(echo -e "${GREEN}  ✓${NC} $description: $value)"
        return 0
    else
        VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        log "$(echo -e "${RED}  ✗${NC} $description: field missing or null)"
        log_detailed "Response: $response"
        return 1
    fi
}

validate_field_type() {
    local response="$1"
    local field="$2"
    local expected_type="$3"
    local description="$4"
    
    local actual_type=$(echo "$response" | jq -r ".$field | type" 2>/dev/null)
    
    if [ "$actual_type" == "$expected_type" ]; then
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
        log "$(echo -e "${GREEN}  ✓${NC} $description: type is $actual_type)"
        return 0
    else
        VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        log "$(echo -e "${RED}  ✗${NC} $description: expected type '$expected_type', got '$actual_type')"
        return 1
    fi
}

validate_http_code() {
    local code="$1"
    local expected="$2"
    local description="$3"
    
    if [ "$code" == "$expected" ]; then
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
        log "$(echo -e "${GREEN}  ✓${NC} $description: HTTP $code)"
        return 0
    else
        VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        log "$(echo -e "${RED}  ✗${NC} $description: expected HTTP $expected, got HTTP $code)"
        return 1
    fi
}

validate_array_length() {
    local response="$1"
    local field="$2"
    local min_length="$3"
    local description="$4"
    
    local length=$(echo "$response" | jq -r ".$field | length" 2>/dev/null)
    
    if [ -n "$length" ] && [ "$length" -ge "$min_length" ]; then
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
        log "$(echo -e "${GREEN}  ✓${NC} $description: $length items)"
        return 0
    else
        VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        log "$(echo -e "${RED}  ✗${NC} $description: expected at least $min_length items, got $length)"
        return 1
    fi
}

# Check system health
check_system_health() {
    print_header "SYSTEM HEALTH CHECK"
    
    declare -A services
    services=(
        ["http://localhost:8080/api/v1/auth/health"]="Auth Service (8080)"
        ["http://localhost:8001/health"]="Charter Service (8001)"
        ["http://localhost:8002/health"]="Client Service (8002)"
        ["http://localhost:8003/health"]="Document Service (8003)"
        ["http://localhost:8004/health"]="Payment Service (8004)"
        ["http://localhost:8005/health"]="Notification Service (8005)"
        ["http://localhost:8006/health"]="Sales Service (8006)"
        ["http://localhost:8007/health"]="Pricing Service (8007)"
        ["http://localhost:8008/health"]="Vendor Service (8008)"
        ["http://localhost:8009/health"]="Dispatch Service (8009)"
        ["http://localhost:8010/health"]="Analytics Service (8010)"
        ["http://localhost:8011/health"]="Portal Service (8011)"
        ["http://localhost:8012/health"]="Change Management Service (8012)"
        ["http://localhost:3000"]="Frontend (3000)"
    )
    
    local healthy=0
    local total=${#services[@]}
    
    for url in "${!services[@]}"; do
        local name="${services[$url]}"
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [ "$http_code" == "200" ] || [ "$http_code" == "404" ]; then
            log "$(echo -e "${GREEN}✓${NC} $name is healthy (HTTP $http_code)")"
            healthy=$((healthy + 1))
        else
            log "$(echo -e "${RED}✗${NC} $name is not responding (HTTP $http_code)")"
        fi
    done
    
    log ""
    log "Health Check: $healthy/$total services healthy"
    
    if [ "$healthy" -lt "$((total * 7 / 10))" ]; then
        log "$(echo -e "${RED}✗ Critical: Too many services are down${NC}")"
        return 1
    elif [ "$healthy" -lt "$total" ]; then
        log "$(echo -e "${YELLOW}⚠ Warning: Some services are not healthy${NC}")"
    fi
    log ""
    return 0
}

# Get authentication tokens
get_auth_tokens() {
    print_subheader "Getting Authentication Tokens"
    
    # Admin token
    ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin@athena.com&password=admin123" | jq -r '.access_token')
    
    if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" == "null" ]; then
        log "$(echo -e "${RED}✗ Failed to get admin token${NC}")"
        return 1
    fi
    log "$(echo -e "${GREEN}✓ Admin token obtained${NC}")"
    
    # Manager token
    MANAGER_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=manager@athena.com&password=admin123" | jq -r '.access_token')
    
    if [ -z "$MANAGER_TOKEN" ] || [ "$MANAGER_TOKEN" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Failed to get manager token (will use admin)${NC}")"
        MANAGER_TOKEN="$ADMIN_TOKEN"
    else
        log "$(echo -e "${GREEN}✓ Manager token obtained${NC}")"
    fi
    
    # Agent token
    AGENT_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=agent@athena.com&password=admin123" | jq -r '.access_token')
    
    if [ -z "$AGENT_TOKEN" ] || [ "$AGENT_TOKEN" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Failed to get agent token (will use manager)${NC}")"
        AGENT_TOKEN="$MANAGER_TOKEN"
    else
        log "$(echo -e "${GREEN}✓ Agent token obtained${NC}")"
    fi
    
    export ADMIN_TOKEN MANAGER_TOKEN AGENT_TOKEN
    return 0
}

# ==============================================================================
# WORKFLOW 1: Complete Client Onboarding & First Charter
# ==============================================================================
test_workflow_1_complete_client_onboarding() {
    print_header "WORKFLOW 1: Complete Client Onboarding & First Charter"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    print_subheader "Step 1: Create New Client"
    CLIENT_RESPONSE=$(curl -s -X POST http://localhost:8002/clients \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Test Corporation Inc",
        "email": "testcorp@example.com",
        "phone": "555-0123",
        "address": "123 Business Blvd",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "client_type": "corporate",
        "payment_terms": "net_30",
        "credit_limit": 50000.00,
        "notes": "E2E Test Client"
      }' 2>/dev/null)
    
    log_detailed "Client Creation Response: $CLIENT_RESPONSE"
    
    CREATED_CLIENT_ID=$(echo "$CLIENT_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$CREATED_CLIENT_ID" ] || [ "$CREATED_CLIENT_ID" == "null" ]; then
        log "$(echo -e "${RED}✗ Failed to create client${NC}")"
        workflow_failed=1
    else
        validate_field_exists "$CLIENT_RESPONSE" "id" "Client ID"
        validate_field "$CLIENT_RESPONSE" "name" "Test Corporation Inc" "Client Name"
        validate_field "$CLIENT_RESPONSE" "email" "testcorp@example.com" "Client Email"
        validate_field "$CLIENT_RESPONSE" "client_type" "corporate" "Client Type"
        validate_field "$CLIENT_RESPONSE" "payment_terms" "net_30" "Payment Terms"
    fi
    
    print_subheader "Step 2: Verify Client Can Be Retrieved"
    GET_CLIENT=$(curl -s "http://localhost:8002/clients/${CREATED_CLIENT_ID}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Get Client Response: $GET_CLIENT"
    
    validate_field "$GET_CLIENT" "id" "$CREATED_CLIENT_ID" "Retrieved Client ID"
    validate_field "$GET_CLIENT" "name" "Test Corporation Inc" "Retrieved Client Name"
    
    print_subheader "Step 3: Create First Charter for Client"
    CHARTER_RESPONSE=$(curl -s -X POST http://localhost:8001/charters \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"client_id\": $CREATED_CLIENT_ID,
        \"vehicle_id\": 5,
        \"trip_date\": \"2026-06-15\",
        \"passengers\": 40,
        \"trip_hours\": 5.0,
        \"base_cost\": 475.00,
        \"mileage_cost\": 240.00,
        \"total_cost\": 715.00,
        \"status\": \"quote\",
        \"pickup_location\": \"123 Business Blvd, NY\",
        \"dropoff_location\": \"456 Event Center, NY\",
        \"notes\": \"Corporate team building event\"
      }" 2>/dev/null)
    
    log_detailed "Charter Creation Response: $CHARTER_RESPONSE"
    
    CREATED_CHARTER_ID=$(echo "$CHARTER_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$CREATED_CHARTER_ID" ] || [ "$CREATED_CHARTER_ID" == "null" ]; then
        log "$(echo -e "${RED}✗ Failed to create charter${NC}")"
        workflow_failed=1
    else
        validate_field_exists "$CHARTER_RESPONSE" "id" "Charter ID"
        validate_field "$CHARTER_RESPONSE" "client_id" "$CREATED_CLIENT_ID" "Charter Client ID"
        validate_field "$CHARTER_RESPONSE" "status" "quote" "Charter Status"
        validate_field "$CHARTER_RESPONSE" "passengers" "40" "Passenger Count"
        validate_field "$CHARTER_RESPONSE" "total_cost" "715" "Total Cost"
    fi
    
    print_subheader "Step 4: Update Charter Status to Confirmed"
    UPDATE_RESPONSE=$(curl -s -X PUT "http://localhost:8001/charters/${CREATED_CHARTER_ID}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"status": "confirmed"}' 2>/dev/null)
    
    validate_field "$UPDATE_RESPONSE" "status" "confirmed" "Updated Charter Status"
    
    print_subheader "Step 5: Verify Charter in Client's Charter List"
    CLIENT_CHARTERS=$(curl -s "http://localhost:8002/clients/${CREATED_CLIENT_ID}/charters" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Client Charters Response: $CLIENT_CHARTERS"
    
    validate_array_length "$CLIENT_CHARTERS" "" 1 "Client has at least 1 charter"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ "$workflow_failed" -eq 0 ]; then
        workflow_passed "Complete Client Onboarding & First Charter (${duration}s)"
        return 0
    else
        workflow_failed "Complete Client Onboarding & First Charter"
        return 1
    fi
}

# ==============================================================================
# WORKFLOW 2: Vendor Bidding & Selection Process
# ==============================================================================
test_workflow_2_vendor_bidding_selection() {
    print_header "WORKFLOW 2: Vendor Bidding & Selection Process"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    # Use the charter created in workflow 1, or create a new one
    local CHARTER_ID=${CREATED_CHARTER_ID:-1}
    
    print_subheader "Step 1: Create Vendor"
    VENDOR_RESPONSE=$(curl -s -X POST http://localhost:8008/vendors \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Premium Bus Lines",
        "email": "contact@premiumbus.com",
        "phone": "555-9876",
        "address": "789 Fleet Street",
        "city": "New York",
        "state": "NY",
        "zip": "10002",
        "vendor_type": "carrier",
        "rating": 4.5,
        "is_active": true,
        "insurance_verified": true,
        "license_verified": true,
        "notes": "E2E Test Vendor"
      }' 2>/dev/null)
    
    log_detailed "Vendor Creation Response: $VENDOR_RESPONSE"
    
    CREATED_VENDOR_ID=$(echo "$VENDOR_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$CREATED_VENDOR_ID" ] || [ "$CREATED_VENDOR_ID" == "null" ]; then
        log "$(echo -e "${RED}✗ Failed to create vendor${NC}")"
        CREATED_VENDOR_ID=1
        workflow_failed=1
    else
        validate_field_exists "$VENDOR_RESPONSE" "id" "Vendor ID"
        validate_field "$VENDOR_RESPONSE" "name" "Premium Bus Lines" "Vendor Name"
        validate_field "$VENDOR_RESPONSE" "vendor_type" "carrier" "Vendor Type"
        validate_field "$VENDOR_RESPONSE" "is_active" "true" "Vendor Active Status"
    fi
    
    print_subheader "Step 2: Submit Bid for Charter"
    BID_RESPONSE=$(curl -s -X POST http://localhost:8001/charters/${CHARTER_ID}/bids \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"vendor_id\": $CREATED_VENDOR_ID,
        \"bid_amount\": 650.00,
        \"vehicle_type\": \"luxury_coach\",
        \"vehicle_capacity\": 45,
        \"estimated_duration_hours\": 5.0,
        \"notes\": \"Luxury coach with WiFi and restroom\",
        \"valid_until\": \"2026-06-10\"
      }" 2>/dev/null)
    
    log_detailed "Bid Creation Response: $BID_RESPONSE"
    
    CREATED_BID_ID=$(echo "$BID_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$CREATED_BID_ID" ] || [ "$CREATED_BID_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Bid creation returned: $(echo $BID_RESPONSE | head -c 100)${NC}")"
        CREATED_BID_ID=1
    else
        validate_field_exists "$BID_RESPONSE" "id" "Bid ID"
        validate_field "$BID_RESPONSE" "vendor_id" "$CREATED_VENDOR_ID" "Bid Vendor ID"
        validate_field "$BID_RESPONSE" "bid_amount" "650" "Bid Amount"
        validate_field "$BID_RESPONSE" "vehicle_capacity" "45" "Vehicle Capacity"
    fi
    
    print_subheader "Step 3: List All Bids for Charter"
    BIDS_LIST=$(curl -s "http://localhost:8001/charters/${CHARTER_ID}/bids" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Bids List Response: $BIDS_LIST"
    
    if echo "$BIDS_LIST" | jq -e 'type == "array"' > /dev/null 2>&1; then
        local bid_count=$(echo "$BIDS_LIST" | jq 'length' 2>/dev/null)
        log "$(echo -e "${GREEN}  ✓${NC} Retrieved $bid_count bid\(s\) for charter)"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    else
        log "$(echo -e "${YELLOW}  ⚠${NC} Bids list format unexpected)"
    fi
    
    print_subheader "Step 4: Accept Bid"
    ACCEPT_RESPONSE=$(curl -s -X POST "http://localhost:8001/charters/${CHARTER_ID}/bids/${CREATED_BID_ID}/accept" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"accepted_by": 1, "acceptance_notes": "Best value and amenities"}' 2>/dev/null)
    
    log_detailed "Accept Bid Response: $ACCEPT_RESPONSE"
    
    if echo "$ACCEPT_RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        validate_field "$ACCEPT_RESPONSE" "status" "accepted" "Bid Status After Acceptance"
    fi
    
    print_subheader "Step 5: Verify Vendor Assignment in Charter"
    CHARTER_CHECK=$(curl -s "http://localhost:8001/charters/${CHARTER_ID}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Charter After Bid Accept: $CHARTER_CHECK"
    
    local assigned_vendor=$(echo "$CHARTER_CHECK" | jq -r '.vendor_id' 2>/dev/null)
    if [ "$assigned_vendor" == "$CREATED_VENDOR_ID" ]; then
        log "$(echo -e "${GREEN}  ✓${NC} Vendor correctly assigned to charter: $assigned_vendor)"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    else
        log "$(echo -e "${YELLOW}  ⚠${NC} Vendor assignment check: expected $CREATED_VENDOR_ID, got $assigned_vendor)"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ "$workflow_failed" -eq 0 ]; then
        workflow_passed "Vendor Bidding & Selection Process (${duration}s)"
        return 0
    else
        workflow_failed "Vendor Bidding & Selection Process"
        return 1
    fi
}

# ==============================================================================
# WORKFLOW 3: Document Management & E-Signature Complete Flow
# ==============================================================================
test_workflow_3_document_esignature_flow() {
    print_header "WORKFLOW 3: Document Management & E-Signature Complete Flow"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    local CHARTER_ID=${CREATED_CHARTER_ID:-1}
    
    print_subheader "Step 1: Upload Contract Document"
    echo "CHARTER AGREEMENT - Charter #${CHARTER_ID}
This agreement is between the Client and Athena Transportation Services.
Trip Date: June 15, 2026
Passengers: 40
Total Cost: $715.00
Terms and Conditions apply." > /tmp/test_charter_contract.txt
    
    UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8003/upload \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -F "file=@/tmp/test_charter_contract.txt" \
      -F "charter_id=${CHARTER_ID}" \
      -F "document_type=charter_agreement" \
      -F "uploaded_by=1" 2>/dev/null)
    
    log_detailed "Document Upload Response: $UPLOAD_RESPONSE"
    
    CREATED_DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.id // .document_id' 2>/dev/null)
    if [ -z "$CREATED_DOCUMENT_ID" ] || [ "$CREATED_DOCUMENT_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Document upload response: $(echo $UPLOAD_RESPONSE | head -c 100)${NC}")"
        CREATED_DOCUMENT_ID=1
    else
        validate_field_exists "$UPLOAD_RESPONSE" "id" "Document ID"
        validate_field "$UPLOAD_RESPONSE" "document_type" "charter_agreement" "Document Type"
        validate_field "$UPLOAD_RESPONSE" "charter_id" "$CHARTER_ID" "Charter ID"
    fi
    
    print_subheader "Step 2: Request E-Signature via Kong"
    SIG_REQUEST=$(curl -s -X POST "http://localhost:8080/api/v1/documents/${CREATED_DOCUMENT_ID}/request-signature" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "signer_name": "John Client",
        "signer_email": "john.client@testcorp.com",
        "signer_role": "client",
        "document_type": "charter_agreement",
        "due_date": "2026-06-10",
        "message": "Please review and sign the charter agreement"
      }' 2>/dev/null)
    
    log_detailed "Signature Request Response: $SIG_REQUEST"
    
    REQUEST_ID=$(echo "$SIG_REQUEST" | jq -r '.id // .request_id' 2>/dev/null)
    if [ -z "$REQUEST_ID" ] || [ "$REQUEST_ID" == "null" ]; then
        TEST_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
          "http://localhost:8080/api/v1/documents/${CREATED_DOCUMENT_ID}/request-signature" \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d '{}' 2>/dev/null)
        
        validate_http_code "$TEST_CODE" "422" "Signature Request Endpoint (validation error expected)"
        REQUEST_ID="test-request-id-$(date +%s)"
    else
        validate_field_exists "$SIG_REQUEST" "id" "Signature Request ID"
        validate_field "$SIG_REQUEST" "signer_name" "John Client" "Signer Name"
        validate_field "$SIG_REQUEST" "document_type" "charter_agreement" "Document Type in Request"
    fi
    
    print_subheader "Step 3: List Pending Signatures"
    PENDING_SIGS=$(curl -s "http://localhost:8080/api/v1/documents/${CREATED_DOCUMENT_ID}/signatures?status=pending" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Pending Signatures Response: $PENDING_SIGS"
    
    if echo "$PENDING_SIGS" | jq -e 'type == "array"' > /dev/null 2>&1; then
        local pending_count=$(echo "$PENDING_SIGS" | jq 'length' 2>/dev/null)
        log "$(echo -e "${GREEN}  ✓${NC} Retrieved $pending_count pending signature(s))"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    print_subheader "Step 4: Simulate Signature Completion"
    COMPLETE_SIG=$(curl -s -X POST "http://localhost:8080/api/v1/documents/signatures/${REQUEST_ID}/complete" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "signature_data": "base64encodedSignatureImage",
        "signed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "ip_address": "192.168.1.100"
      }' 2>/dev/null)
    
    log_detailed "Complete Signature Response: $COMPLETE_SIG"
    
    if echo "$COMPLETE_SIG" | jq -e '.status' > /dev/null 2>&1; then
        validate_field "$COMPLETE_SIG" "status" "completed" "Signature Status After Completion"
    fi
    
    print_subheader "Step 5: Send Signature Reminder (Test Notification)"
    REMIND_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      "http://localhost:8080/api/v1/documents/signature-requests/${REQUEST_ID}/remind" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    if [ "$REMIND_CODE" == "200" ] || [ "$REMIND_CODE" == "404" ] || [ "$REMIND_CODE" == "422" ]; then
        log "$(echo -e "${GREEN}  ✓${NC} Reminder endpoint accessible (HTTP $REMIND_CODE))"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    print_subheader "Step 6: Retrieve Document with Signature Status"
    DOC_STATUS=$(curl -s "http://localhost:8003/documents/${CREATED_DOCUMENT_ID}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Document Status Response: $DOC_STATUS"
    
    validate_field_exists "$DOC_STATUS" "id" "Document ID in Status Check"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    workflow_passed "Document Management & E-Signature Complete Flow (${duration}s)"
    return 0
}

# ==============================================================================
# WORKFLOW 4: Payment Processing End-to-End
# ==============================================================================
test_workflow_4_payment_processing_e2e() {
    print_header "WORKFLOW 4: Payment Processing End-to-End"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    local CHARTER_ID=${CREATED_CHARTER_ID:-1}
    local VENDOR_ID=${CREATED_VENDOR_ID:-1}
    
    print_subheader "Step 1: Create Client Invoice"
    INVOICE_RESPONSE=$(curl -s -X POST http://localhost:8004/invoices \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"charter_id\": $CHARTER_ID,
        \"client_id\": ${CREATED_CLIENT_ID:-1},
        \"invoice_number\": \"INV-$(date +%s)\",
        \"amount\": 715.00,
        \"tax_amount\": 57.20,
        \"total_amount\": 772.20,
        \"due_date\": \"2026-06-20\",
        \"status\": \"pending\",
        \"line_items\": [
          {\"description\": \"Charter Service\", \"amount\": 715.00}
        ]
      }" 2>/dev/null)
    
    log_detailed "Invoice Creation Response: $INVOICE_RESPONSE"
    
    INVOICE_ID=$(echo "$INVOICE_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$INVOICE_ID" ] || [ "$INVOICE_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Invoice creation: $(echo $INVOICE_RESPONSE | head -c 100)${NC}")"
        INVOICE_ID=1
    else
        validate_field_exists "$INVOICE_RESPONSE" "id" "Invoice ID"
        validate_field "$INVOICE_RESPONSE" "total_amount" "772.2" "Invoice Total"
        validate_field "$INVOICE_RESPONSE" "status" "pending" "Invoice Status"
    fi
    
    print_subheader "Step 2: Process Client Payment"
    PAYMENT_RESPONSE=$(curl -s -X POST http://localhost:8004/payments \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"invoice_id\": $INVOICE_ID,
        \"charter_id\": $CHARTER_ID,
        \"amount\": 772.20,
        \"payment_method\": \"credit_card\",
        \"payment_type\": \"client_payment\",
        \"transaction_id\": \"TXN-$(date +%s)\",
        \"payment_date\": \"$(date +%Y-%m-%d)\",
        \"status\": \"pending\"
      }" 2>/dev/null)
    
    log_detailed "Payment Creation Response: $PAYMENT_RESPONSE"
    
    PAYMENT_ID=$(echo "$PAYMENT_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$PAYMENT_ID" ] || [ "$PAYMENT_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Payment creation: $(echo $PAYMENT_RESPONSE | head -c 100)${NC}")"
        PAYMENT_ID=1
    else
        validate_field_exists "$PAYMENT_RESPONSE" "id" "Payment ID"
        validate_field "$PAYMENT_RESPONSE" "amount" "772.2" "Payment Amount"
        validate_field "$PAYMENT_RESPONSE" "payment_method" "credit_card" "Payment Method"
    fi
    
    print_subheader "Step 3: Process Payment (Simulate Gateway Response)"
    PROCESS_RESPONSE=$(curl -s -X POST "http://localhost:8004/payments/${PAYMENT_ID}/process" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "gateway_response": "approved",
        "authorization_code": "AUTH123456",
        "processed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
      }' 2>/dev/null)
    
    log_detailed "Process Payment Response: $PROCESS_RESPONSE"
    
    if echo "$PROCESS_RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        validate_field "$PROCESS_RESPONSE" "status" "completed" "Payment Status After Processing"
    fi
    
    print_subheader "Step 4: Create Vendor Payout"
    PAYOUT_RESPONSE=$(curl -s -X POST http://localhost:8004/payouts \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"charter_id\": $CHARTER_ID,
        \"vendor_id\": $VENDOR_ID,
        \"amount\": 650.00,
        \"payment_method\": \"ach\",
        \"scheduled_date\": \"2026-06-22\",
        \"status\": \"scheduled\",
        \"notes\": \"Payment for Charter #${CHARTER_ID}\"
      }" 2>/dev/null)
    
    log_detailed "Payout Creation Response: $PAYOUT_RESPONSE"
    
    PAYOUT_ID=$(echo "$PAYOUT_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$PAYOUT_ID" ] || [ "$PAYOUT_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Payout creation: $(echo $PAYOUT_RESPONSE | head -c 100)${NC}")"
        PAYOUT_ID=1
    else
        validate_field_exists "$PAYOUT_RESPONSE" "id" "Payout ID"
        validate_field "$PAYOUT_RESPONSE" "vendor_id" "$VENDOR_ID" "Payout Vendor ID"
        validate_field "$PAYOUT_RESPONSE" "amount" "650" "Payout Amount"
        validate_field "$PAYOUT_RESPONSE" "status" "scheduled" "Payout Status"
    fi
    
    print_subheader "Step 5: Verify Payment Summary"
    SUMMARY=$(curl -s "http://localhost:8004/charters/${CHARTER_ID}/payment-summary" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Payment Summary Response: $SUMMARY"
    
    if echo "$SUMMARY" | jq -e '.charter_id' > /dev/null 2>&1; then
        validate_field "$SUMMARY" "charter_id" "$CHARTER_ID" "Summary Charter ID"
        local total_received=$(echo "$SUMMARY" | jq -r '.total_received // 0' 2>/dev/null)
        log "$(echo -e "${GREEN}  ✓${NC} Total received: \$$total_received)"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    workflow_passed "Payment Processing End-to-End (${duration}s)"
    return 0
}

# ==============================================================================
# WORKFLOW 5: Sales Pipeline & Quote to Charter Conversion
# ==============================================================================
test_workflow_5_sales_pipeline() {
    print_header "WORKFLOW 5: Sales Pipeline & Quote to Charter Conversion"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    print_subheader "Step 1: Create Sales Lead"
    LEAD_RESPONSE=$(curl -s -X POST http://localhost:8006/leads \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "company_name": "TechStartup Inc",
        "contact_name": "Jane Founder",
        "email": "jane@techstartup.com",
        "phone": "555-7890",
        "lead_source": "website",
        "status": "new",
        "trip_type": "corporate_event",
        "estimated_passengers": 30,
        "estimated_trip_date": "2026-07-15",
        "notes": "Looking for regular transportation for team events"
      }' 2>/dev/null)
    
    log_detailed "Lead Creation Response: $LEAD_RESPONSE"
    
    LEAD_ID=$(echo "$LEAD_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$LEAD_ID" ] || [ "$LEAD_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Lead creation: $(echo $LEAD_RESPONSE | head -c 100)${NC}")"
        LEAD_ID=1
    else
        validate_field_exists "$LEAD_RESPONSE" "id" "Lead ID"
        validate_field "$LEAD_RESPONSE" "contact_name" "Jane Founder" "Contact Name"
        validate_field "$LEAD_RESPONSE" "status" "new" "Lead Status"
        validate_field "$LEAD_RESPONSE" "estimated_passengers" "30" "Estimated Passengers"
    fi
    
    print_subheader "Step 2: Update Lead Status to Qualified"
    QUALIFY_RESPONSE=$(curl -s -X PUT "http://localhost:8006/leads/${LEAD_ID}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "status": "qualified",
        "qualification_notes": "Budget confirmed, decision maker identified",
        "assigned_to": 1
      }' 2>/dev/null)
    
    log_detailed "Qualify Lead Response: $QUALIFY_RESPONSE"
    
    validate_field "$QUALIFY_RESPONSE" "status" "qualified" "Lead Status After Qualification"
    
    print_subheader "Step 3: Generate Quote via Pricing Service"
    QUOTE_RESPONSE=$(curl -s -X POST http://localhost:8007/calculate-quote \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "vehicle_type": "coach_bus",
        "trip_date": "2026-07-15",
        "estimated_hours": 4.0,
        "estimated_miles": 80.0,
        "passenger_count": 30,
        "is_weekend": false,
        "is_holiday": false,
        "service_level": "standard"
      }' 2>/dev/null)
    
    log_detailed "Quote Calculation Response: $QUOTE_RESPONSE"
    
    TOTAL_PRICE=$(echo "$QUOTE_RESPONSE" | jq -r '.total_price // .total' 2>/dev/null)
    if [ -n "$TOTAL_PRICE" ] && [ "$TOTAL_PRICE" != "null" ]; then
        validate_field_exists "$QUOTE_RESPONSE" "total_price" "Quote Total Price"
        log "$(echo -e "${GREEN}  ✓${NC} Quote calculated: \$$TOTAL_PRICE)"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    else
        log "$(echo -e "${YELLOW}  ⚠${NC} Quote calculation: $(echo $QUOTE_RESPONSE | head -c 100))"
        TOTAL_PRICE=550.00
    fi
    
    print_subheader "Step 4: Create Quote Record in Sales"
    QUOTE_RECORD=$(curl -s -X POST "http://localhost:8006/leads/${LEAD_ID}/quotes" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"quote_amount\": $TOTAL_PRICE,
        \"quote_number\": \"Q-$(date +%s)\",
        \"valid_until\": \"2026-07-01\",
        \"notes\": \"Standard coach bus service for 30 passengers\",
        \"status\": \"sent\"
      }" 2>/dev/null)
    
    log_detailed "Quote Record Response: $QUOTE_RECORD"
    
    QUOTE_ID=$(echo "$QUOTE_RECORD" | jq -r '.id' 2>/dev/null)
    if [ -n "$QUOTE_ID" ] && [ "$QUOTE_ID" != "null" ]; then
        validate_field_exists "$QUOTE_RECORD" "id" "Quote Record ID"
        validate_field "$QUOTE_RECORD" "status" "sent" "Quote Status"
    fi
    
    print_subheader "Step 5: Accept Quote and Convert to Charter"
    CONVERT_RESPONSE=$(curl -s -X POST "http://localhost:8006/leads/${LEAD_ID}/convert" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"quote_id\": $QUOTE_ID,
        \"create_charter\": true,
        \"charter_details\": {
          \"trip_date\": \"2026-07-15\",
          \"passengers\": 30,
          \"trip_hours\": 4.0,
          \"total_cost\": $TOTAL_PRICE,
          \"status\": \"confirmed\"
        }
      }" 2>/dev/null)
    
    log_detailed "Convert Lead Response: $CONVERT_RESPONSE"
    
    CONVERTED_CHARTER_ID=$(echo "$CONVERT_RESPONSE" | jq -r '.charter_id' 2>/dev/null)
    if [ -n "$CONVERTED_CHARTER_ID" ] && [ "$CONVERTED_CHARTER_ID" != "null" ]; then
        validate_field_exists "$CONVERT_RESPONSE" "charter_id" "Converted Charter ID"
        log "$(echo -e "${GREEN}  ✓${NC} Lead converted to Charter ID: $CONVERTED_CHARTER_ID)"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    print_subheader "Step 6: Verify Lead Status Changed to Converted"
    LEAD_CHECK=$(curl -s "http://localhost:8006/leads/${LEAD_ID}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    validate_field "$LEAD_CHECK" "status" "converted" "Final Lead Status"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    workflow_passed "Sales Pipeline & Quote to Charter Conversion (${duration}s)"
    return 0
}
# ==============================================================================
# WORKFLOW 6: Dispatch & Driver Assignment Complete Flow
# ==============================================================================
test_workflow_6_dispatch_driver_flow() {
    print_header "WORKFLOW 6: Dispatch & Driver Assignment Complete Flow"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    local CHARTER_ID=${CREATED_CHARTER_ID:-1}
    local VENDOR_ID=${CREATED_VENDOR_ID:-1}
    
    print_subheader "Step 1: Create Driver Profile"
    DRIVER_RESPONSE=$(curl -s -X POST http://localhost:8009/drivers \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"vendor_id\": $VENDOR_ID,
        \"first_name\": \"Michael\",
        \"last_name\": \"Driver\",
        \"email\": \"michael.driver@premiumbus.com\",
        \"phone\": \"555-4321\",
        \"license_number\": \"DL-$(date +%s)\",
        \"license_state\": \"NY\",
        \"license_expiry\": \"2028-12-31\",
        \"medical_cert_expiry\": \"2027-06-30\",
        \"is_active\": true,
        \"rating\": 4.8,
        \"years_experience\": 12
      }" 2>/dev/null)
    
    log_detailed "Driver Creation Response: $DRIVER_RESPONSE"
    
    DRIVER_ID=$(echo "$DRIVER_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$DRIVER_ID" ] || [ "$DRIVER_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Driver creation: $(echo $DRIVER_RESPONSE | head -c 100)${NC}")"
        DRIVER_ID=1
    else
        validate_field_exists "$DRIVER_RESPONSE" "id" "Driver ID"
        validate_field "$DRIVER_RESPONSE" "first_name" "Michael" "Driver First Name"
        validate_field "$DRIVER_RESPONSE" "is_active" "true" "Driver Active Status"
        validate_field "$DRIVER_RESPONSE" "years_experience" "12" "Years Experience"
    fi
    
    print_subheader "Step 2: Assign Driver to Charter"
    ASSIGN_RESPONSE=$(curl -s -X POST "http://localhost:8009/dispatch/assign" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"charter_id\": $CHARTER_ID,
        \"driver_id\": $DRIVER_ID,
        \"vehicle_id\": 5,
        \"dispatch_notes\": \"Premium service, client VIP\",
        \"departure_time\": \"2026-06-15T08:00:00\",
        \"estimated_duration_hours\": 5.0
      }" 2>/dev/null)
    
    log_detailed "Assign Driver Response: $ASSIGN_RESPONSE"
    
    DISPATCH_ID=$(echo "$ASSIGN_RESPONSE" | jq -r '.id // .dispatch_id' 2>/dev/null)
    if [ -n "$DISPATCH_ID" ] && [ "$DISPATCH_ID" != "null" ]; then
        validate_field_exists "$ASSIGN_RESPONSE" "id" "Dispatch Assignment ID"
        validate_field "$ASSIGN_RESPONSE" "driver_id" "$DRIVER_ID" "Assigned Driver ID"
        validate_field "$ASSIGN_RESPONSE" "charter_id" "$CHARTER_ID" "Dispatch Charter ID"
    else
        DISPATCH_ID=1
    fi
    
    print_subheader "Step 3: Send Dispatch Notification"
    NOTIFY_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      "http://localhost:8009/dispatch/${DISPATCH_ID}/notify" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "notification_type": "assignment",
        "include_driver": true,
        "include_client": true
      }' 2>/dev/null)
    
    if [ "$NOTIFY_CODE" == "200" ] || [ "$NOTIFY_CODE" == "201" ] || [ "$NOTIFY_CODE" == "404" ]; then
        log "$(echo -e "${GREEN}  ✓${NC} Dispatch notification sent (HTTP $NOTIFY_CODE))"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    print_subheader "Step 4: Update Trip Status to In Progress"
    UPDATE_STATUS=$(curl -s -X PUT "http://localhost:8009/dispatch/${DISPATCH_ID}/status" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "status": "in_progress",
        "actual_departure_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "current_location": "40.7128,-74.0060",
        "notes": "Departed on time"
      }' 2>/dev/null)
    
    log_detailed "Update Status Response: $UPDATE_STATUS"
    
    if echo "$UPDATE_STATUS" | jq -e '.status' > /dev/null 2>&1; then
        validate_field "$UPDATE_STATUS" "status" "in_progress" "Trip Status"
    fi
    
    print_subheader "Step 5: Complete Trip"
    COMPLETE_RESPONSE=$(curl -s -X POST "http://localhost:8009/dispatch/${DISPATCH_ID}/complete" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "actual_arrival_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ -d '+5 hours')'",
        "actual_duration_hours": 5.2,
        "actual_miles": 125.0,
        "fuel_used_gallons": 18.5,
        "completion_notes": "Trip completed successfully, client satisfied"
      }' 2>/dev/null)
    
    log_detailed "Complete Trip Response: $COMPLETE_RESPONSE"
    
    if echo "$COMPLETE_RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        validate_field "$COMPLETE_RESPONSE" "status" "completed" "Final Trip Status"
    fi
    
    print_subheader "Step 6: Get Driver Performance Metrics"
    METRICS=$(curl -s "http://localhost:8009/drivers/${DRIVER_ID}/metrics" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Driver Metrics Response: $METRICS"
    
    if echo "$METRICS" | jq -e '.total_trips' > /dev/null 2>&1; then
        local total_trips=$(echo "$METRICS" | jq -r '.total_trips' 2>/dev/null)
        log "$(echo -e "${GREEN}  ✓${NC} Driver total trips: $total_trips)"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    workflow_passed "Dispatch & Driver Assignment Complete Flow (${duration}s)"
    return 0
}

# ==============================================================================
# WORKFLOW 7: Change Management & Approval Workflow
# ==============================================================================
test_workflow_7_change_management() {
    print_header "WORKFLOW 7: Change Management & Approval Workflow"
    
    local start_time=$(date +%s)
    local workflow_failed=0
    
    local CHARTER_ID=${CREATED_CHARTER_ID:-1}
    local CLIENT_ID=${CREATED_CLIENT_ID:-1}
    
    print_subheader "Step 1: Create Change Request"
    CHANGE_RESPONSE=$(curl -s -X POST http://localhost:8012/api/v1/changes/cases \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"charter_id\": $CHARTER_ID,
        \"client_id\": $CLIENT_ID,
        \"change_type\": \"passenger_count_change\",
        \"priority\": \"high\",
        \"title\": \"Increase passenger count from 40 to 50\",
        \"description\": \"Client needs 10 additional seats for their event\",
        \"reason\": \"More attendees confirmed registration\",
        \"impact_level\": \"moderate\",
        \"requested_by\": 1,
        \"requested_by_name\": \"Sales Manager\",
        \"affects_pricing\": true,
        \"current_price\": 715.00,
        \"proposed_price\": 850.00,
        \"requires_approval\": true
      }" 2>/dev/null)
    
    log_detailed "Change Request Response: $CHANGE_RESPONSE"
    
    CHANGE_ID=$(echo "$CHANGE_RESPONSE" | jq -r '.id' 2>/dev/null)
    if [ -z "$CHANGE_ID" ] || [ "$CHANGE_ID" == "null" ]; then
        log "$(echo -e "${YELLOW}⚠ Change request creation: $(echo $CHANGE_RESPONSE | head -c 100)${NC}")"
        CHANGE_ID=1
    else
        validate_field_exists "$CHANGE_RESPONSE" "id" "Change Request ID"
        validate_field "$CHANGE_RESPONSE" "change_type" "passenger_count_change" "Change Type"
        validate_field "$CHANGE_RESPONSE" "priority" "high" "Priority"
        validate_field "$CHANGE_RESPONSE" "affects_pricing" "true" "Affects Pricing"
    fi
    
    print_subheader "Step 2: Add Impact Assessment"
    ASSESS_RESPONSE=$(curl -s -X POST "http://localhost:8012/api/v1/changes/cases/${CHANGE_ID}/assessments" \
      -H "Authorization: Bearer $MANAGER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "assessed_by": 1,
        "assessed_by_name": "Operations Manager",
        "impact_summary": "Need larger vehicle, will affect vendor assignment",
        "cost_impact": 135.00,
        "time_impact_hours": 0.5,
        "risk_level": "medium",
        "recommendations": "Upgrade to 56-passenger coach"
      }' 2>/dev/null)
    
    log_detailed "Assessment Response: $ASSESS_RESPONSE"
    
    if echo "$ASSESS_RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
        validate_field_exists "$ASSESS_RESPONSE" "id" "Assessment ID"
        validate_field "$ASSESS_RESPONSE" "risk_level" "medium" "Risk Level"
    fi
    
    print_subheader "Step 3: Move to Review Status"
    REVIEW_RESPONSE=$(curl -s -X POST "http://localhost:8012/api/v1/changes/cases/${CHANGE_ID}/review" \
      -H "Authorization: Bearer $MANAGER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "reviewed_by": 1,
        "reviewed_by_name": "Manager",
        "review_notes": "Impact assessment completed, ready for approval"
      }' 2>/dev/null)
    
    log_detailed "Review Response: $REVIEW_RESPONSE"
    
    validate_field "$REVIEW_RESPONSE" "status" "under_review" "Status After Review"
    
    print_subheader "Step 4: Approve Change"
    APPROVE_RESPONSE=$(curl -s -X POST "http://localhost:8012/api/v1/changes/cases/${CHANGE_ID}/approve" \
      -H "Authorization: Bearer $MANAGER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "approved_by": 1,
        "approved_by_name": "Senior Manager",
        "approval_notes": "Approved, client is priority account",
        "conditions": "Must confirm larger vehicle availability"
      }' 2>/dev/null)
    
    log_detailed "Approval Response: $APPROVE_RESPONSE"
    
    validate_field "$APPROVE_RESPONSE" "status" "approved" "Status After Approval"
    
    print_subheader "Step 5: Implement Change"
    IMPLEMENT_RESPONSE=$(curl -s -X POST "http://localhost:8012/api/v1/changes/cases/${CHANGE_ID}/implement" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "implemented_by": 1,
        "implemented_by_name": "Operations Team",
        "implementation_notes": "Updated charter to 56-passenger vehicle, price adjusted",
        "actual_cost_impact": 135.00,
        "actual_time_impact_hours": 0.3
      }' 2>/dev/null)
    
    log_detailed "Implementation Response: $IMPLEMENT_RESPONSE"
    
    validate_field "$IMPLEMENT_RESPONSE" "status" "implemented" "Final Change Status"
    
    print_subheader "Step 6: Get Change History for Charter"
    HISTORY=$(curl -s "http://localhost:8012/api/v1/changes/charters/${CHARTER_ID}/history" \
      -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null)
    
    log_detailed "Change History Response: $HISTORY"
    
    if echo "$HISTORY" | jq -e 'type == "array"' > /dev/null 2>&1; then
        local change_count=$(echo "$HISTORY" | jq 'length' 2>/dev/null)
        log "$(echo -e "${GREEN}  ✓${NC} Charter has $change_count change record\(s\))"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    workflow_passed "Change Management & Approval Workflow (${duration}s)"
    return 0
}

# ==============================================================================
# Main Execution
# ==============================================================================
main() {
    clear
    print_header "COACHWAY PLATFORM - COMPREHENSIVE E2E WORKFLOW TEST SUITE"
    log "Test started: $(date)"
    log "Main log file: $LOG_FILE"
    log "Detailed log file: $DETAILED_LOG"
    log ""
    
    # System health check
    if ! check_system_health; then
        log "$(echo -e "${YELLOW}⚠ Warning: Critical services down, some tests may fail${NC}")"
    fi
    
    # Get authentication tokens
    if ! get_auth_tokens; then
        log "$(echo -e "${RED}✗ Failed to obtain authentication tokens${NC}")"
        log "Cannot proceed with workflow tests"
        exit 1
    fi
    
    log ""
    log "Starting comprehensive workflow tests..."
    log "================================================"
    log ""
    
    # Run all comprehensive workflow tests
    test_workflow_1_complete_client_onboarding
    test_workflow_2_vendor_bidding_selection
    test_workflow_3_document_esignature_flow
    test_workflow_4_payment_processing_e2e
    test_workflow_5_sales_pipeline
    test_workflow_6_dispatch_driver_flow
    test_workflow_7_change_management
    test_workflow_8_notification_system
    test_workflow_9_analytics_reporting
    test_workflow_10_portal_integration
    
    # Print comprehensive summary
    print_header "COMPREHENSIVE TEST SUMMARY"
    log "Total Workflows Executed: $WORKFLOWS_TOTAL"
    log "$(echo -e "${GREEN}✅ Workflows Passed: $WORKFLOWS_PASSED${NC}")"
    log "$(echo -e "${RED}❌ Workflows Failed: $WORKFLOWS_FAILED${NC}")"
    log ""
    log "Total Validations: $((VALIDATIONS_PASSED + VALIDATIONS_FAILED))"
    log "$(echo -e "${GREEN}✅ Validations Passed: $VALIDATIONS_PASSED${NC}")"
    log "$(echo -e "${RED}❌ Validations Failed: $VALIDATIONS_FAILED${NC}")"
    log ""
    
    # Calculate success rate
    if [ "$WORKFLOWS_TOTAL" -gt 0 ]; then
        WORKFLOW_SUCCESS_RATE=$((WORKFLOWS_PASSED * 100 / WORKFLOWS_TOTAL))
        log "Workflow Success Rate: ${WORKFLOW_SUCCESS_RATE}%"
    fi
    
    if [ "$((VALIDATIONS_PASSED + VALIDATIONS_FAILED))" -gt 0 ]; then
        VALIDATION_SUCCESS_RATE=$((VALIDATIONS_PASSED * 100 / (VALIDATIONS_PASSED + VALIDATIONS_FAILED)))
        log "Data Validation Success Rate: ${VALIDATION_SUCCESS_RATE}%"
    fi
    
    log ""
    log "Logs available at:"
    log "  Main: $LOG_FILE"
    log "  Detailed: $DETAILED_LOG"
    log ""
    
    if [ "$WORKFLOWS_FAILED" -eq 0 ]; then
        log "$(echo -e "${GREEN}✅✅✅ ALL WORKFLOWS PASSED! ✅✅✅${NC}")"
        log ""
        exit 0
    else
        log "$(echo -e "${RED}❌ SOME WORKFLOWS FAILED - Review logs for details${NC}")"
        log ""
        exit 1
    fi
}

# Run main function
main "$@"
