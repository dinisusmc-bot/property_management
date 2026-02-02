# Invoice and Payment System Implementation

## Overview
Comprehensive invoicing, payment tracking, and automated email system for Athena Coach Services.

## Database Changes

### New Tables Created
1. **invoices** - Main invoice tracking
   - Invoice numbers (auto-generated: INV-00001, INV-00002, etc.)
   - Status tracking (draft, sent, paid, overdue, cancelled, refunded)
   - Amount tracking (subtotal, tax, discount, total, amount_paid, balance_due)
   - Payment terms and due dates
   - Email tracking (last_sent_date, sent_count)

2. **payments** - Payment transaction records
   - Stripe integration (payment_intent_id, charge_id, customer_id)
   - Payment types (deposit, balance, partial, refund)
   - Payment methods (card, check, wire, cash, ach)
   - Status tracking (pending, processing, succeeded, failed, refunded)
   - Card details (last 4 digits, brand)
   - Failure tracking (code, reason)

3. **payment_schedules** - Payment due dates and reminders
   - Payment type (deposit, balance, installments)
   - Due dates and amounts
   - Reminder tracking (sent count, last sent, next reminder date)
   - Status (pending, sent_reminder, paid, overdue, waived)

4. **payment_refunds** - Refund processing
   - Refund amount and reason
   - Stripe refund tracking
   - Status (processing, succeeded, failed, cancelled)

5. **invoice_line_items** - Detailed invoice breakdowns
   - Line item descriptions
   - Quantity, unit price, amounts
   - Categories (base_rate, mileage, fuel_surcharge, tolls, etc.)

6. **email_logs** - Audit trail for all emails
   - Email types (quote, invoice, reminder, approval, confirmation)
   - Recipient tracking
   - Status (sent, failed, bounced, opened, clicked)
   - SendGrid message IDs

### Updated Tables
**charters** - Added new fields:
- `client_confirmation_name` - Contact person for approvals
- `client_confirmation_email` - Email for sending quotes/invoices
- `client_confirmation_date` - When client confirmed booking
- `approval_sent_date` - When approval request was sent
- `quote_signed_date` - When quote was signed/approved
- `tax_rate` - Tax percentage
- `tax_amount` - Calculated tax amount
- `discount_amount` - Any discounts applied
- `invoice_number` - Linked invoice number

### Database Functions
1. **update_invoice_balance()** - Auto-calculates invoice balance when payments are made
2. **generate_invoice_number()** - Auto-generates sequential invoice numbers

### Triggers
- **trigger_update_invoice_balance** - Automatically updates invoice balance_due when payments change status

## Airflow Automation

### New DAG: invoice_payment_reminders.py
**Schedule**: Every 6 hours  
**Purpose**: Automated email reminders for invoices and payments

**Tasks**:
1. **send_new_invoices** - Sends newly created draft invoices
2. **send_upcoming_payment_reminders** - Reminders 3 days before payment due
3. **send_overdue_invoice_reminders** - Urgent reminders for past due invoices (sent every 3 days)

**Features**:
- Integrates with notification service
- Tracks email sending history
- Updates invoice/schedule status automatically
- Respects reminder intervals to avoid spam

## Email Templates

### Created Templates (in notification service):
1. **invoice_notification** - New invoice notification
2. **overdue_invoice_reminder** - Urgent payment reminder with days overdue
3. **upcoming_payment_reminder** - Friendly reminder for upcoming payments
4. **quote_approval_request** - Request client to approve/sign quote
5. **booking_confirmation** - Confirmation after booking is approved

### Template Features:
- Professional HTML and plain text versions
- Dynamic data using Jinja2 templating
- Color-coded urgency (red for overdue, blue for normal, green for confirmation)
- Clear calls-to-action
- Branded with Athena Coach Services

## Frontend Changes

### Charter Detail Page Updates:
1. **New Action Buttons**:
   - **"Send for Approval"** - Visible when status = 'quote'
     - Sends quote approval request to client
     - Marks approval_sent_date
   - **"Send Confirmation"** - Visible when status = 'confirmed' and confirmation not yet sent
     - Sends booking confirmation email
     - Includes deposit and balance due information

2. **Client Confirmation Section** (new):
   - Contact Name (editable)
   - Contact Email (editable)
   - Confirmation Date (auto-set when confirmed)
   - Approval Sent Date (shows when approval was sent)
   - Quote Signed Date (shows when quote was approved)

### Client Detail Page:
- **Order History** section shows all charters for the client
- Displays order ID, trip date, status, passengers, cost, created date
- Summary statistics (total orders, total revenue)
- "View" button to navigate to charter details

### Charter Create Page:
- Added **arrival_time** and **departure_time** fields for each stop
- Better layout for stop information (location, times, notes)

## API Integration

### Payment Service Endpoints (Port 8003):
- POST `/payments/create-intent` - Create Stripe PaymentIntent
- POST `/payments/charge-saved-card` - Charge saved payment method
- GET `/payments/charter/{charter_id}` - List payments for charter
- POST `/payments/refund` - Process refund
- POST `/payments/webhook` - Handle Stripe webhooks
- GET `/payment-schedules/charter/{charter_id}` - Get payment schedule
- POST `/payment-schedules` - Create payment schedule

### Notification Service Endpoints (Port TBD):
- POST `/notifications` - Send notification (email/SMS)
- GET `/notifications/{id}` - Get notification status
- POST `/templates` - Create email template
- GET `/templates` - List templates
- PUT `/templates/{name}` - Update template

## Setup Instructions

### 1. Run Database Migration
```bash
cat /home/Ndini/work_area/coachway_demo/backend/scripts/add_invoice_payment_tables.sql | \
  podman exec -i athena-postgres psql -U athena -d athena
```

### 2. Start Payment Service (when ready)
```bash
podman-compose up -d payments
```

### 3. Start Notification Service (when ready)
```bash
podman-compose up -d notifications
```

### 4. Seed Email Templates
```bash
python /home/Ndini/work_area/coachway_demo/backend/scripts/seed_notification_templates.py
```

### 5. Configure Environment Variables
Add to your `.env` file:
```
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SendGrid
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=noreply@athenacoach.com

# Twilio (optional, for SMS)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_PHONE=+1...
```

## Workflow Examples

### Creating an Invoice
1. Charter is created with status='quote'
2. User clicks "Send for Approval" on charter detail page
3. Approval email sent to `client_confirmation_email`
4. Client approves (manually update status to 'confirmed')
5. Invoice auto-generated when Airflow DAG runs
6. Invoice sent via email
7. Payment reminders sent automatically

### Processing Payments
1. Client makes payment via Stripe
2. Webhook received by payment service
3. Payment record created
4. Invoice balance automatically updated
5. Email notification sent to client
6. Payment schedule updated

### Automated Reminders
- **Day -3**: "Upcoming payment reminder" sent
- **Day 0**: Invoice due
- **Day +3**: "Overdue payment reminder" sent
- **Day +6**: Second overdue reminder
- **Day +9**: Third overdue reminder
- Pattern continues every 3 days

## Next Steps

### Immediate:
1. Add payment service and notification service to docker-compose.yml
2. Configure Kong routes for new services
3. Set up Stripe test account
4. Set up SendGrid account
5. Test email templates

### Future Enhancements:
1. PDF invoice generation
2. Online payment portal for clients
3. Recurring billing for corporate accounts
4. Multi-currency support
5. Payment analytics dashboard
6. ACH/Bank transfer support
7. Invoice dispute handling
8. Automated late fees
9. Credit memo support
10. Payment plan management

## Files Created/Modified

### Backend:
- `/backend/scripts/add_invoice_payment_tables.sql` - Database migration
- `/backend/scripts/seed_notification_templates.py` - Email template seeder
- `/backend/services/payments/` - Complete payment service (9 files)
- `/backend/services/notifications/` - Complete notification service (9 files)
- `/airflow/dags/invoice_payment_reminders.py` - Automated email DAG

### Frontend:
- `/frontend/src/pages/charters/CharterDetail.tsx` - Added approval buttons, client confirmation section
- `/frontend/src/pages/charters/CharterCreate.tsx` - Added time fields for stops
- `/frontend/src/pages/clients/ClientDetail.tsx` - Added order history section

## Testing Checklist

- [ ] Database tables created successfully
- [ ] Invoice number generation works
- [ ] Payment triggers update invoice balance
- [ ] Airflow DAG appears in UI
- [ ] Email templates created in notification service
- [ ] "Send for Approval" button works
- [ ] "Send Confirmation" button works
- [ ] Client confirmation fields save correctly
- [ ] Order history shows on client detail page
- [ ] Stop times display on charter create page
- [ ] Stripe payment intent creation works
- [ ] Payment webhooks process correctly
- [ ] Email notifications send successfully
- [ ] Automated reminders trigger on schedule

## Support

For issues or questions:
1. Check Airflow logs: `podman logs athena-airflow-webserver`
2. Check payment service logs: `podman logs athena-payments`
3. Check notification service logs: `podman logs athena-notifications`
4. Check database: `podman exec athena-postgres psql -U athena -d athena`
