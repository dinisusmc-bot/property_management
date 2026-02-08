-- Migration: Add Charter Enhancement Fields
-- Date: 2026-02-02
-- Phase 2: Multi-stop, cloning, and recurring charters

BEGIN;

-- Add new columns to charters table
ALTER TABLE charters ADD COLUMN IF NOT EXISTS trip_type VARCHAR(50);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS requires_second_driver BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS vehicle_count INT DEFAULT 1;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS parent_charter_id INT REFERENCES charters(id);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS quote_secure_token VARCHAR(255) UNIQUE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS revision_number INT DEFAULT 1;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS recurrence_rule TEXT;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS instance_number INT;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS series_total INT;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS is_series_master BOOLEAN DEFAULT false;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS cloned_from_charter_id INT REFERENCES charters(id);

-- Add new columns to stops table
ALTER TABLE stops ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,7);
ALTER TABLE stops ADD COLUMN IF NOT EXISTS longitude DECIMAL(10,7);
ALTER TABLE stops ADD COLUMN IF NOT EXISTS geocoded_address TEXT;
ALTER TABLE stops ADD COLUMN IF NOT EXISTS stop_type VARCHAR(20) DEFAULT 'waypoint';
ALTER TABLE stops ADD COLUMN IF NOT EXISTS estimated_arrival TIMESTAMP WITH TIME ZONE;
ALTER TABLE stops ADD COLUMN IF NOT EXISTS estimated_departure TIMESTAMP WITH TIME ZONE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_charters_parent ON charters(parent_charter_id);
CREATE INDEX IF NOT EXISTS idx_charters_secure_token ON charters(quote_secure_token);
CREATE INDEX IF NOT EXISTS idx_charters_cloned_from ON charters(cloned_from_charter_id);
CREATE INDEX IF NOT EXISTS idx_charters_series_master ON charters(is_series_master) WHERE is_series_master = true;

-- Add comments for documentation
COMMENT ON COLUMN charters.trip_type IS 'Type of trip: one-way, round-trip, multi-day, etc.';
COMMENT ON COLUMN charters.requires_second_driver IS 'Whether a second driver is required for this charter';
COMMENT ON COLUMN charters.vehicle_count IS 'Number of vehicles needed for this charter';
COMMENT ON COLUMN charters.parent_charter_id IS 'Reference to parent charter for revisions';
COMMENT ON COLUMN charters.quote_secure_token IS 'Secure token for quote landing page access';
COMMENT ON COLUMN charters.revision_number IS 'Version number for charter revisions';
COMMENT ON COLUMN charters.recurrence_rule IS 'iCal-style recurrence rule for recurring charters';
COMMENT ON COLUMN charters.instance_number IS 'Instance number in recurring series (1, 2, 3...)';
COMMENT ON COLUMN charters.series_total IS 'Total number of instances in recurring series';
COMMENT ON COLUMN charters.is_series_master IS 'Whether this is the master record for a recurring series';
COMMENT ON COLUMN charters.cloned_from_charter_id IS 'Original charter ID if this was cloned';

COMMENT ON COLUMN stops.latitude IS 'GPS latitude coordinate';
COMMENT ON COLUMN stops.longitude IS 'GPS longitude coordinate';
COMMENT ON COLUMN stops.geocoded_address IS 'Standardized address from geocoding service';
COMMENT ON COLUMN stops.stop_type IS 'Type: pickup, dropoff, waypoint';
COMMENT ON COLUMN stops.estimated_arrival IS 'Estimated arrival time at this stop';
COMMENT ON COLUMN stops.estimated_departure IS 'Estimated departure time from this stop';

COMMIT;
