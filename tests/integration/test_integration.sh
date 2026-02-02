#!/bin/bash
# Simple integration test script for CoachWay platform
# Tests all services are running and basic workflows

echo "======================================================================"
echo "CoachWay Platform - Integration Tests"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED_TESTS=0
PASSED_TESTS=0

# Test helper function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $name"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $name (Expected $expected_code, got $http_code)"
        echo "   Response: $body"
        ((FAILED_TESTS++))
        return 1
    fi
}

echo "Test 1: Service Health Checks"
echo "----------------------------------------------------------------------"
test_endpoint "Sales Service Health" "http://localhost:8080/api/v1/sales/health"
test_endpoint "Pricing Service Health" "http://localhost:8080/api/v1/pricing/health"
test_endpoint "Vendor Service Health" "http://localhost:8080/api/v1/vendor/health"
test_endpoint "Portal Service Health" "http://localhost:8080/api/v1/portal/health"
test_endpoint "Change Management Health" "http://localhost:8080/api/v1/changes/health"
echo ""

echo "Test 2: Sales Service - Lead Management"
echo "----------------------------------------------------------------------"
# Create a lead
LEAD_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/sales/api/v1/leads" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User",
    "email": "test.'$(date +%s)'@example.com",
    "phone": "555-0100",
    "company_name": "Test Corp",
    "trip_details": "Corporate event",
    "estimated_passengers": 45,
    "source": "web"
  }')

if echo "$LEAD_RESPONSE" | grep -q '"id"'; then
    LEAD_ID=$(echo "$LEAD_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    echo -e "${GREEN}✅ PASS${NC}: Lead created (ID: $LEAD_ID)"
    ((PASSED_TESTS++))
    
    # Get the lead
    if curl -s "http://localhost:8080/api/v1/sales/api/v1/leads/$LEAD_ID" | grep -q '"id"'; then
        echo -e "${GREEN}✅ PASS${NC}: Lead retrieved successfully"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ FAIL${NC}: Failed to retrieve lead"
        ((FAILED_TESTS++))
    fi
else
    echo -e "${RED}❌ FAIL${NC}: Failed to create lead"
    echo "   Response: $LEAD_RESPONSE"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 3: Pricing Service - Calculation"
echo "----------------------------------------------------------------------"
PRICING_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/pricing/calculations" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 1,
    "base_price": 2500.00,
    "distance_miles": 150.0,
    "duration_hours": 4.0,
    "passenger_count": 45,
    "vehicle_type": "motor_coach"
  }')

if echo "$PRICING_RESPONSE" | grep -q '"id"'; then
    PRICING_ID=$(echo "$PRICING_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)
    FINAL_PRICE=$(echo "$PRICING_RESPONSE" | grep -o '"final_price":[0-9.]*' | grep -o '[0-9.]*')
    echo -e "${GREEN}✅ PASS${NC}: Pricing calculated (ID: $PRICING_ID, Price: \$$FINAL_PRICE)"
    ((PASSED_TESTS++))
else
    echo -e "${RED}❌ FAIL${NC}: Failed to create pricing"
    echo "   Response: $PRICING_RESPONSE"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 4: Vendor Service - Opportunity and Bidding"
echo "----------------------------------------------------------------------"
OPP_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/vendor/opportunities" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 1,
    "title": "Integration Test Opportunity",
    "description": "Test opportunity for integration testing",
    "pickup_location": "Downtown",
    "dropoff_location": "Airport",
    "passenger_count": 45,
    "vehicle_type_required": "motor_coach",
    "estimated_budget": 3000.00
  }')

if echo "$OPP_RESPONSE" | grep -q '"id"'; then
    OPP_ID=$(echo "$OPP_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)
    echo -e "${GREEN}✅ PASS${NC}: Opportunity created (ID: $OPP_ID)"
    ((PASSED_TESTS++))
    
    # Submit a bid
    BID_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/vendor/bids" \
      -H "Content-Type: application/json" \
      -d '{
        "opportunity_id": '$OPP_ID',
        "vendor_id": 1,
        "bid_amount": 2800.00,
        "proposal": "We can provide excellent service",
        "vehicle_id": 1
      }')
    
    if echo "$BID_RESPONSE" | grep -q '"id"'; then
        BID_ID=$(echo "$BID_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)
        echo -e "${GREEN}✅ PASS${NC}: Bid submitted (ID: $BID_ID)"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ FAIL${NC}: Failed to submit bid"
        echo "   Response: $BID_RESPONSE"
        ((FAILED_TESTS++))
    fi
else
    echo -e "${RED}❌ FAIL${NC}: Failed to create opportunity"
    echo "   Response: $OPP_RESPONSE"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 5: Portal Service - Preferences and Activity"
echo "----------------------------------------------------------------------"
PREF_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/portal/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "portal_type": "client",
    "notification_email": true,
    "theme": "light"
  }')

if echo "$PREF_RESPONSE" | grep -q '"user_id"'; then
    echo -e "${GREEN}✅ PASS${NC}: Preferences created/updated"
    ((PASSED_TESTS++))
else
    echo -e "${RED}❌ FAIL${NC}: Failed to set preferences"
    echo "   Response: $PREF_RESPONSE"
    ((FAILED_TESTS++))
fi

# Log activity
ACTIVITY_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/portal/activity" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "activity_type": "test_activity",
    "description": "Integration test activity"
  }')

if echo "$ACTIVITY_RESPONSE" | grep -q '"id"'; then
    echo -e "${GREEN}✅ PASS${NC}: Activity logged"
    ((PASSED_TESTS++))
else
    echo -e "${RED}❌ FAIL${NC}: Failed to log activity"
    echo "   Response: $ACTIVITY_RESPONSE"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 6: Change Management - Complete Workflow"
echo "----------------------------------------------------------------------"
CHANGE_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/changes/cases" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": 1,
    "client_id": 1,
    "change_type": "passenger_count_change",
    "priority": "medium",
    "title": "Integration Test Change",
    "description": "Testing change management workflow",
    "reason": "Integration testing",
    "impact_level": "minimal",
    "requested_by": 1,
    "requested_by_name": "Test User"
  }')

if echo "$CHANGE_RESPONSE" | grep -q '"id"'; then
    CHANGE_ID=$(echo "$CHANGE_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)
    CASE_NUMBER=$(echo "$CHANGE_RESPONSE" | grep -o '"case_number":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ PASS${NC}: Change case created (ID: $CHANGE_ID, Number: $CASE_NUMBER)"
    ((PASSED_TESTS++))
    
    # Move to review
    REVIEW_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/changes/cases/$CHANGE_ID/review?reviewed_by=2&reviewed_by_name=Reviewer")
    if echo "$REVIEW_RESPONSE" | grep -q '"status":"under_review"'; then
        echo -e "${GREEN}✅ PASS${NC}: Change moved to review"
        ((PASSED_TESTS++))
        
        # Approve
        APPROVE_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/changes/cases/$CHANGE_ID/approve" \
          -H "Content-Type: application/json" \
          -d '{
            "approved_by": 3,
            "approved_by_name": "Manager",
            "approval_notes": "Approved for testing"
          }')
        
        if echo "$APPROVE_RESPONSE" | grep -q '"status":"approved"'; then
            echo -e "${GREEN}✅ PASS${NC}: Change approved"
            ((PASSED_TESTS++))
            
            # Get history
            HISTORY_RESPONSE=$(curl -s "http://localhost:8080/api/v1/changes/cases/$CHANGE_ID/history")
            if echo "$HISTORY_RESPONSE" | grep -q '"action":"created"'; then
                echo -e "${GREEN}✅ PASS${NC}: Audit trail retrieved"
                ((PASSED_TESTS++))
            else
                echo -e "${RED}❌ FAIL${NC}: Failed to retrieve audit trail"
                ((FAILED_TESTS++))
            fi
        else
            echo -e "${RED}❌ FAIL${NC}: Failed to approve change"
            ((FAILED_TESTS++))
        fi
    else
        echo -e "${RED}❌ FAIL${NC}: Failed to move to review"
        ((FAILED_TESTS++))
    fi
else
    echo -e "${RED}❌ FAIL${NC}: Failed to create change case"
    echo "   Response: $CHANGE_RESPONSE"
    ((FAILED_TESTS++))
fi
echo ""

echo "Test 7: Performance - Concurrent Requests"
echo "----------------------------------------------------------------------"
START_TIME=$(date +%s%N)
for i in {1..20}; do
    curl -s "http://localhost:8080/api/v1/sales/health" > /dev/null &
done
wait
END_TIME=$(date +%s%N)
ELAPSED=$((($END_TIME - $START_TIME) / 1000000))

if [ $ELAPSED -lt 2000 ]; then
    echo -e "${GREEN}✅ PASS${NC}: 20 concurrent requests completed in ${ELAPSED}ms"
    ((PASSED_TESTS++))
else
    echo -e "${YELLOW}⚠ WARN${NC}: 20 concurrent requests took ${ELAPSED}ms (acceptable but slow)"
    ((PASSED_TESTS++))
fi
echo ""

# Summary
echo "======================================================================"
echo "Test Summary"
echo "======================================================================"
echo -e "Total Tests: $((PASSED_TESTS + FAILED_TESTS))"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "======================================================================"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "======================================================================"
    exit 1
fi
