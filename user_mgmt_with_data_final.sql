-- =====================================================
-- User Management System - Complete Database Setup
-- Generated on: 2025-09-18 02:41:46 UTC
-- Target schema: user_mgmt
-- =====================================================

-- This script creates the complete database structure for the User Management System.
-- It includes all tables, indexes, constraints, functions, triggers, views, and sample data.

-- Prerequisites:
-- 1. PostgreSQL 12+ database
-- 2. UUID extension (usually available by default)
-- 3. Sufficient privileges to create schema, tables, functions, and triggers

-- Usage:
-- psql -U your_username -d your_database_name -f complete_database_setup.sql

BEGIN;

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS user_mgmt;

-- Set search path to target schema
SET search_path TO user_mgmt, public;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- User profiles table (main user data with authentication)
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_profiles (
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
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Role junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_user_roles (
    user_id UUID NOT NULL REFERENCES user_mgmt.aaa_profiles(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES user_mgmt.aaa_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- API clients for client credentials flow
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_clients (
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
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_organizations (
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
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_business_units (
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
        FOREIGN KEY (organization_id) REFERENCES user_mgmt.aaa_organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_business_unit_parent
        FOREIGN KEY (parent_unit_id) REFERENCES user_mgmt.aaa_business_units(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_manager
        FOREIGN KEY (manager_id) REFERENCES user_mgmt.aaa_profiles(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_created_by
        FOREIGN KEY (created_by) REFERENCES user_mgmt.aaa_profiles(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_updated_by
        FOREIGN KEY (updated_by) REFERENCES user_mgmt.aaa_profiles(id) ON DELETE SET NULL,
    
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
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_user_business_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_mgmt.aaa_profiles(id) ON DELETE CASCADE,
    business_unit_id UUID NOT NULL REFERENCES user_mgmt.aaa_business_units(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES user_mgmt.aaa_profiles(id),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, business_unit_id)
);

-- =====================================================
-- SECURITY TABLES
-- =====================================================

-- Email OTP table for email-based MFA
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_email_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_mgmt.aaa_profiles(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    otp TEXT NOT NULL,
    purpose TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS user_mgmt.aaa_password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_mgmt.aaa_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- DISABLE ROW LEVEL SECURITY
-- =====================================================

-- Disable RLS on all tables for direct API access
ALTER TABLE user_mgmt.aaa_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_user_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_clients DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_organizations DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_business_units DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_user_business_units DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_email_otps DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mgmt.aaa_password_reset_tokens DISABLE ROW LEVEL SECURITY;

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Core table indexes
CREATE INDEX IF NOT EXISTS idx_aaa_profiles_email ON user_mgmt.aaa_profiles(email);
CREATE INDEX IF NOT EXISTS idx_aaa_profiles_mfa_method ON user_mgmt.aaa_profiles(mfa_method) WHERE mfa_method IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_aaa_user_roles_user_id ON user_mgmt.aaa_user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_user_roles_role_id ON user_mgmt.aaa_user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_aaa_clients_active ON user_mgmt.aaa_clients(is_active) WHERE is_active = TRUE;

-- Organizational indexes
CREATE INDEX IF NOT EXISTS idx_aaa_organizations_company_name ON user_mgmt.aaa_organizations(company_name);
CREATE INDEX IF NOT EXISTS idx_aaa_organizations_email ON user_mgmt.aaa_organizations(email);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_organization_id ON user_mgmt.aaa_business_units(organization_id);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_parent_unit_id ON user_mgmt.aaa_business_units(parent_unit_id);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_manager_id ON user_mgmt.aaa_business_units(manager_id);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_name ON user_mgmt.aaa_business_units(name);
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_code ON user_mgmt.aaa_business_units(code) WHERE code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_is_active ON user_mgmt.aaa_business_units(is_active);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_user_id ON user_mgmt.aaa_user_business_units(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_business_unit_id ON user_mgmt.aaa_user_business_units(business_unit_id);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_assigned_by ON user_mgmt.aaa_user_business_units(assigned_by);
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_active ON user_mgmt.aaa_user_business_units(is_active);

-- Security table indexes
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_user_id ON user_mgmt.aaa_email_otps(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_expires_at ON user_mgmt.aaa_email_otps(expires_at);
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_used ON user_mgmt.aaa_email_otps(used);
CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_user_id ON user_mgmt.aaa_password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_token ON user_mgmt.aaa_password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_expires_at ON user_mgmt.aaa_password_reset_tokens(expires_at);

-- Unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_business_units_unique_code_per_org
    ON user_mgmt.aaa_business_units(organization_id, code)
    WHERE code IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_business_units_unique_name_per_parent
    ON user_mgmt.aaa_business_units(organization_id, COALESCE(parent_unit_id, '00000000-0000-0000-0000-000000000000'), name);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION user_mgmt.update_aaa_business_units_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at timestamp
DROP TRIGGER IF EXISTS trigger_update_aaa_business_units_updated_at ON user_mgmt.aaa_business_units;
CREATE TRIGGER trigger_update_aaa_business_units_updated_at
    BEFORE UPDATE ON user_mgmt.aaa_business_units
    FOR EACH ROW
    EXECUTE FUNCTION user_mgmt.update_aaa_business_units_updated_at();

-- Function to prevent circular hierarchy
CREATE OR REPLACE FUNCTION user_mgmt.check_business_unit_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check if parent_unit_id is being set
    IF NEW.parent_unit_id IS NOT NULL THEN
        -- Check if the new parent would create a circular reference
        WITH RECURSIVE hierarchy_check AS (
            -- Start with the proposed parent
            SELECT parent_unit_id, 1 as level
            FROM user_mgmt.aaa_business_units
            WHERE id = NEW.parent_unit_id
            
            UNION ALL
            
            -- Follow the hierarchy up
            SELECT bu.parent_unit_id, hc.level + 1
            FROM user_mgmt.aaa_business_units bu
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
            SELECT 1 FROM user_mgmt.aaa_business_units
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
DROP TRIGGER IF EXISTS trigger_check_business_unit_hierarchy ON user_mgmt.aaa_business_units;
CREATE TRIGGER trigger_check_business_unit_hierarchy
    BEFORE INSERT OR UPDATE ON user_mgmt.aaa_business_units
    FOR EACH ROW
    EXECUTE FUNCTION user_mgmt.check_business_unit_hierarchy();

-- =====================================================
-- DATABASE VIEWS
-- =====================================================

-- User details view with organizational context
CREATE OR REPLACE VIEW user_mgmt.vw_user_details AS
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
FROM user_mgmt.aaa_profiles p
LEFT JOIN user_mgmt.aaa_user_roles ur ON p.id = ur.user_id
LEFT JOIN user_mgmt.aaa_roles r ON ur.role_id = r.id
LEFT JOIN user_mgmt.aaa_user_business_units ubu ON p.id = ubu.user_id AND ubu.is_active = true
LEFT JOIN user_mgmt.aaa_business_units bu ON ubu.business_unit_id = bu.id AND bu.is_active = true
LEFT JOIN user_mgmt.aaa_organizations org ON bu.organization_id = org.id
GROUP BY p.id, p.email, p.first_name, p.middle_name, p.last_name, p.is_admin,
         p.mfa_secret, p.mfa_method, p.created_at, p.updated_at,
         bu.id, bu.name, org.id, org.company_name;

-- Business unit hierarchy view
CREATE OR REPLACE VIEW user_mgmt.vw_business_unit_hierarchy AS
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
    FROM user_mgmt.aaa_business_units bu
    LEFT JOIN user_mgmt.aaa_organizations org ON bu.organization_id = org.id
    LEFT JOIN user_mgmt.aaa_profiles p ON bu.manager_id = p.id
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
    FROM user_mgmt.aaa_business_units bu
    JOIN hierarchy h ON bu.parent_unit_id = h.id
    LEFT JOIN user_mgmt.aaa_profiles p ON bu.manager_id = p.id
)
SELECT * FROM hierarchy;

-- =====================================================
-- SAMPLE DATA
-- =====================================================

-- Data exported from existing database

-- Data exported from aaa_roles
INSERT INTO user_mgmt.aaa_roles (created_at, id, name) VALUES
    ('2025-08-23T08:43:57.212975-04:00', 'e7064b56-f331-4d93-89d0-a51eaa532503', 'super_user'),
    ('2025-08-23T08:43:57.212975-04:00', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', 'user'),
    ('2025-08-23T08:43:57.212975-04:00', 'd86b86aa-03f2-4208-96f5-9fd88d0f6336', 'group_admin'),
    ('2025-08-23T08:43:57.212975-04:00', '1b591fc8-ac4d-48fb-bf62-bcba424a235b', 'firm_admin'),
    ('2025-08-23T08:44:27.747919-04:00', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', 'admin'),
    ('2025-08-24T10:11:25.980111-04:00', 'fc026ba0-d094-4a57-a2e2-51ca3e6ba08b', 'account_admin'),
    ('2025-08-29T09:10:39.699215-04:00', '2d99be35-8b19-4870-a95d-44a5a31f7bb8', 'viewer'),
    ('2025-08-29T09:10:39.699215-04:00', '1b7af0fb-fe6d-407d-b38c-545dae07dfdd', 'editor'),
    ('2025-08-29T09:10:39.699215-04:00', '05766212-c660-478d-8a97-4a0668e374a7', 'manager')
ON CONFLICT DO NOTHING;

-- Data exported from aaa_organizations
INSERT INTO user_mgmt.aaa_organizations (address_1, address_2, city_town, company_name, country, created_at, email, id, phone_number, state, updated_at, zip) VALUES
    ('11 Washington', NULL, 'Boston', 'eagles', 'Usa', '2025-09-08T22:25:16.852542-04:00', 'n_sivakumar@yahoo.com', 'b428f3cc-cc5c-43bc-bd39-e628147f01da', '+16176394049', 'Ma', '2025-09-08T22:25:16.852542-04:00', '02053'),
    ('1 Add1', NULL, 'City', 'eagles2', 'Usa', '2025-09-09T11:36:04.185854-04:00', 'n_sivakumar@yahoo.com', 'f9f10037-6c82-4e77-8e6d-982fe511b71b', '16176394049', 'State', '2025-09-10T21:47:32.919021-04:00', '02053')
ON CONFLICT DO NOTHING;

-- Data exported from aaa_profiles
INSERT INTO user_mgmt.aaa_profiles (created_at, email, first_name, id, is_admin, last_name, mfa_method, mfa_secret, middle_name, password_hash, updated_at) VALUES
    ('2025-08-23T09:11:34.856828-04:00', 'n_sivakumar@yahoo.com', 'Sivakumar', 'd11ba7c1-5f3b-4906-a728-983364e7b12c', TRUE, 'Natarajan', 'totp', 'DIMYV5YF5GGECOPCCOZPTC5BDCZJJZEF', 'Natarajan', '$2b$12$tWufgbsd4UFKvJAg21xTyuT6osZvZr.53U4uWyEWBey1g0vHpI74m', '2025-09-16T18:22:33.050772-04:00'),
    ('2025-08-28T17:07:02.226524-04:00', 'ai.tools.test.2000@gmail.com', 'ai tools', 'd027cdcd-d024-4343-87e4-9877c0239eba', FALSE, 'real local test2', 'email', NULL, NULL, '$2b$12$c.xn/yHJuFPr0BQHr5O5du4hNWa7lO914w7.zeznUd4sBuF9ymck6', '2025-09-16T18:35:45.411407-04:00'),
    ('2025-09-04T07:55:07.196621-04:00', 'sriramh@gmail.com', 'sriram', '2d53c6b4-0996-4348-94ac-936502a98844', FALSE, 'hariram', NULL, NULL, NULL, '$2b$12$A3AbwudD2oSSCES96CZzdeUbRYXxkedvPvv/IrhiHvVAnkDjNktcK', '2025-09-04T22:24:40.587300-04:00'),
    ('2025-09-10T22:32:10.038701-04:00', 'eag_mark@c.com', 'eagle', 'd865cc55-05e6-4259-871d-409977409181', FALSE, 'Mark one', NULL, NULL, NULL, '$2b$12$KekJ6080g0qPRckub6IHE.bHTcEzu5rJ1KPegdiL7fEodesmaL1ra', '2025-09-12T20:59:17.951798-04:00'),
    ('2025-09-10T22:35:07.221586-04:00', 'eag_hr@h.com', 'eag 1', '699ec5dd-b298-4405-ba18-0be15a21fe24', FALSE, 'fin one1', NULL, NULL, NULL, '$2b$12$jiE.ri2mdhIpqb2yJZIjbugKFK.2zjC4KlbopzaifjAdgXbgtXN/a', '2025-09-17T17:54:40.406847-04:00'),
    ('2025-09-11T21:14:18.117483-04:00', 'mar_eag2@gmail.com', 'MAR', '64caa9bf-17c9-40ab-bce9-f7f41f64a1f7', FALSE, 'EAG2', NULL, NULL, NULL, '$2b$12$JUt1MV4Tq/fJ29dqQ/Rhi.VktSLorUGOgPtE3nfOTwO3m60UPqw.K', '2025-09-14T05:21:39.527624-04:00'),
    ('2025-09-11T21:42:27.925057-04:00', 'user_user@eagles2.com', 'user', '97ed717e-733b-4d3b-8d67-9da3b0e83174', FALSE, 'user2', NULL, NULL, NULL, '$2b$12$VK.wo5a4Wk6YLT6e2T/fQOTSIxzqIVKhfvaRojyG2hqPRPKTYU/.W', '2025-09-12T09:26:17.042386-04:00'),
    ('2025-09-13T14:51:13.070067-04:00', 'EAG_IT_UG@gmail.com', 'EAG1', '8d53a99f-837c-48df-9663-bc53d9d94062', FALSE, 'IT_BUS_ADM1', NULL, NULL, NULL, '$2b$12$Z.JPKIQPxgLRFssca602tuKdRmoL0EcNBPfxzb4bxueVp7OEuyCn6', '2025-09-14T08:54:18.254073-04:00'),
    ('2025-09-13T15:46:48.186128-04:00', 'EAG_IT_USER@gmail.com', 'EAG', '1c89d605-8c6a-4538-a234-1b15913be4e7', FALSE, 'IT User1', NULL, NULL, NULL, '$2b$12$yCTPOUgOvrNnIc.L71vPd.RssFMCoowTbAUoiaZEVgce89crobQ2i', '2025-09-14T05:20:40.123321-04:00'),
    ('2025-09-13T16:58:04.799842-04:00', 'sivakumarnatar@gmail.com', 'siva', '91b10c42-58ab-476c-b4ac-55dc59b2a25b', FALSE, 'natarajan', NULL, NULL, NULL, '$2b$12$WhGADRaqFvYQOm5oKAXJ7urDuIVqnxG3h.OoAIqbRT.BvP/50A4jK', '2025-09-13T16:58:34.518657-04:00'),
    ('2025-09-16T08:53:43.642394-04:00', 'eag_it_one@gmail.com', 'eag', 'ef9f4961-9df9-4539-8a8b-7127c4d05dac', FALSE, 'it one', NULL, NULL, NULL, '$2b$12$Tx7FjXNWhKQeVDJid0mIledHYSVHOf5Zj9C1n.1Eo6mP89sq3YH7K', '2025-09-16T08:53:43.642394-04:00'),
    ('2025-09-16T08:56:26.813526-04:00', 'son_eag_hr_one1@gmail.com', 'son', 'de339bb3-ea23-4486-a5a0-3b15ade1ffa9', FALSE, 'eag hr one', NULL, NULL, NULL, '$2b$12$y43r2F2TAAWlUWjTBII3de88yH5z1.cCeLiTD11XtQs/GOyrikBm6', '2025-09-16T08:56:26.813526-04:00'),
    ('2025-09-16T21:41:54.780838-04:00', 'one.new@gmail.com', 'one', 'f7a766db-be0d-4d0d-9c73-f4683c1d09b3', FALSE, 'newb', NULL, NULL, NULL, '$2b$12$iuFNwhAjDk80iDbf/OiWcexHytaTOe/zU8BMon1ymKafSAYBNpvV.', '2025-09-16T21:41:54.780838-04:00')
ON CONFLICT DO NOTHING;

-- Data exported from aaa_clients
INSERT INTO user_mgmt.aaa_clients (client_id, client_secret, created_at, is_active, name, scopes, updated_at) VALUES
    ('my_test_client_id', 'my_test_client_secret', '2025-08-23T08:46:00.298407-04:00', TRUE, 'My Test Application', ARRAY['read:users', 'manage:users'], '2025-08-23T08:46:00.298407-04:00')
ON CONFLICT DO NOTHING;

-- Data exported from aaa_business_units
INSERT INTO user_mgmt.aaa_business_units (code, country, created_at, created_by, description, email, id, is_active, location, manager_id, name, organization_id, parent_unit_id, phone_number, region, updated_at, updated_by) VALUES
    ('FIN_BOS', 'Usa', '2025-09-09T10:07:53.833516-04:00', NULL, 'To manage users within boston finance department', 'bos_fin@eagles.com', 'abb1e1b5-4596-43de-b7ca-f02b209e5d00', TRUE, 'Boston', NULL, 'Finance One', 'b428f3cc-cc5c-43bc-bd39-e628147f01da', NULL, '16762341234', 'Ne', '2025-09-14T05:15:29.360247-04:00', NULL),
    (NULL, NULL, '2025-09-09T11:23:17.402456-04:00', NULL, NULL, NULL, '62b4d306-e9dd-4bb2-b8d6-1b91f106af80', TRUE, NULL, 'd865cc55-05e6-4259-871d-409977409181', 'Marketing One', 'b428f3cc-cc5c-43bc-bd39-e628147f01da', NULL, NULL, NULL, '2025-09-17T17:53:19.058113-04:00', NULL),
    ('HR_CHI', 'Usa', '2025-09-09T11:38:28.510829-04:00', NULL, NULL, NULL, 'a5b1f3ec-f21c-48f6-b83e-c83e55472dde', TRUE, 'Chicago', NULL, 'HR ONE Chicago', 'b428f3cc-cc5c-43bc-bd39-e628147f01da', NULL, NULL, 'Central', '2025-09-17T17:53:08.232311-04:00', NULL),
    ('FIN2_EAG2', NULL, '2025-09-09T11:41:35.588123-04:00', NULL, NULL, NULL, '234044fc-7c0c-457c-be43-e809da427245', TRUE, 'PHI', NULL, 'Finance Two', 'f9f10037-6c82-4e77-8e6d-982fe511b71b', NULL, NULL, NULL, '2025-09-14T05:21:26.220107-04:00', NULL),
    ('HR2_EAG2', NULL, '2025-09-09T11:41:57.287531-04:00', NULL, NULL, NULL, 'fc5f393b-47ae-4b0d-89d2-b1480fa1f298', TRUE, NULL, NULL, 'HR2', 'f9f10037-6c82-4e77-8e6d-982fe511b71b', NULL, NULL, NULL, '2025-09-14T04:49:01.987436-04:00', NULL),
    ('IT_BOS', 'Usa', '2025-09-11T20:49:39.134229-04:00', NULL, 'IT boston users', 'bos_it@eagles.com', 'e3a1d41f-ada6-4ada-96ac-ac4adaac2dd6', TRUE, 'boston', NULL, 'IT One', 'b428f3cc-cc5c-43bc-bd39-e628147f01da', NULL, '16762341234', 'Ne', '2025-09-12T21:00:07.605787-04:00', NULL)
ON CONFLICT DO NOTHING;

-- Data exported from aaa_user_business_units
INSERT INTO user_mgmt.aaa_user_business_units (assigned_at, assigned_by, business_unit_id, created_at, id, is_active, updated_at, user_id) VALUES
    ('2025-09-10T00:00:07.212144-04:00', 'd11ba7c1-5f3b-4906-a728-983364e7b12c', 'a5b1f3ec-f21c-48f6-b83e-c83e55472dde', '2025-09-10T00:00:07.212144-04:00', '07b72580-2b61-473b-a5b8-9bcd1b666834', TRUE, '2025-09-10T00:00:07.212144-04:00', 'd11ba7c1-5f3b-4906-a728-983364e7b12c'),
    ('2025-09-10T00:01:29.406036-04:00', '2d53c6b4-0996-4348-94ac-936502a98844', 'fc5f393b-47ae-4b0d-89d2-b1480fa1f298', '2025-09-10T00:01:29.406036-04:00', '09b32580-2b61-473b-a5b8-9bcd1b666834', TRUE, '2025-09-10T00:01:29.406036-04:00', '2d53c6b4-0996-4348-94ac-936502a98844'),
    ('2025-09-12T20:59:17.954889-04:00', 'd027cdcd-d024-4343-87e4-9877c0239eba', '62b4d306-e9dd-4bb2-b8d6-1b91f106af80', '2025-09-12T20:59:17.954889-04:00', 'c01b5620-16bc-4b24-99ae-80f745bcb2d7', TRUE, '2025-09-12T20:59:17.954889-04:00', 'd865cc55-05e6-4259-871d-409977409181'),
    ('2025-09-13T16:58:04.802025-04:00', 'd027cdcd-d024-4343-87e4-9877c0239eba', 'abb1e1b5-4596-43de-b7ca-f02b209e5d00', '2025-09-13T16:58:04.802025-04:00', 'cd044ca0-8c09-4a07-b6b9-3f28c75f60e4', TRUE, '2025-09-13T16:58:04.802025-04:00', '91b10c42-58ab-476c-b4ac-55dc59b2a25b'),
    ('2025-09-13T18:05:53.445834-04:00', '2d53c6b4-0996-4348-94ac-936502a98844', '62b4d306-e9dd-4bb2-b8d6-1b91f106af80', '2025-09-13T18:05:53.445834-04:00', 'e6638655-88cb-4277-acae-baefed970838', TRUE, '2025-09-13T18:05:53.445834-04:00', 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-14T05:20:40.133279-04:00', '2d53c6b4-0996-4348-94ac-936502a98844', 'e3a1d41f-ada6-4ada-96ac-ac4adaac2dd6', '2025-09-14T05:20:40.133279-04:00', 'c6161a06-a097-4fd4-a87d-dc013b90a8fa', TRUE, '2025-09-14T05:20:40.133279-04:00', '1c89d605-8c6a-4538-a234-1b15913be4e7'),
    ('2025-09-14T08:54:18.281275-04:00', '2d53c6b4-0996-4348-94ac-936502a98844', 'e3a1d41f-ada6-4ada-96ac-ac4adaac2dd6', '2025-09-14T08:54:18.281275-04:00', '8cf093d8-438d-4138-8028-86d31cb8538e', TRUE, '2025-09-14T08:54:18.281275-04:00', '8d53a99f-837c-48df-9663-bc53d9d94062'),
    ('2025-09-16T08:53:43.660280-04:00', '8d53a99f-837c-48df-9663-bc53d9d94062', 'e3a1d41f-ada6-4ada-96ac-ac4adaac2dd6', '2025-09-16T08:53:43.660280-04:00', 'ac44b8e0-7323-45c9-a78c-27cd109e218c', TRUE, '2025-09-16T08:53:43.660280-04:00', 'ef9f4961-9df9-4539-8a8b-7127c4d05dac'),
    ('2025-09-16T08:56:26.815499-04:00', NULL, 'a5b1f3ec-f21c-48f6-b83e-c83e55472dde', '2025-09-16T08:56:26.815499-04:00', '8ce614d3-0c26-4ea8-b3fd-3453cd9d7360', TRUE, '2025-09-16T21:40:27.189763-04:00', 'de339bb3-ea23-4486-a5a0-3b15ade1ffa9'),
    ('2025-09-17T17:54:40.416483-04:00', '2d53c6b4-0996-4348-94ac-936502a98844', 'abb1e1b5-4596-43de-b7ca-f02b209e5d00', '2025-09-17T17:54:40.416483-04:00', 'db1c1eaa-e3e8-4147-a335-ddb77c92df04', TRUE, '2025-09-17T17:54:40.416483-04:00', '699ec5dd-b298-4405-ba18-0be15a21fe24')
ON CONFLICT DO NOTHING;

-- Data exported from aaa_email_otps
INSERT INTO user_mgmt.aaa_email_otps (created_at, email, expires_at, id, otp, purpose, used, user_id) VALUES
    ('2025-09-16T18:35:25.402249-04:00', 'ai.tools.test.2000@gmail.com', '2025-09-16T18:45:25.402231-04:00', '1a87427d-f0cb-4194-a66f-6bd9d86d61d8', '967289', 'setup', FALSE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-16T21:56:48.090262-04:00', 'ai.tools.test.2000@gmail.com', '2025-09-16T22:01:48.090205-04:00', 'e26baa2b-9df9-46bb-ab92-deae8a6caa71', '285475', 'login', FALSE, 'd027cdcd-d024-4343-87e4-9877c0239eba')
ON CONFLICT DO NOTHING;

-- Data exported from aaa_password_reset_tokens
INSERT INTO user_mgmt.aaa_password_reset_tokens (created_at, expires_at, id, token, used, user_id) VALUES
    ('2025-09-02T17:36:45.797475-04:00', '2025-09-02T18:06:45.797381-04:00', '09ad7cda-d00d-4f40-a96b-560b8a01f9aa', 'x8G2J-ZJFcriGnfBikNmj3rLltlByt6SagBHYZAahWo', FALSE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-02T17:42:22.909032-04:00', '2025-09-02T18:12:22.907998-04:00', '76e55e17-1da7-41cc-bd22-337042180ecf', 'N2yg1ggCafw4iRm_B-tq3f34NaKVwlLUQMgd52E1fms', TRUE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-04T13:19:46.548073-04:00', '2025-09-04T13:49:46.546140-04:00', 'ea12ed9e-c0ba-4a07-90d3-e5e01b3cc94a', 'mJT4tqufHxrAY5axOuD_t458NEvwgZv4n_0RgfdUPDY', TRUE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-04T21:57:47.469696-04:00', '2025-09-04T22:27:47.469567-04:00', 'cca13b90-edc2-4c40-b79b-3a75a141b9c2', '-7aRGXsv1ONwQTvm9gA8ijMTYeM6885vydYqQ64rgcw', FALSE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-04T22:25:20.957392-04:00', '2025-09-04T22:55:20.956094-04:00', 'bc52e72c-8d20-4733-b468-48558a972c61', 'AKNzSpYCdPJvVriJOxhu6r18PzojMyjQEOi8L58Ff-0', FALSE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-13T16:54:07.983155-04:00', '2025-09-13T17:24:07.956807-04:00', 'faf00729-1648-4843-add6-29d1ec9d5531', '-sCRZosqoS4mY-TrC0lyx_gvjL-78Va9NMxhLjYATdI', TRUE, 'd027cdcd-d024-4343-87e4-9877c0239eba'),
    ('2025-09-13T16:58:04.809173-04:00', '2025-09-13T17:28:04.799645-04:00', '26887d73-1e88-4430-926e-febc8c691292', 'luXg9WJffa9H3_3_K7RrDF8f3eoEvD_2VbM861RP-gE', TRUE, '91b10c42-58ab-476c-b4ac-55dc59b2a25b'),
    ('2025-09-13T18:05:53.447673-04:00', '2025-09-13T18:35:53.377806-04:00', '6ec04e2a-ef5b-4706-bf9b-a3ad24d324f6', '6muRmCSBjEihDoWPlFKNuBKxUle1ez7UFdh_1nnsec0', FALSE, 'd027cdcd-d024-4343-87e4-9877c0239eba')
ON CONFLICT DO NOTHING;


INSERT INTO user_mgmt.aaa_user_roles VALUES ('d11ba7c1-5f3b-4906-a728-983364e7b12c', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-08-24 10:54:06.682291-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('d865cc55-05e6-4259-871d-409977409181', 'd86b86aa-03f2-4208-96f5-9fd88d0f6336', '2025-09-12 20:59:17.953461-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('2d53c6b4-0996-4348-94ac-936502a98844', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-09-04 07:55:07.202664-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('91b10c42-58ab-476c-b4ac-55dc59b2a25b', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-13 16:58:04.805913-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('d027cdcd-d024-4343-87e4-9877c0239eba', '1b591fc8-ac4d-48fb-bf62-bcba424a235b', '2025-09-13 18:05:53.444341-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('1c89d605-8c6a-4538-a234-1b15913be4e7', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-14 05:20:40.126585-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('64caa9bf-17c9-40ab-bce9-f7f41f64a1f7', 'd86b86aa-03f2-4208-96f5-9fd88d0f6336', '2025-09-14 05:21:39.528947-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('8d53a99f-837c-48df-9663-bc53d9d94062', 'd86b86aa-03f2-4208-96f5-9fd88d0f6336', '2025-09-14 08:54:18.277816-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('ef9f4961-9df9-4539-8a8b-7127c4d05dac', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-16 08:53:43.666037-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('de339bb3-ea23-4486-a5a0-3b15ade1ffa9', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-16 08:56:26.818997-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('f7a766db-be0d-4d0d-9c73-f4683c1d09b3', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-16 21:41:54.790978-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('699ec5dd-b298-4405-ba18-0be15a21fe24', 'd86b86aa-03f2-4208-96f5-9fd88d0f6336', '2025-09-17 17:54:40.410465-04');
INSERT INTO user_mgmt.aaa_user_roles VALUES ('97ed717e-733b-4d3b-8d67-9da3b0e83174', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-12 09:26:17.050367-04');


-- =====================================================
-- TABLE AND COLUMN COMMENTS
-- =====================================================

-- Core table comments
COMMENT ON TABLE user_mgmt.aaa_profiles IS 'User profiles with authentication data';
COMMENT ON TABLE user_mgmt.aaa_roles IS 'System roles for authorization';
COMMENT ON TABLE user_mgmt.aaa_user_roles IS 'Many-to-many relationship between users and roles';
COMMENT ON TABLE user_mgmt.aaa_clients IS 'API clients for machine-to-machine authentication';

-- Organizational table comments
COMMENT ON TABLE user_mgmt.aaa_organizations IS 'Organizations/companies in the system';
COMMENT ON TABLE user_mgmt.aaa_business_units IS 'Business units within organizations supporting hierarchical structure';
COMMENT ON TABLE user_mgmt.aaa_user_business_units IS 'Assignment of users to business units';

-- Security table comments
COMMENT ON TABLE user_mgmt.aaa_email_otps IS 'Email-based one-time passwords for MFA';
COMMENT ON TABLE user_mgmt.aaa_password_reset_tokens IS 'Tokens for password reset functionality';

-- Key column comments
COMMENT ON COLUMN user_mgmt.aaa_profiles.mfa_method IS 'MFA method: totp (authenticator app) or email';
COMMENT ON COLUMN user_mgmt.aaa_business_units.parent_unit_id IS 'Parent business unit for hierarchical structure';
COMMENT ON COLUMN user_mgmt.aaa_business_units.code IS 'Internal reference code (alphanumeric, unique per organization)';

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
    WHERE table_schema = 'user_mgmt'
    AND table_name LIKE 'aaa_%';
    
    RAISE NOTICE 'Created % AAA tables in schema user_mgmt', table_count;
    
    IF table_count < 9 THEN
        RAISE WARNING 'Expected at least 9 AAA tables, but found %', table_count;
    ELSE
        RAISE NOTICE 'Database setup completed successfully in schema user_mgmt!';
    END IF;
END $$;

-- Display sample data counts
SELECT
    'Roles' as entity,
    COUNT(*) as count
FROM user_mgmt.aaa_roles
UNION ALL
SELECT
    'Organizations' as entity,
    COUNT(*) as count
FROM user_mgmt.aaa_organizations
UNION ALL
SELECT
    'Business Units' as entity,
    COUNT(*) as count
FROM user_mgmt.aaa_business_units
UNION ALL
SELECT
    'Users' as entity,
    COUNT(*) as count
FROM user_mgmt.aaa_profiles;

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
-- 2025-09-18 02:41:46 UTC



