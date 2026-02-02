-- Payment tracking system for vendor payments and client payments
-- This creates two tables to properly track debits (what we pay vendors) and credits (what clients pay us)

-- Vendor Payments Table (Debits - Money Out)
CREATE TABLE IF NOT EXISTS vendor_payments (
    id SERIAL PRIMARY KEY,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    vendor_id INTEGER NOT NULL,  -- FK to auth service users table
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATE,
    payment_method VARCHAR(50),  -- check, wire_transfer, ach, credit_card, cash, other
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, paid, cancelled
    reference_number VARCHAR(100),  -- Check number, transaction ID, etc.
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER,  -- FK to auth service users table (who created the payment record)
    
    CONSTRAINT vendor_payments_amount_positive CHECK (amount > 0)
);

-- Client Payments Table (Credits - Money In)
CREATE TABLE IF NOT EXISTS client_payments (
    id SERIAL PRIMARY KEY,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL,  -- FK to client service clients table
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATE,
    payment_method VARCHAR(50),  -- check, wire_transfer, ach, credit_card, cash, invoice, other
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, paid, partial, cancelled
    payment_type VARCHAR(20),  -- deposit, full_payment, partial_payment, final_payment
    reference_number VARCHAR(100),  -- Invoice number, check number, transaction ID, etc.
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER,  -- FK to auth service users table (who created the payment record)
    
    CONSTRAINT client_payments_amount_positive CHECK (amount > 0)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_vendor_payments_charter ON vendor_payments(charter_id);
CREATE INDEX IF NOT EXISTS idx_vendor_payments_vendor ON vendor_payments(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_payments_status ON vendor_payments(payment_status);
CREATE INDEX IF NOT EXISTS idx_vendor_payments_date ON vendor_payments(payment_date);

CREATE INDEX IF NOT EXISTS idx_client_payments_charter ON client_payments(charter_id);
CREATE INDEX IF NOT EXISTS idx_client_payments_client ON client_payments(client_id);
CREATE INDEX IF NOT EXISTS idx_client_payments_status ON client_payments(payment_status);
CREATE INDEX IF NOT EXISTS idx_client_payments_date ON client_payments(payment_date);

-- Add comments for documentation
COMMENT ON TABLE vendor_payments IS 'Tracks payments made to vendors (debits/money out)';
COMMENT ON TABLE client_payments IS 'Tracks payments received from clients (credits/money in)';

COMMENT ON COLUMN vendor_payments.charter_id IS 'Links payment to specific charter';
COMMENT ON COLUMN vendor_payments.vendor_id IS 'Vendor receiving the payment';
COMMENT ON COLUMN vendor_payments.amount IS 'Amount paid to vendor';
COMMENT ON COLUMN vendor_payments.payment_status IS 'Status: pending, paid, cancelled';
COMMENT ON COLUMN vendor_payments.payment_method IS 'How payment was made: check, wire_transfer, ach, credit_card, cash, other';

COMMENT ON COLUMN client_payments.charter_id IS 'Links payment to specific charter';
COMMENT ON COLUMN client_payments.client_id IS 'Client making the payment';
COMMENT ON COLUMN client_payments.amount IS 'Amount received from client';
COMMENT ON COLUMN client_payments.payment_status IS 'Status: pending, paid, partial, cancelled';
COMMENT ON COLUMN client_payments.payment_type IS 'Type: deposit, full_payment, partial_payment, final_payment';
COMMENT ON COLUMN client_payments.payment_method IS 'How payment was received: check, wire_transfer, ach, credit_card, cash, invoice, other';

-- Add helper views for quick totals
CREATE OR REPLACE VIEW vendor_payment_summary AS
SELECT 
    vendor_id,
    COUNT(*) as total_payments,
    SUM(CASE WHEN payment_status = 'paid' THEN amount ELSE 0 END) as total_paid,
    SUM(CASE WHEN payment_status = 'pending' THEN amount ELSE 0 END) as total_pending,
    SUM(amount) as total_amount
FROM vendor_payments
GROUP BY vendor_id;

CREATE OR REPLACE VIEW client_payment_summary AS
SELECT 
    client_id,
    COUNT(*) as total_payments,
    SUM(CASE WHEN payment_status = 'paid' THEN amount ELSE 0 END) as total_paid,
    SUM(CASE WHEN payment_status = 'pending' THEN amount ELSE 0 END) as total_pending,
    SUM(amount) as total_amount
FROM client_payments
GROUP BY client_id;

CREATE OR REPLACE VIEW charter_payment_summary AS
SELECT 
    c.id as charter_id,
    COALESCE(SUM(vp.amount), 0) as vendor_payments_total,
    COALESCE(SUM(CASE WHEN vp.payment_status = 'paid' THEN vp.amount ELSE 0 END), 0) as vendor_payments_paid,
    COALESCE(SUM(CASE WHEN vp.payment_status = 'pending' THEN vp.amount ELSE 0 END), 0) as vendor_payments_pending,
    COALESCE(SUM(cp.amount), 0) as client_payments_total,
    COALESCE(SUM(CASE WHEN cp.payment_status = 'paid' THEN cp.amount ELSE 0 END), 0) as client_payments_paid,
    COALESCE(SUM(CASE WHEN cp.payment_status = 'pending' THEN cp.amount ELSE 0 END), 0) as client_payments_pending
FROM charters c
LEFT JOIN vendor_payments vp ON c.id = vp.charter_id
LEFT JOIN client_payments cp ON c.id = cp.charter_id
GROUP BY c.id;
