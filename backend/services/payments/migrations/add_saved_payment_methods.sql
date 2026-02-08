-- ============================================================================
-- Migration: Add Saved Payment Methods Support
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Add stripe_customer_id to clients and create payment methods table
-- ============================================================================

-- Add stripe_customer_id to clients table
ALTER TABLE clients 
  ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100) UNIQUE;

COMMENT ON COLUMN clients.stripe_customer_id IS 'Stripe Customer ID for saved payment methods';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_clients_stripe_customer 
  ON clients(stripe_customer_id) 
  WHERE stripe_customer_id IS NOT NULL;

-- Create saved_payment_methods table
CREATE TABLE IF NOT EXISTS saved_payment_methods (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    stripe_payment_method_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Card details (for display)
    card_brand VARCHAR(50),
    card_last4 VARCHAR(4),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    nickname VARCHAR(100),  -- e.g., "Work Visa", "Personal Card"
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    last_used_at TIMESTAMP,
    
    -- Ensure only one default per client
    CONSTRAINT unique_default_per_client UNIQUE NULLS NOT DISTINCT (client_id, is_default)
        DEFERRABLE INITIALLY DEFERRED
);

-- Indexes
CREATE INDEX idx_payment_methods_client ON saved_payment_methods(client_id);
CREATE INDEX idx_payment_methods_stripe ON saved_payment_methods(stripe_payment_method_id);
CREATE INDEX idx_payment_methods_default ON saved_payment_methods(client_id, is_default) 
  WHERE is_default = TRUE;

-- Comments
COMMENT ON TABLE saved_payment_methods IS 'Saved payment methods linked to Stripe Customer';
COMMENT ON COLUMN saved_payment_methods.is_default IS 'Default payment method for client (only one per client)';
COMMENT ON COLUMN saved_payment_methods.last_used_at IS 'Tracks when method was last charged';

-- ============================================================================
-- Rollback Script
-- ============================================================================
-- DROP TABLE IF EXISTS saved_payment_methods CASCADE;
-- ALTER TABLE clients DROP COLUMN IF EXISTS stripe_customer_id;
