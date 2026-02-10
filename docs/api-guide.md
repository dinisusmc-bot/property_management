# 📡 API Guide

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

All endpoints (except `/health`) require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Login Endpoint

**POST** `/api/v1/auth/login`

```json
{
  "email": "admin@pm-demo.com",
  "password": "password"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "admin@pm-demo.com",
    "role": "admin"
  }
}
```

---

## Owners Service (`/api/v1/owners`)

### List Owners

**GET** `/api/v1/owners/owners`

**Query Params**:
- `skip` (default: 0)
- `limit` (default: 100)
- `is_active` (default: true)

**Response (200 OK)**:
```json
[
  {
    "id": 1,
    "email": "john.smith@example.com",
    "full_name": "John Smith",
    "phone": "(555) 123-4567",
    "company_name": "Smith Holdings LLC",
    "address": "123 Main St, City, State 12345",
    "is_active": true,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-02-01T09:15:00Z"
  }
]
```

### Create Owner

**POST** `/api/v1/owners/owners`

**Request**:
```json
{
  "email": "new.owner@example.com",
  "full_name": "New Owner",
  "phone": "(555) 987-6543",
  "company_name": "New Holdings Inc",
  "address": "456 Oak Ave, City, State 67890",
  "is_active": true
}
```

**Response (201 Created)**: Same as GET response

### Get Owner

**GET** `/api/v1/owners/owners/{owner_id}`

**Response (200 OK)**: Owner object

### Update Owner

**PUT** `/api/v1/owners/owners/{owner_id}`

**Request**: Any subset of fields (partial update)

### Create Owner Note

**POST** `/api/v1/owners/owners/{owner_id}/notes`

**Request**:
```json
{
  "note": "Needs follow-up on lease renewal",
  "is_private": true
}
```

---

## Properties Service (`/api/v1/properties`)

### List Properties

**GET** `/api/v1/properties/properties`

**Query Params**:
- `owner_id` (filter by owner)
- `is_active` (default: true)

### Create Property

**POST** `/api/v1/properties/properties`

**Request**:
```json
{
  "name": "Sunset Ridge Apartments",
  "address": "1234 Sunset Blvd, Los Angeles, CA 90028",
  "owner_id": 1,
  "status": "active"
}
```

---

## Units Service (`/api/v1/units`)

### List Units

**GET** `/api/v1/units/units`

**Query Params**:
- `property_id` (required, filter by property)

### Create Unit

**POST** `/api/v1/units/units`

**Request**:
```json
{
  "unit_number": "101",
  "property_id": 1,
  "type": "studio",
  "rent": 1800.00,
  "status": "vacant"
}
```

---

## Tenants Service (`/api/v1/tenants`)

### List Tenants

**GET** `/api/v1/tenants/tenants`

**Query Params**:
- `unit_id` (filter by unit)
- `status` (active, inactive, pending)

### Create Tenant

**POST** `/api/v1/tenants/tenants`

**Request**:
```json
{
  "full_name": "Jane Doe",
  "email": "jane.doe@example.com",
  "phone": "(555) 987-6543",
  "unit_id": 1,
  "is_primary": true,
  "status": "active"
}
```

---

## Maintenance Service (`/api/v1/maintenance`)

### Create Request

**POST** `/api/v1/maintenance/requests`

**Request**:
```json
{
  "unit_id": 1,
  "title": "Leaky faucet in kitchen",
  "description": "Water dripping from faucet spout",
  "urgency": "medium",
  "photos": ["https://example.com/photo1.jpg"],
  "requested_by": "tenant_1"
}
```

### Approve Request

**POST** `/api/v1/maintenance/requests/{id}/approve`

**Request**:
```json
{
  "approved_by": "manager_1",
  "approved_at": "2026-02-10T12:00:00Z",
  "budget": 150.00
}
```

### Assign Contractor

**POST** `/api/v1/maintenance/requests/{id}/assign`

**Request**:
```json
{
  "contractor_id": 5,
  "bid_amount": 150.00
}
```

---

## Errors

| Status | Code | Message |
|--------|------|---------|
| 400 | INVALID_REQUEST | Invalid or missing parameters |
| 401 | UNAUTHORIZED | Missing or invalid JWT token |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Duplicate entry |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

**Error Response**:
```json
{
  "detail": "User does not have permission to perform this action",
  "code": "FORBIDDEN"
}
```

---

## Rate Limits

| Endpoint | Requests/Minute |
|----------|-----------------|
| `/api/v1/auth/*` | 10 |
| `/api/v1/owners/*` | 60 |
| `/api/v1/properties/*` | 60 |
| `/api/v1/units/*` | 60 |
| `/api/v1/tenants/*` | 60 |
| `/api/v1/maintenance/*` | 30 |
| `/api/v1/leases/*` | 30 |

---

*Last updated: 2026-02-10*
