# Feature Documentation

## Driver Feature

### Overview
The driver user type provides a restricted, mobile-friendly interface for drivers to access only their assigned charter information, track location, and leave notes.

### Database Schema
- **Table**: `charters`
- **Column**: `driver_id` (INTEGER, nullable, indexed)
- **Purpose**: Links charter to specific driver user

### User Accounts
Test driver accounts (password: `admin123`):
- driver1@athena.com
- driver2@athena.com
- driver3@athena.com
- driver4@athena.com

### API Endpoints

#### GET `/api/v1/charters/driver/my-charter`
Returns the charter assigned to the logged-in driver.

**Response:**
```json
{
  "id": 1,
  "trip_date": "2025-12-15",
  "status": "confirmed",
  "passengers": 25,
  "vehicle": {...},
  "itinerary": [...]
}
```

#### PATCH `/api/v1/charters/{charter_id}/driver-notes`
Allows driver to update notes field.

**Request:**
```json
{
  "vendor_notes": "Traffic heavy on I-95. Running 10 minutes behind."
}
```

#### PATCH `/api/v1/charters/{charter_id}/location`
Updates driver's current GPS location.

**Request:**
```json
{
  "location": "40.232550,-74.301440",
  "timestamp": "2025-12-08T14:30:00Z"
}
```

### Frontend Features

#### Driver Dashboard (`/driver`)
1. **Charter Details Card**
   - Trip date, status, passenger count
   - Vehicle information
   - Read-only charter notes

2. **Location Tracking**
   - Browser geolocation API
   - Auto-updates every 2 minutes
   - Start/stop toggle button
   - Displays current lat/long

3. **Trip Itinerary**
   - All stops in sequence
   - Location, arrival/departure times
   - Stop-specific notes

4. **Driver Notes**
   - Multi-line text area
   - Save button
   - Updates charter `vendor_notes` field

### User Experience
- Drivers auto-redirect to `/driver` on login
- No sidebar navigation (full-width layout)
- Only header with avatar and logout
- Blocked from all other routes
- Mobile-optimized responsive design

---

## Invoice & Payment System

### Overview
Comprehensive invoicing, payment tracking, and automated email reminders integrated with Stripe.

### Database Tables

#### invoices
- Auto-generated invoice numbers (INV-00001, INV-00002...)
- Status: draft, sent, paid, overdue, cancelled, refunded
- Amount tracking: subtotal, tax, discount, total, paid, balance
- Payment terms and due dates
- Email tracking

#### payments
- Stripe integration (payment_intent_id, charge_id)
- Payment types: deposit, balance, partial, refund
- Methods: card, check, wire, cash, ach
- Status: pending, processing, succeeded, failed, refunded
- Card details (last 4, brand)

#### payment_schedules
- Payment due dates and reminder tracking
- Types: deposit, balance, installments
- Status: pending, sent_reminder, paid, overdue, waived
- Automatic reminder date calculation

#### payment_refunds
- Refund amount and reason
- Stripe refund tracking
- Processing status

#### invoice_line_items
- Detailed invoice breakdowns
- Categories: base_rate, mileage, fuel_surcharge, tolls, etc.

#### email_logs
- Audit trail for all sent emails
- Types: quote, invoice, reminder, approval, confirmation
- Status: sent, failed, bounced, opened, clicked
- SendGrid message IDs

### Automation (Airflow)

#### DAG: invoice_payment_reminders
**Schedule**: Every 6 hours

**Tasks**:
1. **send_new_invoices** - Send newly created draft invoices
2. **send_upcoming_payment_reminders** - 3 days before due date
3. **send_overdue_invoice_reminders** - Every 3 days for past due

### Email Templates
- invoice_notification
- overdue_invoice_reminder
- upcoming_payment_reminder
- quote_approval_request
- booking_confirmation

### Frontend Pages
- **Accounts Receivable** (`/accounting/receivable`) - Client payments
- **Accounts Payable** (`/accounting/payable`) - Vendor payments
- **Invoice Management** - Create, send, track invoices

---

## Document Management

### Overview
File upload and storage system using MongoDB GridFS for charter-related documents.

### Infrastructure
- **Service**: document-service (port 8003)
- **Storage**: MongoDB 7.0 with GridFS
- **Database**: athena_documents
- **Max File Size**: 10MB

### Supported File Types
- **Documents**: PDF, DOC, DOCX, XLS, XLSX, TXT, CSV
- **Images**: JPG, JPEG, PNG, GIF, BMP

### API Endpoints

#### POST `/api/v1/documents/upload`
Upload a document for a charter.

**Form Data:**
- `file`: File binary
- `charter_id`: Integer
- `document_type`: approval | booking | confirmation | contract | invoice | receipt | insurance | other
- `description`: Optional string

#### GET `/api/v1/documents/charter/{charter_id}`
List all documents for a charter.

#### GET `/api/v1/documents/{id}/download`
Download document by ID.

#### DELETE `/api/v1/documents/{id}`
Delete document (admin/superuser only).

### Database Schema

#### PostgreSQL: charter_documents
- Document metadata
- References to MongoDB GridFS files
- Upload tracking

#### MongoDB: GridFS
- Binary file storage
- Automatic file chunking
- Metadata includes charter_id and document_type

### Workflow Integration
Documents can be uploaded at specific workflow stages:
- **Quote → Approved**: Upload approval document
- **Approved → Booked**: Upload booking confirmation
- **Booked → Confirmed**: Upload client confirmation

### Frontend Component
`DocumentUploadDialog.tsx` provides:
- File selection and validation
- Progress bar with percentage
- Custom fields (approval amount, booking cost)
- Error handling
- MIME type checking

---

## Charter Workflow

### Workflow Stages

```
Quote → Approved → Booked → Confirmed → In Progress → Completed
```

#### 1. Quote
- Initial charter request
- Pricing calculation
- Action: "Send for Approval" (sends email to client)

#### 2. Approved
- Client has approved quote
- Ready for vendor assignment
- Action: "Vendor Booked" (upload booking doc)

#### 3. Booked
- Vendor confirmed
- Booking cost recorded
- Action: "Send Confirmation" (email to client)

#### 4. Confirmed
- Client confirmed booking
- Charter ready for execution
- Driver can be assigned

#### 5. In Progress
- Charter actively running
- Driver tracking location
- Notes being updated

#### 6. Completed
- Trip finished successfully
- Ready for invoicing
- Final notes recorded

### Automated Actions
- Email notifications at each stage
- Document upload prompts
- Payment schedule creation
- Invoice generation (on completion)
- Reminder emails (Airflow)

---

## Monitoring & Dashboards

### Grafana Dashboards

#### Business Overview
- **Revenue Metrics**: Total, monthly, by client
- **Charter Counts**: By status, by vehicle type
- **Vendor Performance**: Charter count, revenue, completion rate
- **Driver Performance**: Charters, completed, in progress

#### Operations Dashboard
- **Today's Schedule**: All charters for current date with driver assignments
- **Unassigned Charters**: Missing vendor or driver
- **Upcoming Volume**: 14-day charter forecast

#### Charter Locations
- **Active Charter Map**: Real-time GPS positions
- **Recent Check-ins**: Last 20 location updates with driver info
- **Location History**: Track charter movements

#### System Metrics
- **Container Health**: All 21 containers
- **API Response Times**: Per service
- **Database Performance**: Query times, connections
- **Queue Depth**: RabbitMQ message counts

### Email Reports
Grafana can send scheduled PDF reports:
1. Configure SMTP in docker-compose.yml
2. Use Grafana UI to create report schedule
3. Select dashboard and recipients
4. Choose frequency (daily, weekly, monthly)

---

## Location Tracking

### Coordinate Format
All charter locations use coordinate format: `latitude,longitude`

Example: `40.232550,-74.301440`

### Dashboard Queries
SQL queries use `SPLIT_PART` to parse coordinates:
```sql
CAST(SPLIT_PART(last_checkin_location, ',', 1) AS FLOAT) AS latitude,
CAST(SPLIT_PART(last_checkin_location, ',', 2) AS FLOAT) AS longitude
```

### Driver Location Updates
- Browser Geolocation API
- Updates every 2 minutes when tracking active
- Stored in `charters.last_checkin_location`
- Timestamp in `charters.last_checkin_time`

### Map Visualization
Grafana geomap panel displays:
- Active charter positions
- Driver assignments
- Vehicle information
- Client names
- Last check-in time

---

## Pricing Engine

### Calculation Method
- **Base Cost**: From vehicle rate card × hours
- **Mileage Cost**: Distance × $2.50/mile
- **Additional Fees**: Tolls, parking, etc.

### Vendor Pricing (75% of client charge)
- `vendor_base_cost` = client_base × 0.75
- `vendor_mileage_cost` = client_mileage × 0.75
- `vendor_additional_fees` = client_fees × 0.75

### Client Pricing (100%)
- `client_base_charge` = base cost
- `client_mileage_charge` = mileage cost
- `client_additional_fees` = additional fees

### Profit Margin
Default 25% margin on all charges
`profit_margin = (client_total - vendor_total) / client_total`

### Tax Calculation
- Configurable tax rate per charter
- Applied to subtotal before total
- Stored separately for reporting

---

## API Gateway (Kong)

### Service Routes
All microservices accessible via Kong on port 8080:

```
/api/v1/auth/*       → athena-auth-service:8000
/api/v1/charters/*   → athena-charter-service:8000
/api/v1/clients/*    → athena-client-service:8000
/api/v1/documents/*  → athena-document-service:8000
/api/v1/notifications/* → athena-notification-service:8000
/api/v1/payments/*   → athena-payment-service:8000
```

### Features
- Rate limiting
- Request/response logging
- API key authentication
- CORS handling
- Load balancing (when scaled)

### Admin API
Kong admin API on port 8001:
- View services: `curl http://localhost:8001/services`
- View routes: `curl http://localhost:8001/routes`
- Health check: `curl http://localhost:8001/status`
