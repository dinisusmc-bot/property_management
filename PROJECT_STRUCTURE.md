# Athena Charter Management System - Project Structure

**Last Updated**: February 4, 2026  
**Version**: 2.0.0  
**Status**: Production Ready - Frontend Integration Phase

---

## 📁 Root Directory Structure

```
coachway_demo/
├── backend/              # Backend microservices & scripts
├── frontend/             # React/TypeScript SPA
├── airflow/             # Apache Airflow ETL workflows
├── monitoring/          # Prometheus & Grafana configs
├── tests/               # Integration & E2E tests
├── docs/                # Technical documentation
├── docker-compose.yml   # Service orchestration
├── start-all.sh        # System startup script
├── stop-all.sh         # System shutdown script
└── .env                # Environment configuration
```

---

## 🏗️ Backend Architecture (`/backend`)

### Directory Layout
```
backend/
├── services/           # 14 Microservices (FastAPI)
│   ├── auth/          # Authentication & Authorization
│   ├── clients/       # Customer Management (CRM)
│   ├── charters/      # Charter Operations
│   ├── vendor/        # Vendor Management
│   ├── payments/      # Payment Processing
│   ├── documents/     # Document Management & E-Signatures
│   ├── dispatch/      # Driver Assignment & Dispatch
│   ├── notifications/ # Email/SMS/Push Notifications
│   ├── sales/         # Sales Pipeline & Quotes
│   ├── pricing/       # Dynamic Pricing Engine
│   ├── portals/       # Client/Vendor/Driver Portals
│   ├── change_mgmt/   # Change Orders & Approvals
│   ├── analytics/     # Business Intelligence
│   └── document/      # (Legacy - being consolidated)
│
└── scripts/           # Database migrations & utilities
    ├── seed_data.py   # Sample data seeder
    └── migrations/    # Schema migrations
```

### Service Architecture Pattern

Each microservice follows this standard structure:

```
service_name/
├── main.py            # FastAPI app & route definitions
├── models.py          # SQLAlchemy ORM models
├── schemas.py         # Pydantic request/response schemas
├── database.py        # DB connection & session management
├── config.py          # Service configuration
├── business_logic.py  # Core business logic (if complex)
├── Dockerfile         # Container build spec
└── requirements.txt   # Python dependencies
```

### Microservices Details

#### 1. **Auth Service** (Port 8000)
- **Purpose**: JWT authentication, RBAC, MFA
- **Database**: PostgreSQL (users, roles, permissions)
- **Key Features**:
  - Multi-factor authentication (TOTP)
  - Role-based access control (Admin, Manager, Vendor, Driver)
  - Password reset flows
  - Session management

#### 2. **Client Service** (Port 8002)
- **Purpose**: Customer relationship management
- **Database**: PostgreSQL (clients, contacts)
- **Key Features**:
  - Client profiles (corporate, personal, government)
  - Contact management
  - Credit limit tracking
  - Payment terms (net_30, net_60, etc.)
  - Stripe customer integration

#### 3. **Charter Service** (Port 8001)
- **Purpose**: Core charter operations
- **Database**: PostgreSQL (charters, itineraries, vehicles)
- **Key Features**:
  - Charter creation & management
  - Multi-vehicle charters
  - Recurring/series charters
  - Status workflow (quote → booked → confirmed → completed)
  - Vehicle assignment
  - Pricing calculations

#### 4. **Vendor Service** (Port 8008)
- **Purpose**: Vendor/subcontractor management
- **Database**: PostgreSQL (vendors, bids)
- **Key Features**:
  - Vendor profiles & ratings
  - Bid management
  - Insurance tracking (COI)
  - Performance metrics
  - Vendor assignments

#### 5. **Payment Service** (Port 8004)
- **Purpose**: Payment processing & invoicing
- **Database**: PostgreSQL (transactions, invoices)
- **Integrations**: Stripe API
- **Key Features**:
  - Invoice generation
  - Payment processing
  - Refund handling
  - Payment history
  - Deposit tracking

#### 6. **Document Service** (Port 8003)
- **Purpose**: Document management & e-signatures
- **Database**: MongoDB (file storage) + PostgreSQL (metadata)
- **Key Features**:
  - Document upload/download
  - E-signature workflows (DocuSign-style)
  - Version control
  - Document types (contracts, invoices, COI, etc.)
  - Expiration tracking

#### 7. **Dispatch Service** (Port 8012)
- **Purpose**: Driver assignment & tracking
- **Database**: PostgreSQL (drivers, assignments, check-ins)
- **Key Features**:
  - Driver availability management
  - Real-time location tracking
  - Check-in/check-out
  - Emergency reassignment
  - Driver performance

#### 8. **Notification Service** (Port 8005)
- **Purpose**: Multi-channel notifications
- **Database**: PostgreSQL (notification log)
- **Integrations**: RabbitMQ (message queue)
- **Key Features**:
  - Email notifications (SendGrid/SMTP)
  - SMS notifications (Twilio)
  - Push notifications
  - Notification templates
  - Delivery tracking

#### 9. **Sales Service** (Port 8009)
- **Purpose**: Sales pipeline & lead management
- **Database**: PostgreSQL (leads, opportunities, quotes)
- **Key Features**:
  - Lead capture & scoring
  - Sales pipeline stages
  - Quote generation
  - Proposal templates
  - Conversion tracking

#### 10. **Pricing Service** (Port 8007)
- **Purpose**: Dynamic pricing engine
- **Database**: PostgreSQL (pricing rules, rate cards)
- **Key Features**:
  - Base rate + mileage calculations
  - Seasonal/event pricing
  - Client-specific rates
  - Profit margin optimization
  - Pricing approvals

#### 11. **Portals Service** (Port 8010)
- **Purpose**: External portal access
- **Database**: PostgreSQL (portal configurations)
- **Key Features**:
  - Client portal (booking, tracking)
  - Vendor portal (bids, assignments)
  - Driver portal (assignments, check-in)
  - Secure token-based access

#### 12. **Change Management Service** (Port 8011)
- **Purpose**: Change orders & approvals
- **Database**: PostgreSQL (change requests, approvals)
- **Key Features**:
  - Change request workflow
  - Multi-level approvals
  - Change history/audit log
  - Notification triggers
  - Auto-approval rules

#### 13. **Analytics Service** (Port 8013)
- **Purpose**: Business intelligence & reporting
- **Database**: PostgreSQL (aggregated data)
- **Key Features**:
  - Revenue analytics
  - Utilization reports
  - Performance KPIs
  - Custom dashboards
  - Data exports (CSV, Excel)

#### 14. **Document (Legacy)** (Port 8006)
- **Status**: Being deprecated
- **Note**: Functionality consolidated into Documents Service (Port 8003)

---

## 🎨 Frontend Architecture (`/frontend`)

### Structure
```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   │   ├── auth/       # Login, Register, MFA
│   │   ├── charters/   # Charter management UI
│   │   ├── clients/    # Client management UI
│   │   ├── vendors/    # Vendor management UI
│   │   ├── common/     # Shared components (buttons, forms)
│   │   └── layout/     # Layout components (header, sidebar)
│   │
│   ├── pages/          # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Charters.tsx
│   │   ├── Clients.tsx
│   │   └── ...
│   │
│   ├── services/       # API client services
│   │   ├── api.ts      # Axios instance & interceptors
│   │   ├── charterService.ts
│   │   ├── clientService.ts
│   │   └── ...
│   │
│   ├── store/          # State management (Redux/Zustand)
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript type definitions
│   ├── utils/          # Utility functions
│   └── App.tsx         # Main app component
│
├── public/             # Static assets
├── nginx.conf          # Nginx config for production
├── Dockerfile          # Container build spec
├── package.json        # Node dependencies
├── tsconfig.json       # TypeScript config
└── vite.config.ts      # Vite bundler config
```

### Technology Stack
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: Redux Toolkit / Zustand
- **UI Library**: Material-UI / Tailwind CSS
- **Routing**: React Router v6
- **API Client**: Axios
- **Forms**: React Hook Form + Zod validation
- **Production Server**: Nginx

### API Integration Points

All API calls route through Kong API Gateway at `http://localhost:8080/api/v1/`

```typescript
// Example service structure
const charterService = {
  getAll: () => axios.get('/api/v1/charters'),
  getById: (id) => axios.get(`/api/v1/charters/${id}`),
  create: (data) => axios.post('/api/v1/charters', data),
  update: (id, data) => axios.put(`/api/v1/charters/${id}`, data),
  delete: (id) => axios.delete(`/api/v1/charters/${id}`)
};
```

---

## 🔄 Apache Airflow (`/airflow`)

### Structure
```
airflow/
├── dags/               # Airflow DAG definitions
│   ├── daily_reports.py       # Daily reporting
│   ├── invoice_generation.py  # Automated invoicing
│   ├── data_cleanup.py        # Data maintenance
│   └── backup_jobs.py         # Database backups
│
├── plugins/            # Custom Airflow operators
├── logs/              # Execution logs
├── requirements.txt   # Python dependencies
└── Dockerfile         # Container build spec
```

### DAGs Overview

1. **Daily Reports DAG**
   - Schedule: Daily at 8 AM
   - Tasks: Generate revenue, utilization, performance reports
   - Output: Email PDFs to management

2. **Invoice Generation DAG**
   - Schedule: End of month
   - Tasks: Create invoices, calculate taxes, send to clients
   - Integration: Payment service API

3. **Data Cleanup DAG**
   - Schedule: Weekly
   - Tasks: Archive old records, delete temp files
   - Database: PostgreSQL maintenance

4. **Backup DAG**
   - Schedule: Daily at 2 AM
   - Tasks: PostgreSQL dump, MongoDB backup, S3 upload

---

## 📊 Monitoring Stack (`/monitoring`)

### Structure
```
monitoring/
├── prometheus.yml      # Prometheus config
├── alerts.yml         # Alert rules
├── dashboards/        # Grafana dashboard JSONs
│   ├── service_health.json
│   ├── business_metrics.json
│   └── system_metrics.json
│
└── provisioning/      # Grafana provisioning
    ├── datasources/   # Data source configs
    └── dashboards/    # Dashboard configs
```

### Metrics Collection
- **Prometheus**: Scrapes metrics from all services
- **Grafana**: Visualizes metrics & business KPIs
- **Endpoints**: All services expose `/metrics` endpoint

### Key Dashboards
1. **Service Health**: Uptime, response times, error rates
2. **Business Metrics**: Revenue, bookings, utilization
3. **System Metrics**: CPU, memory, disk, network

---

## 🧪 Testing Infrastructure (`/tests`)

### Structure
```
tests/
├── integration/              # Service integration tests
│   ├── run_all_workflows.py # 15 E2E workflows
│   └── test_*.py            # Individual test modules
│
├── e2e/                     # End-to-end tests
│   ├── auth/               # Authentication flows
│   ├── charter_lifecycle/  # Full charter workflows
│   └── payment_flows/      # Payment processing
│
├── api/                    # API endpoint tests
│   ├── test_auth.py
│   ├── test_charters.py
│   └── ...
│
├── performance/            # Load & stress tests
│   └── locustfile.py
│
├── conftest.py            # Pytest fixtures
└── requirements.txt       # Test dependencies
```

### Test Coverage

**Current Status** (as of Feb 4, 2026):
- ✅ 15/15 Workflow tests passing (100%)
- ✅ 20/20 Data validations passing (100%)
- ✅ All services accessible through Kong

### Test Workflows
1. Client Onboarding & First Charter
2. Vendor Bidding & Selection
3. Document Management & E-Signature
4. Payment Processing End-to-End
5. Sales Pipeline & Quote Conversion
6. Dispatch & Driver Assignment
7. Change Management & Approvals
8. Multi-Vehicle Charter Coordination
9. Charter Modification & Cancellation
10. Recurring/Series Charter Creation
11. Driver Check-In & Real-Time Operations
12. Invoice Reconciliation & Accounting
13. Emergency Dispatch Reassignment
14. Analytics & Reporting
15. User Management & Permissions

---

## 🌐 Infrastructure Layer

### Kong API Gateway (Port 8080)
- **Purpose**: Unified API entry point
- **Features**:
  - Route management
  - Authentication
  - Rate limiting
  - Request/response transformation
  - Logging & metrics

### Databases

#### PostgreSQL (Port 5432)
- **Primary Database**: Shared by all services
- **Schema**: Each service has its own schema/tables
- **Users**: Service-specific credentials
- **Backup**: Daily automated backups via Airflow

#### MongoDB (Port 27017)
- **Purpose**: Document storage
- **Used By**: Document service
- **Collections**: files, metadata, versions

#### Redis (Airflow)
- **Purpose**: Celery task queue for Airflow
- **Port**: 6379 (internal)

### Message Queue

#### RabbitMQ
- **Purpose**: Async task processing
- **Used By**: Notification service
- **Queues**: 
  - email_notifications
  - sms_notifications
  - push_notifications

---

## 📝 Documentation (`/docs`)

### Current Documentation Files

```
docs/
├── PROJECT_STRUCTURE.md        # This file
├── DEPLOYMENT.md               # Deployment guide
├── KONG_TESTING_STANDARD.md    # API testing standards
├── WORKFLOW_TEST_REPORT.md     # Test results
├── PHASE8_SUMMARY.md           # Phase 8 completion
├── client_needs.md             # Requirements doc
└── implementation_plan/        # Feature plans
```

### Documentation to Keep
- ✅ `PROJECT_STRUCTURE.md` - Architecture reference
- ✅ `DEPLOYMENT.md` - Production deployment
- ✅ `KONG_TESTING_STANDARD.md` - Testing guidelines
- ✅ `WORKFLOW_TEST_REPORT.md` - Current test status

### Documentation to Archive/Remove
- ⚠️ `PHASE8_COMPLETE*.md` - Historical, can archive
- ⚠️ `GAP_ANALYSIS*.md` - Completed, can archive
- ⚠️ Multiple duplicate test reports - Consolidate

---

## 🚀 Getting Started for Frontend Integration

### 1. Verify Backend Services

```bash
# Check all services are running
docker compose ps

# Expected: 20+ containers running (healthy)
```

### 2. Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React App |
| Kong Gateway | http://localhost:8080 | API Entry Point |
| Grafana | http://localhost:3001 | Monitoring |
| Airflow | http://localhost:8082 | ETL Workflows |

### 3. API Base URL

```typescript
// frontend/src/services/api.ts
const API_BASE_URL = 'http://localhost:8080/api/v1';
```

### 4. Authentication Flow

```
1. POST /api/v1/auth/login → JWT token
2. Store token in localStorage/sessionStorage
3. Add to all requests: Authorization: Bearer {token}
4. Handle 401 → redirect to login
```

### 5. Key API Endpoints

```
Authentication:
  POST   /api/v1/auth/login
  POST   /api/v1/auth/register
  POST   /api/v1/auth/mfa/verify
  POST   /api/v1/auth/refresh

Charters:
  GET    /api/v1/charters
  POST   /api/v1/charters
  GET    /api/v1/charters/{id}
  PUT    /api/v1/charters/{id}
  DELETE /api/v1/charters/{id}
  POST   /api/v1/charters/recurring

Clients:
  GET    /api/v1/clients
  POST   /api/v1/clients
  GET    /api/v1/clients/{id}
  PUT    /api/v1/clients/{id}

Vendors:
  GET    /api/v1/vendors
  POST   /api/v1/vendors
  GET    /api/v1/vendors/{id}

Documents:
  POST   /api/v1/documents/upload
  GET    /api/v1/documents/{id}
  POST   /api/v1/documents/{id}/signature-request

Payments:
  GET    /api/v1/invoices
  POST   /api/v1/payments/process
  POST   /api/v1/payments/refund
```

---

## 🔒 Environment Variables

### Required `.env` Configuration

```bash
# Database
DATABASE_URL=postgresql://athena:athena_dev_password@postgres:5432/athena
MONGODB_URL=mongodb://mongodb:27017/athena_documents

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# External Services
STRIPE_API_KEY=sk_test_...
SENDGRID_API_KEY=SG...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...

# Kong
KONG_DATABASE_HOST=kong-database
KONG_DATABASE_NAME=kong
KONG_DATABASE_USER=kong
KONG_DATABASE_PASSWORD=kong

# Airflow
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin
```

---

## 📦 Service Dependencies

```mermaid
Frontend (React)
    ↓
Kong API Gateway
    ↓
┌─────────────────────────────────────────┐
│ Microservices Layer                     │
├─────────────────────────────────────────┤
│ Auth ← All services depend              │
│ Clients                                 │
│ Charters ← Clients, Vendors, Vehicles  │
│ Vendors                                 │
│ Payments ← Charters, Clients            │
│ Documents ← Charters                    │
│ Dispatch ← Charters, Drivers            │
│ Notifications ← All services            │
│ Sales ← Clients, Charters               │
│ Pricing ← Charters                      │
│ Portals ← Clients, Vendors, Drivers    │
│ Change Management ← Charters            │
│ Analytics ← All services                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Data Layer                              │
├─────────────────────────────────────────┤
│ PostgreSQL (main database)              │
│ MongoDB (document storage)              │
│ Redis (caching/queue)                   │
│ RabbitMQ (message queue)                │
└─────────────────────────────────────────┘
```

---

## 🎯 Next Steps for Frontend Integration

### Phase 1: Core Features (Week 1-2)
1. ✅ Authentication & MFA
2. ✅ Dashboard layout & navigation
3. ✅ Charter CRUD operations
4. ✅ Client management

### Phase 2: Advanced Features (Week 3-4)
1. ✅ Document upload & e-signatures
2. ✅ Payment processing
3. ✅ Vendor management
4. ✅ Driver dispatch

### Phase 3: Business Features (Week 5-6)
1. ✅ Sales pipeline
2. ✅ Change management
3. ✅ Recurring charters
4. ✅ Multi-vehicle bookings

### Phase 4: Analytics & Polish (Week 7-8)
1. ✅ Analytics dashboards
2. ✅ Reporting tools
3. ✅ Performance optimization
4. ✅ Mobile responsiveness

---

## 📊 System Health Check

```bash
# Run comprehensive health check
curl http://localhost:8080/api/v1/auth/health
curl http://localhost:8080/api/v1/charters/health
curl http://localhost:8080/api/v1/clients/health

# Run integration tests
cd /home/nick/work_area/coachway_demo
python3 tests/integration/run_all_workflows.py

# Expected: 15/15 workflows passing
```

---

## 🤝 Contributing

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **TypeScript**: ESLint, Prettier, strict mode
- **Commits**: Conventional commits (feat:, fix:, docs:)
- **Testing**: 80%+ coverage required

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `hotfix/*` - Emergency fixes

---

## 📞 Support

For questions or issues:
- **Architecture**: Contact system architect
- **API Issues**: Check Kong logs
- **Service Errors**: Check service logs via `docker compose logs {service}`
- **Performance**: Review Grafana dashboards

---

**System Status**: ✅ Production Ready  
**Test Coverage**: 100% (15/15 workflows)  
**Last Updated**: February 4, 2026  
**Next Milestone**: Frontend Integration Complete
