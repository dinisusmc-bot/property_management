-- Fix confidence_score precision in geocoding_cache table
-- The TomTom API returns confidence scores that can exceed 10, so DECIMAL(3,2) is too small
-- Changing to DECIMAL(10,4) to handle values like 12.4741983414

ALTER TABLE pricing.geocoding_cache 
    ALTER COLUMN confidence_score TYPE DECIMAL(10,4);

-- Add comment to document the field
COMMENT ON COLUMN pricing.geocoding_cache.confidence_score IS 
    'Geocoding confidence score from provider (0-100 scale, higher is better)';
