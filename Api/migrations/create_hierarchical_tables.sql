-- Migration: Create hierarchical functional roles tables
-- This creates the actual tables needed for organization and business unit functional role assignments

-- Create organization functional roles table
CREATE TABLE IF NOT EXISTS aaa_organization_functional_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES aaa_organizations(id) ON DELETE CASCADE,
    functional_role_id UUID NOT NULL REFERENCES aaa_functional_roles(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES aaa_profiles(id),
    notes TEXT,
    UNIQUE(organization_id, functional_role_id)
);

-- Create business unit functional roles table  
CREATE TABLE IF NOT EXISTS aaa_business_unit_functional_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_unit_id UUID NOT NULL REFERENCES aaa_business_units(id) ON DELETE CASCADE,
    functional_role_id UUID NOT NULL REFERENCES aaa_functional_roles(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES aaa_profiles(id),
    notes TEXT,
    UNIQUE(business_unit_id, functional_role_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_org_functional_roles_org_id ON aaa_organization_functional_roles(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_functional_roles_role_id ON aaa_organization_functional_roles(functional_role_id);
CREATE INDEX IF NOT EXISTS idx_org_functional_roles_enabled ON aaa_organization_functional_roles(is_enabled);

CREATE INDEX IF NOT EXISTS idx_bu_functional_roles_bu_id ON aaa_business_unit_functional_roles(business_unit_id);
CREATE INDEX IF NOT EXISTS idx_bu_functional_roles_role_id ON aaa_business_unit_functional_roles(functional_role_id);
CREATE INDEX IF NOT EXISTS idx_bu_functional_roles_enabled ON aaa_business_unit_functional_roles(is_enabled);

-- Disable RLS for direct access
ALTER TABLE aaa_organization_functional_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_business_unit_functional_roles DISABLE ROW LEVEL SECURITY;

-- Add table comments
COMMENT ON TABLE aaa_organization_functional_roles IS 'Functional roles enabled at organization level';
COMMENT ON TABLE aaa_business_unit_functional_roles IS 'Functional roles enabled at business unit level';

-- Display table structure
\d aaa_organization_functional_roles;
\d aaa_business_unit_functional_roles;