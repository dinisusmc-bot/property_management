-- ============================================================================
-- Migration: Add E-Signature Support
-- Author: Development Team
-- Date: 2026-02-03
-- Description: Add custom e-signature capture and storage
-- ============================================================================

-- Create document schema if not exists
CREATE SCHEMA IF NOT EXISTS document;

-- Create signature_requests table
CREATE TABLE IF NOT EXISTS document.signature_requests (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    
    -- Signer info
    signer_name VARCHAR(200) NOT NULL,
    signer_email VARCHAR(255) NOT NULL,
    signer_role VARCHAR(100),  -- 'client', 'vendor', 'driver', etc.
    
    -- Request details
    request_message TEXT,
    expires_at TIMESTAMP,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, signed, expired, declined, cancelled
    
    -- Signature data
    signature_image TEXT,  -- Base64 encoded PNG
    signed_at TIMESTAMP,
    signer_ip_address VARCHAR(45),
    signer_user_agent TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    -- Reminders
    last_reminder_sent_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,
    
    CONSTRAINT valid_signature_status CHECK (status IN ('pending', 'signed', 'expired', 'declined', 'cancelled'))
);

-- Indexes for signature_requests
CREATE INDEX IF NOT EXISTS idx_signature_requests_document ON document.signature_requests(document_id);
CREATE INDEX IF NOT EXISTS idx_signature_requests_email ON document.signature_requests(signer_email);
CREATE INDEX IF NOT EXISTS idx_signature_requests_status ON document.signature_requests(status);
CREATE INDEX IF NOT EXISTS idx_signature_requests_expires ON document.signature_requests(expires_at) 
  WHERE status = 'pending';

-- Comments for signature_requests
COMMENT ON TABLE document.signature_requests IS 'E-signature requests for documents';
COMMENT ON COLUMN document.signature_requests.signature_image IS 'Base64 encoded PNG of signature (max 2MB)';
COMMENT ON COLUMN document.signature_requests.signer_ip_address IS 'IP address at time of signing for audit trail';
COMMENT ON COLUMN document.signature_requests.signer_user_agent IS 'Browser info at time of signing for audit trail';
COMMENT ON COLUMN document.signature_requests.reminder_count IS 'Number of reminder emails sent';

-- Create documents table if not exists (for testing)
CREATE TABLE IF NOT EXISTS document.documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    charter_id INTEGER,
    uploaded_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Add signature fields to documents table
ALTER TABLE document.documents 
  ADD COLUMN IF NOT EXISTS requires_signature BOOLEAN DEFAULT FALSE;
  
ALTER TABLE document.documents
  ADD COLUMN IF NOT EXISTS all_signed BOOLEAN DEFAULT FALSE;
  
ALTER TABLE document.documents
  ADD COLUMN IF NOT EXISTS signed_document_url TEXT;

-- Comments for document columns
COMMENT ON COLUMN document.documents.requires_signature IS 'Whether document requires signatures';
COMMENT ON COLUMN document.documents.all_signed IS 'All required signatures have been collected';
COMMENT ON COLUMN document.documents.signed_document_url IS 'URL to final signed PDF with all signatures';

-- Sample test data (optional - comment out for production)
-- INSERT INTO document.documents (filename, file_path, file_type, uploaded_by)
-- VALUES ('Charter Agreement.pdf', '/documents/charter_agreement.pdf', 'application/pdf', 1)
-- ON CONFLICT DO NOTHING;

COMMENT ON SCHEMA document IS 'Schema for document management and e-signatures';

-- ============================================================================
-- Rollback Script (DO NOT RUN - for reference only)
-- ============================================================================
-- ALTER TABLE document.documents DROP COLUMN IF EXISTS requires_signature;
-- ALTER TABLE document.documents DROP COLUMN IF EXISTS all_signed;
-- ALTER TABLE document.documents DROP COLUMN IF EXISTS signed_document_url;
-- DROP TABLE IF EXISTS document.signature_requests CASCADE;
