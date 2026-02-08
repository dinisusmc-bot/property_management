-- ============================================================================
-- Migration: Add Secure Quote Links
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Add secure shareable links for charter quotes (Task 8.4)
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS charter;

-- Create charter_share_links table (works with existing charters table)
CREATE TABLE IF NOT EXISTS charter.charter_share_links (
    id SERIAL PRIMARY KEY,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    
    -- Security
    token VARCHAR(500) NOT NULL UNIQUE,  -- JWT token
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,
    
    -- Optional password protection
    password_hash VARCHAR(255),  -- bcrypt hash if password protected
    
    CONSTRAINT valid_expiration CHECK (expires_at > created_at)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_charter_share_links_token ON charter.charter_share_links(token) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_charter_share_links_charter ON charter.charter_share_links(charter_id);
CREATE INDEX IF NOT EXISTS idx_charter_share_links_expires ON charter.charter_share_links(expires_at) WHERE is_active = TRUE;

-- Comments
COMMENT ON TABLE charter.charter_share_links IS 'Secure shareable links for charter quotes (Task 8.4)';
COMMENT ON COLUMN charter.charter_share_links.token IS 'JWT token for secure access';
COMMENT ON COLUMN charter.charter_share_links.expires_at IS 'Link expiration timestamp';
COMMENT ON COLUMN charter.charter_share_links.view_count IS 'Number of times link has been viewed';
COMMENT ON COLUMN charter.charter_share_links.password_hash IS 'Optional password hash for link protection';

-- Add tracking fields to charters table
ALTER TABLE charters 
  ADD COLUMN IF NOT EXISTS last_shared_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS share_count INTEGER DEFAULT 0;

COMMENT ON COLUMN charters.last_shared_at IS 'Last time charter was shared via link';
COMMENT ON COLUMN charters.share_count IS 'Total number of times charter has been shared';

-- ============================================================================
-- Rollback Script
-- ============================================================================
-- ALTER TABLE charters DROP COLUMN IF EXISTS last_shared_at;
-- ALTER TABLE charters DROP COLUMN IF EXISTS share_count;
-- DROP TABLE IF EXISTS charter.charter_share_links CASCADE;
