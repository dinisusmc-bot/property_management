-- Add invoicing and payment tracking tables
-- Run this migration to add comprehensive order and payment tracking

-- Add client confirmation field to charters
ALTER TABLE charters ADD COLUMN IF NOT EXISTS client_confirmation_name VARCHAR(255);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS client_confirmation_email VARCHAR(255);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS client_confirmation_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS approval_sent_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS quote_signed_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS tax_rate DECIMAL(5,4) DEFAULT 0.0;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS tax_amount DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50);

-- Create invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL,
    
    -- Invoice details
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, sent, paid, overdue, cancelled, refunded
    
    -- Amounts
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0.0,
    discount_amount DECIMAL(10,2) DEFAULT 0.0,
    total_amount DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) DEFAULT 0.0,
    balance_due DECIMAL(10,2) NOT NULL,
    
    -- Payment terms
    payment_terms TEXT,
    notes TEXT,
    
    -- Email tracking
    last_sent_date TIMESTAMP WITH TIME ZONE,
    sent_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT invoice_balance_check CHECK (balance_due >= 0)
);

CREATE INDEX IF NOT EXISTS idx_invoices_charter_id ON invoices(charter_id);
CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    
    -- Payment details
    amount DECIMAL(10,2) NOT NULL,
    payment_type VARCHAR(50) NOT NULL, -- deposit, balance, partial, refund
    payment_method VARCHAR(50) NOT NULL, -- card, check, wire, cash, ach
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, succeeded, failed, refunded
    
    -- Stripe integration
    stripe_payment_intent_id VARCHAR(255),
    stripe_charge_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    stripe_refund_id VARCHAR(255),
    
    -- Card details (last 4 digits only)
    card_last4 VARCHAR(4),
    card_brand VARCHAR(50),
    
    -- Transaction details
    transaction_id VARCHAR(255),
    reference_number VARCHAR(255),
    description TEXT,
    
    -- Failure tracking
    failure_code VARCHAR(100),
    failure_reason TEXT,
    
    -- Timestamps
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT payment_amount_positive CHECK (amount > 0)
);

CREATE INDEX IF NOT EXISTS idx_payments_invoice_id ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_charter_id ON payments(charter_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_intent ON payments(stripe_payment_intent_id);

-- Create payment schedules table
CREATE TABLE IF NOT EXISTS payment_schedules (
    id SERIAL PRIMARY KEY,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Schedule details
    payment_type VARCHAR(50) NOT NULL, -- deposit, balance, installment_1, installment_2, etc
    amount_due DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, sent_reminder, paid, overdue, waived
    
    -- Reminder tracking
    reminder_sent_count INTEGER DEFAULT 0,
    last_reminder_sent TIMESTAMP WITH TIME ZONE,
    next_reminder_date DATE,
    
    -- Payment tracking
    paid_amount DECIMAL(10,2) DEFAULT 0.0,
    paid_date DATE,
    payment_id INTEGER REFERENCES payments(id),
    
    -- Notes
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT schedule_amount_positive CHECK (amount_due > 0)
);

CREATE INDEX IF NOT EXISTS idx_payment_schedules_charter_id ON payment_schedules(charter_id);
CREATE INDEX IF NOT EXISTS idx_payment_schedules_due_date ON payment_schedules(due_date);
CREATE INDEX IF NOT EXISTS idx_payment_schedules_status ON payment_schedules(status);

-- Create refunds table
CREATE TABLE IF NOT EXISTS payment_refunds (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    
    -- Refund details
    amount DECIMAL(10,2) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'processing', -- processing, succeeded, failed, cancelled
    
    -- Stripe integration
    stripe_refund_id VARCHAR(255),
    
    -- Details
    notes TEXT,
    processed_by INTEGER, -- user_id who processed the refund
    
    -- Timestamps
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT refund_amount_positive CHECK (amount > 0)
);

CREATE INDEX IF NOT EXISTS idx_refunds_payment_id ON payment_refunds(payment_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON payment_refunds(status);

-- Create invoice line items table (optional, for detailed invoicing)
CREATE TABLE IF NOT EXISTS invoice_line_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Line item details
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    
    -- Categorization
    category VARCHAR(100), -- base_rate, mileage, fuel_surcharge, tolls, parking, waiting_time, etc
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_line_items_invoice_id ON invoice_line_items(invoice_id);

-- Create email log table for tracking sent invoices/approvals
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    charter_id INTEGER REFERENCES charters(id) ON DELETE CASCADE,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Email details
    email_type VARCHAR(50) NOT NULL, -- quote, invoice, reminder, approval, confirmation
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    subject VARCHAR(500),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'sent', -- sent, failed, bounced, opened, clicked
    
    -- External IDs
    sendgrid_message_id VARCHAR(255),
    
    -- Timestamps
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_email_logs_charter_id ON email_logs(charter_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_invoice_id ON email_logs(invoice_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);

-- Function to automatically update balance_due on invoices
CREATE OR REPLACE FUNCTION update_invoice_balance()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE invoices 
    SET 
        amount_paid = COALESCE((
            SELECT SUM(amount) 
            FROM payments 
            WHERE invoice_id = NEW.invoice_id 
            AND status = 'succeeded'
        ), 0),
        balance_due = total_amount - COALESCE((
            SELECT SUM(amount) 
            FROM payments 
            WHERE invoice_id = NEW.invoice_id 
            AND status = 'succeeded'
        ), 0),
        updated_at = NOW()
    WHERE id = NEW.invoice_id;
    
    -- Update status to paid if balance is zero
    UPDATE invoices
    SET status = 'paid'
    WHERE id = NEW.invoice_id 
    AND balance_due = 0 
    AND status != 'paid';
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update invoice balance when payments change
DROP TRIGGER IF EXISTS trigger_update_invoice_balance ON payments;
CREATE TRIGGER trigger_update_invoice_balance
    AFTER INSERT OR UPDATE OF status, amount ON payments
    FOR EACH ROW
    WHEN (NEW.invoice_id IS NOT NULL)
    EXECUTE FUNCTION update_invoice_balance();

-- Function to generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number()
RETURNS TEXT AS $$
DECLARE
    next_num INTEGER;
    invoice_num TEXT;
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(invoice_number FROM 5) AS INTEGER)), 0) + 1
    INTO next_num
    FROM invoices
    WHERE invoice_number LIKE 'INV-%';
    
    invoice_num := 'INV-' || TO_CHAR(next_num, 'FM00000');
    RETURN invoice_num;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE invoices IS 'Stores invoice records for charters with payment tracking';
COMMENT ON TABLE payments IS 'Tracks all payment transactions including Stripe integration';
COMMENT ON TABLE payment_schedules IS 'Manages payment due dates and reminders';
COMMENT ON TABLE payment_refunds IS 'Tracks refund transactions';
COMMENT ON TABLE invoice_line_items IS 'Detailed line items for invoices';
COMMENT ON TABLE email_logs IS 'Audit log for all emails sent (invoices, quotes, approvals)';
