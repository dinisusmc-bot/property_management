# Comprehensive Gap Analysis & Implementation Plan
## CoachWay Demo - Backend Capabilities vs Client Requirements

**Date:** January 31, 2026  
**Scope:** Backend services enhancement and new service development  
**Testing Strategy:** Admin portal-first, then role-specific UIs

---

## Executive Summary

### Current State
- **6 Backend Services Implemented:** Auth, Charter, Client, Document, Payment, Notification
- **60+ API Endpoints** across all services
- **14 Database Tables** (PostgreSQL + MongoDB GridFS)
- **8 Airflow DAGs** for automation
- **Basic Admin UI** with charter/client/user management

### Gap Analysis Results
- **✅ COMPLETE:** 28% of client requirements (core CRUD, basic booking workflow)
- **🟡 PARTIAL:** 35% of requirements (foundations exist, need enhancement)
- **🟠 STUB:** 12% of requirements (placeholders only)
- **❌ MISSING:** 25% of requirements (new development needed)

### Services Requiring Work

#### **ENHANCE Existing Services (6)**
1. Auth Service - Add RBAC field-level permissions, role management UI
2. Charter Service - Add itinerary multi-stop, recurring charters, cloning
3. Client Service - Add lead management extensions
4. Payment Service - Complete QuickBooks sync, AR/AP aging reports
5. Notification Service - Add email preference management, template UI
6. Document Service - Add COI tracking, expiration alerts

#### **BUILD New Services (4)**
1. **Sales Service** (Port 8007) - Lead management, pipeline, assignment
2. **Pricing Service** (Port 8008) - Modifiers, promo codes, configuration UI
3. **Vendor Service** (Port 8006) - Vendor portal, bid management, COI tracking
4. **Change Management Service** (Port 8010) - Change case workflow, approval process

---

## Part 1: Detailed Gap Analysis by Functional Area

### 1. LEAD & OPPORTUNITY MANAGEMENT

#### Client Requirements (Sales Agents Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Lead capture with contact info | ❌ MISSING | No lead table exists | Need Sales Service with leads table |
| Lead assignment (round-robin) | ❌ MISSING | No assignment logic | Need assignment algorithm + queue management |
| Lead assignment (existing client auto-assign) | ❌ MISSING | No client matching | Need client lookup by email/phone |
| Recent leads view (last 30 days) | ❌ MISSING | No lead queries | Need API endpoint with date filters |
| Open quotes view (next 120 days) | 🟡 PARTIAL | Charter service has quotes | Need status filter + date range query |
| Convert lead → quote (one step) | ❌ MISSING | No lead-to-charter conversion | Need conversion endpoint |
| Follow-up email tracking | ❌ MISSING | No email tracking | Need email_log table + tracking |
| Disable automated emails per client | ❌ MISSING | No preference system | Need client_email_preferences table |
| Lead scoring/prioritization | ❌ MISSING | No scoring logic | Future enhancement (P3) |
| Hot leads / Pipeline tracking | ❌ MISSING | No pipeline stages | Need lead status workflow |

#### Implementation Plan
**New Service Required:** Sales Service (Port 8007)

**Database Schema Additions:**
```sql
-- New table: leads
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  source VARCHAR(50) NOT NULL,  -- online, phone, email, referral, walk-in
  status VARCHAR(20) DEFAULT 'new',  -- new, contacted, qualified, quoted, converted, lost
  lead_score INT DEFAULT 0,
  
  -- Contact info
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  company VARCHAR(255),
  
  -- Trip details
  trip_date DATE,
  origin VARCHAR(255),
  destination VARCHAR(255),
  passenger_count INT,
  vehicle_type VARCHAR(50),
  
  -- Assignment
  assigned_to INT REFERENCES users(id),
  assigned_at TIMESTAMP,
  assignment_method VARCHAR(20),  -- round_robin, manual, existing_client
  
  -- Tracking
  last_contact_date TIMESTAMP,
  next_follow_up TIMESTAMP,
  contact_count INT DEFAULT 0,
  
  -- Conversion
  converted_to_charter_id INT REFERENCES charters(id),
  converted_at TIMESTAMP,
  lost_reason TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: lead_assignment_queue
CREATE TABLE lead_assignment_queue (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) UNIQUE,
  position INT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  max_daily_leads INT DEFAULT NULL,
  leads_assigned_today INT DEFAULT 0,
  last_assigned_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: lead_activities
CREATE TABLE lead_activities (
  id SERIAL PRIMARY KEY,
  lead_id INT REFERENCES leads(id),
  activity_type VARCHAR(50) NOT NULL,  -- email, call, meeting, note
  description TEXT,
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: email_tracking
CREATE TABLE email_tracking (
  id SERIAL PRIMARY KEY,
  lead_id INT REFERENCES leads(id),
  charter_id INT REFERENCES charters(id),
  client_id INT REFERENCES clients(id),
  email_type VARCHAR(50) NOT NULL,
  recipient_email VARCHAR(255) NOT NULL,
  subject VARCHAR(500),
  sent_at TIMESTAMP,
  opened_at TIMESTAMP,
  clicked_at TIMESTAMP,
  status VARCHAR(20) DEFAULT 'sent',
  sendgrid_message_id VARCHAR(255)
);

-- New table: client_email_preferences
CREATE TABLE client_email_preferences (
  id SERIAL PRIMARY KEY,
  client_id INT REFERENCES clients(id) UNIQUE,
  automated_quotes_enabled BOOLEAN DEFAULT true,
  automated_reminders_enabled BOOLEAN DEFAULT true,
  automated_followups_enabled BOOLEAN DEFAULT true,
  marketing_enabled BOOLEAN DEFAULT true,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints Needed:**
```
POST   /api/v1/leads                      # Create lead
GET    /api/v1/leads                      # List (filters: status, assigned_to, date_range)
GET    /api/v1/leads/{id}                 # Get lead details
PUT    /api/v1/leads/{id}                 # Update lead
POST   /api/v1/leads/{id}/convert         # Convert to charter
POST   /api/v1/leads/{id}/activities      # Log activity
GET    /api/v1/leads/{id}/activities      # Get activity history

GET    /api/v1/leads/pipeline             # Pipeline view (grouped by status)
GET    /api/v1/leads/my-leads             # Current user's leads
POST   /api/v1/leads/assign               # Manual assignment
GET    /api/v1/leads/assignment-queue     # View queue order
PUT    /api/v1/leads/assignment-queue     # Update queue settings

GET    /api/v1/email-preferences/{client_id}  # Get preferences
PUT    /api/v1/email-preferences/{client_id}  # Update preferences
```

**Admin Portal Testing Pages:**
- `/admin/leads` - Lead list with filters
- `/admin/leads/{id}` - Lead detail + activity timeline
- `/admin/leads/pipeline` - Kanban-style pipeline view
- `/admin/leads/assignment` - Queue management UI

---

### 2. QUOTE BUILDER & ITINERARY

#### Client Requirements (Sales Agents Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Mirror client-facing quote calculator | ✅ COMPLETE | Charter service has calculator | Exists in QuoteLanding.tsx |
| Multi-stop itinerary builder | 🟡 PARTIAL | `itinerary_stops` table exists | Need drag/reorder UI + sequence management |
| Geocoding locations | ❌ MISSING | No geocoding service | Need Google Maps Geocoding API integration |
| DOT regulation checks (hours/miles) | ❌ MISSING | No compliance logic | Need DOT rules engine |
| Second driver flag | ❌ MISSING | No driver count field | Need `requires_second_driver` field + logic |
| Trip type selector | 🟡 PARTIAL | Has `is_overnight` only | Need `trip_type` enum field |
| Auto vehicle recommendations | 🟡 PARTIAL | Basic capacity matching | Need recommendation engine |
| Manual vehicle override | ✅ COMPLETE | Can select any vehicle | Works in current UI |
| Add/remove vehicles from quote | ❌ MISSING | Single vehicle only | Need multi-vehicle support |
| Edit vehicle count | ❌ MISSING | No count field | Need `vehicle_count` field |
| Promo codes | ❌ MISSING | No promo system | Need Pricing Service |
| Amenity selection | ❌ MISSING | No amenity system | Need amenities table + pricing |
| Amenity real-time pricing | ❌ MISSING | No pricing API | Need dynamic calculation endpoint |
| Email quote with secure link | 🟡 PARTIAL | Can email, no secure link | Need signed JWT link |
| Revise/resend without duplication | 🟡 PARTIAL | Can update charter | Need revision tracking |

#### Implementation Plan
**Services to Enhance:** Charter Service, Pricing Service (NEW)

**Charter Service - Database Schema Updates:**
```sql
-- Modify charters table
ALTER TABLE charters ADD COLUMN trip_type VARCHAR(50);
-- one_way, round_trip, overnight, multi_day, local, shuttle, event

ALTER TABLE charters ADD COLUMN requires_second_driver BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN vehicle_count INT DEFAULT 1;
ALTER TABLE charters ADD COLUMN revision_number INT DEFAULT 1;
ALTER TABLE charters ADD COLUMN parent_quote_id INT REFERENCES charters(id);
ALTER TABLE charters ADD COLUMN quote_secure_token VARCHAR(255) UNIQUE;

-- New table: charter_amenities
CREATE TABLE charter_amenities (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  amenity_id INT REFERENCES amenities(id),
  quantity INT DEFAULT 1,
  price_per_unit DECIMAL(10,2),
  total_price DECIMAL(10,2),
  added_at TIMESTAMP DEFAULT NOW()
);

-- Modify itinerary_stops table
ALTER TABLE itinerary_stops ADD COLUMN latitude DECIMAL(10,7);
ALTER TABLE itinerary_stops ADD COLUMN longitude DECIMAL(10,7);
ALTER TABLE itinerary_stops ADD COLUMN geocoded_address TEXT;
ALTER TABLE itinerary_stops ADD COLUMN stop_type VARCHAR(20);
-- pickup, dropoff, waypoint, stop

ALTER TABLE itinerary_stops ADD COLUMN estimated_arrival TIME;
ALTER TABLE itinerary_stops ADD COLUMN estimated_departure TIME;
ALTER TABLE itinerary_stops ADD COLUMN actual_arrival TIMESTAMP;
ALTER TABLE itinerary_stops ADD COLUMN actual_departure TIMESTAMP;
```

**Pricing Service - NEW SERVICE (Port 8008)**

**Database Schema:**
```sql
-- New table: amenities
CREATE TABLE amenities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  category VARCHAR(50),  -- refreshments, entertainment, comfort, accessibility
  base_price DECIMAL(10,2) NOT NULL,
  pricing_type VARCHAR(20),  -- flat_fee, per_passenger, per_hour, per_day
  is_active BOOLEAN DEFAULT true,
  display_order INT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: promo_codes
CREATE TABLE promo_codes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  description TEXT,
  discount_type VARCHAR(20) NOT NULL,  -- percentage, fixed_amount
  discount_value DECIMAL(10,2) NOT NULL,
  
  -- Validity
  valid_from DATE,
  valid_until DATE,
  max_uses INT,
  uses_count INT DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  
  -- Restrictions
  min_purchase_amount DECIMAL(10,2),
  applicable_vehicle_types TEXT[],  -- ARRAY
  applicable_trip_types TEXT[],
  
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: promo_code_usage
CREATE TABLE promo_code_usage (
  id SERIAL PRIMARY KEY,
  promo_code_id INT REFERENCES promo_codes(id),
  charter_id INT REFERENCES charters(id),
  client_id INT REFERENCES clients(id),
  discount_amount DECIMAL(10,2),
  used_at TIMESTAMP DEFAULT NOW()
);

-- New table: pricing_modifiers
CREATE TABLE pricing_modifiers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  modifier_type VARCHAR(50) NOT NULL,
  -- day_of_week, event_based, hub_based, asap, peak_season, holiday
  
  adjustment_type VARCHAR(20) NOT NULL,  -- percentage, fixed_amount
  adjustment_value DECIMAL(10,2) NOT NULL,
  
  -- Conditions
  applicable_days TEXT[],  -- ['monday', 'friday']
  applicable_hubs TEXT[],
  event_types TEXT[],
  date_ranges JSONB,  -- [{start: '2026-07-01', end: '2026-07-04'}]
  
  priority INT DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: dot_regulations
CREATE TABLE dot_regulations (
  id SERIAL PRIMARY KEY,
  regulation_name VARCHAR(100) NOT NULL,
  regulation_type VARCHAR(50),  -- driving_hours, distance, rest_period
  threshold_value DECIMAL(10,2) NOT NULL,
  threshold_unit VARCHAR(20),  -- hours, miles
  requires_second_driver BOOLEAN DEFAULT false,
  description TEXT,
  is_active BOOLEAN DEFAULT true
);
```

**Pricing Service API Endpoints:**
```
POST   /api/v1/calculate-quote            # Full quote calculation with amenities
POST   /api/v1/validate-promo-code        # Check promo code validity
POST   /api/v1/check-dot-compliance       # Check if trip requires 2nd driver

GET    /api/v1/amenities                  # List available amenities
GET    /api/v1/amenities/{id}             # Get amenity details

GET    /api/v1/promo-codes                # List promo codes (admin)
POST   /api/v1/promo-codes                # Create promo code
PUT    /api/v1/promo-codes/{id}           # Update promo code
DELETE /api/v1/promo-codes/{id}           # Deactivate promo code

GET    /api/v1/pricing-modifiers          # List modifiers
POST   /api/v1/pricing-modifiers          # Create modifier
PUT    /api/v1/pricing-modifiers/{id}     # Update modifier
DELETE /api/v1/pricing-modifiers/{id}     # Delete modifier

GET    /api/v1/pricing-config             # Get all pricing configuration
PUT    /api/v1/pricing-config             # Update pricing rules
```

**Charter Service - New API Endpoints:**
```
POST   /api/v1/charters/{id}/geocode-stops     # Geocode all stops
PUT    /api/v1/charters/{id}/reorder-stops     # Reorder itinerary sequence
POST   /api/v1/charters/{id}/amenities         # Add amenity
DELETE /api/v1/charters/{id}/amenities/{aid}   # Remove amenity
POST   /api/v1/charters/{id}/calculate         # Recalculate with amenities
GET    /api/v1/charters/{id}/secure-link       # Get secure quote link
POST   /api/v1/charters/{id}/revise            # Create revision (increment version)
```

**Admin Portal Testing Pages:**
- `/admin/charters/new` - Enhanced quote builder with multi-stop map
- `/admin/charters/{id}/edit` - Itinerary management with drag/drop
- `/admin/pricing/amenities` - Amenity management
- `/admin/pricing/promo-codes` - Promo code CRUD
- `/admin/pricing/modifiers` - Pricing modifier configuration
- `/admin/pricing/dot-rules` - DOT compliance configuration

---

### 3. CLIENT PORTAL & BOOKING FLOW

#### Client Requirements (Sales Agents + Clients Roles)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| View client portal as agent | ❌ MISSING | No impersonation | Need "View as client" feature |
| Seamless client login | 🟡 PARTIAL | Auth exists, no MFA | Need MFA, forgot password |
| Email-based login | ✅ COMPLETE | Uses email for login | Works |
| Frictionless new client entry | 🟡 PARTIAL | Can create client | Need auto-account on first booking |
| Client payment status view | 🟡 PARTIAL | Payment tables exist | Need client portal UI |
| Client payment methods view | ❌ MISSING | No saved payment methods | Need Stripe Customer Portal |
| Booking notification task | ❌ MISSING | No task system | Need task assignment |
| View current/historical trips | 🟡 PARTIAL | Charter list exists | Need client-scoped queries |
| View quotes for future trips | 🟡 PARTIAL | Charter status='quote' exists | Need client portal UI |
| Detailed itinerary view | ✅ COMPLETE | Itinerary stops exist | Need portal UI |
| Payment breakdown | 🟡 PARTIAL | Payment records exist | Need portal display |
| Flexible payment (CC, PO, ACH) | 🟡 PARTIAL | Stripe CC works | Need ACH, PO tracking |
| E-signature for terms | ❌ MISSING | No signature system | Need DocuSign or custom |
| Zero-balance confirmation | 🟡 PARTIAL | Can calculate balance | Need confirmation page |
| Opt-in SMS updates | ❌ MISSING | No SMS preferences | Need preferences table |

#### Implementation Plan
**Services to Enhance:** Auth Service, Payment Service, Client Service  
**New Service:** Portals Service (Port 8009)

**Auth Service Enhancements:**
```sql
-- Modify users table
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(255);
ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45);

-- New table: user_sessions
CREATE TABLE user_sessions (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  session_token VARCHAR(255) UNIQUE NOT NULL,
  impersonated_by INT REFERENCES users(id),  -- For "View as client"
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  last_activity TIMESTAMP DEFAULT NOW()
);
```

**Payment Service Enhancements:**
```sql
-- New table: saved_payment_methods
CREATE TABLE saved_payment_methods (
  id SERIAL PRIMARY KEY,
  client_id INT REFERENCES clients(id),
  stripe_payment_method_id VARCHAR(255) UNIQUE NOT NULL,
  type VARCHAR(20),  -- card, bank_account
  
  -- Card details
  card_brand VARCHAR(20),
  card_last4 VARCHAR(4),
  card_exp_month INT,
  card_exp_year INT,
  
  -- Bank details
  bank_name VARCHAR(100),
  bank_account_last4 VARCHAR(4),
  bank_routing_last4 VARCHAR(4),
  
  is_default BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: payment_plans
CREATE TABLE payment_plans (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id) UNIQUE,
  
  deposit_amount DECIMAL(10,2) NOT NULL,
  deposit_due_date DATE NOT NULL,
  deposit_paid BOOLEAN DEFAULT false,
  deposit_paid_at TIMESTAMP,
  
  balance_amount DECIMAL(10,2) NOT NULL,
  balance_due_date DATE NOT NULL,
  balance_paid BOOLEAN DEFAULT false,
  balance_paid_at TIMESTAMP,
  
  custom_installments JSONB,  -- For multi-payment plans
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: e_signatures
CREATE TABLE e_signatures (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  client_id INT REFERENCES clients(id),
  document_type VARCHAR(50),  -- terms_conditions, contract, waiver
  signature_data TEXT,  -- Base64 or DocuSign envelope ID
  ip_address VARCHAR(45),
  signed_at TIMESTAMP DEFAULT NOW()
);
```

**Client Service Enhancements:**
```sql
-- Modify clients table
ALTER TABLE clients ADD COLUMN sms_notifications_enabled BOOLEAN DEFAULT false;
ALTER TABLE clients ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT true;
ALTER TABLE clients ADD COLUMN stripe_customer_id VARCHAR(255) UNIQUE;
ALTER TABLE clients ADD COLUMN auto_pay_enabled BOOLEAN DEFAULT false;
ALTER TABLE clients ADD COLUMN preferred_payment_method_id INT;
ALTER TABLE clients ADD COLUMN portal_password_set BOOLEAN DEFAULT false;
```

**Portals Service - NEW SERVICE (Port 8009)**

**API Endpoints:**
```
# Client Portal
POST   /api/v1/portal/client/login            # Client authentication
POST   /api/v1/portal/client/register         # New client registration
POST   /api/v1/portal/client/forgot-password  # Password reset request
POST   /api/v1/portal/client/reset-password   # Complete password reset
POST   /api/v1/portal/client/enable-mfa       # Enable MFA
POST   /api/v1/portal/client/verify-mfa       # Verify MFA code

GET    /api/v1/portal/client/dashboard        # Dashboard with upcoming trips
GET    /api/v1/portal/client/charters         # My charters (filters: status, date)
GET    /api/v1/portal/client/charters/{id}    # Charter details
GET    /api/v1/portal/client/quotes           # My quotes
POST   /api/v1/portal/client/quotes/{id}/accept  # Accept quote

GET    /api/v1/portal/client/payments         # Payment history
GET    /api/v1/portal/client/payment-methods  # Saved payment methods
POST   /api/v1/portal/client/payment-methods  # Add payment method
DELETE /api/v1/portal/client/payment-methods/{id}  # Remove payment method
POST   /api/v1/portal/client/make-payment     # Make payment

POST   /api/v1/portal/client/sign-document    # E-sign document
GET    /api/v1/portal/client/documents        # My documents

PUT    /api/v1/portal/client/preferences      # Update notification preferences

# Agent Impersonation
POST   /api/v1/admin/impersonate/{client_id}  # Start impersonation session
POST   /api/v1/admin/stop-impersonation       # End impersonation
```

**Admin Portal Testing Pages:**
- `/admin/clients/{id}/portal-view` - View as client (impersonation)
- `/admin/payments/methods` - Saved payment methods management
- `/admin/payments/plans` - Payment plan configuration
- `/admin/documents/signatures` - E-signature tracking

**Client Portal Pages (for reference):**
- `/portal/login` - Client login with MFA
- `/portal/dashboard` - Client dashboard
- `/portal/trips` - My trips list
- `/portal/trips/{id}` - Trip details
- `/portal/payments` - Payment history
- `/portal/settings` - Notification preferences

---

### 4. PRE-BOOKING CHARTER TOOLS

#### Client Requirements (Sales Agents Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Clone/duplicate charter | ❌ MISSING | No clone endpoint | Need duplicate with date picker |
| Multi-date cloning (calendar) | ❌ MISSING | No batch operations | Need batch creation API |
| Recurring charter support | ❌ MISSING | No recurrence | Need recurrence_rule + series management |
| Instance-level delete (recurring) | ❌ MISSING | No instance tracking | Need parent/child relationship |
| Document attachments | ✅ COMPLETE | Document service exists | Already works |
| Vendor bid attachments | 🟡 PARTIAL | Can attach documents | Need bid-specific document type |
| Client doc attachments | ✅ COMPLETE | Document service works | Already works |
| T&C attachments | 🟡 PARTIAL | Can attach documents | Need T&C document type |
| Assign quote to another agent | ❌ MISSING | No reassignment | Need ownership transfer endpoint |
| Prevent taking others' quotes | 🟡 PARTIAL | Has ownership field | Need permission checks |

#### Implementation Plan
**Service to Enhance:** Charter Service

**Database Schema Updates:**
```sql
-- Modify charters table
ALTER TABLE charters ADD COLUMN recurrence_rule TEXT;
-- RRULE format: "FREQ=DAILY;COUNT=20" or "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=12"

ALTER TABLE charters ADD COLUMN parent_charter_id INT REFERENCES charters(id);
ALTER TABLE charters ADD COLUMN instance_number INT;
ALTER TABLE charters ADD COLUMN series_total INT;
ALTER TABLE charters ADD COLUMN is_series_master BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN cloned_from_charter_id INT REFERENCES charters(id);

ALTER TABLE charters ADD COLUMN assigned_sales_agent_id INT REFERENCES users(id);
ALTER TABLE charters ADD COLUMN assigned_at TIMESTAMP;
ALTER TABLE charters ADD COLUMN assigned_by INT REFERENCES users(id);

-- New table: charter_series
CREATE TABLE charter_series (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  recurrence_rule TEXT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE,
  master_charter_id INT REFERENCES charters(id),
  total_instances INT,
  active_instances INT,
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Modify charter_documents table
ALTER TABLE charter_documents ADD COLUMN document_category VARCHAR(50);
-- vendor_bid, client_document, terms_conditions, contract, invoice, receipt
```

**New API Endpoints:**
```
POST   /api/v1/charters/{id}/clone              # Clone single charter
POST   /api/v1/charters/{id}/clone-multiple     # Clone to multiple dates
POST   /api/v1/charters/create-recurring        # Create recurring series
GET    /api/v1/charters/series/{series_id}      # Get series instances
DELETE /api/v1/charters/{id}/from-series        # Delete instance from series
PUT    /api/v1/charters/{id}/assign-agent       # Reassign to another agent
GET    /api/v1/charters/my-quotes               # Current user's quotes only
```

**Clone Request Schema:**
```json
{
  "charter_id": 123,
  "new_dates": ["2026-02-15", "2026-02-22", "2026-03-01"],
  "adjust_pricing": true,
  "copy_documents": false,
  "copy_vendor_assignment": true
}
```

**Recurring Charter Request Schema:**
```json
{
  "base_charter_id": 123,
  "series_name": "Daily Shuttle - Corporate Campus",
  "recurrence_rule": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR;COUNT=60",
  "start_date": "2026-02-01",
  "end_date": "2026-05-01",
  "adjust_pricing_per_instance": false
}
```

**Admin Portal Testing Pages:**
- `/admin/charters/{id}` - Add "Clone" button with date picker modal
- `/admin/charters/{id}` - Add "Create Recurring" button
- `/admin/charters/series/{id}` - Series management view with instance list
- `/admin/charters/{id}` - Add "Reassign Agent" dropdown

---

### 5. SALES AGENT DASHBOARD & REPORTS

#### Client Requirements (Sales Agents Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Open quotes count | 🟡 PARTIAL | Can query charters | Need aggregation endpoint |
| Follow-ups due | ❌ MISSING | No follow-up tracking | Need lead follow-up dates |
| Leads received today | ❌ MISSING | No lead system | Need leads table |
| Upcoming departures | 🟡 PARTIAL | Can query charters | Need date filter + my clients only |
| Non-CC money due | 🟡 PARTIAL | Payment tracking exists | Need report aggregation |
| MTD booked revenue | ❌ MISSING | No reporting | Need financial aggregation |
| MTD profit | ❌ MISSING | No profit tracking | Need profit calculation |
| Hot leads | ❌ MISSING | No lead scoring | Need hot lead definition |
| Pipeline tracking | ❌ MISSING | No pipeline stages | Need stage-based workflow |
| Filtered to own clients | 🟡 PARTIAL | Has assigned_to field | Need consistent data scoping |

#### Implementation Plan
**Services: Sales Service (NEW), Reporting Module in multiple services**

**Sales Service - Dashboard API Endpoints:**
```
GET    /api/v1/dashboard/sales-agent          # Complete agent dashboard
GET    /api/v1/dashboard/sales-agent/metrics  # Key metrics summary
GET    /api/v1/reports/sales-agent/pipeline   # Pipeline breakdown
GET    /api/v1/reports/sales-agent/mtd        # Month-to-date stats
GET    /api/v1/reports/sales-agent/upcoming   # Upcoming departures
```

**Dashboard Response Schema:**
```json
{
  "metrics": {
    "open_quotes": 12,
    "leads_received_today": 3,
    "leads_received_this_month": 47,
    "follow_ups_due_today": 5,
    "follow_ups_overdue": 2,
    "upcoming_departures_7days": 8,
    "non_cc_money_due": 15000.00,
    "mtd_booked_revenue": 125000.00,
    "mtd_profit": 31250.00,
    "hot_leads_count": 4
  },
  "pipeline": {
    "new": 8,
    "contacted": 15,
    "qualified": 10,
    "quoted": 12,
    "converted": 25,
    "lost": 5
  },
  "recent_activities": [
    {
      "type": "lead_assigned",
      "lead_id": 456,
      "timestamp": "2026-01-31T10:30:00Z"
    }
  ]
}
```

**Admin Portal Testing Pages:**
- `/admin/dashboard/sales` - Sales agent dashboard (filtered to logged-in agent)
- `/admin/reports/sales/pipeline` - Pipeline visualization
- `/admin/reports/sales/mtd` - Month-to-date performance

---

### 6. CHANGE MANAGEMENT

#### Client Requirements (Sales Support Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Change case dashboard | ❌ MISSING | No change case system | Need Change Management Service |
| Auto-create on booking change | ❌ MISSING | No trigger system | Need change detection logic |
| Full change history (who/what/when) | 🟡 PARTIAL | Has updated_at field | Need detailed audit log |
| Workflow: review → vendor re-quote → client approval | ❌ MISSING | No workflow engine | Need status-based workflow |
| Post-booking amenity changes | 🟡 PARTIAL | Can update amenities | Need change tracking |
| Change snapshots | ❌ MISSING | No versioning | Need before/after snapshots |

#### Implementation Plan
**New Service:** Change Management Service (Port 8010)

**Database Schema:**
```sql
-- New table: change_cases
CREATE TABLE change_cases (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id) NOT NULL,
  case_number VARCHAR(50) UNIQUE NOT NULL,  -- CC-00001, CC-00002
  
  change_type VARCHAR(50) NOT NULL,
  -- date_change, time_change, location_change, vehicle_change, 
  -- passenger_count_change, amenity_change, cancellation, other
  
  status VARCHAR(20) DEFAULT 'pending',
  -- pending, under_review, vendor_quoted, awaiting_client_approval, 
  -- approved, rejected, implemented, cancelled
  
  -- Change details
  description TEXT NOT NULL,
  requested_by INT REFERENCES users(id),
  requested_at TIMESTAMP DEFAULT NOW(),
  
  -- Workflow tracking
  reviewed_by INT REFERENCES users(id),
  reviewed_at TIMESTAMP,
  review_notes TEXT,
  
  vendor_quoted_at TIMESTAMP,
  vendor_quote_amount DECIMAL(10,2),
  vendor_notes TEXT,
  
  client_notified_at TIMESTAMP,
  client_approved_at TIMESTAMP,
  client_approval_method VARCHAR(20),  -- email, phone, portal
  
  implemented_by INT REFERENCES users(id),
  implemented_at TIMESTAMP,
  
  -- Financial impact
  price_difference DECIMAL(10,2),
  requires_additional_payment BOOLEAN DEFAULT false,
  payment_received BOOLEAN DEFAULT false,
  
  -- Snapshots
  before_snapshot JSONB,  -- Charter state before change
  after_snapshot JSONB,   -- Charter state after change
  
  priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, urgent
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: change_case_activities
CREATE TABLE change_case_activities (
  id SERIAL PRIMARY KEY,
  change_case_id INT REFERENCES change_cases(id),
  activity_type VARCHAR(50) NOT NULL,
  -- status_change, comment_added, email_sent, document_attached
  description TEXT,
  performed_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: charter_audit_log
CREATE TABLE charter_audit_log (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  table_name VARCHAR(50),  -- charters, itinerary_stops, charter_amenities
  record_id INT,
  action VARCHAR(20),  -- INSERT, UPDATE, DELETE
  old_values JSONB,
  new_values JSONB,
  changed_by INT REFERENCES users(id),
  changed_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**
```
POST   /api/v1/change-cases                    # Create change case
GET    /api/v1/change-cases                    # List (filters: status, priority, charter_id)
GET    /api/v1/change-cases/{id}               # Get case details
PUT    /api/v1/change-cases/{id}/status        # Update status
POST   /api/v1/change-cases/{id}/review        # Review case
POST   /api/v1/change-cases/{id}/vendor-quote  # Add vendor quote
POST   /api/v1/change-cases/{id}/notify-client # Send client notification
POST   /api/v1/change-cases/{id}/approve       # Client approval
POST   /api/v1/change-cases/{id}/implement     # Implement change
POST   /api/v1/change-cases/{id}/activities    # Add activity/comment
GET    /api/v1/change-cases/{id}/activities    # Get activity history

GET    /api/v1/change-cases/dashboard          # Summary dashboard
GET    /api/v1/change-cases/my-assignments     # Assigned to current user

GET    /api/v1/audit-log/charter/{id}          # Get charter audit history
```

**Business Logic - Auto-Create Change Case:**
```python
# Trigger on charter UPDATE
def on_charter_update(old_charter, new_charter, user_id):
    if old_charter.status == 'booked':
        significant_changes = detect_significant_changes(old_charter, new_charter)
        if significant_changes:
            create_change_case(
                charter_id=old_charter.id,
                changes=significant_changes,
                before_snapshot=serialize(old_charter),
                after_snapshot=serialize(new_charter),
                requested_by=user_id
            )
```

**Admin Portal Testing Pages:**
- `/admin/change-cases` - Change case list with status filters
- `/admin/change-cases/{id}` - Case detail with workflow timeline
- `/admin/change-cases/dashboard` - Summary dashboard by status
- `/admin/charters/{id}/audit` - Full audit log for charter

---

### 7. FINANCIAL TRACKING & AR/AP

#### Client Requirements (Accounting + Sales Support Roles)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| QuickBooks bidirectional sync | 🟠 STUB | Stub exists | Need full OAuth + sync logic |
| AR aging report (30/60/90/120) | ❌ MISSING | No aging calculation | Need aging report endpoint |
| AP aging report | ❌ MISSING | No vendor bills | Need vendor_bills table + aging |
| Outstanding receivables | 🟡 PARTIAL | Can query payments | Need aggregation by client |
| Vendor payables | 🟡 PARTIAL | vendor_payments table exists | Need aggregation by vendor |
| Charter-linked paid/unpaid | 🟡 PARTIAL | Payment status exists | Need charter payment summary |
| Zero-balance view | 🟡 PARTIAL | Can calculate balance | Need reporting |
| PO payment tracking | 🟡 PARTIAL | Has payment_method='invoice' | Need PO-specific fields |
| Apply payment to multiple charters | ❌ MISSING | Single charter only | Need payment application table |
| Payment date adjustment | 🟡 PARTIAL | Can update payment_date | Works but no audit |
| Manual card charging | 🟡 PARTIAL | Stripe charge endpoint exists | Need UI + permissions |
| Departed trips by agent/month | ❌ MISSING | No reporting | Need report endpoint |
| Cancellation reporting | ❌ MISSING | No cancel tracking | Need enhanced status |
| Cancel fees tracking | ❌ MISSING | No cancel fee field | Need cancellation_fee field |
| Unearned revenue report | ❌ MISSING | No calculation | Need paid but not departed query |
| Daily check log | ❌ MISSING | No report | Need payment method filter |
| Upcoming payment due dates | 🟡 PARTIAL | payment_schedules exists | Need report |
| Configurable payment structures | ❌ MISSING | Hard-coded 25% deposit | Need configuration table |

#### Implementation Plan
**Service to Enhance:** Payment Service  
**Service to Build:** QuickBooks Integration Module

**Payment Service - Database Schema Additions:**
```sql
-- Modify payments table
ALTER TABLE payments ADD COLUMN client_name VARCHAR(255);
ALTER TABLE payments ADD COLUMN check_number VARCHAR(50);
ALTER TABLE payments ADD COLUMN bank_name VARCHAR(100);
ALTER TABLE payments ADD COLUMN applied_to_multiple_charters BOOLEAN DEFAULT false;

-- New table: payment_applications
CREATE TABLE payment_applications (
  id SERIAL PRIMARY KEY,
  payment_id INT REFERENCES payments(id),
  charter_id INT REFERENCES charters(id),
  amount_applied DECIMAL(10,2) NOT NULL,
  applied_at TIMESTAMP DEFAULT NOW(),
  applied_by INT REFERENCES users(id)
);

-- New table: vendor_bills
CREATE TABLE vendor_bills (
  id SERIAL PRIMARY KEY,
  bill_number VARCHAR(50) UNIQUE NOT NULL,
  vendor_id INT REFERENCES users(id) NOT NULL,
  charter_id INT REFERENCES charters(id),
  
  bill_date DATE NOT NULL,
  due_date DATE NOT NULL,
  
  subtotal DECIMAL(10,2) NOT NULL,
  tax DECIMAL(10,2) DEFAULT 0,
  total_amount DECIMAL(10,2) NOT NULL,
  paid_amount DECIMAL(10,2) DEFAULT 0,
  balance_due DECIMAL(10,2),
  
  status VARCHAR(20) DEFAULT 'received',
  -- received, approved, paid, partially_paid, overdue, disputed
  
  approved_by INT REFERENCES users(id),
  approved_at TIMESTAMP,
  
  payment_terms VARCHAR(50),  -- Net 30, Net 60, Due on Receipt
  
  notes TEXT,
  quickbooks_bill_id VARCHAR(255),
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: vendor_bill_payments
CREATE TABLE vendor_bill_payments (
  id SERIAL PRIMARY KEY,
  vendor_bill_id INT REFERENCES vendor_bills(id),
  payment_id INT,  -- Links to outgoing payment record
  amount DECIMAL(10,2) NOT NULL,
  payment_date DATE NOT NULL,
  payment_method VARCHAR(20),  -- check, ach, wire, credit_card
  check_number VARCHAR(50),
  reference_number VARCHAR(100),
  notes TEXT,
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Modify charters table
ALTER TABLE charters ADD COLUMN cancellation_date TIMESTAMP;
ALTER TABLE charters ADD COLUMN cancellation_reason TEXT;
ALTER TABLE charters ADD COLUMN cancellation_fee DECIMAL(10,2);
ALTER TABLE charters ADD COLUMN cancellation_fee_paid BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN cancelled_by INT REFERENCES users(id);

-- New table: payment_configuration
CREATE TABLE payment_configuration (
  id SERIAL PRIMARY KEY,
  config_name VARCHAR(100) UNIQUE NOT NULL,
  
  deposit_percentage DECIMAL(5,2) DEFAULT 25.00,
  deposit_days_before INT DEFAULT 30,
  
  balance_due_days_before INT DEFAULT 2,
  
  allow_autopay BOOLEAN DEFAULT true,
  require_cc_on_file BOOLEAN DEFAULT false,
  
  po_allowed_client_types TEXT[],  -- ['government', 'corporate']
  po_credit_limit DECIMAL(10,2),
  
  updated_by INT REFERENCES users(id),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: quickbooks_sync_queue
CREATE TABLE quickbooks_sync_queue (
  id SERIAL PRIMARY KEY,
  entity_type VARCHAR(50) NOT NULL,  -- customer, vendor, invoice, payment, bill
  entity_id INT NOT NULL,
  operation VARCHAR(20) NOT NULL,  -- create, update, delete
  status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, synced, failed
  quickbooks_id VARCHAR(255),
  error_message TEXT,
  retry_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP
);
```

**Payment Service - New API Endpoints:**
```
# AR/AP Reports
GET    /api/v1/reports/ar-aging                # AR aging (30/60/90/120)
GET    /api/v1/reports/ap-aging                # AP aging
GET    /api/v1/reports/outstanding-receivables # Summary by client
GET    /api/v1/reports/vendor-payables         # Summary by vendor
GET    /api/v1/reports/charter-payment-status  # Payment status by charter
GET    /api/v1/reports/zero-balance-charters   # Fully paid charters
GET    /api/v1/reports/unearned-revenue        # Paid but not departed
GET    /api/v1/reports/daily-check-log         # Daily cash receipts
GET    /api/v1/reports/upcoming-payments       # Payment due dates
GET    /api/v1/reports/departed-by-agent       # Agent performance
GET    /api/v1/reports/cancellation-report     # Cancellation analysis

# Payment Application
POST   /api/v1/payments/{id}/apply-multiple    # Apply to multiple charters
GET    /api/v1/payments/{id}/applications      # View applications

# Vendor Bills
POST   /api/v1/vendor-bills                    # Create bill
GET    /api/v1/vendor-bills                    # List bills
GET    /api/v1/vendor-bills/{id}               # Get bill
PUT    /api/v1/vendor-bills/{id}               # Update bill
POST   /api/v1/vendor-bills/{id}/approve       # Approve bill
POST   /api/v1/vendor-bills/{id}/pay           # Record payment

# Payment Configuration
GET    /api/v1/payment-config                  # Get config
PUT    /api/v1/payment-config                  # Update config

# QuickBooks Integration
POST   /api/v1/quickbooks/connect              # OAuth flow start
GET    /api/v1/quickbooks/callback             # OAuth callback
POST   /api/v1/quickbooks/sync-customer        # Sync client to QB
POST   /api/v1/quickbooks/sync-invoice         # Sync invoice to QB
POST   /api/v1/quickbooks/sync-payment         # Sync payment to QB
POST   /api/v1/quickbooks/sync-vendor          # Sync vendor to QB
POST   /api/v1/quickbooks/sync-bill            # Sync bill to QB
GET    /api/v1/quickbooks/sync-status          # Check sync status
POST   /api/v1/quickbooks/webhook              # QB webhook handler
```

**QuickBooks Integration Module:**
- OAuth 2.0 authentication with QuickBooks
- Entity mapping (clients → customers, vendors → vendors)
- Sync queue for asynchronous processing
- Webhook handling for bidirectional updates
- Conflict resolution (last-write-wins or manual)
- Error logging and retry logic

**Admin Portal Testing Pages:**
- `/admin/reports/ar-aging` - AR aging report with drill-down
- `/admin/reports/ap-aging` - AP aging report
- `/admin/reports/financial-dashboard` - Overall financial health
- `/admin/payments/applications` - Payment application management
- `/admin/vendor-bills` - Vendor bill list
- `/admin/vendor-bills/{id}` - Bill detail + approval
- `/admin/settings/payment-config` - Payment configuration UI
- `/admin/integrations/quickbooks` - QuickBooks connection + sync status

---

### 8. DISPATCH & OPERATIONS

#### Client Requirements (Dispatch Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Dispatch board (2 days pre-departure) | 🟡 PARTIAL | Can query charters | Need filtered view + date logic |
| Visual icon-based status | ❌ MISSING | No icon system | Need status icons UI |
| Task auto-complete → icons disappear | ❌ MISSING | No task system | Need task completion tracking |
| Driver confirmation/contact | 🟡 PARTIAL | Driver assigned | Need confirmation status |
| Route access | 🟡 PARTIAL | Itinerary exists | Need route optimization |
| Special instructions | 🟡 PARTIAL | Has notes field | Need structured instructions |
| Real-time GPS map | 🟡 PARTIAL | GPS tracking exists | Need real-time map UI |
| Recurring shuttle tracking (Day X of Y) | ❌ MISSING | No series tracking | Need series_total/instance display |
| Place charter into recovery | ❌ MISSING | No recovery status | Need recovery workflow |
| Add vendor bids (dispatch) | ❌ MISSING | No bid system | Need Vendor Service |
| Award vendors (dispatch) | 🟡 PARTIAL | Can assign vendor | Need bid acceptance |
| Split charters | ❌ MISSING | No split logic | Need multi-charter creation |
| Cancel charter (dispatch) | 🟡 PARTIAL | Can update status | Need cancellation workflow |

#### Implementation Plan
**Service to Enhance:** Charter Service (Operations)  
**Service to Build:** Dispatch Module (within Operations)

**Charter Service - Database Schema Additions:**
```sql
-- Modify charters table
ALTER TABLE charters ADD COLUMN dispatch_status VARCHAR(20);
-- not_ready, ready, dispatched, in_transit, on_site, completed, issue

ALTER TABLE charters ADD COLUMN driver_confirmed BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN driver_confirmed_at TIMESTAMP;
ALTER TABLE charters ADD COLUMN driver_confirmation_method VARCHAR(20);

ALTER TABLE charters ADD COLUMN vendor_confirmed BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN vendor_confirmed_at TIMESTAMP;

ALTER TABLE charters ADD COLUMN recovery_status VARCHAR(20);
-- not_needed, pending, vendor_search, vendor_assigned, resolved

ALTER TABLE charters ADD COLUMN recovery_initiated_at TIMESTAMP;
ALTER TABLE charters ADD COLUMN recovery_reason TEXT;
ALTER TABLE charters ADD COLUMN recovery_resolved_at TIMESTAMP;

ALTER TABLE charters ADD COLUMN route_optimized BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN estimated_route_distance DECIMAL(10,2);
ALTER TABLE charters ADD COLUMN estimated_duration_hours DECIMAL(5,2);

-- New table: dispatch_tasks
CREATE TABLE dispatch_tasks (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  task_type VARCHAR(50) NOT NULL,
  -- vehicle_assigned, driver_assigned, vendor_confirmed, 
  -- driver_confirmed, route_verified, documents_ready, pre_trip_complete
  
  task_name VARCHAR(255) NOT NULL,
  description TEXT,
  is_required BOOLEAN DEFAULT true,
  
  status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, skipped
  
  completed_at TIMESTAMP,
  completed_by INT REFERENCES users(id),
  
  due_by TIMESTAMP,
  priority VARCHAR(20) DEFAULT 'medium',
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: special_instructions
CREATE TABLE special_instructions (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  instruction_type VARCHAR(50),
  -- pickup_instructions, dropoff_instructions, route_notes, 
  -- passenger_requirements, equipment_needed, safety_notes
  
  instruction_text TEXT NOT NULL,
  priority VARCHAR(20) DEFAULT 'normal',  -- normal, important, critical
  display_to_driver BOOLEAN DEFAULT true,
  display_to_vendor BOOLEAN DEFAULT true,
  
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: charter_splits
CREATE TABLE charter_splits (
  id SERIAL PRIMARY KEY,
  original_charter_id INT REFERENCES charters(id),
  split_charter_id INT REFERENCES charters(id),
  split_reason TEXT,
  passenger_distribution VARCHAR(100),  -- "30/26" or "Vehicle 1: 30, Vehicle 2: 26"
  split_by INT REFERENCES users(id),
  split_at TIMESTAMP DEFAULT NOW()
);
```

**New API Endpoints:**
```
# Dispatch Board
GET    /api/v1/dispatch/board                  # Dispatch board (filters: date_range, status)
GET    /api/v1/dispatch/board/today            # Today's charters
GET    /api/v1/dispatch/board/upcoming         # Next 2 days
GET    /api/v1/dispatch/ready-check/{id}       # Check if charter ready for dispatch

# Driver/Vendor Confirmation
POST   /api/v1/dispatch/{id}/confirm-driver    # Mark driver confirmed
POST   /api/v1/dispatch/{id}/confirm-vendor    # Mark vendor confirmed
POST   /api/v1/dispatch/{id}/contact-driver    # Log contact attempt
POST   /api/v1/dispatch/{id}/contact-vendor    # Log contact attempt

# Tasks
GET    /api/v1/dispatch/{id}/tasks             # Get charter tasks
POST   /api/v1/dispatch/{id}/tasks             # Create task
PUT    /api/v1/dispatch/tasks/{task_id}        # Update task
POST   /api/v1/dispatch/tasks/{task_id}/complete  # Complete task

# Special Instructions
POST   /api/v1/dispatch/{id}/instructions      # Add instruction
GET    /api/v1/dispatch/{id}/instructions      # Get instructions
PUT    /api/v1/dispatch/instructions/{inst_id} # Update instruction

# Recovery
POST   /api/v1/dispatch/{id}/initiate-recovery # Start recovery process
POST   /api/v1/dispatch/{id}/resolve-recovery  # Mark recovery resolved
GET    /api/v1/dispatch/recovery-board         # Active recovery cases

# Route Optimization
POST   /api/v1/dispatch/{id}/optimize-route    # Optimize itinerary
GET    /api/v1/dispatch/{id}/route-map         # Get map data

# Charter Operations
POST   /api/v1/dispatch/{id}/split             # Split charter into multiple
POST   /api/v1/dispatch/{id}/cancel            # Cancel with workflow
```

**Dispatch Task Auto-Generation Logic:**
```python
def generate_dispatch_tasks(charter):
    tasks = []
    
    # 7 days before
    if not charter.vehicle_id:
        tasks.append(Task(type='vehicle_assigned', due_by=charter.trip_date - 7 days))
    
    # 5 days before
    if not charter.vendor_id:
        tasks.append(Task(type='vendor_assigned', due_by=charter.trip_date - 5 days))
    
    # 3 days before
    if not charter.vendor_confirmed:
        tasks.append(Task(type='vendor_confirmed', due_by=charter.trip_date - 3 days))
    
    # 2 days before
    if not charter.driver_id:
        tasks.append(Task(type='driver_assigned', due_by=charter.trip_date - 2 days))
    
    # 1 day before
    tasks.append(Task(type='driver_confirmed', due_by=charter.trip_date - 1 days))
    tasks.append(Task(type='route_verified', due_by=charter.trip_date - 1 days))
    tasks.append(Task(type='documents_ready', due_by=charter.trip_date - 1 days))
    
    return tasks
```

**Admin Portal Testing Pages:**
- `/admin/dispatch/board` - Visual dispatch board with icon indicators
- `/admin/dispatch/board/map` - Real-time GPS map of active charters
- `/admin/dispatch/recovery` - Recovery cases dashboard
- `/admin/dispatch/charters/{id}` - Dispatch detail view with tasks
- `/admin/dispatch/charters/{id}/route` - Route optimization UI

---

### 9. MANAGER & EXECUTIVE DASHBOARDS

#### Client Requirements (Managers Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Cross-agent sales view | ❌ MISSING | No aggregation | Need multi-agent reporting |
| Cross-agent profit view | ❌ MISSING | No profit tracking | Need profit aggregation |
| Open cases count | ❌ MISSING | No change case system | Need Change Service |
| QC backlog | ❌ MISSING | No QC system | Need task tracking |
| Customizable reports | ❌ MISSING | No report builder | Need report configuration |
| Saved report templates | ❌ MISSING | No template system | Need template storage |
| Full charter change log | 🟡 PARTIAL | Has updated_at | Need audit log |
| Price/payment adjustment tracking | 🟡 PARTIAL | Can view changes | Need audit table |
| Promo code management | ❌ MISSING | No promo system | Need Pricing Service |
| Pricing matrix configuration | ❌ MISSING | Hard-coded pricing | Need config UI |
| Pricing modifiers (day/event/hub) | ❌ MISSING | No modifiers | Need Pricing Service |
| Vendor COI tracking | ❌ MISSING | No COI system | Need Vendor Service |
| COI expiration alerts | ❌ MISSING | No alert system | Need scheduled job |
| Lead queue management | ❌ MISSING | No lead system | Need Sales Service |
| Max leads per day setting | ❌ MISSING | No throttling | Need queue config |
| User/role management | 🟡 PARTIAL | Basic users exist | Need RBAC UI |
| Granular permissions | 🟠 STUB | RBAC schema exists | Need permission UI |
| Vendor bid analytics | ❌ MISSING | No bid system | Need Vendor Service |
| Peak period identification | ❌ MISSING | No analytics | Future enhancement |

#### Implementation Plan
**Services: Reporting Service (NEW), Pricing Service (NEW), Vendor Service (NEW)**

**Reporting Service - NEW SERVICE (Port 8011)**

**Database Schema:**
```sql
-- New table: report_templates
CREATE TABLE report_templates (
  id SERIAL PRIMARY KEY,
  template_name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  report_type VARCHAR(50) NOT NULL,
  -- sales_by_agent, profit_analysis, charter_status, payment_summary, etc.
  
  -- Configuration
  filters JSONB,  -- {date_range: "mtd", status: ["booked", "completed"]}
  grouping JSONB,  -- {group_by: ["agent", "vehicle_type"]}
  columns JSONB,  -- ["charter_number", "client_name", "total_cost"]
  aggregations JSONB,  -- {sum: ["revenue"], avg: ["profit_margin"]}
  
  visualization VARCHAR(20),  -- table, bar_chart, line_chart, pie_chart
  
  is_public BOOLEAN DEFAULT false,
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: scheduled_reports
CREATE TABLE scheduled_reports (
  id SERIAL PRIMARY KEY,
  report_template_id INT REFERENCES report_templates(id),
  schedule_rule VARCHAR(100),  -- daily, weekly, monthly, cron expression
  recipient_emails TEXT[],
  is_active BOOLEAN DEFAULT true,
  last_run_at TIMESTAMP,
  next_run_at TIMESTAMP,
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- New table: report_runs
CREATE TABLE report_runs (
  id SERIAL PRIMARY KEY,
  report_template_id INT REFERENCES report_templates(id),
  run_by INT REFERENCES users(id),
  run_at TIMESTAMP DEFAULT NOW(),
  parameters JSONB,
  result_data JSONB,
  execution_time_ms INT
);

-- New table: manager_dashboards
CREATE TABLE manager_dashboards (
  id SERIAL PRIMARY KEY,
  dashboard_name VARCHAR(255) NOT NULL,
  user_id INT REFERENCES users(id),
  layout JSONB,  -- Widget positions and configurations
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Reporting Service API Endpoints:**
```
# Report Templates
GET    /api/v1/reports/templates              # List templates
POST   /api/v1/reports/templates              # Create template
GET    /api/v1/reports/templates/{id}         # Get template
PUT    /api/v1/reports/templates/{id}         # Update template
DELETE /api/v1/reports/templates/{id}         # Delete template
POST   /api/v1/reports/templates/{id}/run     # Execute report

# Pre-built Reports
GET    /api/v1/reports/sales-by-agent         # Sales performance by agent
GET    /api/v1/reports/profit-analysis        # Profit analysis
GET    /api/v1/reports/charter-status-summary # Status breakdown
GET    /api/v1/reports/payment-summary        # Payment status summary
GET    /api/v1/reports/vehicle-utilization    # Vehicle usage stats
GET    /api/v1/reports/vendor-performance     # Vendor metrics
GET    /api/v1/reports/qc-backlog             # Quality control backlog

# Scheduled Reports
POST   /api/v1/reports/schedule               # Schedule report
GET    /api/v1/reports/scheduled              # List scheduled reports
PUT    /api/v1/reports/scheduled/{id}         # Update schedule
DELETE /api/v1/reports/scheduled/{id}         # Delete schedule

# Dashboards
GET    /api/v1/dashboards                     # List dashboards
POST   /api/v1/dashboards                     # Create dashboard
GET    /api/v1/dashboards/{id}                # Get dashboard
PUT    /api/v1/dashboards/{id}                # Update dashboard
DELETE /api/v1/dashboards/{id}                # Delete dashboard
```

**Admin Portal Testing Pages:**
- `/admin/reports/builder` - Report builder UI
- `/admin/reports/templates` - Saved report templates
- `/admin/reports/scheduled` - Scheduled reports management
- `/admin/dashboard/manager` - Manager executive dashboard
- `/admin/dashboard/customize` - Dashboard customization UI
- `/admin/settings/pricing` - Pricing configuration UI (from Pricing Service)
- `/admin/settings/rbac` - Role and permission management UI

---

### 10. VENDOR PORTAL & BID MANAGEMENT

#### Client Requirements (Vendors Role + Dispatch)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Vendor portal login | ❌ MISSING | No vendor portal | Need Vendor Service |
| View assigned charters | 🟡 PARTIAL | Can query by vendor_id | Need portal UI |
| Pending assignments list | ❌ MISSING | No assignment workflow | Need bid/assignment system |
| Detailed charter view | 🟡 PARTIAL | Charter details exist | Need vendor-specific view |
| Accept/Decline assignment | ❌ MISSING | No acceptance workflow | Need status tracking |
| Bid submission | ❌ MISSING | No bid system | Need bid table |
| Bid on >200mi charters | ❌ MISSING | No distance-based alerts | Need notification trigger |
| Final itinerary + attachments | 🟡 PARTIAL | Documents exist | Need portal access |
| Upcoming trips overview | 🟡 PARTIAL | Can query charters | Need portal UI |
| Historical job list | 🟡 PARTIAL | Can query past charters | Need portal UI |
| Email alerts for pending jobs | 🟡 PARTIAL | Notification service exists | Need email templates |
| Email alerts for recoveries | ❌ MISSING | No recovery system | Need recovery workflow |
| Email alerts for cancellations | 🟡 PARTIAL | Can send notifications | Need cancel workflow |
| COI upload/tracking | ❌ MISSING | No COI system | Need document type + expiration |
| Jotform integration | ❌ MISSING | No Jotform webhook | Need webhook endpoint |
| View bid history | ❌ MISSING | No bid table | Need Vendor Service |

#### Implementation Plan
**New Service:** Vendor Service (Port 8006)

**Database Schema:**
```sql
-- New table: vendors (extends users with vendor-specific data)
CREATE TABLE vendors (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) UNIQUE NOT NULL,
  
  -- Company info
  company_name VARCHAR(255) NOT NULL,
  dba_name VARCHAR(255),
  business_type VARCHAR(50),  -- sole_proprietor, llc, corporation
  
  -- Contact
  primary_contact_name VARCHAR(255),
  primary_contact_phone VARCHAR(20),
  primary_contact_email VARCHAR(255),
  dispatch_phone VARCHAR(20),
  dispatch_email VARCHAR(255),
  
  -- Address
  address VARCHAR(255),
  city VARCHAR(100),
  state VARCHAR(2),
  zip_code VARCHAR(10),
  
  -- Compliance
  dot_number VARCHAR(20),
  mc_number VARCHAR(20),
  tax_id VARCHAR(20),
  
  -- Insurance
  coi_document_id INT REFERENCES charter_documents(id),
  coi_expiration_date DATE,
  coi_verified BOOLEAN DEFAULT false,
  coi_verified_by INT REFERENCES users(id),
  coi_verified_at TIMESTAMP,
  
  -- Financial
  payment_terms VARCHAR(50),  -- Net 30, Net 60
  preferred_payment_method VARCHAR(20),  -- check, ach, wire
  
  -- Operational
  service_radius_miles INT,  -- Service area radius
  base_location_lat DECIMAL(10,7),
  base_location_lon DECIMAL(10,7),
  
  -- Fleet
  fleet_size INT,
  available_vehicle_types TEXT[],
  
  -- Rating
  rating DECIMAL(3,2),  -- 4.50 out of 5.00
  total_jobs INT DEFAULT 0,
  completed_jobs INT DEFAULT 0,
  cancelled_jobs INT DEFAULT 0,
  on_time_percentage DECIMAL(5,2),
  
  -- Status
  vendor_status VARCHAR(20) DEFAULT 'active',
  -- active, suspended, blacklisted, inactive
  
  is_approved BOOLEAN DEFAULT false,
  approved_by INT REFERENCES users(id),
  approved_at TIMESTAMP,
  
  notes TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- New table: vendor_bids
CREATE TABLE vendor_bids (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  vendor_id INT REFERENCES vendors(id),
  
  bid_amount DECIMAL(10,2) NOT NULL,
  vehicle_type VARCHAR(50),
  vehicle_count INT DEFAULT 1,
  
  bid_status VARCHAR(20) DEFAULT 'submitted',
  -- submitted, under_review, accepted, declined, withdrawn, expired
  
  notes TEXT,
  valid_until TIMESTAMP,
  
  submitted_at TIMESTAMP DEFAULT NOW(),
  reviewed_by INT REFERENCES users(id),
  reviewed_at TIMESTAMP,
  review_notes TEXT,
  
  accepted_at TIMESTAMP,
  declined_reason TEXT
);

-- New table: vendor_assignments
CREATE TABLE vendor_assignments (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id) UNIQUE,
  vendor_id INT REFERENCES vendors(id),
  bid_id INT REFERENCES vendor_bids(id),
  
  assignment_type VARCHAR(20),  -- direct_assign, bid_accepted, subcontract
  
  agreed_amount DECIMAL(10,2) NOT NULL,
  
  status VARCHAR(20) DEFAULT 'pending',
  -- pending, confirmed, declined, in_progress, completed, cancelled
  
  assigned_by INT REFERENCES users(id),
  assigned_at TIMESTAMP DEFAULT NOW(),
  
  confirmed_at TIMESTAMP,
  declined_at TIMESTAMP,
  declined_reason TEXT,
  
  recovery_requested BOOLEAN DEFAULT false,
  recovery_reason TEXT,
  recovery_requested_at TIMESTAMP
);

-- New table: coi_expiration_alerts
CREATE TABLE coi_expiration_alerts (
  id SERIAL PRIMARY KEY,
  vendor_id INT REFERENCES vendors(id),
  alert_type VARCHAR(20),  -- 30_day, 15_day, 7_day, expired
  alert_date DATE NOT NULL,
  alert_sent BOOLEAN DEFAULT false,
  alert_sent_at TIMESTAMP
);

-- New table: jotform_submissions
CREATE TABLE jotform_submissions (
  id SERIAL PRIMARY KEY,
  submission_id VARCHAR(255) UNIQUE NOT NULL,
  form_id VARCHAR(255),
  company_name VARCHAR(255),
  contact_name VARCHAR(255),
  contact_email VARCHAR(255),
  contact_phone VARCHAR(20),
  submission_data JSONB,
  status VARCHAR(20) DEFAULT 'pending',
  -- pending, reviewed, approved, rejected
  processed_at TIMESTAMP,
  vendor_id INT REFERENCES vendors(id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Vendor Service API Endpoints:**
```
# Vendor Management (Admin)
GET    /api/v1/vendors                        # List vendors
POST   /api/v1/vendors                        # Create vendor
GET    /api/v1/vendors/{id}                   # Get vendor
PUT    /api/v1/vendors/{id}                   # Update vendor
DELETE /api/v1/vendors/{id}                   # Deactivate vendor
POST   /api/v1/vendors/{id}/approve           # Approve vendor
POST   /api/v1/vendors/{id}/upload-coi        # Upload COI document
GET    /api/v1/vendors/coi-expiring           # Vendors with expiring COI

# Vendor Portal (Vendor-facing)
GET    /api/v1/vendor-portal/dashboard        # Vendor dashboard
GET    /api/v1/vendor-portal/assignments      # My assignments
GET    /api/v1/vendor-portal/assignments/{id} # Assignment details
POST   /api/v1/vendor-portal/assignments/{id}/confirm   # Confirm assignment
POST   /api/v1/vendor-portal/assignments/{id}/decline   # Decline assignment
POST   /api/v1/vendor-portal/assignments/{id}/request-recovery  # Can't do job

GET    /api/v1/vendor-portal/bid-opportunities  # Available bids (>200mi)
POST   /api/v1/vendor-portal/bids              # Submit bid
GET    /api/v1/vendor-portal/bids              # My bids
PUT    /api/v1/vendor-portal/bids/{id}         # Update bid
DELETE /api/v1/vendor-portal/bids/{id}         # Withdraw bid

GET    /api/v1/vendor-portal/jobs              # Job history
GET    /api/v1/vendor-portal/documents         # My documents

# Bid Management (Admin/Dispatch)
GET    /api/v1/bids                            # All bids (filters: status, charter_id)
GET    /api/v1/bids/{id}                       # Get bid
POST   /api/v1/bids/{id}/accept                # Accept bid (assign vendor)
POST   /api/v1/bids/{id}/decline               # Decline bid
GET    /api/v1/charters/{charter_id}/bids      # Bids for charter

# Assignment Management
POST   /api/v1/assignments                     # Create assignment (direct)
GET    /api/v1/assignments                     # List assignments
GET    /api/v1/assignments/{id}                # Get assignment
PUT    /api/v1/assignments/{id}                # Update assignment
POST   /api/v1/assignments/{id}/notify         # Send notification to vendor

# Jotform Integration
POST   /api/v1/jotform/webhook                 # Receive Jotform submission
GET    /api/v1/jotform/submissions             # List submissions
POST   /api/v1/jotform/submissions/{id}/approve  # Approve and create vendor
```

**Business Logic - Bid Opportunity Trigger:**
```python
# When charter created/updated with pickup >200mi from hub
def check_bid_opportunity(charter):
    if charter.status in ['quote', 'booked']:
        distance_from_hub = calculate_distance(charter.pickup_location, HUB_LOCATION)
        
        if distance_from_hub > 200:
            # Notify vendors in that region
            eligible_vendors = get_vendors_in_radius(
                location=charter.pickup_location,
                radius=100
            )
            
            for vendor in eligible_vendors:
                send_notification(
                    vendor_id=vendor.id,
                    type='bid_opportunity',
                    charter_id=charter.id,
                    message=f"New charter {charter.id} available for bidding"
                )
```

**Airflow DAG - COI Expiration Monitoring:**
```python
# Runs daily at 8 AM
def check_coi_expirations():
    # 30 days before
    vendors_30day = get_vendors_with_coi_expiring(days=30)
    send_expiration_alerts(vendors_30day, alert_type='30_day')
    
    # 15 days before
    vendors_15day = get_vendors_with_coi_expiring(days=15)
    send_expiration_alerts(vendors_15day, alert_type='15_day')
    
    # 7 days before
    vendors_7day = get_vendors_with_coi_expiring(days=7)
    send_expiration_alerts(vendors_7day, alert_type='7_day')
    
    # Expired
    vendors_expired = get_vendors_with_expired_coi()
    send_expiration_alerts(vendors_expired, alert_type='expired')
    suspend_vendors(vendors_expired)  # Auto-suspend
```

**Admin Portal Testing Pages:**
- `/admin/vendors` - Vendor list with COI status
- `/admin/vendors/{id}` - Vendor profile with rating
- `/admin/vendors/{id}/jobs` - Job history
- `/admin/bids` - All bids by charter
- `/admin/bids/{id}` - Bid detail with accept/decline
- `/admin/vendors/coi-expiring` - COI expiration dashboard

**Vendor Portal Pages:**
- `/vendor/login` - Vendor authentication
- `/vendor/dashboard` - Dashboard with pending assignments
- `/vendor/assignments` - My assignments list
- `/vendor/assignments/{id}` - Assignment detail with confirm/decline
- `/vendor/opportunities` - Bid opportunities (>200mi charters)
- `/vendor/bids` - My bid history
- `/vendor/jobs` - Historical jobs
- `/vendor/profile` - Update company info, upload COI

---

### 11. DRIVER MOBILE APP

#### Client Requirements (Drivers Role)

| Capability | Status | Current Implementation | Gap Details |
|-----------|--------|----------------------|-------------|
| Mobile-first interface | ✅ COMPLETE | DriverDashboard.tsx exists | Works |
| Secure login | ✅ COMPLETE | Auth service | Works |
| View upcoming trips | 🟡 PARTIAL | Can query assigned charters | Need mobile-optimized list |
| View current trip | ✅ COMPLETE | Driver endpoint exists | Works |
| Full itinerary + stops | ✅ COMPLETE | Itinerary stops exist | Works |
| Special instructions | 🟡 PARTIAL | Has notes field | Need structured instructions view |
| One-tap GPS activation | 🟡 PARTIAL | GPS tracking exists | Need native GPS integration |
| In-app note logging | 🟡 PARTIAL | Can update vendor_notes | Works |
| In-app photo upload | ❌ MISSING | No photo upload from driver | Need mobile upload |
| Today's jobs | ✅ COMPLETE | Can filter by date | Works |
| Click to dial dispatch | ❌ MISSING | No tel: link | Need phone integration |

#### Implementation Plan
**Service to Enhance:** Charter Service (driver endpoints)

**Database Schema Updates:**
```sql
-- Modify charters table
ALTER TABLE charters ADD COLUMN driver_notes TEXT;

-- New table: driver_checklist
CREATE TABLE driver_checklist (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  checklist_item VARCHAR(255) NOT NULL,
  is_completed BOOLEAN DEFAULT false,
  completed_at TIMESTAMP,
  completed_by INT REFERENCES users(id),
  notes TEXT
);

-- New table: driver_photos
CREATE TABLE driver_photos (
  id SERIAL PRIMARY KEY,
  charter_id INT REFERENCES charters(id),
  driver_id INT REFERENCES users(id),
  photo_type VARCHAR(50),  -- vehicle_exterior, vehicle_interior, damage, other
  document_id INT REFERENCES charter_documents(id),
  caption TEXT,
  uploaded_at TIMESTAMP DEFAULT NOW()
);
```

**New API Endpoints:**
```
# Driver App
GET    /api/v1/driver/dashboard               # Driver dashboard data
GET    /api/v1/driver/trips/today             # Today's trips
GET    /api/v1/driver/trips/upcoming          # Upcoming trips (7 days)
GET    /api/v1/driver/trips/{id}              # Trip detail
POST   /api/v1/driver/trips/{id}/start        # Start trip (change status)
POST   /api/v1/driver/trips/{id}/complete     # Complete trip
POST   /api/v1/driver/trips/{id}/notes        # Add driver note
POST   /api/v1/driver/trips/{id}/photos       # Upload photo
POST   /api/v1/driver/trips/{id}/gps-update   # Update GPS location

GET    /api/v1/driver/checklist/{charter_id}  # Get pre-trip checklist
POST   /api/v1/driver/checklist/{id}/complete # Complete checklist item
```

**Admin Portal Testing Pages:**
- `/admin/drivers` - Driver list with current assignments
- `/admin/drivers/{id}` - Driver profile + job history
- `/admin/drivers/{id}/active-trip` - Real-time trip monitoring
- `/driver` - Mobile driver dashboard (test in mobile view)

---

## Part 2: Service Architecture & Dependencies

### New Services to Build

#### 1. **Sales Service** (Port 8007) - Priority: P0
**Purpose:** Lead management, pipeline, assignment  
**Dependencies:** Auth Service (users), Client Service (clients)  
**Database Tables:** leads, lead_assignment_queue, lead_activities, email_tracking, client_email_preferences  
**Estimated Development:** 2-3 weeks

#### 2. **Pricing Service** (Port 8008) - Priority: P1
**Purpose:** Dynamic pricing, promo codes, amenities, modifiers  
**Dependencies:** None (standalone)  
**Database Tables:** amenities, promo_codes, promo_code_usage, pricing_modifiers, dot_regulations  
**Estimated Development:** 2-3 weeks

#### 3. **Vendor Service** (Port 8006) - Priority: P1
**Purpose:** Vendor portal, bid management, COI tracking  
**Dependencies:** Auth Service (users), Charter Service (charters), Document Service (COI docs)  
**Database Tables:** vendors, vendor_bids, vendor_assignments, coi_expiration_alerts, jotform_submissions  
**Estimated Development:** 3-4 weeks

#### 4. **Change Management Service** (Port 8010) - Priority: P2
**Purpose:** Change case workflow, approval process  
**Dependencies:** Charter Service (charters), Notification Service (alerts)  
**Database Tables:** change_cases, change_case_activities, charter_audit_log  
**Estimated Development:** 2 weeks

#### 5. **Portals Service** (Port 8009) - Priority: P1
**Purpose:** Client portal, vendor portal orchestration  
**Dependencies:** All services (aggregation layer)  
**Database Tables:** user_sessions (for impersonation)  
**Estimated Development:** 2-3 weeks

#### 6. **Reporting Service** (Port 8011) - Priority: P2
**Purpose:** Report builder, templates, scheduled reports  
**Dependencies:** All services (queries data from all)  
**Database Tables:** report_templates, scheduled_reports, report_runs, manager_dashboards  
**Estimated Development:** 3-4 weeks

### Existing Services to Enhance

#### 1. **Auth Service** (Port 8000) - Priority: P1
**Enhancements:**
- MFA support (TOTP)
- Password reset flow
- Session management with impersonation
- RBAC UI for permission management

**Estimated Effort:** 1 week

#### 2. **Charter Service** (Port 8001) - Priority: P0
**Enhancements:**
- Recurring charter support
- Clone/duplicate functionality
- Dispatch module (tasks, recovery)
- Multi-vehicle support
- Driver mobile enhancements

**Estimated Effort:** 3-4 weeks

#### 3. **Client Service** (Port 8002) - Priority: P1
**Enhancements:**
- Stripe customer integration
- Notification preferences
- Client portal features

**Estimated Effort:** 1 week

#### 4. **Payment Service** (Port 8004) - Priority: P0
**Enhancements:**
- QuickBooks full bidirectional sync
- AR/AP aging reports
- Vendor bills management
- Payment applications (multi-charter)
- Saved payment methods
- Payment plans

**Estimated Effort:** 3-4 weeks

#### 5. **Document Service** (Port 8003) - Priority: P2
**Enhancements:**
- Document categorization
- COI expiration tracking integration

**Estimated Effort:** 3-5 days

#### 6. **Notification Service** (Port 8005) - Priority: P2
**Enhancements:**
- Email preference management
- Template UI
- More notification templates

**Estimated Effort:** 1 week

---

## Part 3: Incremental Rollout Plan

### Phase 0: Foundation (Weeks 1-2) - CRITICAL BLOCKERS

#### Goal: Core capabilities for admin testing

**Backend Tasks:**
1. ✅ **Charter Service Enhancement - Recurring Charters**
   - Add recurrence fields to charters table
   - Build clone/duplicate API endpoints
   - Test recurring series creation

2. ✅ **Payment Service Enhancement - Core AR/AP**
   - Add vendor_bills table
   - Build payment application logic
   - Test multi-charter payment application

3. ✅ **Sales Service - MVP Lead Management**
   - Create Sales Service skeleton
   - Build leads table
   - Create basic CRUD endpoints
   - Implement round-robin assignment

**Admin Portal Updates:**
- `/admin/charters/{id}` - Add clone/duplicate buttons
- `/admin/charters/new-recurring` - Recurring charter wizard
- `/admin/payments/apply` - Payment application page
- `/admin/leads` - Basic lead list page
- `/admin/leads/{id}` - Lead detail page

**Testing Checklist:**
- [ ] Create recurring charter (20 instances)
- [ ] Clone single charter to new date
- [ ] Delete instance from recurring series
- [ ] Create lead and auto-assign
- [ ] Apply single payment to 3 charters
- [ ] View applied payment breakdown

---

### Phase 1: Sales & Booking Workflow (Weeks 3-5) - HIGH PRIORITY

#### Goal: Complete lead-to-booking pipeline

**Backend Tasks:**
1. ✅ **Sales Service - Full Implementation**
   - Lead activity tracking
   - Lead-to-quote conversion
   - Email tracking integration
   - Pipeline stages

2. ✅ **Pricing Service - MVP**
   - Amenities table + CRUD
   - Promo codes table + validation
   - Basic pricing calculation with amenities
   - DOT compliance checker

3. ✅ **Charter Service - Quote Builder Enhancements**
   - Multi-stop itinerary with geocoding
   - Amenity selection
   - Secure quote link generation
   - Quote revision tracking

4. ✅ **Notification Service - Templates**
   - Quote email template
   - Booking confirmation template
   - Follow-up email template
   - Email preference checking

**Admin Portal Updates:**
- `/admin/leads/pipeline` - Kanban board
- `/admin/leads/{id}/convert` - Convert to quote
- `/admin/charters/quote-builder` - Enhanced quote builder with map
- `/admin/pricing/amenities` - Amenity management
- `/admin/pricing/promo-codes` - Promo code CRUD
- `/admin/charters/{id}/itinerary` - Visual itinerary with drag/drop

**Testing Checklist:**
- [ ] Create lead → convert to quote → book
- [ ] Build multi-stop itinerary (5 stops)
- [ ] Add 3 amenities to quote, see price update
- [ ] Apply promo code, verify discount
- [ ] Check DOT compliance (should flag 2nd driver)
- [ ] Send quote email with secure link
- [ ] Track email open/click

---

### Phase 2: Financial & QuickBooks (Weeks 6-8) - HIGH PRIORITY

#### Goal: Complete accounting integration

**Backend Tasks:**
1. ✅ **Payment Service - QuickBooks Integration**
   - OAuth 2.0 flow implementation
   - Entity mapping (clients → customers)
   - Sync queue processing
   - Webhook handlers
   - Conflict resolution

2. ✅ **Payment Service - AR/AP Reporting**
   - AR aging report (30/60/90/120)
   - AP aging report
   - Outstanding receivables by client
   - Vendor payables by vendor
   - Unearned revenue calculation
   - Departed trips by agent

3. ✅ **Payment Service - Vendor Bills**
   - Vendor bill CRUD
   - Bill approval workflow
   - Payment to bills
   - Bill aging

4. ✅ **Payment Service - Payment Configuration**
   - Configurable deposit percentage
   - Configurable due dates
   - Payment terms by client type

**Admin Portal Updates:**
- `/admin/integrations/quickbooks` - QB connection page
- `/admin/integrations/quickbooks/sync` - Sync status dashboard
- `/admin/reports/ar-aging` - AR aging with drill-down
- `/admin/reports/ap-aging` - AP aging with drill-down
- `/admin/reports/financial-dashboard` - Overall financial health
- `/admin/vendor-bills` - Bill list
- `/admin/vendor-bills/{id}` - Bill detail + approval
- `/admin/settings/payment-config` - Payment configuration UI

**Testing Checklist:**
- [ ] Connect to QuickBooks sandbox
- [ ] Sync 10 clients to QB as customers
- [ ] Sync 5 invoices to QB
- [ ] Sync 3 payments to QB
- [ ] View AR aging (verify 30/60/90 buckets)
- [ ] Create vendor bill and approve
- [ ] Pay vendor bill, verify payment
- [ ] Generate unearned revenue report
- [ ] Update payment config (deposit 30%)

---

### Phase 3: Vendor Management & Dispatch (Weeks 9-11) - HIGH PRIORITY

#### Goal: Vendor portal and dispatch operations

**Backend Tasks:**
1. ✅ **Vendor Service - Full Implementation**
   - Vendors table + CRUD
   - Vendor bids table + workflow
   - Vendor assignments
   - COI tracking with expiration
   - Jotform webhook
   - Vendor portal endpoints

2. ✅ **Charter Service - Dispatch Module**
   - Dispatch tasks table
   - Special instructions table
   - Recovery workflow
   - Charter splitting
   - Driver/vendor confirmation tracking

3. ✅ **Airflow DAG - COI Expiration Monitoring**
   - Daily COI check
   - Alert generation (30/15/7/0 days)
   - Auto-suspension of expired vendors

4. ✅ **Airflow DAG - Bid Opportunity Notifications**
   - Check new charters >200mi from hub
   - Notify eligible vendors
   - Track bid opportunity emails

**Admin Portal Updates:**
- `/admin/vendors` - Vendor list with COI status
- `/admin/vendors/{id}` - Vendor profile
- `/admin/vendors/{id}/coi` - COI upload/tracking
- `/admin/bids` - Bid management page
- `/admin/bids/{id}` - Bid detail with accept/decline
- `/admin/dispatch/board` - Dispatch board with tasks
- `/admin/dispatch/recovery` - Recovery dashboard
- `/admin/charters/{id}/split` - Charter split UI

**Vendor Portal Pages:**
- `/vendor/login` - Vendor login
- `/vendor/dashboard` - Vendor dashboard
- `/vendor/assignments` - My assignments
- `/vendor/opportunities` - Bid opportunities
- `/vendor/bids` - My bids

**Testing Checklist:**
- [ ] Create vendor with COI (expires in 20 days)
- [ ] Receive COI expiration alert
- [ ] Create charter >200mi, verify vendor notification
- [ ] Vendor submits bid
- [ ] Accept bid and assign vendor
- [ ] Vendor confirms assignment
- [ ] Vendor requests recovery
- [ ] Dispatcher finds replacement vendor
- [ ] Split charter into 2 vehicles
- [ ] Complete dispatch tasks, see icons disappear

---

### Phase 4: Change Management & Client Portal (Weeks 12-14) - MEDIUM PRIORITY

#### Goal: Post-booking changes and client self-service

**Backend Tasks:**
1. ✅ **Change Management Service - Full Implementation**
   - Change cases table + workflow
   - Auto-create trigger on charter updates
   - Approval workflow
   - Before/after snapshots
   - Charter audit log

2. ✅ **Portals Service - Client Portal**
   - Client authentication
   - Client dashboard
   - My charters view
   - My quotes view
   - Payment history
   - Saved payment methods
   - E-signature integration
   - Notification preferences

3. ✅ **Auth Service - Impersonation**
   - Session management
   - "View as client" feature
   - Impersonation logging

4. ✅ **Payment Service - Client Payment Features**
   - Saved payment methods table
   - Payment plans
   - Stripe Customer Portal integration

**Admin Portal Updates:**
- `/admin/change-cases` - Change case list
- `/admin/change-cases/{id}` - Case workflow page
- `/admin/change-cases/dashboard` - Dashboard by status
- `/admin/clients/{id}/portal-view` - Impersonate client
- `/admin/payments/plans` - Payment plan configuration

**Client Portal Pages:**
- `/portal/login` - Client login with MFA
- `/portal/dashboard` - Client dashboard
- `/portal/trips` - My trips
- `/portal/trips/{id}` - Trip detail
- `/portal/quotes` - My quotes
- `/portal/quotes/{id}/accept` - Accept quote
- `/portal/payments` - Payment history
- `/portal/payments/make-payment` - Make payment
- `/portal/settings` - Preferences

**Testing Checklist:**
- [ ] Update booked charter date, see change case auto-create
- [ ] Review change case, add vendor quote
- [ ] Send client approval request
- [ ] Client approves in portal
- [ ] Implement change
- [ ] Agent impersonates client
- [ ] Client logs in, views trips
- [ ] Client accepts quote
- [ ] Client makes payment
- [ ] Client updates notification preferences

---

### Phase 5: Reporting & Analytics (Weeks 15-17) - MEDIUM PRIORITY

#### Goal: Manager dashboards and reporting

**Backend Tasks:**
1. ✅ **Reporting Service - Full Implementation**
   - Report templates table
   - Report builder API
   - Pre-built reports
   - Scheduled reports
   - Dashboard customization

2. ✅ **Pricing Service - Configuration UI Support**
   - Pricing modifiers endpoint
   - Pricing matrix API
   - Configuration endpoints

3. ✅ **Auth Service - RBAC UI Support**
   - Role management endpoints
   - Permission assignment endpoints
   - User role assignment

**Admin Portal Updates:**
- `/admin/reports/builder` - Visual report builder
- `/admin/reports/templates` - Saved templates
- `/admin/reports/scheduled` - Schedule management
- `/admin/dashboard/manager` - Manager dashboard
- `/admin/dashboard/customize` - Dashboard customization
- `/admin/settings/pricing/modifiers` - Pricing modifiers
- `/admin/settings/pricing/matrix` - Pricing matrix
- `/admin/settings/rbac/roles` - Role management
- `/admin/settings/rbac/permissions` - Permission assignment

**Testing Checklist:**
- [ ] Create custom report (sales by agent)
- [ ] Save report template
- [ ] Schedule daily email report
- [ ] Customize manager dashboard (add/remove widgets)
- [ ] Configure pricing modifier (weekend +10%)
- [ ] Create new role with specific permissions
- [ ] Assign role to user, verify access

---

### Phase 6: Polish & Role-Specific UIs (Weeks 18-20) - LOW PRIORITY

#### Goal: Build dedicated role-specific interfaces

**Frontend Tasks:**
1. ✅ **Sales Agent Interface**
   - Dedicated sales dashboard
   - Simplified quote builder
   - My pipeline view
   - Follow-up reminders

2. ✅ **Dispatch Interface**
   - Visual dispatch board
   - Real-time GPS map
   - Task checklist view
   - Recovery management

3. ✅ **Accounting Interface**
   - Financial dashboard
   - Quick access to AR/AP
   - QB sync status
   - Payment processing

4. ✅ **Driver Mobile App**
   - Mobile-optimized layout
   - Native GPS integration
   - Photo upload
   - One-tap actions

**Pages:**
- `/sales/dashboard` - Sales agent view
- `/sales/quotes` - My quotes
- `/sales/leads` - My leads
- `/dispatch/board` - Dispatch board
- `/dispatch/map` - Live GPS map
- `/accounting/dashboard` - Accounting view
- `/accounting/ar` - AR management
- `/accounting/ap` - AP management
- `/driver` - Driver mobile view (enhanced)

**Testing Checklist:**
- [ ] Sales agent: create quote from lead
- [ ] Sales agent: view MTD performance
- [ ] Dispatch: view today's board
- [ ] Dispatch: complete all tasks for charter
- [ ] Accounting: view AR aging
- [ ] Accounting: sync to QuickBooks
- [ ] Driver: complete pre-trip checklist
- [ ] Driver: upload vehicle photo

---

## Part 4: Testing Strategy

### Admin Portal Testing Approach

**Principle:** Build all backend capabilities first, test through admin portal before creating role-specific UIs.

#### Testing Environment Setup
1. **Admin User:** Full permissions to test all features
2. **Test Data:** Seed database with realistic scenarios
3. **Test Clients:** Multiple clients for different scenarios
4. **Test Vendors:** 5-10 vendors with varying attributes
5. **Test Drivers:** 3-5 driver accounts

#### Testing Matrix by Phase

**Phase 0 Testing:**
- Admin creates recurring charter series
- Admin clones charter to multiple dates
- Admin deletes instance from series
- Admin creates lead, system assigns
- Admin applies payment to 3 charters

**Phase 1 Testing:**
- Admin converts lead to quote
- Admin builds complex itinerary (5+ stops)
- Admin adds amenities, verifies pricing
- Admin applies promo code
- Admin sends quote with secure link
- Admin tracks email engagement

**Phase 2 Testing:**
- Admin connects QuickBooks
- Admin syncs entities to QB
- Admin views AR/AP aging
- Admin creates and approves vendor bill
- Admin pays vendor bill
- Admin modifies payment configuration

**Phase 3 Testing:**
- Admin creates vendor with COI
- Admin accepts vendor bid
- Admin assigns vendor to charter
- Admin monitors dispatch board
- Admin completes dispatch tasks
- Admin initiates recovery

**Phase 4 Testing:**
- Admin triggers change case
- Admin processes change workflow
- Admin impersonates client
- Admin configures payment plan
- "Client" (admin impersonating) makes payment
- "Client" accepts quote

**Phase 5 Testing:**
- Admin creates custom report
- Admin schedules report
- Admin configures pricing modifier
- Admin creates role and assigns permissions
- Admin customizes dashboard

**Phase 6 Testing:**
- Sales agent (separate account) tests sales UI
- Dispatch (separate account) tests dispatch UI
- Accounting (separate account) tests accounting UI
- Driver (separate account) tests mobile app

#### Automated Testing
- Unit tests for business logic
- Integration tests for API endpoints
- End-to-end tests for critical workflows

---

## Part 5: Priority Summary

### P0 - Critical (Must Have for MVP)
1. ✅ Sales Service - Lead management
2. ✅ Charter Service - Recurring/cloning
3. ✅ Payment Service - AR/AP core
4. ✅ Payment Service - QuickBooks sync

**Estimated: 6-8 weeks**

### P1 - High Priority (Core Features)
1. ✅ Pricing Service - Amenities, promo codes
2. ✅ Vendor Service - Vendor portal, bids
3. ✅ Portals Service - Client portal
4. ✅ Charter Service - Dispatch module
5. ✅ Auth Service - MFA, impersonation

**Estimated: 8-10 weeks**

### P2 - Medium Priority (Enhanced Features)
1. ✅ Change Management Service
2. ✅ Reporting Service
3. ✅ Document Service - COI tracking
4. ✅ Charter Service - Driver enhancements

**Estimated: 6-8 weeks**

### P3 - Low Priority (Future Enhancements)
1. ⏳ Advanced lead scoring
2. ⏳ Peak period analytics
3. ⏳ AI-powered route optimization
4. ⏳ Vendor bid analytics

**Estimated: 4-6 weeks**

---

## Part 6: Development Resources Needed

### Backend Development
- **Python/FastAPI expertise:** 3-4 developers
- **Database design:** 1 developer (PostgreSQL)
- **Integration expertise:** 1 developer (QuickBooks, Stripe, Google Maps)
- **Airflow/workflow automation:** 1 developer

### Frontend Development
- **React/TypeScript:** 2-3 developers
- **UI/UX design:** 1 designer
- **Mobile optimization:** 1 developer (driver app)

### DevOps
- **Container orchestration:** 1 engineer
- **Monitoring/logging:** 1 engineer

### QA/Testing
- **Manual QA:** 2 testers
- **Automation:** 1 QA engineer

### Estimated Timeline
- **P0 Features:** 6-8 weeks
- **P1 Features:** 8-10 weeks
- **P2 Features:** 6-8 weeks
- **Total MVP:** 20-26 weeks (5-6 months)

---

## Part 7: Risk Mitigation

### Technical Risks

**Risk 1: QuickBooks API Complexity**
- **Mitigation:** Start with one-way sync, then bidirectional
- **Fallback:** Export/import via CSV

**Risk 2: Performance with Large Data**
- **Mitigation:** Implement pagination, caching, indexing
- **Fallback:** Database query optimization

**Risk 3: Service Communication Latency**
- **Mitigation:** Use message queues for async operations
- **Fallback:** Service consolidation if needed

**Risk 4: Third-party API Dependencies**
- **Mitigation:** Implement retry logic, circuit breakers
- **Fallback:** Graceful degradation

### Business Risks

**Risk 1: Feature Scope Creep**
- **Mitigation:** Strict prioritization, phase-based rollout
- **Fallback:** Cut P3 features

**Risk 2: User Adoption**
- **Mitigation:** Extensive training, phased rollout
- **Fallback:** Parallel legacy system operation

---

## Conclusion

This gap analysis identifies **89 distinct capabilities** requested by the client, of which:
- **25 are complete** in current system
- **31 are partially implemented** (need enhancement)
- **11 have stubs** (need completion)
- **22 are missing** (need full build)

The implementation plan spans **20-26 weeks** across 6 phases, building from critical backend services through role-specific UIs. All capabilities will be tested through the admin portal first before creating dedicated role interfaces.

**Next Steps:**
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 0 implementation
4. Schedule weekly progress reviews
5. Prepare test data and scenarios

---

**Document Version:** 1.0  
**Last Updated:** January 31, 2026  
**Maintained By:** Development Team
