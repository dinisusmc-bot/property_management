# Kong Gateway Testing Standard

**Updated:** February 2, 2026  
**Status:** MANDATORY for all phases

---

## Overview

**ALL testing MUST go through Kong API Gateway** to validate production architecture.

## Architecture

```
Client/Tests → Kong Gateway (8080) → Services (8000)
              ↓
         Admin API (8081)
```

### Service Routing

All services accessible via Kong Gateway:

```
http://localhost:8080/api/v1/auth          → auth-service:8000
http://localhost:8080/api/v1/charters      → charter-service:8000
http://localhost:8080/api/v1/clients       → client-service:8000
http://localhost:8080/api/v1/documents     → document-service:8000
http://localhost:8080/api/v1/payments      → payment-service:8000
http://localhost:8080/api/v1/notifications → notification-service:8000
http://localhost:8080/api/v1/pricing       → pricing-service:8000
http://localhost:8080/api/v1/vendors       → vendor-service:8000
http://localhost:8080/api/v1/dispatch      → dispatch-service:8000
http://localhost:8080/api/v1/analytics     → analytics-service:8000
http://localhost:8080/api/v1/sales         → sales-service:8000
```

## Testing Requirements

### ❌ NEVER Test Directly on Service Ports

```bash
# WRONG - Bypasses Kong Gateway
curl http://localhost:8004/payments/health
curl http://localhost:8013/analytics/revenue

# CORRECT - Through Kong Gateway
curl http://localhost:8080/api/v1/payments/health
curl http://localhost:8080/api/v1/analytics/revenue
```

### ✅ Always Use Kong Gateway URLs

All test scripts must use:
- **Base URL**: `http://localhost:8080/api/v1/{service}`
- **Authentication**: JWT token in Authorization header
- **Routes**: All routes have `strip_path: true` configured

### Test Script Template

```bash
#!/bin/bash

# Kong Gateway Base URL
BASE_URL="http://localhost:8080/api/v1"

# Authenticate
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

# Test endpoints through Kong
curl -X GET "$BASE_URL/charters/charters" \
  -H "Authorization: Bearer $TOKEN"

curl -X GET "$BASE_URL/analytics/revenue/summary" \
  -H "Authorization: Bearer $TOKEN"
```

## Kong Route Configuration

### Standard Route Template

Every service MUST have:

```bash
# Register Service
curl -X POST http://localhost:8081/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{service-name}",
    "host": "{service-name}",
    "port": 8000,
    "protocol": "http"
  }'

# Register Route
curl -X POST http://localhost:8081/services/{service-name}/routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{service}-route",
    "paths": ["/api/v1/{service}"],
    "strip_path": true
  }'
```

**Key Settings:**
- `strip_path: true` - Required to remove `/api/v1/{service}` prefix
- `host: {service-name}` - Matches Docker service name
- `port: 8000` - All services listen on port 8000 internally

## Verification

### Check Kong Health

```bash
# Verify Kong is running
curl http://localhost:8081/status

# List all services
curl http://localhost:8081/services | jq '.data[] | {name, host, port}'

# List all routes
curl http://localhost:8081/routes | jq '.data[] | {name, paths, strip_path}'
```

### Test Service Through Kong

```bash
# Health check (no auth required)
curl http://localhost:8080/api/v1/{service}/health

# Authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/v1/{service}/{endpoint}
```

## Phase Validation Checklist

Before marking any phase complete:

- [ ] Service registered with Kong
- [ ] Route configured with `strip_path: true`
- [ ] Health endpoint accessible via Kong
- [ ] All test scripts use Kong URLs
- [ ] No direct port access in test scripts
- [ ] Tests pass through Kong Gateway
- [ ] Comprehensive test run completed

## Comprehensive Test Script

Use `test_all_phases_kong.sh` to validate all phases:

```bash
chmod +x test_all_phases_kong.sh
./test_all_phases_kong.sh
```

This tests:
- Phase 1: Payment, Document, Notification services
- Phase 2: Charter enhancements
- Phase 3: Pricing features
- Phase 4: Vendor management
- Phase 5: Dispatch service
- Phase 6: Analytics service
- Phase 7: Quote landing page
- All through Kong Gateway

## Why This Matters

### Production Architecture
- Kong Gateway is the ONLY entry point in production
- Direct service ports are not exposed
- All authentication, rate limiting, logging at gateway level

### Testing Validity
- Tests must validate the actual production architecture
- Gateway routing issues caught in development
- Authentication flows validated end-to-end

### Security
- Services are protected behind gateway
- JWT validation at gateway level
- Rate limiting and abuse prevention

## Common Issues

### Route Not Found (404)
```bash
# Check route exists
curl http://localhost:8081/routes | jq '.data[] | select(.name=="{service}-route")'

# Verify strip_path is true
curl http://localhost:8081/routes/{route-id} | jq '.strip_path'
```

### Service Unavailable (502/503)
```bash
# Check service registration
curl http://localhost:8081/services/{service-name}

# Verify service is running
docker ps | grep {service-name}

# Check service health directly (debugging only)
curl http://localhost:800X/health  # X = service port
```

### Authentication Failures
```bash
# Verify auth service works
curl http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Check token validity
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq
```

## Maintaining Standards

### For New Services
1. Create service with port 8000 internally
2. Register with Kong immediately
3. Configure route with `strip_path: true`
4. Write tests using Kong URLs from start
5. Never bypass Kong in tests

### For Existing Services
1. Verify Kong registration
2. Update test scripts to use Kong URLs
3. Run comprehensive test suite
4. Document any Kong-specific configurations

## References

- Kong Admin API: http://localhost:8081
- Kong Gateway: http://localhost:8080
- All Tests: `test_all_phases_kong.sh`
- Route Config: Check `docker-compose.yml` for Kong setup

---

**Remember:** If you're not testing through Kong, you're not testing production architecture! ✅
