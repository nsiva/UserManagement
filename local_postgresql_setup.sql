-- ========================================================================
-- LOCAL POSTGRESQL SETUP SCRIPT FOR USER MANAGEMENT SYSTEM
-- ========================================================================
-- This script recreates the complete User Management database schema
-- in a local PostgreSQL instance using the 'aaa' schema.
--
-- Tables: aaa_profiles, aaa_roles, aaa_user_roles, aaa_clients, aaa_password_reset_tokens
-- Features: Complete schema with indexes, constraints, and sample data
-- ========================================================================

-- Step 1: Create the 'aaa' schema
CREATE SCHEMA IF NOT EXISTS aaa;

-- Step 2: Set search path to use the aaa schema
SET search_path TO aaa, public;

-- ========================================================================
-- TABLE CREATION
-- ========================================================================

-- User profiles table (main user data with authentication)
CREATE TABLE aaa.aaa_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    mfa_secret TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Roles definition table
CREATE TABLE aaa.aaa_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Role junction table (many-to-many relationship)
CREATE TABLE aaa.aaa_user_roles (
    user_id UUID NOT NULL REFERENCES aaa.aaa_profiles(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES aaa.aaa_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- API clients for client credentials flow
CREATE TABLE aaa.aaa_clients (
    client_id TEXT PRIMARY KEY,
    client_secret TEXT NOT NULL,
    name TEXT, -- Optional: human-readable client name
    scopes TEXT[], -- Optional: array of allowed scopes
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Password reset tokens table for forgot password functionality
CREATE TABLE aaa.aaa_password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES aaa.aaa_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================================================
-- INDEXES FOR PERFORMANCE
-- ========================================================================

-- Profiles table indexes
CREATE INDEX idx_aaa_profiles_email ON aaa.aaa_profiles(email);
CREATE INDEX idx_aaa_profiles_is_admin ON aaa.aaa_profiles(is_admin) WHERE is_admin = TRUE;
CREATE INDEX idx_aaa_profiles_created_at ON aaa.aaa_profiles(created_at);

-- User roles junction table indexes
CREATE INDEX idx_aaa_user_roles_user_id ON aaa.aaa_user_roles(user_id);
CREATE INDEX idx_aaa_user_roles_role_id ON aaa.aaa_user_roles(role_id);

-- Clients table indexes
CREATE INDEX idx_aaa_clients_active ON aaa.aaa_clients(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_aaa_clients_created_at ON aaa.aaa_clients(created_at);

-- Password reset tokens indexes
CREATE INDEX idx_password_reset_tokens_token ON aaa.aaa_password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON aaa.aaa_password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_expires_at ON aaa.aaa_password_reset_tokens(expires_at);
CREATE INDEX idx_password_reset_tokens_used ON aaa.aaa_password_reset_tokens(used) WHERE used = FALSE;

-- ========================================================================
-- CONSTRAINTS AND ADDITIONAL RULES
-- ========================================================================

-- Email validation constraint
ALTER TABLE aaa.aaa_profiles ADD CONSTRAINT check_email_format 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Role name constraints
ALTER TABLE aaa.aaa_roles ADD CONSTRAINT check_role_name_not_empty 
    CHECK (LENGTH(TRIM(name)) > 0);

-- Client constraints
ALTER TABLE aaa.aaa_clients ADD CONSTRAINT check_client_id_not_empty 
    CHECK (LENGTH(TRIM(client_id)) > 0);

ALTER TABLE aaa.aaa_clients ADD CONSTRAINT check_client_secret_not_empty 
    CHECK (LENGTH(TRIM(client_secret)) > 0);

-- Password reset token constraints
ALTER TABLE aaa.aaa_password_reset_tokens ADD CONSTRAINT check_expires_at_future 
    CHECK (expires_at > created_at);

-- ========================================================================
-- TRIGGER FOR AUTO-UPDATING updated_at FIELDS
-- ========================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION aaa.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_aaa_profiles_updated_at
    BEFORE UPDATE ON aaa.aaa_profiles
    FOR EACH ROW
    EXECUTE FUNCTION aaa.update_updated_at_column();

CREATE TRIGGER update_aaa_clients_updated_at
    BEFORE UPDATE ON aaa.aaa_clients
    FOR EACH ROW
    EXECUTE FUNCTION aaa.update_updated_at_column();

-- ========================================================================
-- DEFAULT ROLES DATA
-- ========================================================================

-- Insert default roles
INSERT INTO aaa.aaa_roles (name) VALUES
    ('admin'),
    ('manager'), 
    ('editor'),
    ('viewer'),
    ('user'),
    ('group_admin'),
    ('firm_admin'),
    ('super_user')
ON CONFLICT (name) DO NOTHING;

-- ========================================================================
-- DEFAULT API CLIENT FOR TESTING
-- ========================================================================

-- Insert default API client for development/testing
INSERT INTO aaa.aaa_clients (client_id, client_secret, name, scopes, is_active) VALUES
    ('my_test_client_id', 'my_test_client_secret', 'My Test Application', 
     ARRAY['read:users', 'manage:users'], TRUE)
ON CONFLICT (client_id) DO NOTHING;

-- ========================================================================
-- SAMPLE ADMIN USER (OPTIONAL - UNCOMMENT IF NEEDED)
-- ========================================================================

-- Uncomment the following lines to create a sample admin user
-- Password is "admin123" (bcrypt hashed)
-- 
-- INSERT INTO aaa.aaa_profiles (email, password_hash, first_name, last_name, is_admin) VALUES
--     ('admin@example.com', 
--      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWUGVCdOhJdx.kM2', 
--      'System', 'Administrator', TRUE)
-- ON CONFLICT (email) DO NOTHING;
-- 
-- -- Assign admin role to the admin user
-- INSERT INTO aaa.aaa_user_roles (user_id, role_id)
-- SELECT 
--     p.id, 
--     r.id
-- FROM aaa.aaa_profiles p, aaa.aaa_roles r
-- WHERE p.email = 'admin@example.com' AND r.name = 'admin'
-- ON CONFLICT (user_id, role_id) DO NOTHING;

-- ========================================================================
-- VERIFICATION QUERIES
-- ========================================================================

-- Check that all tables were created successfully
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'aaa'
ORDER BY tablename;

-- Check that all indexes were created
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_indexes 
WHERE schemaname = 'aaa'
ORDER BY tablename, indexname;

-- Check default data
SELECT 'Roles' as table_name, name as data FROM aaa.aaa_roles
UNION ALL
SELECT 'Clients' as table_name, client_id as data FROM aaa.aaa_clients;

-- ========================================================================
-- USAGE NOTES
-- ========================================================================

-- 1. This script creates all tables in the 'aaa' schema to keep them organized
-- 2. All tables have proper foreign key relationships with CASCADE delete
-- 3. Indexes are created for optimal query performance
-- 4. Triggers auto-update the updated_at timestamp fields
-- 5. Default roles and test client are inserted
-- 6. Email validation and other business rules are enforced via constraints
--
-- To use this in your application:
-- 1. Update your database connection to use schema 'aaa' 
-- 2. Or update table references to include schema: 'aaa.aaa_profiles'
-- 3. Export your current Supabase data and run INSERT statements after this script
--
-- Connection example:
-- DATABASE_URL="postgresql://user:password@localhost:5432/dbname?search_path=aaa"

COMMIT;