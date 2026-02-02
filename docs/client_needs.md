Role-Based Views & Needs
US Coachways Next-Gen Platform
This document defines the tailored interfaces, workflows, dashboards, and
permissions required for each major user group to perform their core responsibilities
efficiently.
1. Sales Agents
Primary Goal
Generate quotes, convert leads, close sales, manage client relationships, and capture
accurate initial trip details.
Key Views & Capabilities - Lead & Opportunity Pipeline
- Recent leads (last 30 days) + open quotes (next 120 days)
- Convert lead → quote/opportunity in one step.
- Round-robin assignment for new leads; auto-assign to owner for existing clients
- Automated follow-up email tracking
- Enable Sales Agents to disable system automated emails to their clients.
- Quote Builder
- Mirror client-facing quote calculator for simulation
- Build multi-stop itineraries (add/reorder stops, geocode locations, dates/ times)
- Auto-DOT regulation checks (hours/miles → second driver flags)
- Trip-type selector (one-way, round-trip, overnight, local, event-specific)
- Auto vehicle recommendations + manual override, add or remove vehicles from
quote, edit original vehicle count.
- Promo codes (add a field for this client to populate or agent for the client), amenity
selection (real-time pricing)
- Email quote with secure booking link; revise/resend without duplication.
- Client & Booking Flow
- View the client portal as the client sees it
- Seamless login for existing clients; frictionless entry for new
- Login should be the client's email. Booking notification (“book charter”
task)
- View client payment status/methods
- Selected amenities should also pre-populate into vendor notes.
- Pre-Booking Charter Tools
- Clone/duplication (single or multi-date calendar picker)
- Recurring charter support (with instance-level delete)
- Document attachments (vendor bids, client docs, T&C’s)
- Agents need the ability to assign a quote in their name to another agent. They are not
to have the ability to take a quote or client account out of another agent's name.
Personal Dashboard & Reports
- Open quotes, follow-ups, leads received, upcoming departures, non-CC money
due, MTD booked/profit, Hot leads/Pipeline tracking.
- Filtered to the agent’s own clients only
- Permissions
- Restricted manual price overrides post-quote/booking
- Integrations
- Phone system (Vonage-style) for click-to-dial + call logging
Top Improvements Needed
Mass duplication/cloning, simplified mobile experience (replacement for Salesforce
app).
2. Sales Support
Primary Goal
Handle post-booking changes, track non-credit-card payments, coordinate vendors,
and perform quality control.
Key Views & Capabilities - Change Management
- Open the change-case dashboard (assigned by the system when anyone makes a
change on a booked trip)
- Auto-create case on client-requested itinerary change
- Full change history snapshots (who, what, when)
- Workflow: review → vendor re-quote → client approval → update
- Post-booking amenity removal/addition
- Financial Tracking
- Non-CC money-due report (checks, wires, POs)
- Manual payment application (wire/PO)
- PO linking to receivables
- Real-time updated totals visible in the client portal
- Quality Control (QC)
- Open QC tasks post-booking
- Verify addresses, payments, and special requirements
- Vendor Coordination
- View bid history per charter
- Track multi-vendor negotiations
- Permissions
- Granular edit rights on financial/change fields
- Ability in financials to charge cards manually.
- Ability to adjust payment dates.
- Automated Triggers
- Trip-type-specific tasks (flight number, hotel rooms, casino slot id’s etc.)
Top Improvements Needed
Streamline change-case workflow; eliminate client “acceptance login” for price
increases.
3. Accounting
Primary Goal
Manage AR/AP, financial reconciliation, reporting, and QuickBooks
integration.
Key Views & Capabilities - QuickBooks Integration
- Preferred: bidirectional API sync
- Fallback: structured export for validation
- AR/AP Oversight
- Outstanding client receivables + vendor payables
- Charter-linked paid/unpaid status + zero-balance view -
- Aging vendor payable report 30-60-90-120
- Application for payment for lump sum payment received apply
to multiple charters
- Purchase order payments overdue reporting ( schools,
government agencies)
Reporting & Commissions
- Departed trips by agent/month (profit field required) - Overall
sales, profit, and financial health dashboards
- Cancellation reporting by cancel date
- cancel fees collected vs uncollected
- Unearned revenue reporting (Funds collected where trips
have not departed)
- Daily check log report
- today's collected accounts receivable report ( Credit cards,
wires, ach, checks)
- upcoming collectable payments due for Credit card and
check
- Payment Flexibility
- Configurable structures (deposit %, due dates)
- Manual adjustments (partial payments)
- Permissions
- Broad financial access, segmented from operations
Top Improvements Needed
Reliable, clean QuickBooks sync; accurate, accessible financial data.
4. Dispatch
Primary Goal
Manage trip execution, driver assignments, and real-time vehicle
monitoring.
Key Views & Capabilities - Dispatch Board
- Charters entering dispatch stage (2 days pre-departure)
- Visual overview (icon-based like Athena) for status & needs
- Tasks auto-complete → icons disappear
- Driver & Route Management
- Driver confirmation/contact
- Route + special instruction access
- Real-time GPS map of active vehicles
- Recurring Shuttles
- Multi-day tracking (e.g., “Day 1 of 20”)
- Permissions
- Operational execution + real-time monitoring focus
- Dispatch should have the ability to place a charter into recovery, access to add vendor
bids, award vendors, split charters, and cancel if needed.
Top Improvements Needed
Modern mobile driver app, robust GPS tracking, and intuitive visual board.
5. Managers & Executives
Primary Goal
Provide strategic oversight, performance monitoring, team management, and
system configuration.
Key Views & Capabilities - Enterprise Dashboards
- Cross-agent view: sales, profit, open cases, QC backlog
- Customizable reports with saved templates
- Audit & History
- Full charter change log (who/what/when)
- Price/payment adjustment tracking
- Configuration Tools
- Promo code management
- Pricing matrix + modifiers (day-of, event, hub, ASAP)
- Vendor COI expiration tracking & alerts
- Ability to add/remove sales agents from lead queue as well as ability to set max
amount of leads per day. (Auto-assigned leads should still work even if agent is above
max or not in the lead assignment queue)
- User & Role Management
- Create/edit roles & granular permissions
- Strategic Insights
- Vendor bid analytics, peak period identification
Top Improvements Needed
User-friendly pricing/configuration UI; eliminate developer dependency for most
changes.
6. Clients (Self-Service Portal)
Primary Goal
Self-quote, book, manage reservations, and pay securely.
Key Views & Capabilities - Quote Calculator (Public Website)
- Simple inputs → real-time pricing
- Trip type, vehicle recommendations, amenities, promo codes
- DOT miles/hours display
- Client Portal
- Easy login (forgot password + MFA)
- New-client frictionless entry (password set post-booking)
- View current/historical trips, quotes for future trips & booked
charters.
- Detailed itinerary, vehicle, payment breakdown
- Flexible payment (CC, PO(School trips only), ACH/wire)
- E-signature for terms
- Zero-balance confirmation
- Opt-in SMS updates
Top Improvements Needed
Low-friction booking, reliable pricing adjustments, and confident direct online
conversion.
7. Drivers (Mobile App)
Primary Goal
View assignments, provide real-time location, and log trip notes.
Key Views & Capabilities - Mobile-First Interface
- Secure, separate login
- Upcoming/current trip list
- Trip Execution
- Full itinerary + stops + instructions
- One-tap GPS activation
- In-app note & photo upload
- Simple Dashboard
- Today’s jobs + upcoming assignments
- Click to dial to dispatch.
Top Improvements Needed
Modern, reliable mobile experience with strong tracking.
8. Vendors (Vendor Portal)
Primary Goal
Review, confirm, and manage assigned charter jobs.
Key Views & Capabilities - Vendor Portal
- Secure login; vendors see only their assignments
- Pending Assignments
- Vendor Coordination
- View bid history per charter
- Track multi-vendor negotiations
- List of charters awaiting confirmation
- Detailed view: itinerary, vehicle needs, amenities, agreed rate
- Clear Accept / Decline (with optional reason)
- Post-Confirmation
- Will vendors be able to receive notification when a charter books that is outside 200
miles from the pickup location and place bids to feed back to us for
negotiations/awarding?
- Final itinerary + attachments
- Upcoming trip overview
- Historical job list
- Notifications
- Email alerts with portal link for pending jobs, recoveries (Vendor can’t do charter) &
cancellations.
- Jotform notifications- This is a form that new vendors send in their credentials to start
doing business with us.
Permissions
- Strictly limited to own charters; no client/financial data
Top Improvements Needed
Replace verbal/email confirmations with a centralized, trackable portal process.
