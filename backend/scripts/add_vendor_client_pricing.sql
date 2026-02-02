-- Add vendor cost and client charge fields to differentiate pricing
-- Vendor cost: what we pay the vendor
-- Client charge: what we charge the client

ALTER TABLE charters 
ADD COLUMN IF NOT EXISTS vendor_base_cost FLOAT,
ADD COLUMN IF NOT EXISTS vendor_mileage_cost FLOAT,
ADD COLUMN IF NOT EXISTS vendor_additional_fees FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS vendor_total_cost FLOAT,
ADD COLUMN IF NOT EXISTS client_base_charge FLOAT,
ADD COLUMN IF NOT EXISTS client_mileage_charge FLOAT,
ADD COLUMN IF NOT EXISTS client_additional_fees FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS client_total_charge FLOAT,
ADD COLUMN IF NOT EXISTS profit_margin FLOAT;

-- Update existing records to use the old total_cost as client_total_charge
UPDATE charters 
SET 
    client_base_charge = base_cost,
    client_mileage_charge = mileage_cost,
    client_additional_fees = additional_fees,
    client_total_charge = total_cost,
    vendor_base_cost = base_cost * 0.75,  -- Assume 25% margin initially
    vendor_mileage_cost = mileage_cost * 0.75,
    vendor_additional_fees = additional_fees * 0.75,
    vendor_total_cost = total_cost * 0.75,
    profit_margin = 0.25
WHERE vendor_base_cost IS NULL;

-- Add comment to explain the pricing structure
COMMENT ON COLUMN charters.vendor_base_cost IS 'Base cost we pay to the vendor';
COMMENT ON COLUMN charters.vendor_mileage_cost IS 'Mileage cost we pay to the vendor';
COMMENT ON COLUMN charters.vendor_additional_fees IS 'Additional fees we pay to the vendor';
COMMENT ON COLUMN charters.vendor_total_cost IS 'Total cost we pay to the vendor';
COMMENT ON COLUMN charters.client_base_charge IS 'Base charge to the client';
COMMENT ON COLUMN charters.client_mileage_charge IS 'Mileage charge to the client';
COMMENT ON COLUMN charters.client_additional_fees IS 'Additional fees charged to the client';
COMMENT ON COLUMN charters.client_total_charge IS 'Total charge to the client';
COMMENT ON COLUMN charters.profit_margin IS 'Profit margin as decimal (e.g., 0.25 = 25%)';
