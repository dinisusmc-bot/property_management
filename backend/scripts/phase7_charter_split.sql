-- Phase 7 Task 7.2: Charter Splitting
-- Database migration for charters service

\c athena
SET search_path TO public;

-- Add charter splitting support
ALTER TABLE charters ADD COLUMN IF NOT EXISTS parent_charter_id INTEGER REFERENCES charters(id);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS is_split_charter BOOLEAN DEFAULT FALSE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS split_sequence INTEGER;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_charters_parent ON charters(parent_charter_id) WHERE parent_charter_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_charters_split ON charters(is_split_charter) WHERE is_split_charter = TRUE;
CREATE INDEX IF NOT EXISTS idx_charters_split_seq ON charters(parent_charter_id, split_sequence);

-- Verify changes
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'charters' 
  AND column_name IN ('parent_charter_id', 'is_split_charter', 'split_sequence')
ORDER BY ordinal_position;

-- Show indexes
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'charters'
  AND (indexname LIKE '%split%' OR indexname LIKE '%parent%')
ORDER BY indexname;
