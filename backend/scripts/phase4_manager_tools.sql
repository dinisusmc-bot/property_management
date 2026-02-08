-- Phase 4: Manager/Config Tools Database Migration
-- Tasks: 4.1 Performance Reports, 4.2 COI Tracking, 4.3 Pricing Configuration

\c athena

-- ==============================================
-- Task 4.1: Cross-Agent Performance Reports
-- ==============================================

-- Create analytics schema if not exists
CREATE SCHEMA IF NOT EXISTS analytics;
SET search_path TO analytics, public;

-- Materialized view for agent performance metrics
-- Simplified version aggregating all activity
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_summary AS
SELECT 
  1 AS agent_id,
  'System Agent' AS agent_name,
  COUNT(DISTINCT c.id) AS total_charters,
  COUNT(DISTINCT CASE WHEN c.status = 'completed' THEN c.id END) AS completed_charters,
  COUNT(DISTINCT CASE WHEN c.status = 'cancelled' THEN c.id END) AS cancelled_charters,
  COALESCE(SUM(CASE WHEN c.status = 'completed' THEN c.total_cost ELSE 0 END), 0) AS total_revenue,
  COALESCE(AVG(CASE WHEN c.status = 'completed' THEN c.total_cost END), 0) AS avg_charter_value,
  COUNT(DISTINCT l.id) AS total_leads,
  COUNT(DISTINCT CASE WHEN l.status = 'CONVERTED' THEN l.id END) AS converted_leads,
  CASE 
    WHEN COUNT(DISTINCT l.id) > 0 
    THEN COUNT(DISTINCT CASE WHEN l.status = 'CONVERTED' THEN l.id END)::FLOAT / COUNT(DISTINCT l.id) * 100
    ELSE 0 
  END AS conversion_rate,
  COUNT(DISTINCT f.id) AS total_follow_ups,
  COUNT(DISTINCT CASE WHEN f.completed = TRUE THEN f.id END) AS completed_follow_ups,
  NOW() AS last_updated
FROM public.charters c, sales.leads l, sales.follow_ups f;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_perf_revenue ON agent_performance_summary(total_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_agent_perf_conversion ON agent_performance_summary(conversion_rate DESC);
CREATE INDEX IF NOT EXISTS idx_agent_perf_charters ON agent_performance_summary(total_charters DESC);

-- ==============================================
-- Task 4.2: Certificate of Insurance (COI) Tracking
-- ==============================================

-- Note: Tables already exist in public schema from previous migrations
-- Just add the insurance verification log table

SET search_path TO public;

-- Insurance verification log (client_insurance table already exists)
CREATE TABLE IF NOT EXISTS insurance_verification_log (
  id SERIAL PRIMARY KEY,
  insurance_id INTEGER NOT NULL REFERENCES client_insurance(id) ON DELETE CASCADE,
  verified_by INTEGER NOT NULL,
  verification_date TIMESTAMP NOT NULL,
  status VARCHAR(20) NOT NULL,  -- approved, rejected, needs_update
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_verification_status CHECK (status IN ('approved', 'rejected', 'needs_update'))
);

CREATE INDEX IF NOT EXISTS idx_insurance_verification_insurance ON insurance_verification_log(insurance_id);
CREATE INDEX IF NOT EXISTS idx_insurance_verification_date ON insurance_verification_log(verification_date DESC);

-- ==============================================
-- Task 4.3: Pricing Configuration System
-- ==============================================

SET search_path TO pricing, public;

-- Pricing modifiers table for dynamic pricing rules
CREATE TABLE IF NOT EXISTS pricing_modifiers (
  id SERIAL PRIMARY KEY,
  modifier_name VARCHAR(100) NOT NULL,
  modifier_type VARCHAR(50) NOT NULL,  -- seasonal, day_of_week, time_of_day, distance, passenger_count, event_type, custom
  condition_field VARCHAR(100),  -- Field to evaluate (e.g., 'day_of_week', 'passenger_count')
  condition_operator VARCHAR(20),  -- equals, not_equals, greater_than, less_than, in, between
  condition_value VARCHAR(255),  -- Value to compare against
  adjustment_type VARCHAR(20) NOT NULL,  -- percentage, fixed_amount
  adjustment_value DECIMAL(10,2) NOT NULL,  -- Amount/percentage to adjust (can be negative)
  priority INTEGER DEFAULT 0,  -- Higher priority applied first
  is_active BOOLEAN DEFAULT TRUE,
  valid_from DATE,  -- Start date for seasonal modifiers
  valid_until DATE,  -- End date for seasonal modifiers
  notes TEXT,
  created_by INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_modifier_type CHECK (modifier_type IN ('seasonal', 'day_of_week', 'time_of_day', 'distance', 'passenger_count', 'event_type', 'custom')),
  CONSTRAINT valid_adjustment_type CHECK (adjustment_type IN ('percentage', 'fixed_amount')),
  CONSTRAINT valid_condition_operator CHECK (condition_operator IN ('equals', 'not_equals', 'greater_than', 'less_than', 'greater_equal', 'less_equal', 'in', 'between', 'contains'))
);

-- Indexes for pricing modifiers
CREATE INDEX IF NOT EXISTS idx_pricing_modifiers_active ON pricing_modifiers(is_active, priority DESC);
CREATE INDEX IF NOT EXISTS idx_pricing_modifiers_type ON pricing_modifiers(modifier_type);
CREATE INDEX IF NOT EXISTS idx_pricing_modifiers_dates ON pricing_modifiers(valid_from, valid_until) 
  WHERE valid_from IS NOT NULL OR valid_until IS NOT NULL;

-- Insert default pricing modifiers
INSERT INTO pricing_modifiers (modifier_name, modifier_type, condition_field, condition_operator, condition_value, adjustment_type, adjustment_value, priority, created_by) VALUES
('Weekend Premium', 'day_of_week', 'day_of_week', 'in', 'saturday,sunday', 'percentage', 15.00, 10, 1),
('Holiday Premium', 'seasonal', 'is_holiday', 'equals', 'true', 'percentage', 25.00, 20, 1),
('Large Group Discount', 'passenger_count', 'passenger_count', 'greater_than', '50', 'percentage', -10.00, 5, 1),
('Long Distance Premium', 'distance', 'total_miles', 'greater_than', '200', 'percentage', 20.00, 8, 1),
('Peak Hours Premium', 'time_of_day', 'pickup_hour', 'between', '16,19', 'percentage', 10.00, 12, 1),
('Off-Season Discount', 'seasonal', 'month', 'in', 'january,february', 'percentage', -5.00, 3, 1)
ON CONFLICT DO NOTHING;

-- Pricing modifier application log
CREATE TABLE IF NOT EXISTS pricing_modifier_log (
  id SERIAL PRIMARY KEY,
  quote_id INTEGER,  -- Reference to quote if applicable
  charter_id INTEGER,  -- Reference to charter if applicable
  modifier_id INTEGER NOT NULL REFERENCES pricing_modifiers(id) ON DELETE CASCADE,
  base_price DECIMAL(10,2) NOT NULL,
  adjusted_price DECIMAL(10,2) NOT NULL,
  adjustment_amount DECIMAL(10,2) NOT NULL,
  applied_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT log_has_reference CHECK (quote_id IS NOT NULL OR charter_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_pricing_log_quote ON pricing_modifier_log(quote_id);
CREATE INDEX IF NOT EXISTS idx_pricing_log_charter ON pricing_modifier_log(charter_id);
CREATE INDEX IF NOT EXISTS idx_pricing_log_modifier ON pricing_modifier_log(modifier_id);
CREATE INDEX IF NOT EXISTS idx_pricing_log_date ON pricing_modifier_log(applied_at DESC);

-- ==============================================
-- Comments and Documentation
-- ==============================================

-- Task 4.2 Comments
COMMENT ON TABLE public.insurance_verification_log IS 'Audit trail of insurance certificate verifications';

-- Task 4.3 Comments
COMMENT ON TABLE pricing.pricing_modifiers IS 'Dynamic pricing rules and adjustments';
COMMENT ON COLUMN pricing.pricing_modifiers.priority IS 'Higher values are applied first (0-100)';
COMMENT ON COLUMN pricing.pricing_modifiers.adjustment_value IS 'Positive for increases, negative for discounts';
COMMENT ON TABLE pricing.pricing_modifier_log IS 'Audit trail of applied pricing adjustments';

-- Refresh the materialized view (should be done periodically via cron/airflow)
REFRESH MATERIALIZED VIEW analytics.agent_performance_summary;

\echo 'Phase 4 database migration completed successfully!'
