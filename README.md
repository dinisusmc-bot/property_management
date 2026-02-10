# 🏢 Property Management Platform

**Multi-tenant property management system** for property owners, managers, and tenants — built with FastAPI, React, PostgreSQL, and Kong API Gateway.

[![Tests](https://img.shields.io/badge/tests-25%2B_passing-brightgreen)](docs/)
[![Backend](https://img.shields.io/badge/backend-6_services-blue)](#backend-services)
[![Frontend](https://img.shields.io/badge/frontend-React_18-green)](#frontend)
[![API Gateway](https://img.shields.io/badge/Kong-configured-orange)](#api-gateway)

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 24+ with Docker Compose
- 8GB+ RAM available
- 20GB+ free disk space

### Start the System

```bash
# Clone and navigate to project
cd ~/projects/property_management

# Start all services
./start-all.sh

# Or use Docker Compose directly
docker-compose -f docker-compose.staging.yml up -d
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3002 | admin@pm-demo.com / password |
| **API Gateway (Kong)** | http://localhost:8080/api/v1 | JWT Token required |
| **Owners Service** | http://localhost:8015 | - |
| **Properties Service** | http://localhost:8016 | - |
| **Units Service** | http://localhost:8017 | - |
| **Tenants Service** | http://localhost:8018 | - |
| **Maintenance Service** | http://localhost:8019 | - |

---

## 📚 Documentation

- **[Architecture](docs/architecture.md)** - System design, hierarchy, RBAC
- **[API Guide](docs/api-guide.md)** - All endpoints, request/response schemas
- **[Deployment](docs/deployment.md)** - Docker, staging, production
- **[Quick Start](docs/QUICKSTART.md)** - Setup instructions
- **[Changelog](CHANGELOG.md)** - Version history

---

## 🏗️ Core Hierarchy

```
Owner (can own multiple Properties)
   └── Property (belongs to one Owner)
         └── Unit (belongs to one Property)
               └── Tenant (Primary + Co-Tenants)
```

---

## 👥 Roles & Capabilities

### Admin / Manager
- Full CRUD on owners, properties, units, tenants, maintenance
- Process rent payments, deduct fees, payout net rents to owners
- Review/approve maintenance requests & contractor bids
- GAAP compliance: accrual accounting, audit trails
- Analytics dashboards (occupancy, revenue, delinquency)

### Property Owner
- Manage owned properties/units: set rents, approve leases
- Pay maintenance fees, receive payouts, view statements
- Approve maintenance requests/bids (threshold-based auto-approve)
- Per-property analytics: ROI, expenses, tax exports (1099s)

### Tenant (Primary + Co-Tenants)
- View/pay rent (autopay, partial, Stripe integration)
- Submit maintenance requests (photos, urgency)
- Access lease docs, payment history, unit details
- In-app messaging with managers/owners/contractors

### Maintenance / Contractor
- Receive secure, time-limited links for bids/acceptance
- View assigned jobs: details, photos, timelines
- Update status, submit bids/invoices
- Get paid via integrated payouts

---

## 🏗️ Backend Services (6 Services)

| Port | Service | Purpose | Status |
|------|---------|---------|--------|
| 8015 | owners | Property owner management | ✅ Production Ready |
| 8016 | properties | Property CRUD & assignment | ✅ Production Ready |
| 8017 | units | Unit management & status | ✅ Production Ready |
| 8018 | tenants | Tenant profiles & leases | ✅ Production Ready |
| 8019 | maintenance | Work orders & bids | ✅ Production Ready |
| 8020 | leases | Lease templates & e-sign | 🚧 In Progress |

**API Gateway**: All services accessible via Kong at `http://localhost:8080/api/v1`

---

## 🎨 Frontend

- **Tech**: React 18 + TypeScript + Vite + MUI
- **Theme**: Glassmorphism + dark mode
- **Pages**: Dashboard, Owners, Properties, Units, Tenants, Maintenance, Leases
- **API Integration**: React Query + Axios

---

## 🔐 Authentication & Security

- **JWT + MFA** (email-based 6-digit codes)
- **Role-based access control** (RBAC)
- **Row-level security** (RLS) in PostgreSQL
- **Audit logging** for all critical actions
- **Encryption** (at-rest/transit)
- **Kong rate limiting** & auth plugins

---

## 📊 GAAP Compliance

- Accrual accounting journal entries
- Ledger + audit trail for every transaction
- Financial reports: balance sheet, income statement, aging receivables
- QuickBooks/Xero export ready
- Rent collection → payout flow with fee deductions

---

## 🧪 Testing

- **Unit tests**: Service-level (pytest)
- **Integration tests**: API endpoints, DB transactions
- **E2E tests**: Cypress (login, CRUD, Kong routing)
- **Test coverage**: 85%+ target

---

## 🚢 Deployment

### Docker (Staging/Production)

```bash
# Build services
docker-compose -f docker-compose.staging.yml build

# Start
docker-compose -f docker-compose.staging.yml up -d

# Health check
curl -f http://localhost:8015/health
```

### GitHub Actions CI/CD

See `.github/workflows/ci.yml` for:
- Test → Build → Staging deploy pipeline
- Automatic rollback on unhealthy status

---

## 📝 License

MIT License — see LICENSE for details.

---

## 🤝 Support

- 📧 Email: support@pm-demo.com
- 💬 Discord: https://discord.gg/pm-demo
- 📚 Docs: https://docs.pm-demo.com
