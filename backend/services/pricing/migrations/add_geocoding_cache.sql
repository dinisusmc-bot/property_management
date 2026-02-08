-- ============================================================================
-- Migration: Add Geocoding Cache
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Cache geocoding results to reduce API calls and improve performance
-- ============================================================================

-- Create pricing schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS pricing;

-- Create geocoding cache table
CREATE TABLE IF NOT EXISTS pricing.geocoding_cache (
    id SERIAL PRIMARY KEY,
    
    -- Input address
    address_text TEXT NOT NULL,
    address_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 hash for fast lookups
    
    -- Geocoded location
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    formatted_address TEXT,
    
    -- Address components
    street_number VARCHAR(50),
    street_name VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    
    -- Metadata
    confidence_score DECIMAL(3, 2),  -- 0.00 to 1.00
    geocoding_provider VARCHAR(50) DEFAULT 'tomtom',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1,
    
    -- Performance
    CONSTRAINT valid_coordinates CHECK (
        latitude BETWEEN -90 AND 90 AND
        longitude BETWEEN -180 AND 180
    )
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_geocoding_address_hash ON pricing.geocoding_cache(address_hash);
CREATE INDEX IF NOT EXISTS idx_geocoding_coordinates ON pricing.geocoding_cache(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_geocoding_last_used ON pricing.geocoding_cache(last_used_at);

-- Comments
COMMENT ON TABLE pricing.geocoding_cache IS 'Cache for geocoded addresses to reduce API calls';
COMMENT ON COLUMN pricing.geocoding_cache.address_hash IS 'SHA256 hash of normalized address for fast lookups';
COMMENT ON COLUMN pricing.geocoding_cache.confidence_score IS 'Confidence score from geocoding provider (0-1)';
COMMENT ON COLUMN pricing.geocoding_cache.use_count IS 'Number of times this cached result has been used';

-- Add geocoding fields to charter stops (if charter schema exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'charter') THEN
        ALTER TABLE charter.stops 
          ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
          ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8),
          ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP;

        CREATE INDEX IF NOT EXISTS idx_stops_coordinates 
          ON charter.stops(latitude, longitude) 
          WHERE latitude IS NOT NULL;

        COMMENT ON COLUMN charter.stops.latitude IS 'Latitude from TomTom geocoding';
        COMMENT ON COLUMN charter.stops.longitude IS 'Longitude from TomTom geocoding';
        COMMENT ON COLUMN charter.stops.geocoded_at IS 'Timestamp when address was geocoded';
    END IF;
END $$;

-- Function to calculate distance between two points (Haversine formula)
CREATE OR REPLACE FUNCTION pricing.calculate_distance(
    lat1 DECIMAL,
    lon1 DECIMAL,
    lat2 DECIMAL,
    lon2 DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    earth_radius DECIMAL := 3959.0;  -- miles
    dlat DECIMAL;
    dlon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := RADIANS(lat2 - lat1);
    dlon := RADIANS(lon2 - lon1);
    
    a := SIN(dlat/2) * SIN(dlat/2) + 
         COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * 
         SIN(dlon/2) * SIN(dlon/2);
    
    c := 2 * ATAN2(SQRT(a), SQRT(1-a));
    
    RETURN earth_radius * c;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION pricing.calculate_distance IS 'Calculate distance in miles between two lat/lon points using Haversine formula';

-- ============================================================================
-- Rollback Script (commented out)
-- ============================================================================
-- DROP FUNCTION IF EXISTS pricing.calculate_distance;
-- ALTER TABLE charter.stops DROP COLUMN IF EXISTS latitude;
-- ALTER TABLE charter.stops DROP COLUMN IF EXISTS longitude;
-- ALTER TABLE charter.stops DROP COLUMN IF EXISTS geocoded_at;
-- DROP TABLE IF EXISTS pricing.geocoding_cache CASCADE;
-- DROP SCHEMA IF EXISTS pricing CASCADE;
