-- Phase 7 Task 7.4: Email Tracking & Analytics
-- Database migration for notifications service

\c athena
SET search_path TO public;

-- Create email tracking table for open and click tracking
CREATE TABLE IF NOT EXISTS email_tracking (
  id SERIAL PRIMARY KEY,
  email_log_id INTEGER REFERENCES email_logs(id) ON DELETE CASCADE,
  tracking_token VARCHAR(255) UNIQUE NOT NULL,
  opened BOOLEAN DEFAULT FALSE,
  opened_at TIMESTAMP,
  open_count INTEGER DEFAULT 0,
  clicked BOOLEAN DEFAULT FALSE,
  clicked_at TIMESTAMP,
  click_count INTEGER DEFAULT 0,
  user_agent TEXT,
  ip_address VARCHAR(45),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_email_tracking_token ON email_tracking(tracking_token);
CREATE INDEX IF NOT EXISTS idx_email_tracking_log ON email_tracking(email_log_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_opened ON email_tracking(opened, opened_at);
CREATE INDEX IF NOT EXISTS idx_email_tracking_clicked ON email_tracking(clicked, clicked_at);
CREATE INDEX IF NOT EXISTS idx_email_tracking_created ON email_tracking(created_at);

-- Verify email tracking table
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'email_tracking'
ORDER BY ordinal_position;

-- Show indexes
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'email_tracking'
ORDER BY indexname;
