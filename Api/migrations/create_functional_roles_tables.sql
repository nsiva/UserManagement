-- Migration: Create functional roles system
-- This creates separate tables for functional roles and user assignments

-- Create functional roles table
CREATE TABLE IF NOT EXISTS aaa_functional_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general', -- e.g., 'fleet', 'finance', 'operations'
    permissions TEXT[], -- Array of permission strings
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES aaa_profiles(id),
    updated_by UUID REFERENCES aaa_profiles(id)
);

-- Create user-functional-role junction table
CREATE TABLE IF NOT EXISTS aaa_user_functional_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    functional_role_id UUID NOT NULL REFERENCES aaa_functional_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES aaa_profiles(id),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration
    notes TEXT, -- Optional assignment notes
    UNIQUE(user_id, functional_role_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_functional_roles_name ON aaa_functional_roles(name);

CREATE INDEX IF NOT EXISTS idx_user_functional_roles_user_id ON aaa_user_functional_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_functional_roles_role_id ON aaa_user_functional_roles(functional_role_id);
CREATE INDEX IF NOT EXISTS idx_user_functional_roles_active ON aaa_user_functional_roles(is_active);

-- Note: updated_at timestamps are now handled explicitly in API code

-- Disable RLS for direct access
ALTER TABLE aaa_functional_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_user_functional_roles DISABLE ROW LEVEL SECURITY;

-- Insert initial functional roles
INSERT INTO aaa_functional_roles (name, label, description, category, permissions) VALUES
('fleet_manager', 'Fleet Manager', 'Manages vehicles and fleet operations', 'fleet', 
 ARRAY['vehicles:read', 'vehicles:write', 'vehicles:delete', 'drivers:read', 'drivers:write', 'fleet:reports']),
('accountant', 'Accountant', 'Access to financial data and expense management', 'finance', 
 ARRAY['expenses:read', 'expenses:write', 'fuel:read', 'fuel:write', 'financial:reports', 'invoices:read']),
('dispatcher', 'Dispatcher', 'Monitors vehicle locations and coordinates routes', 'operations', 
 ARRAY['vehicles:read', 'telematics:read', 'routes:read', 'routes:write', 'drivers:read', 'dispatch:reports']),
('mechanic', 'Mechanic', 'Manages work orders and vehicle maintenance', 'maintenance', 
 ARRAY['work_orders:read', 'work_orders:write', 'vehicles:read', 'maintenance:read', 'maintenance:write', 'parts:read']),
('driver', 'Driver', 'Basic access to own profile and assigned vehicle', 'operations', 
 ARRAY['profile:read', 'profile:write', 'own_vehicle:read', 'own_telematics:read', 'own_routes:read'])
ON CONFLICT (name) DO UPDATE SET
    label = EXCLUDED.label,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    permissions = EXCLUDED.permissions,
    updated_at = NOW();

-- Add table comments
COMMENT ON TABLE aaa_functional_roles IS 'Functional roles that define job-specific permissions';
COMMENT ON TABLE aaa_user_functional_roles IS 'Assignment of functional roles to users';

-- Display created roles
SELECT name, label, category, array_length(permissions, 1) as permission_count 
FROM aaa_functional_roles 
ORDER BY category, name;