-- Update charter workflow and add document tracking fields
-- New workflow: quote -> approved -> booked -> confirmed -> in_progress -> completed

-- Add workflow tracking fields
ALTER TABLE charters ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS approval_amount DECIMAL(10,2);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS approval_document_id VARCHAR(255);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS approved_by INTEGER;

ALTER TABLE charters ADD COLUMN IF NOT EXISTS booking_status VARCHAR(50);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS booking_cost DECIMAL(10,2);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS booking_document_id VARCHAR(255);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS booked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS booked_by INTEGER;

ALTER TABLE charters ADD COLUMN IF NOT EXISTS confirmation_status VARCHAR(50);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS confirmation_document_id VARCHAR(255);
ALTER TABLE charters ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE charters ADD COLUMN IF NOT EXISTS confirmed_by INTEGER;

-- Create charter_documents table for tracking documents in MongoDB
CREATE TABLE IF NOT EXISTS charter_documents (
    id SERIAL PRIMARY KEY,
    charter_id INTEGER NOT NULL REFERENCES charters(id) ON DELETE CASCADE,
    
    -- Document details
    document_type VARCHAR(50) NOT NULL, -- approval, booking, confirmation, contract, invoice, receipt, other
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- MongoDB reference
    mongodb_id VARCHAR(255) NOT NULL UNIQUE, -- MongoDB ObjectId
    
    -- Metadata
    description TEXT,
    uploaded_by INTEGER, -- user_id
    
    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_document_type CHECK (document_type IN (
        'approval', 'booking', 'confirmation', 'contract', 
        'invoice', 'receipt', 'insurance', 'other'
    ))
);

CREATE INDEX IF NOT EXISTS idx_charter_documents_charter_id ON charter_documents(charter_id);
CREATE INDEX IF NOT EXISTS idx_charter_documents_type ON charter_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_charter_documents_mongodb_id ON charter_documents(mongodb_id);

COMMENT ON TABLE charter_documents IS 'Tracks documents stored in MongoDB for charters';
COMMENT ON COLUMN charter_documents.mongodb_id IS 'Reference to document in MongoDB GridFS';
COMMENT ON COLUMN charter_documents.document_type IS 'Type of document: approval, booking, confirmation, contract, invoice, receipt, insurance, other';
