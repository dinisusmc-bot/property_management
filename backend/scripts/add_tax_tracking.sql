-- Migration: Add tax tracking fields to charters table
-- Purpose: Support tax calculation, reporting, and business expense tracking
-- Date: 2025-12-08

-- Add tax tracking columns
ALTER TABLE charters
ADD COLUMN tax_rate FLOAT,
ADD COLUMN tax_amount FLOAT,
ADD COLUMN tax_status VARCHAR(50),
ADD COLUMN tax_category VARCHAR(100);

-- Add comments for clarity
COMMENT ON COLUMN charters.tax_rate IS 'Tax rate as decimal (e.g., 0.08 = 8%)';
COMMENT ON COLUMN charters.tax_amount IS 'Calculated tax amount';
COMMENT ON COLUMN charters.tax_status IS 'Tax filing status: pending, filed, paid';
COMMENT ON COLUMN charters.tax_category IS 'Tax category for reporting: business_travel, charter_service, other';

-- Create index for tax reporting queries
CREATE INDEX idx_charters_tax_status ON charters(tax_status);
CREATE INDEX idx_charters_tax_category ON charters(tax_category);

-- Future enhancement: Create expenses table for non-charter business expenses
-- This will allow tracking of:
-- - Office expenses
-- - Vehicle maintenance
-- - Insurance
-- - Fuel costs
-- - Marketing expenses
-- - Administrative costs
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    expense_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,  -- fuel, maintenance, insurance, office, marketing, administrative, other
    subcategory VARCHAR(100),
    amount FLOAT NOT NULL,
    vendor_name VARCHAR(255),
    payment_method VARCHAR(50),  -- check, credit_card, cash, ach, wire_transfer, other
    payment_status VARCHAR(50) DEFAULT 'pending',  -- pending, paid, reimbursed
    reference_number VARCHAR(100),
    description TEXT,
    receipt_url VARCHAR(500),  -- Link to receipt/invoice document
    tax_deductible BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER  -- FK to auth service user
);

-- Create indexes for expense tracking
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_payment_status ON expenses(payment_status);
CREATE INDEX idx_expenses_tax_deductible ON expenses(tax_deductible);

-- Add comments to expenses table
COMMENT ON TABLE expenses IS 'Track non-charter business expenses for accounting and tax purposes';
COMMENT ON COLUMN expenses.category IS 'Main expense category for reporting and tax purposes';
COMMENT ON COLUMN expenses.tax_deductible IS 'Whether this expense is tax deductible';

-- Create view for tax reporting summary
CREATE OR REPLACE VIEW tax_summary AS
SELECT 
    EXTRACT(YEAR FROM c.trip_date) AS tax_year,
    EXTRACT(QUARTER FROM c.trip_date) AS tax_quarter,
    EXTRACT(MONTH FROM c.trip_date) AS tax_month,
    COUNT(*) AS charter_count,
    
    -- Revenue (Client Charges)
    SUM(COALESCE(c.client_total_charge, c.total_cost)) AS gross_revenue,
    SUM(COALESCE(c.tax_amount, 0)) AS total_tax_collected,
    
    -- Costs (Vendor Payments)
    SUM(COALESCE(c.vendor_total_cost, c.total_cost * 0.75)) AS total_vendor_costs,
    
    -- Profit
    SUM(COALESCE(c.client_total_charge, c.total_cost) - COALESCE(c.vendor_total_cost, c.total_cost * 0.75)) AS gross_profit,
    
    -- Tax status breakdown
    COUNT(*) FILTER (WHERE c.tax_status = 'pending') AS tax_pending_count,
    COUNT(*) FILTER (WHERE c.tax_status = 'filed') AS tax_filed_count,
    COUNT(*) FILTER (WHERE c.tax_status = 'paid') AS tax_paid_count
    
FROM charters c
WHERE c.status = 'completed'
GROUP BY EXTRACT(YEAR FROM c.trip_date), EXTRACT(QUARTER FROM c.trip_date), EXTRACT(MONTH FROM c.trip_date)
ORDER BY tax_year DESC, tax_quarter DESC, tax_month DESC;

COMMENT ON VIEW tax_summary IS 'Aggregated tax reporting data by year, quarter, and month';

-- Create view for expense summary
CREATE OR REPLACE VIEW expense_summary AS
SELECT 
    EXTRACT(YEAR FROM e.expense_date) AS expense_year,
    EXTRACT(QUARTER FROM e.expense_date) AS expense_quarter,
    EXTRACT(MONTH FROM e.expense_date) AS expense_month,
    e.category,
    COUNT(*) AS expense_count,
    SUM(e.amount) AS total_amount,
    SUM(CASE WHEN e.tax_deductible THEN e.amount ELSE 0 END) AS tax_deductible_amount,
    SUM(CASE WHEN e.payment_status = 'paid' THEN e.amount ELSE 0 END) AS paid_amount,
    SUM(CASE WHEN e.payment_status = 'pending' THEN e.amount ELSE 0 END) AS pending_amount
FROM expenses e
GROUP BY EXTRACT(YEAR FROM e.expense_date), EXTRACT(QUARTER FROM e.expense_date), EXTRACT(MONTH FROM e.expense_date), e.category
ORDER BY expense_year DESC, expense_quarter DESC, expense_month DESC, e.category;

COMMENT ON VIEW expense_summary IS 'Aggregated expense data by year, quarter, month, and category';

-- Create comprehensive financial summary view
CREATE OR REPLACE VIEW financial_summary AS
SELECT 
    EXTRACT(YEAR FROM date_range) AS fiscal_year,
    EXTRACT(QUARTER FROM date_range) AS fiscal_quarter,
    EXTRACT(MONTH FROM date_range) AS fiscal_month,
    
    -- Revenue from charters
    COALESCE(revenue.gross_revenue, 0) AS charter_revenue,
    COALESCE(revenue.total_tax_collected, 0) AS tax_collected,
    
    -- Costs
    COALESCE(revenue.total_vendor_costs, 0) AS vendor_costs,
    COALESCE(expenses.total_expenses, 0) AS business_expenses,
    COALESCE(revenue.total_vendor_costs, 0) + COALESCE(expenses.total_expenses, 0) AS total_costs,
    
    -- Profit
    COALESCE(revenue.gross_revenue, 0) - COALESCE(revenue.total_vendor_costs, 0) - COALESCE(expenses.total_expenses, 0) AS net_profit,
    
    -- Payment tracking
    COALESCE(client_payments.paid, 0) AS client_payments_received,
    COALESCE(vendor_payments.paid, 0) AS vendor_payments_made,
    COALESCE(expenses.paid_expenses, 0) AS expenses_paid,
    
    -- Outstanding balances
    COALESCE(revenue.gross_revenue, 0) - COALESCE(client_payments.paid, 0) AS outstanding_receivables,
    COALESCE(revenue.total_vendor_costs, 0) - COALESCE(vendor_payments.paid, 0) AS outstanding_payables
    
FROM generate_series(
    DATE_TRUNC('month', (SELECT MIN(trip_date) FROM charters)),
    DATE_TRUNC('month', CURRENT_DATE),
    INTERVAL '1 month'
) AS date_range

LEFT JOIN (
    SELECT 
        DATE_TRUNC('month', c.trip_date) AS month,
        SUM(COALESCE(c.client_total_charge, c.total_cost)) AS gross_revenue,
        SUM(COALESCE(c.tax_amount, 0)) AS total_tax_collected,
        SUM(COALESCE(c.vendor_total_cost, c.total_cost * 0.75)) AS total_vendor_costs
    FROM charters c
    WHERE c.status = 'completed'
    GROUP BY DATE_TRUNC('month', c.trip_date)
) revenue ON DATE_TRUNC('month', date_range) = revenue.month

LEFT JOIN (
    SELECT 
        DATE_TRUNC('month', e.expense_date) AS month,
        SUM(e.amount) AS total_expenses,
        SUM(CASE WHEN e.payment_status = 'paid' THEN e.amount ELSE 0 END) AS paid_expenses
    FROM expenses e
    GROUP BY DATE_TRUNC('month', e.expense_date)
) expenses ON DATE_TRUNC('month', date_range) = expenses.month

LEFT JOIN (
    SELECT 
        DATE_TRUNC('month', c.trip_date) AS month,
        SUM(cp.amount) FILTER (WHERE cp.payment_status = 'paid') AS paid
    FROM client_payments cp
    JOIN charters c ON cp.charter_id = c.id
    GROUP BY DATE_TRUNC('month', c.trip_date)
) client_payments ON DATE_TRUNC('month', date_range) = client_payments.month

LEFT JOIN (
    SELECT 
        DATE_TRUNC('month', c.trip_date) AS month,
        SUM(vp.amount) FILTER (WHERE vp.payment_status = 'paid') AS paid
    FROM vendor_payments vp
    JOIN charters c ON vp.charter_id = c.id
    GROUP BY DATE_TRUNC('month', c.trip_date)
) vendor_payments ON DATE_TRUNC('month', date_range) = vendor_payments.month

ORDER BY fiscal_year DESC, fiscal_quarter DESC, fiscal_month DESC;

COMMENT ON VIEW financial_summary IS 'Comprehensive financial summary including revenue, expenses, and profit by month';

-- Sample data for testing (commented out - uncomment to test)
-- INSERT INTO expenses (expense_date, category, subcategory, amount, vendor_name, payment_method, payment_status, description, tax_deductible)
-- VALUES 
-- ('2025-12-01', 'fuel', 'diesel', 250.00, 'Shell Gas Station', 'credit_card', 'paid', 'Fuel for charter trips', TRUE),
-- ('2025-12-01', 'maintenance', 'oil_change', 150.00, 'Quick Lube', 'credit_card', 'paid', 'Regular vehicle maintenance', TRUE),
-- ('2025-12-01', 'office', 'supplies', 75.50, 'Office Depot', 'credit_card', 'paid', 'Office supplies and printer paper', TRUE),
-- ('2025-12-05', 'insurance', 'vehicle', 500.00, 'State Farm', 'ach', 'paid', 'Monthly vehicle insurance', TRUE),
-- ('2025-12-07', 'marketing', 'advertising', 200.00, 'Google Ads', 'credit_card', 'pending', 'Online advertising campaign', TRUE);
