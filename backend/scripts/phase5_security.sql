-- ============================================================================
-- PHASE 5: Portal Security & User Management - Database Migration
-- ============================================================================
-- Description: Enhanced authentication and security features
-- Tasks:
--   5.1: Multi-Factor Authentication (MFA)
--   5.2: Password Reset Flow
--   5.3: Account Impersonation
-- ============================================================================

\c athena

-- ============================================================================
-- TASK 5.1: Multi-Factor Authentication (MFA)
-- ============================================================================

-- MFA settings table
CREATE TABLE IF NOT EXISTS user_mfa (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_type VARCHAR(20) DEFAULT 'totp',  -- totp, sms, email
    mfa_secret VARCHAR(255),  -- Encrypted TOTP secret
    backup_codes TEXT[],  -- Array of encrypted backup codes
    phone_number VARCHAR(20),  -- For SMS MFA
    last_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_mfa_type CHECK (mfa_type IN ('totp', 'sms', 'email'))
);

CREATE INDEX idx_user_mfa_user ON user_mfa(user_id);
CREATE INDEX idx_user_mfa_enabled ON user_mfa(mfa_enabled) WHERE mfa_enabled = TRUE;

-- MFA verification attempts (audit trail)
CREATE TABLE IF NOT EXISTS mfa_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attempt_type VARCHAR(20) NOT NULL,  -- totp, sms, email, backup_code
    success BOOLEAN NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    attempted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mfa_attempts_user ON mfa_attempts(user_id, attempted_at DESC);

-- Update users table for MFA
ALTER TABLE users ADD COLUMN IF NOT EXISTS require_mfa BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enforced_at TIMESTAMP;

-- ============================================================================
-- TASK 5.2: Password Reset Flow
-- ============================================================================

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_password_reset_token ON password_reset_tokens(token_hash) WHERE NOT used;
CREATE INDEX idx_password_reset_user ON password_reset_tokens(user_id, created_at DESC);
CREATE INDEX idx_password_reset_expires ON password_reset_tokens(expires_at) WHERE NOT used;

-- Password history (prevent reuse)
CREATE TABLE IF NOT EXISTS password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_password_history_user ON password_history(user_id, created_at DESC);

-- Add password change tracking to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_password_change TIMESTAMP DEFAULT NOW();
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_required BOOLEAN DEFAULT FALSE;

-- ============================================================================
-- TASK 5.3: Account Impersonation
-- ============================================================================

-- Impersonation sessions table
CREATE TABLE IF NOT EXISTS impersonation_sessions (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    impersonated_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT no_self_impersonation CHECK (admin_user_id != impersonated_user_id)
);

CREATE INDEX idx_impersonation_admin ON impersonation_sessions(admin_user_id, started_at DESC);
CREATE INDEX idx_impersonation_target ON impersonation_sessions(impersonated_user_id, started_at DESC);
CREATE INDEX idx_impersonation_active ON impersonation_sessions(is_active) WHERE is_active = TRUE;

-- Audit log for impersonation actions
CREATE TABLE IF NOT EXISTS impersonation_audit_log (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES impersonation_sessions(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_impersonation_audit_session ON impersonation_audit_log(session_id, created_at DESC);
CREATE INDEX idx_impersonation_audit_action ON impersonation_audit_log(action, created_at DESC);

-- ============================================================================
-- Session Management Enhancements
-- ============================================================================

-- Enhanced sessions table (if not exists from Phase 1)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSONB,
    mfa_verified BOOLEAN DEFAULT FALSE,
    impersonation_session_id INTEGER REFERENCES impersonation_sessions(id),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id) WHERE NOT revoked;
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token) WHERE NOT revoked;
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at) WHERE NOT revoked;

-- ============================================================================
-- Security Audit Log (Enhanced)
-- ============================================================================

-- Comprehensive audit log
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- login, logout, mfa_setup, password_reset, etc.
    event_category VARCHAR(30) NOT NULL,  -- authentication, authorization, security
    severity VARCHAR(20) DEFAULT 'info',  -- info, warning, critical
    success BOOLEAN,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_audit_user ON security_audit_log(user_id, created_at DESC);
CREATE INDEX idx_security_audit_type ON security_audit_log(event_type, created_at DESC);
CREATE INDEX idx_security_audit_category ON security_audit_log(event_category, created_at DESC);
CREATE INDEX idx_security_audit_severity ON security_audit_log(severity, created_at DESC) WHERE severity IN ('warning', 'critical');

-- ============================================================================
-- Insert Sample Data / Configuration
-- ============================================================================

-- Set MFA requirement for admin users (optional)
-- UPDATE users SET require_mfa = TRUE WHERE role = 'admin';

-- ============================================================================
-- Database Functions for Security
-- ============================================================================

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired password reset tokens
    DELETE FROM password_reset_tokens
    WHERE expires_at < NOW() AND NOT used;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_user_id INTEGER,
    p_event_type VARCHAR,
    p_event_category VARCHAR,
    p_severity VARCHAR DEFAULT 'info',
    p_success BOOLEAN DEFAULT TRUE,
    p_details JSONB DEFAULT '{}',
    p_ip_address VARCHAR DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    new_id INTEGER;
BEGIN
    INSERT INTO security_audit_log (
        user_id, event_type, event_category, severity,
        success, details, ip_address, user_agent
    ) VALUES (
        p_user_id, p_event_type, p_event_category, p_severity,
        p_success, p_details, p_ip_address, p_user_agent
    ) RETURNING id INTO new_id;
    
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Verification & Grants
-- ============================================================================

-- Verify tables created
SELECT 
    schemaname, 
    tablename,
    hasindexes
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN (
    'user_mfa', 
    'mfa_attempts',
    'password_reset_tokens',
    'password_history',
    'impersonation_sessions',
    'impersonation_audit_log',
    'user_sessions',
    'security_audit_log'
)
ORDER BY tablename;

-- Grant permissions (adjust based on your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO athena_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA auth TO athena_app;

-- ============================================================================
-- Migration Complete
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Phase 5 Migration Complete!';
    RAISE NOTICE '   - MFA tables created';
    RAISE NOTICE '   - Password reset flow ready';
    RAISE NOTICE '   - Impersonation system configured';
    RAISE NOTICE '   - Security audit logging enhanced';
END $$;
