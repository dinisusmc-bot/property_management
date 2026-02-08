-- Phase 3: Sales & Lead Management Database Migration
-- Date: February 2, 2026
-- Description: Follow-up tracking, lead scoring, and ownership transfer

\c athena
SET search_path TO sales, public;

-- =================================================================
-- Task 3.1: Follow-Up Tracking System
-- =================================================================

CREATE TABLE IF NOT EXISTS follow_ups (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  activity_id INTEGER REFERENCES activities(id),
  follow_up_type VARCHAR(50) NOT NULL,
  scheduled_date DATE NOT NULL,
  scheduled_time TIME,
  completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  completed_by INTEGER,
  outcome VARCHAR(50),
  notes TEXT,
  reminder_sent BOOLEAN DEFAULT FALSE,
  assigned_to INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_follow_up_type CHECK (follow_up_type IN ('call', 'email', 'meeting', 'quote', 'other')),
  CONSTRAINT valid_outcome CHECK (outcome IS NULL OR outcome IN ('successful', 'no_answer', 'voicemail', 'rescheduled', 'lost'))
);

CREATE INDEX idx_follow_ups_lead ON follow_ups(lead_id);
CREATE INDEX idx_follow_ups_assigned ON follow_ups(assigned_to);
CREATE INDEX idx_follow_ups_scheduled ON follow_ups(scheduled_date, completed) WHERE NOT completed;
CREATE INDEX idx_follow_ups_overdue ON follow_ups(scheduled_date) 
  WHERE NOT completed AND scheduled_date < CURRENT_DATE;

-- Add follow-up tracking to leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_follow_up_date TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_follow_up_date TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_up_count INTEGER DEFAULT 0;

COMMENT ON TABLE follow_ups IS 'Follow-up tasks for leads with scheduling and outcomes';
COMMENT ON COLUMN leads.last_follow_up_date IS 'Date of most recent completed follow-up';
COMMENT ON COLUMN leads.next_follow_up_date IS 'Date/time of next scheduled follow-up';
COMMENT ON COLUMN leads.follow_up_count IS 'Total number of completed follow-ups';

-- =================================================================
-- Task 3.2: Lead Scoring System
-- =================================================================

-- Add scoring to leads
ALTER TABLE leads ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS score_updated_at TIMESTAMP;

-- Scoring rules table
CREATE TABLE IF NOT EXISTS lead_scoring_rules (
  id SERIAL PRIMARY KEY,
  rule_name VARCHAR(100) NOT NULL,
  rule_type VARCHAR(50) NOT NULL,
  condition_field VARCHAR(100),
  condition_operator VARCHAR(20),
  condition_value VARCHAR(255),
  points INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_rule_type CHECK (rule_type IN ('attribute', 'activity', 'engagement')),
  CONSTRAINT valid_operator CHECK (condition_operator IN ('equals', 'not_equals', 'greater_than', 'less_than', 'contains', 'not_contains'))
);

-- Score change history
CREATE TABLE IF NOT EXISTS lead_score_history (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  old_score INTEGER NOT NULL,
  new_score INTEGER NOT NULL,
  points_changed INTEGER NOT NULL,
  reason VARCHAR(255),
  changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_score_history_lead ON lead_score_history(lead_id);

COMMENT ON TABLE lead_scoring_rules IS 'Rules for automatic lead score calculation';
COMMENT ON TABLE lead_score_history IS 'Audit trail of lead score changes';
COMMENT ON COLUMN leads.score IS 'Lead quality score (0-100)';

-- Insert default scoring rules
INSERT INTO lead_scoring_rules (rule_name, rule_type, condition_field, condition_operator, condition_value, points) VALUES
('Large Group Size', 'attribute', 'estimated_passengers', 'greater_than', '50', 20),
('Medium Group Size', 'attribute', 'estimated_passengers', 'greater_than', '25', 10),
('High Budget', 'attribute', 'estimated_value', 'greater_than', '5000', 25),
('Medium Budget', 'attribute', 'estimated_value', 'greater_than', '2000', 15),
('Responded to Email', 'engagement', 'email_response', 'equals', 'true', 10),
('Called Back', 'engagement', 'phone_response', 'equals', 'true', 15),
('Requested Quote', 'activity', 'quote_requested', 'equals', 'true', 20),
('Repeat Client', 'attribute', 'is_repeat', 'equals', 'true', 30)
ON CONFLICT DO NOTHING;

-- =================================================================
-- Task 3.3: Lead Ownership Transfer
-- =================================================================

CREATE TABLE IF NOT EXISTS lead_transfers (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  from_user_id INTEGER NOT NULL,
  to_user_id INTEGER NOT NULL,
  transfer_reason TEXT,
  transferred_by INTEGER NOT NULL,
  transferred_at TIMESTAMP DEFAULT NOW(),
  notes TEXT
);

CREATE INDEX idx_lead_transfers_lead ON lead_transfers(lead_id);
CREATE INDEX idx_lead_transfers_from ON lead_transfers(from_user_id);
CREATE INDEX idx_lead_transfers_to ON lead_transfers(to_user_id);

COMMENT ON TABLE lead_transfers IS 'History of lead ownership changes between users';

-- =================================================================
-- GRANT PERMISSIONS
-- =================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sales TO athena;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sales TO athena;

-- =================================================================
-- MIGRATION COMPLETE
-- =================================================================
-- Summary of changes:
-- - Added follow_ups table for task tracking
-- - Added 3 follow-up fields to leads table
-- - Added lead scoring system (score, rules, history)
-- - Inserted 8 default scoring rules
-- - Added lead_transfers table for ownership changes
-- =================================================================
