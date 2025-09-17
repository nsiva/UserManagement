-- =====================================================
-- User Management System - Complete Database Setup
-- Generated on: 2025-09-17 22:00:16 UTC
-- =====================================================

-- This script creates the complete database structure for the User Management System.
-- It includes all tables, indexes, constraints, functions, triggers, views, and sample data.

-- Prerequisites:
-- 1. PostgreSQL 12+ database
-- 2. UUID extension (usually available by default)
-- 3. Sufficient privileges to create tables, functions, and triggers

-- Usage:
-- psql -U your_username -d your_database_name -f complete_database_setup.sql

BEGIN;

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CORE TABLES
-- =====================================================

-- User profiles table (main user data with authentication)
CREATE TABLE IF NOT EXISTS aaa_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    mfa_secret TEXT,
    mfa_method TEXT CHECK (mfa_method IN ('totp', 'email')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Roles definition table
CREATE TABLE IF NOT EXISTS aaa_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Role junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS aaa_user_roles (
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES aaa_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- API clients for client credentials flow
CREATE TABLE IF NOT EXISTS aaa_clients (
    client_id TEXT PRIMARY KEY,
    client_secret TEXT NOT NULL,
    name TEXT,
    scopes TEXT[],
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ORGANIZATIONAL STRUCTURE TABLES
-- =====================================================

-- Organizations table for company/organization management
CREATE TABLE IF NOT EXISTS aaa_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    address_1 TEXT,
    address_2 TEXT,
    city_town TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,
    email TEXT,
    phone_number TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Business Units table for organizational structure management
CREATE TABLE IF NOT EXISTS aaa_business_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    code TEXT,
    organization_id UUID NOT NULL,
    parent_unit_id UUID,
    manager_id UUID,
    location TEXT,
    country TEXT,
    region TEXT,
    email TEXT,
    phone_number TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Foreign key constraints
    CONSTRAINT fk_business_unit_organization
        FOREIGN KEY (organization_id) REFERENCES aaa_organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_business_unit_parent
        FOREIGN KEY (parent_unit_id) REFERENCES aaa_business_units(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_manager
        FOREIGN KEY (manager_id) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_created_by
        FOREIGN KEY (created_by) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_updated_by
        FOREIGN KEY (updated_by) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    
    -- Business logic constraints
    CONSTRAINT chk_business_unit_not_self_parent
        CHECK (parent_unit_id != id),
    CONSTRAINT chk_business_unit_name_length
        CHECK (LENGTH(TRIM(name)) >= 2),
    CONSTRAINT chk_business_unit_code_format
        CHECK (code IS NULL OR (LENGTH(TRIM(code)) >= 2 AND code ~ '^[A-Z0-9_-]+$')),
    CONSTRAINT chk_business_unit_email_format
        CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- User-Business Unit junction table
CREATE TABLE IF NOT EXISTS aaa_user_business_units (
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    business_unit_id UUID NOT NULL REFERENCES aaa_business_units(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    PRIMARY KEY (user_id, business_unit_id)
);

-- =====================================================
-- SECURITY TABLES
-- =====================================================

-- Email OTP table for email-based MFA
CREATE TABLE IF NOT EXISTS aaa_email_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    otp TEXT NOT NULL,
    purpose TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS aaa_password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- DISABLE ROW LEVEL SECURITY
-- =====================================================

-- Disable RLS on all tables for direct API access
ALTER TABLE aaa_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_user_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_clients DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_organizations DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_business_units DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_user_business_units DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_email_otps DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_password_reset_tokens DISABLE ROW LEVEL SECURITY;

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Core table indexes
CREATE INDEX IF NOT EXISTS idx_aaa_profiles_email ON aaa_profiles(email);
CREATE INDEX IF NOT EXISTS idx_aaa_profiles_mfa_method ON aaa_profiles(mfa_method) WHERE mfa_method IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_aaa_user_roles_user_id ON aaa_user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_user_roles_role_id ON aaa_user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_aaa_clients_active ON aaa_clients(is_active) WHERE is_active = TRUE;

-- Organizational indexes
CREATE INDEX IF NOT EXISTS idx_aaa_organizations_company_name ON aaa_organizations(company_name);
CREATE INDEX IF NOT EXISTS idx_aaa_organizations_email ON aaa_organizations(email);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_organization_id ON aaa_business_units(organization_id);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_parent_unit_id ON aaa_business_units(parent_unit_id);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_manager_id ON aaa_business_units(manager_id);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_name ON aaa_business_units(name);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_code ON aaa_business_units(code) WHERE code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_is_active ON aaa_business_units(is_active);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_user_id ON aaa_user_business_units(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_business_unit_id ON aaa_user_business_units(business_unit_id);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_active ON aaa_user_business_units(is_active);

-- Security table indexes
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_user_id ON aaa_email_otps(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_expires_at ON aaa_email_otps(expires_at);
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_used ON aaa_email_otps(used);
CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_user_id ON aaa_password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_token ON aaa_password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_expires_at ON aaa_password_reset_tokens(expires_at);

-- Unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_business_units_unique_code_per_org
    ON aaa_business_units(organization_id, code)
    WHERE code IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_business_units_unique_name_per_parent
    ON aaa_business_units(organization_id, COALESCE(parent_unit_id, '00000000-0000-0000-0000-000000000000'), name);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_aaa_business_units_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at timestamp
DROP TRIGGER IF EXISTS trigger_update_aaa_business_units_updated_at ON aaa_business_units;
CREATE TRIGGER trigger_update_aaa_business_units_updated_at
    BEFORE UPDATE ON aaa_business_units
    FOR EACH ROW
    EXECUTE FUNCTION update_aaa_business_units_updated_at();

-- Function to prevent circular hierarchy
CREATE OR REPLACE FUNCTION check_business_unit_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check if parent_unit_id is being set
    IF NEW.parent_unit_id IS NOT NULL THEN
        -- Check if the new parent would create a circular reference
        WITH RECURSIVE hierarchy_check AS (
            -- Start with the proposed parent
            SELECT parent_unit_id, 1 as level
            FROM aaa_business_units
            WHERE id = NEW.parent_unit_id
            
            UNION ALL
            
            -- Follow the hierarchy up
            SELECT bu.parent_unit_id, hc.level + 1
            FROM aaa_business_units bu
            JOIN hierarchy_check hc ON bu.id = hc.parent_unit_id
            WHERE hc.level < 10 -- Prevent infinite recursion
        )
        SELECT 1 FROM hierarchy_check
        WHERE parent_unit_id = NEW.id
        LIMIT 1;
        
        -- If we found the current record in its own ancestry, it's circular
        IF FOUND THEN
            RAISE EXCEPTION 'Cannot create circular hierarchy: Business unit cannot be an ancestor of itself';
        END IF;
        
        -- Also check that parent belongs to same organization
        IF EXISTS (
            SELECT 1 FROM aaa_business_units
            WHERE id = NEW.parent_unit_id
            AND organization_id != NEW.organization_id
        ) THEN
            RAISE EXCEPTION 'Parent business unit must belong to the same organization';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce hierarchy constraints
DROP TRIGGER IF EXISTS trigger_check_business_unit_hierarchy ON aaa_business_units;
CREATE TRIGGER trigger_check_business_unit_hierarchy
    BEFORE INSERT OR UPDATE ON aaa_business_units
    FOR EACH ROW
    EXECUTE FUNCTION check_business_unit_hierarchy();

-- =====================================================
-- DATABASE VIEWS
-- =====================================================

-- User details view with organizational context
CREATE OR REPLACE VIEW vw_user_details AS
SELECT
    p.id,
    p.email,
    p.first_name,
    p.middle_name,
    p.last_name,
    p.is_admin,
    p.mfa_secret,
    p.mfa_method,
    p.created_at,
    p.updated_at,
    -- Role information
    ARRAY_AGG(DISTINCT r.name ORDER BY r.name) FILTER (WHERE r.name IS NOT NULL) as roles,
    -- Business unit information
    bu.id as business_unit_id,
    bu.name as business_unit_name,
    -- Organization information
    org.id as organization_id,
    org.company_name as organization_name
FROM aaa_profiles p
LEFT JOIN aaa_user_roles ur ON p.id = ur.user_id
LEFT JOIN aaa_roles r ON ur.role_id = r.id
LEFT JOIN aaa_user_business_units ubu ON p.id = ubu.user_id AND ubu.is_active = true
LEFT JOIN aaa_business_units bu ON ubu.business_unit_id = bu.id AND bu.is_active = true
LEFT JOIN aaa_organizations org ON bu.organization_id = org.id
GROUP BY p.id, p.email, p.first_name, p.middle_name, p.last_name, p.is_admin,
         p.mfa_secret, p.mfa_method, p.created_at, p.updated_at,
         bu.id, bu.name, org.id, org.company_name;

-- Business unit hierarchy view
CREATE OR REPLACE VIEW vw_business_unit_hierarchy AS
WITH RECURSIVE hierarchy AS (
    -- Root business units (no parent)
    SELECT
        bu.id,
        bu.name,
        bu.organization_id,
        org.company_name as organization_name,
        bu.parent_unit_id,
        NULL::TEXT as parent_name,
        bu.manager_id,
        CONCAT(p.first_name, ' ', p.last_name) as manager_name,
        bu.location,
        bu.email,
        bu.phone_number,
        bu.is_active,
        1 as level,
        ARRAY[bu.name] as path
    FROM aaa_business_units bu
    LEFT JOIN aaa_organizations org ON bu.organization_id = org.id
    LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
    WHERE bu.parent_unit_id IS NULL
    
    UNION ALL
    
    -- Child business units
    SELECT
        bu.id,
        bu.name,
        bu.organization_id,
        h.organization_name,
        bu.parent_unit_id,
        h.name as parent_name,
        bu.manager_id,
        CONCAT(p.first_name, ' ', p.last_name) as manager_name,
        bu.location,
        bu.email,
        bu.phone_number,
        bu.is_active,
        h.level + 1,
        h.path || bu.name
    FROM aaa_business_units bu
    JOIN hierarchy h ON bu.parent_unit_id = h.id
    LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
)
SELECT * FROM hierarchy;

-- =====================================================
-- SAMPLE DATA
-- =====================================================

-- Insert default roles
INSERT INTO aaa_roles (name) VALUES
    ('admin'),
    ('super_user'),
    ('firm_admin'),
    ('group_admin'),
    ('user')
ON CONFLICT (name) DO NOTHING;

-- Insert sample API client
INSERT INTO aaa_clients (client_id, client_secret, name, scopes) VALUES
    ('sample_client_id', 'sample_client_secret_change_in_production', 'Sample API Client', ARRAY['read:users', 'manage:users'])
ON CONFLICT (client_id) DO NOTHING;

-- Insert sample organizations
INSERT INTO aaa_organizations (id, company_name, address_1, city_town, state, zip, country, email, phone_number) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Tech Solutions Inc', '123 Innovation Drive', 'San Francisco', 'CA', '94105', 'USA', 'contact@techsolutions.com', '+1-555-0101'),
    ('22222222-2222-2222-2222-222222222222', 'Global Manufacturing Corp', '456 Industrial Blvd', 'Detroit', 'MI', '48201', 'USA', 'info@globalmanufacturing.com', '+1-555-0202')
ON CONFLICT (id) DO NOTHING;

-- Insert sample business units
INSERT INTO aaa_business_units (id, name, description, code, organization_id, location, email, phone_number) VALUES
    ('33333333-3333-3333-3333-333333333333', 'Engineering', 'Software Development Team', 'ENG', '11111111-1111-1111-1111-111111111111', 'San Francisco, CA', 'engineering@techsolutions.com', '+1-555-0301'),
    ('44444444-4444-4444-4444-444444444444', 'Sales', 'Sales and Marketing Department', 'SALES', '11111111-1111-1111-1111-111111111111', 'San Francisco, CA', 'sales@techsolutions.com', '+1-555-0302'),
    ('55555555-5555-5555-5555-555555555555', 'Production', 'Manufacturing Production Line', 'PROD', '22222222-2222-2222-2222-222222222222', 'Detroit, MI', 'production@globalmanufacturing.com', '+1-555-0303'),
    ('66666666-6666-6666-6666-666666666666', 'Quality Assurance', 'Quality Control Department', 'QA', '22222222-2222-2222-2222-222222222222', 'Detroit, MI', 'qa@globalmanufacturing.com', '+1-555-0304')
ON CONFLICT (id) DO NOTHING;

-- Insert sample admin user (password: admin123)
-- Note: In production, use proper password hashing and change default passwords
INSERT INTO aaa_profiles (id, email, password_hash, first_name, last_name, is_admin) VALUES
    ('77777777-7777-7777-7777-777777777777', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj7fKnKw82cO', 'System', 'Administrator', true)
ON CONFLICT (email) DO NOTHING;

-- Assign admin role to admin user
DO $$
DECLARE
    admin_role_id UUID;
    admin_user_id UUID := '77777777-7777-7777-7777-777777777777';
BEGIN
    SELECT id INTO admin_role_id FROM aaa_roles WHERE name = 'admin';
    
    IF admin_role_id IS NOT NULL THEN
        INSERT INTO aaa_user_roles (user_id, role_id) VALUES
            (admin_user_id, admin_role_id)
        ON CONFLICT (user_id, role_id) DO NOTHING;
    END IF;
END $$;

-- =====================================================
-- TABLE AND COLUMN COMMENTS
-- =====================================================

-- Core table comments
COMMENT ON TABLE aaa_profiles IS 'User profiles with authentication data';
COMMENT ON TABLE aaa_roles IS 'System roles for authorization';
COMMENT ON TABLE aaa_user_roles IS 'Many-to-many relationship between users and roles';
COMMENT ON TABLE aaa_clients IS 'API clients for machine-to-machine authentication';

-- Organizational table comments
COMMENT ON TABLE aaa_organizations IS 'Organizations/companies in the system';
COMMENT ON TABLE aaa_business_units IS 'Business units within organizations supporting hierarchical structure';
COMMENT ON TABLE aaa_user_business_units IS 'Assignment of users to business units';

-- Security table comments
COMMENT ON TABLE aaa_email_otps IS 'Email-based one-time passwords for MFA';
COMMENT ON TABLE aaa_password_reset_tokens IS 'Tokens for password reset functionality';

-- Key column comments
COMMENT ON COLUMN aaa_profiles.mfa_method IS 'MFA method: totp (authenticator app) or email';
COMMENT ON COLUMN aaa_business_units.parent_unit_id IS 'Parent business unit for hierarchical structure';
COMMENT ON COLUMN aaa_business_units.code IS 'Internal reference code (alphanumeric, unique per organization)';

-- =====================================================
-- VERIFICATION AND COMPLETION
-- =====================================================

-- Verify table creation
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE 'aaa_%';
    
    RAISE NOTICE 'Created % AAA tables', table_count;
    
    IF table_count < 9 THEN
        RAISE WARNING 'Expected at least 9 AAA tables, but found %', table_count;
    ELSE
        RAISE NOTICE 'Database setup completed successfully!';
    END IF;
END $$;

-- Display sample data counts
SELECT
    'Roles' as entity,
    COUNT(*) as count
FROM aaa_roles
UNION ALL
SELECT
    'Organizations' as entity,
    COUNT(*) as count
FROM aaa_organizations
UNION ALL
SELECT
    'Business Units' as entity,
    COUNT(*) as count
FROM aaa_business_units
UNION ALL
SELECT
    'Users' as entity,
    COUNT(*) as count
FROM aaa_profiles;

COMMIT;

-- =====================================================
-- SETUP COMPLETE
-- =====================================================

-- The database setup is now complete. You can:
-- 1. Create additional users via the API or admin interface
-- 2. Add more organizations and business units as needed
-- 3. Configure MFA for users
-- 4. Set up API clients for external integrations

-- Default admin credentials:
-- Email: admin@example.com
-- Password: admin123
-- IMPORTANT: Change the default password immediately in production!

-- Generated by User Management System Database Setup Generator
-- 2025-09-17 22:00:16 UTC
