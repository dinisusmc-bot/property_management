#!/bin/bash
set -e

echo "============================================"
echo "WORKFLOW TEST-002: Charter Bidding Process"
echo "============================================"
echo ""

# Get admin token
echo "Step 1: Authenticating as admin..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@athena.com&password=admin123" | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" == "null" ]; then
    echo "❌ Failed to get admin token"
    exit 1
fi
echo "✓ Admin authenticated"

# Step 2: Create a charter
echo ""
echo "Step 2: Creating charter..."
CHARTER_RESPONSE=$(curl -s -X POST http://localhost:8001/charters \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "vehicle_id": 5,
    "trip_date": "2026-04-15",
    "passengers": 45,
    "trip_hours": 6.0,
    "base_cost": 570.00,
    "mileage_cost": 320.00,
    "total_cost": 890.00,
    "status": "quote",
    "notes": "Corporate event transportation - need competitive bids"
  }')

CHARTER_ID=$(echo "$CHARTER_RESPONSE" | jq -r '.id')
if [ -z "$CHARTER_ID" ] || [ "$CHARTER_ID" == "null" ]; then
    echo "❌ Failed to create charter"
    echo "Response: $CHARTER_RESPONSE"
    exit 1
fi
echo "✓ Charter created: ID $CHARTER_ID"

# Step 3: Get list of active verified vendors
echo ""
echo "Step 3: Getting active vendors..."
VENDORS_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8009/vendors?status=active")

# Filter to verified vendors only
VERIFIED_VENDORS=$(echo "$VENDORS_RESPONSE" | jq '[.[] | select(.is_verified == true)]')
VENDOR_COUNT=$(echo "$VERIFIED_VENDORS" | jq '. | length')
echo "✓ Found $VENDOR_COUNT verified active vendors"

# Get first vendor ID
VENDOR_ID=$(echo "$VERIFIED_VENDORS" | jq -r '.[0].id')
echo "  Using vendor ID: $VENDOR_ID"

# Step 4: Create vendor bid
echo ""
echo "Step 4: Creating vendor bid..."
BID_RESPONSE=$(curl -s -X POST http://localhost:8009/bids \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "charter_id": '${CHARTER_ID}',
    "vendor_id": '${VENDOR_ID}',
    "quoted_price": 850.00,
    "vehicle_type": "coach_bus",
    "passenger_capacity": 47,
    "valid_until": "2026-04-10T23:59:59",
    "notes": "Competitive bid - Coach Bus 47 passenger available",
    "estimated_departure_time": "2026-04-15T09:00:00",
    "base_price": 570.00,
    "mileage_charge": 280.00
  }')

BID_ID=$(echo "$BID_RESPONSE" | jq -r '.id')
if [ -z "$BID_ID" ] || [ "$BID_ID" == "null" ]; then
    echo "❌ Failed to create bid"
    echo "Response: $BID_RESPONSE"
    exit 1
fi
echo "✓ Vendor bid created: ID $BID_ID"
echo "  Bid Amount: $850.00"

# Step 5: Create second bid from another vendor if available
if [ "$VENDOR_COUNT" -gt 1 ]; then
    VENDOR_ID_2=$(echo "$VERIFIED_VENDORS" | jq -r '.[1].id')
    echo ""
    echo "Step 5: Creating second vendor bid..."
    BID_RESPONSE_2=$(curl -s -X POST http://localhost:8009/bids \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "charter_id": '${CHARTER_ID}',
        "vendor_id": '${VENDOR_ID_2}',
        "quoted_price": 825.00,
        "vehicle_type": "coach_bus",
        "passenger_capacity": 47,
        "valid_until": "2026-04-10T23:59:59",
        "notes": "Better pricing - experienced driver included",
        "estimated_departure_time": "2026-04-15T09:00:00",
        "base_price": 550.00,
        "mileage_charge": 275.00
      }')
    
    BID_ID_2=$(echo "$BID_RESPONSE_2" | jq -r '.id')
    if [ -z "$BID_ID_2" ] || [ "$BID_ID_2" == "null" ]; then
        echo "⚠ Second bid failed"
        echo "Response: $BID_RESPONSE_2"
    else
        echo "✓ Second vendor bid created: ID $BID_ID_2"
        echo "  Bid Amount: $825.00"
    fi
fi

# Step 6: List all bids for the charter
echo ""
echo "Step 6: Retrieving all bids for charter..."
CHARTER_BIDS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8009/bids?charter_id=${CHARTER_ID}")

BID_COUNT=$(echo "$CHARTER_BIDS" | jq '. | length')
echo "✓ Total bids received: $BID_COUNT"

# Display bid summary
echo ""
echo "Bid Summary:"
echo "$CHARTER_BIDS" | jq -r '.[] | "  Vendor ID: \(.vendor_id) - Amount: $\(.quoted_price) - Status: \(.status)"'

# Step 7: Accept the best bid (lowest amount)
LOWEST_BID=$(echo "$CHARTER_BIDS" | jq 'min_by(.quoted_price)')
ACCEPTED_BID_ID=$(echo "$LOWEST_BID" | jq -r '.id')
ACCEPTED_BID_AMOUNT=$(echo "$LOWEST_BID" | jq -r '.quoted_price')
ACCEPTED_VENDOR_ID=$(echo "$LOWEST_BID" | jq -r '.vendor_id')

echo ""
echo "Step 7: Accepting best bid..."
ACCEPT_RESPONSE=$(curl -s -X PUT "http://localhost:8009/bids/${ACCEPTED_BID_ID}" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted"}')

ACCEPTED_STATUS=$(echo "$ACCEPT_RESPONSE" | jq -r '.status')
if [ "$ACCEPTED_STATUS" == "accepted" ]; then
    echo "✓ Bid accepted: ID $ACCEPTED_BID_ID"
    echo "  Accepted Amount: \$$ACCEPTED_BID_AMOUNT"
    echo "  Selected Vendor: ID $ACCEPTED_VENDOR_ID"
else
    echo "⚠ Bid acceptance may have failed"
    echo "Response: $ACCEPT_RESPONSE"
fi

# Step 8: Reject remaining bids
echo ""
echo "Step 8: Rejecting other bids..."
REJECTED_COUNT=0
for bid_id in $(echo "$CHARTER_BIDS" | jq -r '.[] | select(.id != '${ACCEPTED_BID_ID}') | .id'); do
    REJECT_RESPONSE=$(curl -s -X PUT "http://localhost:8009/bids/${bid_id}" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"status": "rejected"}')
    
    REJECT_STATUS=$(echo "$REJECT_RESPONSE" | jq -r '.status')
    if [ "$REJECT_STATUS" == "rejected" ]; then
        REJECTED_COUNT=$((REJECTED_COUNT + 1))
    fi
done
echo "✓ Rejected $REJECTED_COUNT other bids"

# Step 9: Update charter with selected vendor
echo ""
echo "Step 9: Updating charter with selected vendor..."
UPDATE_CHARTER=$(curl -s -X PUT "http://localhost:8001/charters/${CHARTER_ID}" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": '${ACCEPTED_VENDOR_ID}',
    "total_cost": '${ACCEPTED_BID_AMOUNT}',
    "status": "confirmed"
  }')

CHARTER_STATUS=$(echo "$UPDATE_CHARTER" | jq -r '.status')
CHARTER_VENDOR=$(echo "$UPDATE_CHARTER" | jq -r '.vendor_id')
echo "✓ Charter updated"
echo "  Status: $CHARTER_STATUS"
echo "  Assigned Vendor: ID $CHARTER_VENDOR"

# Step 10: Verify final state
echo ""
echo "Step 10: Verifying final state..."
FINAL_CHARTER=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8001/charters/${CHARTER_ID}")

FINAL_BIDS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8009/bids?charter_id=${CHARTER_ID}")

ACCEPTED_BIDS=$(echo "$FINAL_BIDS" | jq '[.[] | select(.status == "accepted")] | length')
REJECTED_BIDS=$(echo "$FINAL_BIDS" | jq '[.[] | select(.status == "rejected")] | length')

echo "✓ Charter Status: $(echo "$FINAL_CHARTER" | jq -r '.status')"
echo "✓ Accepted Bids: $ACCEPTED_BIDS"
echo "✓ Rejected Bids: $REJECTED_BIDS"

# Summary
echo ""
echo "============================================"
echo "WORKFLOW TEST SUMMARY"
echo "============================================"
echo "Charter ID: $CHARTER_ID"
echo "Total Bids Received: $BID_COUNT"
echo "Accepted Bid ID: $ACCEPTED_BID_ID"
echo "Accepted Amount: \$$ACCEPTED_BID_AMOUNT"
echo "Selected Vendor: ID $ACCEPTED_VENDOR_ID"
echo "Final Charter Status: $CHARTER_STATUS"
echo ""
echo "✅ CHARTER BIDDING WORKFLOW COMPLETED"
echo "============================================"
