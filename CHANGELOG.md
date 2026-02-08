# Changelog

All notable changes and features implemented in the Athena Charter Management System.

---

## [Phase 8] - February 2026 ✅ **COMPLETE**

### Added Features

#### Task 8.1: Saved Payment Methods
- Stripe Customer Portal integration
- Secure payment method storage (PCI compliant)
- Default payment method selection
- Payment method removal with cascade cleanup
- 4 new API endpoints

#### Task 8.2: TomTom Geocoding with Caching
- TomTom Search API integration
- Redis caching layer with 1-hour TTL
- Batch geocoding support (up to 100 addresses)
- Confidence scoring and address normalization
- Database fallback on Redis unavailability
- 2 new API endpoints
- **Tests**: 11/11 passing

#### Task 8.3: Multi-Vehicle Pricing
- Dynamic pricing engine with multiple factors
- Distance-based and time-based pricing
- Peak/off-peak multipliers
- Vehicle capacity optimization
- Surcharge calculation system
- 2 new API endpoints
- **Tests**: 12/12 passing

#### Task 8.4: Secure Charter Share Links
- JWT-based secure sharing tokens
- Bcrypt password protection (optional)
- Automatic expiration (1-90 days)
- View tracking and analytics
- Public charter viewing without authentication
- 4 new API endpoints
- **Tests**: 9/9 passing

#### Task 8.5: E-Signature System
- Complete custom e-signature implementation
- Canvas-based signature capture (frontend-ready)
- Base64 signature image storage
- Multi-signer support (unlimited signers)
- Comprehensive audit trail (IP, user-agent, timestamps)
- Public signing without authentication
- Signature validation (format, size, dimensions)
- Reminder system and cancellation
- 6 new API endpoints
- **Tests**: 13/13 passing

### Technical Improvements
- Added 4 new database tables
- Created 15 indexes for performance
- Implemented audit logging for signatures
- Added Redis caching for geocoding
- Enhanced security with JWT and bcrypt
- Comprehensive error handling

### Dependencies Added
- `httpx==0.24.1` - Async HTTP client
- `pyjwt==2.8.0` - JWT token generation
- `bcrypt==4.1.2` - Password hashing
- `pillow==10.1.0` - Image validation
- `email-validator==2.1.0` - Email schemas

### Documentation
- [Phase 8 Complete Guide](docs/PHASE8_COMPLETE.md)
- [Phase 8 Quick Reference](docs/PHASE8_QUICK_REFERENCE.md)
- [Phase 8 Summary](docs/PHASE8_SUMMARY.md)

### Testing
- **Total Tests**: 55
- **Pass Rate**: 100%
- **Coverage**: All features validated

---

## Current Version - December 2025

### ✅ Completed Features

#### Core System Infrastructure
- **21-container microservices architecture** with Docker Compose
- **PostgreSQL 15** database with connection pooling
- **MongoDB 7.0** for document storage with GridFS
- **Redis 7** for session and data caching
- **RabbitMQ 3** message queue for async operations
- **Kong API Gateway** with routing and rate limiting
- **Apache Airflow 2.8** for workflow automation
- **Prometheus + Grafana** monitoring stack

#### Authentication & Authorization
- JWT token-based authentication
- Role-based access control (admin, manager, user, vendor, driver)
- Secure password hashing with bcrypt
- Kong-validated JWT tokens
- Session management with Redis

#### Charter Management
- Complete CRUD operations for charters
- Multi-stage workflow: Quote → Approved → Booked → Confirmed → In Progress → Completed
- Automatic pricing calculation (vendor 75%, client 100%)
- 25% profit margin tracking
- Multi-stop itinerary planning
- Vendor assignment and tracking
- Driver assignment with restricted access
- Location tracking with GPS coordinates
- Charter notes and vendor notes

#### Driver Feature (NEW)
- Driver user type with restricted access
- Mobile-friendly driver dashboard
- View assigned charter only
- Real-time GPS location tracking (every 2 minutes)
- Browser Geolocation API integration
- Driver notes functionality
- Trip itinerary display
- No sidebar navigation (full-width layout)
- Auto-redirect on login
- 4 test driver accounts created

#### Document Management
- MongoDB GridFS file storage
- 10MB file upload limit
- Supported formats: PDF, DOC, DOCX, XLS, XLSX, TXT, CSV, images
- Document metadata in PostgreSQL
- Document types: approval, booking, confirmation, contract, invoice, receipt, insurance
- Upload dialogs integrated into workflow stages
- Download and delete functionality
- Admin-only delete permissions
- Kong API routes configured

#### Financial Management
- Invoice generation with auto-incrementing numbers (INV-00001, etc.)
- Payment tracking (deposit, balance, partial, refund)
- Stripe integration (payment_intent_id, charge_id)
- Payment methods: card, check, wire, cash, ach
- Payment status tracking: pending, processing, succeeded, failed, refunded
- Payment schedules with due dates
- Automated balance calculation
- Refund processing
- Invoice line items with categories
- Tax and discount handling
- Accounts Receivable page
- Accounts Payable page

#### Email & Notifications
- SendGrid integration
- Email templates (HTML + plain text):
  - Invoice notification
  - Overdue invoice reminder
  - Upcoming payment reminder
  - Quote approval request
  - Booking confirmation
- Email audit trail (email_logs table)
- RabbitMQ-based notification queue
- Template rendering with Jinja2

#### Airflow Automation
- **Charter Preparation DAG** - Daily charter readiness checks
- **Daily Reports DAG** - Automated reporting at 7 AM
- **Email Notifications DAG** - Workflow-based emails
- **Invoice Generation DAG** - Automatic invoice creation
- **Invoice Payment Reminders DAG** - Every 6 hours
  - Send new invoices
  - Upcoming payment reminders (3 days before)
  - Overdue invoice reminders (every 3 days)
- **Payment Processing DAG** - Payment reconciliation
- **Data Quality DAG** - Validation and integrity checks
- **Vendor Location Sync DAG** - Vendor data synchronization

#### Monitoring & Analytics
- **Business Overview Dashboard**:
  - Total revenue metrics
  - Charter counts by status
  - Vendor performance (charters, revenue, completion rate)
  - Driver performance (NEW - charters, completed, in progress)
- **Operations Dashboard**:
  - Today's charter schedule with driver assignments (NEW)
  - Unassigned charters (vendor AND driver tracking - NEW)
  - Upcoming charter volume (14 days)
- **Charter Locations Dashboard**:
  - Real-time GPS map of active charters
  - Driver name display on map (NEW)
  - Recent check-ins with driver info (NEW)
  - Location history tracking
- **System Metrics Dashboard**:
  - Container health monitoring
  - API response times
  - Database performance
  - Queue depth tracking
- Email report scheduling support (Grafana)
- Prometheus metrics collection
- Alert configuration

#### Frontend (React + TypeScript)
- Material-UI component library
- Responsive design
- Pages:
  - Dashboard (role-specific)
  - Charter list and detail
  - Charter creation and editing
  - Client management
  - Vendor management
  - Driver dashboard (NEW)
  - Accounts Receivable
  - Accounts Payable
  - Document management
- Components:
  - DocumentUploadDialog with progress bar
  - Layout with role-based navigation
  - Status chips with color coding
  - Workflow action buttons
- Services:
  - API client with Kong integration
  - Authentication service
  - Error handling

#### Database Schema
**Tables:**
- users (authentication and profiles)
- charters (with driver_id column - NEW)
- clients
- vehicles
- stops (itinerary)
- invoices
- payments
- payment_schedules
- payment_refunds
- invoice_line_items
- email_logs
- charter_documents
- vendor_payments
- client_payments

**Functions:**
- update_invoice_balance()
- generate_invoice_number()

**Triggers:**
- trigger_update_invoice_balance

#### Data & Seeding
- Comprehensive seed_data.py script
- 12 test users (admin, manager, dispatcher, 5 vendors, 4 drivers)
- 11 sample charters with realistic data
- 9 charters with driver assignments
- Vendor and client pricing populated
- Payment records and schedules
- Location data in coordinate format (40.232550,-74.301440)

#### API Endpoints
**Auth Service:**
- POST /auth/login
- POST /auth/register
- GET /auth/me

**Charter Service:**
- GET /charters
- POST /charters
- GET /charters/{id}
- PUT /charters/{id}
- DELETE /charters/{id}
- GET /charters/driver/my-charter (NEW)
- PATCH /charters/{id}/driver-notes (NEW)
- PATCH /charters/{id}/location (NEW)

**Document Service:**
- POST /documents/upload
- GET /documents/charter/{charter_id}
- GET /documents/{id}
- GET /documents/{id}/download
- DELETE /documents/{id}

**Payment Service:**
- POST /payments
- GET /payments/charter/{charter_id}
- PATCH /payments/{id}/status

**Notification Service:**
- POST /notifications/send
- GET /notifications/templates

---

## Recent Updates (December 2025)

### Driver Feature Implementation
- Added driver_id column to charters table with index
- Created 4 driver test accounts
- Built driver dashboard with location tracking
- Implemented 3 new API endpoints for driver operations
- Added driver fields to CharterResponse Pydantic schema (critical fix)
- Updated frontend routing for driver auto-redirect
- Modified Layout component for driver role (no sidebar)
- JWT token decoding to extract user_id from email

### Grafana Dashboard Updates
- Added driver columns to all relevant SQL queries
- Created Driver Performance dashboard panel
- Updated Today's Schedule to show driver assignments
- Modified unassigned charters to track both vendor AND driver
- Added driver name to location tracking queries
- Restarted Grafana to load new configurations

### Location Data Fix
- Changed all charter locations from street addresses to coordinates
- Format: latitude,longitude (e.g., 40.232550,-74.301440)
- Updated seed_data.py with proper coordinate format
- Fixed dashboard queries to parse coordinates correctly
- Verified SPLIT_PART SQL function works for lat/long extraction

### Documentation Consolidation
- Removed 7 redundant markdown files
- Created comprehensive README.md
- Created QUICKSTART.md with step-by-step instructions
- Created docs/FEATURES.md with detailed feature documentation
- Moved specialized docs to docs/ folder
- Organized all documentation for easy navigation

---

## Known Issues

None currently reported.

---

## Planned Features

### Short Term
- User management UI (create/edit/delete users)
- Vehicle management CRUD operations
- Client portal for quote approvals
- SMS notifications via Twilio
- PDF invoice generation
- Payment gateway testing sandbox

### Medium Term
- Multi-tenant support
- Advanced reporting and analytics
- Calendar view for charter scheduling
- Automated dispatch optimization
- Driver mobile app (native)
- Real-time chat/messaging

### Long Term
- Machine learning for pricing optimization
- Predictive maintenance for vehicles
- Integration with accounting software (QuickBooks)
- Customer loyalty program
- Advanced route optimization
- Fleet management integration

---

## Migration Notes

### Database Migrations Applied
1. Initial schema creation (init_db.sql)
2. Invoice and payment system tables (add_invoice_payment_tables.sql)
3. Workflow and document tracking (add_workflow_document_tracking.sql)
4. Driver field addition (manual ALTER TABLE)

### Configuration Changes
- MongoDB authentication added (authSource=admin)
- Kong routes configured for all 6 services
- Grafana SMTP setup for email reports
- Airflow DAGs deployed and activated
- Seed data updated with driver assignments

---

## Version History

### v1.0 - December 2025
- Initial production-ready release
- All core features implemented
- Driver feature added
- Documentation consolidated
- System fully tested and operational

---

## Contributors

Development Team:
- System Architecture
- Backend Development (FastAPI microservices)
- Frontend Development (React + TypeScript)
- Database Design (PostgreSQL + MongoDB)
- DevOps (Docker, Kong, Airflow)
- Monitoring (Prometheus + Grafana)

---

## License

Proprietary - US Coachways Internal Use Only
