-- Alter Phase 5 tables for simplified email-based MFA
-- Run this to update existing Phase 5 tables

\c athena

-- Update user_mfa table for email-based 6-digit codes
ALTER TABLE user_mfa 
  DROP COLUMN IF EXISTS mfa_secret,
  DROP COLUMN IF EXISTS phone_number,
  ADD COLUMN IF NOT EXISTS current_code VARCHAR(6),
  ADD COLUMN IF NOT EXISTS code_expires_at TIMESTAMP,
  ALTER COLUMN mfa_type SET DEFAULT 'email';

-- Drop the old check constraint and add new one
ALTER TABLE user_mfa DROP CONSTRAINT IF EXISTS valid_mfa_type;
-- No new constraint needed - email is the only type

-- Update existing records to use email type
UPDATE user_mfa SET mfa_type = 'email' WHERE mfa_type IN ('totp', 'sms');

\echo '✅ Phase 5 tables updated for email-based MFA'
