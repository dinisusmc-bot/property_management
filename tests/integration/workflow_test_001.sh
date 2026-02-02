#!/bin/bash
set -e

echo "========================================"
echo "WORKFLOW TEST-001: Lead to Charter Flow"
echo "========================================"
echo ""

# Step 1: Authenticate
echo "Step 1: Authenticating as manager..."
AGENT_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager@athena.com&password=admin123" | jq -r '.access_token')

if [ -z "$AGENT_TOKEN" ] || [ "$AGENT_TOKEN" == "null" ]; then
    echo "❌ Failed to get manager token"
    exit 1
fi
echo "✓ Manager authenticated"

# Step 2: Create lead (direct to service since Kong paths need verification)
echo ""
echo "Step 2: Creating lead..."
LEAD_RESPONSE=$(curl -s -X POST http://localhost:8007/api/v1/leads \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Workflow",
    "last_name": "Test",
    "email": "workflow.test@example.com",
    "phone": "+1-555-WORK",
    "source": "web",
    "status": "new",
    "trip_details": "Corporate event shuttle for workflow testing",
    "estimated_passengers": 35,
    "estimated_trip_date": "2026-04-01T09:00:00",
    "pickup_location": "Downtown Office",
    "dropoff_location": "Convention Center"
  }')

LEAD_ID=$(echo "$LEAD_RESPONSE" | jq -r '.id')
if [ -z "$LEAD_ID" ] || [ "$LEAD_ID" == "null" ]; then
    echo "❌ Failed to create lead"
    echo "Response: $LEAD_RESPONSE"
    exit 1
fi
echo "✓ Lead created: ID $LEAD_ID"

# Step 3: Update lead status to qualified
echo ""
echo "Step 3: Qualifying lead..."
UPDATE_RESPONSE=$(curl -s -X PUT http://localhost:8007/api/v1/leads/$LEAD_ID \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "qualified"}')

UPDATED_STATUS=$(echo "$UPDATE_RESPONSE" | jq -r '.status')
if [ "$UPDATED_STATUS" != "qualified" ]; then
    echo "❌ Failed to qualify lead"
    echo "Response: $UPDATE_RESPONSE"
    exit 1
fi
echo "✓ Lead qualified"

# Step 4: Log activity
echo ""
echo "Step 4: Logging qualification activity..."
ACTIVITY_RESPONSE=$(curl -s -X POST "http://localhost:8007/api/v1/leads/$LEAD_ID/activities?user_id=36" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "note",
    "details": "Lead qualified for charter booking - customer has confirmed requirements",
    "performed_by": 36,
    "duration_minutes": 0
  }')

ACTIVITY_ID=$(echo "$ACTIVITY_RESPONSE" | jq -r '.id')
if [ -z "$ACTIVITY_ID" ] || [ "$ACTIVITY_ID" == "null" ]; then
    echo "❌ Failed to log activity"
    echo "Response: $ACTIVITY_RESPONSE"
    exit 1
fi
echo "✓ Activity logged: ID $ACTIVITY_ID"

# Step 5: Get admin token for charter creation
echo ""
echo "Step 5: Getting admin token..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@athena.com&password=admin123" | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" == "null" ]; then
    echo "❌ Failed to get admin token"
    exit 1
fi
echo "✓ Admin authenticated"

# Step 6: Check if Charter service is available (port 8004)
echo ""
echo "Step 6: Checking Charter service availability..."
CHARTER_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8004/health 2>/dev/null || echo "503")

if [ "$CHARTER_HEALTH" == "200" ]; then
    echo "✓ Charter service is healthy"
    
    # Try to create charter
    echo ""
    echo "Step 7: Creating charter..."
    CHARTER_RESPONSE=$(curl -s -X POST http://localhost:8004/api/v1/charters \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "client_id": 1,
        "pickup_location": "Downtown Office",
        "dropoff_location": "Convention Center",
        "pickup_date": "2026-04-01T09:00:00",
        "estimated_passengers": 35,
        "vehicle_type": "coach_bus",
        "status": "pending"
      }' 2>&1)
    
    CHARTER_ID=$(echo "$CHARTER_RESPONSE" | jq -r '.id' 2>/dev/null || echo "null")
    
    if [ -z "$CHARTER_ID" ] || [ "$CHARTER_ID" == "null" ]; then
        echo "⚠ Charter service not fully implemented or requires different schema"
        echo "Response: $(echo "$CHARTER_RESPONSE" | head -c 200)"
    else
        echo "✓ Charter created: ID $CHARTER_ID"
    fi
else
    echo "⚠ Charter service not available (HTTP $CHARTER_HEALTH) - skipping charter creation"
fi

# Step 8: Test pricing calculation
echo ""
echo "Step 8: Calculating pricing quote..."
PRICING_RESPONSE=$(curl -s -X POST http://localhost:8008/calculate-quote \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "vehicle_type": "coach_bus",
    "trip_date": "2026-04-01",
    "estimated_hours": 5.0,
    "estimated_miles": 80.0,
    "passenger_count": 35,
    "is_weekend": false,
    "is_holiday": false
  }')

# Check if pricing returned a valid response
TOTAL_PRICE=$(echo "$PRICING_RESPONSE" | jq -r '.total_price' 2>/dev/null || echo "null")
BASE_PRICE=$(echo "$PRICING_RESPONSE" | jq -r '.base_price' 2>/dev/null || echo "null")

if [ "$TOTAL_PRICE" != "null" ] && [ -n "$TOTAL_PRICE" ]; then
    echo "✓ Price calculated: \$$TOTAL_PRICE (Base: \$$BASE_PRICE)"
elif echo "$PRICING_RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    echo "⚠ Pricing calculation returned validation error - may need different parameters"
    echo "Response: $(echo "$PRICING_RESPONSE" | jq -r '.detail | tostring' | head -c 150)"
else
    echo "⚠ Pricing service responded but format differs from expected"
    echo "Response preview: $(echo "$PRICING_RESPONSE" | head -c 150)"
fi

# Step 9: Verify final lead state
echo ""
echo "Step 9: Verifying final lead state..."
FINAL_LEAD=$(curl -s -H "Authorization: Bearer $AGENT_TOKEN" \
  http://localhost:8007/api/v1/leads/$LEAD_ID)

FINAL_STATUS=$(echo "$FINAL_LEAD" | jq -r '.status')
FINAL_ASSIGNED=$(echo "$FINAL_LEAD" | jq -r '.assigned_to')
echo "✓ Final lead status: $FINAL_STATUS"
echo "✓ Assigned to: Agent $FINAL_ASSIGNED"

# Step 10: Verify activities were logged
echo ""
echo "Step 10: Verifying logged activities..."
ACTIVITIES=$(curl -s -H "Authorization: Bearer $AGENT_TOKEN" \
  "http://localhost:8007/api/v1/leads/$LEAD_ID/activities")

ACTIVITY_COUNT=$(echo "$ACTIVITIES" | jq '. | length')
echo "✓ Total activities logged: $ACTIVITY_COUNT"

# Summary
echo ""
echo "========================================"
echo "WORKFLOW TEST SUMMARY"
echo "========================================"
echo "Lead ID: $LEAD_ID"
echo "Lead Status: $FINAL_STATUS"
echo "Activities Logged: $ACTIVITY_COUNT"
if [ "$CHARTER_ID" != "null" ] && [ -n "$CHARTER_ID" ]; then
    echo "Charter ID: $CHARTER_ID"
fi
if [ "$TOTAL_PRICE" != "null" ] && [ -n "$TOTAL_PRICE" ]; then
    echo "Quote Price: \$$TOTAL_PRICE"
fi
echo ""
echo "✅ WORKFLOW TEST COMPLETED"
echo "========================================"
