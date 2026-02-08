-- Phase 7 Task 7.1: Enhanced Recovery Workflow
-- Database migration for dispatch service

\c athena
SET search_path TO public;

-- Add recovery workflow enhancements to recoveries table
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS recovery_priority VARCHAR(20) DEFAULT 'normal';
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS estimated_recovery_time TIMESTAMP;
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS recovery_attempts INTEGER DEFAULT 0;
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS last_contact_at TIMESTAMP;
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS last_contact_method VARCHAR(50);
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS escalated BOOLEAN DEFAULT FALSE;
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS escalated_to INTEGER REFERENCES users(id);
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP;
ALTER TABLE recoveries ADD COLUMN IF NOT EXISTS recovery_notes TEXT;

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_recoveries_priority ON recoveries(recovery_priority);
CREATE INDEX IF NOT EXISTS idx_recoveries_status ON recoveries(status);
CREATE INDEX IF NOT EXISTS idx_recoveries_escalated ON recoveries(escalated) WHERE escalated = TRUE;
CREATE INDEX IF NOT EXISTS idx_recoveries_attempts ON recoveries(recovery_attempts);

-- Add constraint for valid priority values
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'valid_recovery_priority'
    ) THEN
        ALTER TABLE recoveries 
        ADD CONSTRAINT valid_recovery_priority 
        CHECK (recovery_priority IN ('low', 'normal', 'high', 'critical'));
    END IF;
END $$;

-- Create function to auto-escalate after 3 attempts
CREATE OR REPLACE FUNCTION auto_escalate_recovery()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.recovery_attempts >= 3 AND NEW.escalated = FALSE THEN
        NEW.recovery_priority := 'high';
        -- In production, this would trigger a notification to managers
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-escalation
DROP TRIGGER IF EXISTS trigger_auto_escalate ON recoveries;
CREATE TRIGGER trigger_auto_escalate
    BEFORE UPDATE ON recoveries
    FOR EACH ROW
    WHEN (OLD.recovery_attempts < NEW.recovery_attempts)
    EXECUTE FUNCTION auto_escalate_recovery();

-- Verify changes
SELECT 
    column_name, 
    data_type, 
    column_default 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'recoveries' 
  AND column_name IN (
    'recovery_priority', 
    'estimated_recovery_time', 
    'recovery_attempts', 
    'last_contact_at', 
    'last_contact_method', 
    'escalated', 
    'escalated_to', 
    'escalated_at', 
    'recovery_notes'
  )
ORDER BY ordinal_position;
