-- Phase 7 Task 7.3: SMS Preferences & Opt-Out
-- Database migration for notifications service

\c athena
SET search_path TO public;

-- Create SMS preferences table for opt-out management
CREATE TABLE IF NOT EXISTS sms_preferences (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(20) UNIQUE NOT NULL,
  opted_out BOOLEAN DEFAULT FALSE,
  opted_out_at TIMESTAMP,
  opt_out_reason VARCHAR(255),
  preferences JSONB DEFAULT '{}',  -- marketing, transactional, reminders
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sms_prefs_phone ON sms_preferences(phone_number);
CREATE INDEX IF NOT EXISTS idx_sms_prefs_opted_out ON sms_preferences(opted_out) WHERE opted_out = TRUE;

-- Add opt-out tracking to notifications table
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS recipient_opted_out BOOLEAN DEFAULT FALSE;

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_sms_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for timestamp updates
DROP TRIGGER IF EXISTS trigger_update_sms_prefs_timestamp ON sms_preferences;
CREATE TRIGGER trigger_update_sms_prefs_timestamp
    BEFORE UPDATE ON sms_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_sms_preferences_timestamp();

-- Verify SMS preferences table
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'sms_preferences'
ORDER BY ordinal_position;

-- Show indexes
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'sms_preferences'
ORDER BY indexname;
