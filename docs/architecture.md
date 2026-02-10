# 🏗️ Architecture

## Overview

The Property Management Platform is a **multi-tenant SaaS application** built with a **microservices architecture** on Kubernetes/Docker.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               API Gateway (Kong)                            │
│                        http://localhost:8080/api/v1                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │                                   │                                   │
        ▼                                   ▼                                   ▼
┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
│   Owners Service  │           │ Properties Service│           │   Units Service   │
│      Port 8015    │           │      Port 8016    │           │      Port 8017    │
└───────────────────┘           └───────────────────┘           └───────────────────┘
        │                                   │                                   │
        ┼───────────────────────────────────┼───────────────────────────────────┼
        │                                   │                                   │
        ▼                                   ▼                                   ▼
┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
│   Tenants Service │           │ Maintenance Service│          │    Leases Service │
│      Port 8018    │           │      Port 8019    │           │      Port 8020    │
└───────────────────┘           └───────────────────┘           └───────────────────┘
        │                                   │                                   │
        └───────────────────────────────────┴───────────────────────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │   PostgreSQL    │
                                    │  (Primary + RLS)│
                                    └─────────────────┘
```

## Data Hierarchy

```
Owner (owners)
   ├── id
   ├── email
   ├── full_name
   ├── phone
   ├── company_name
   ├── address
   └── is_active

   └── Properties (properties)
         ├── id
         ├── name
         ├── address
         ├── owner_id (FK → owners.id)
         └── status

         └── Units (units)
               ├── id
               ├── unit_number
               ├── property_id (FK → properties.id)
               ├── type (studio, 1br, 2br, 3br, commercial)
               ├── rent
               └── status (vacant, occupied, maintenance)

               └── Tenants (tenants)
                     ├── id
                     ├── full_name
                     ├── email
                     ├── phone
                     ├── unit_id (FK → units.id)
                     ├── is_primary
                     └── status (active, inactive, pending)
```

## Role-Based Access Control (RBAC)

| Role | Owners | Properties | Units | Tenants | Maintenance | Leases | Payments | Reports |
|------|--------|------------|-------|---------|-------------|--------|----------|---------|
| Admin | CRUD | CRUD | CRUD | CRUD | Full | Full | Full | Full |
| Manager | CRUD | CRUD | CRUD | CRUD | Approve | Read | Full | Read |
| Owner | Own only | Own only | Own only | Own only | Approve (<$threshold) | Read | Read | Own only |
| Tenant | N/A | N/A | Own only | Own only | Submit | Read | Pay | Own only |
| Contractor | N/A | N/A | N/A | N/A | Complete jobs | N/A | N/A | N/A |

## Row-Level Security (RLS)

PostgreSQL RLS policies ensure tenants can only access their own data:

```sql
-- Tenants can only see their own record
CREATE POLICY tenant_isolation ON tenants
  FOR ALL
  USING (user_id = current_setting('app.current_user_id')::int);
```

## API Gateway (Kong)

All backend services are registered with Kong:

| Path | Upstream Service |
|------|------------------|
| `/api/v1/owners/*` | owners:8015 |
| `/api/v1/properties/*` | properties:8016 |
| `/api/v1/units/*` | units:8017 |
| `/api/v1/tenants/*` | tenants:8018 |
| `/api/v1/maintenance/*` | maintenance:8019 |
| `/api/v1/leases/*` | leases:8020 |
| `/api/v1/payments/*` | payments:8004 (legacy) |
| `/api/v1/auth/*` | auth:8000 (legacy) |

**Authentication**: Kong JWT plugin validates bearer tokens before routing.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python), SQLAlchemy, PostgreSQL |
| Frontend | React 18, TypeScript, Vite, MUI |
| Auth | JWT + MFA (email), Password reset, Impersonation |
| API Gateway | Kong (rate limiting, auth plugins) |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |
| Testing | pytest (unit/integration), Cypress (E2E) |

## Security

- **Input validation**: Pydantic schemas + SQLAlchemy constraints
- **SQL injection prevention**: Parameterized queries (SQLAlchemy ORM)
- **XSS prevention**: React's built-in escaping + CSP headers
- **CSRF protection**: SameSite cookies + CSRF tokens
- **MFA enforcement**: Per-role policy (Admin/Manager = required)
- **Audit logging**: All CRUD + auth events logged
- **Encryption**: TLS 1.3, AES-256 at rest

---

*Last updated: 2026-02-10*
