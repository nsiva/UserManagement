-- Create a comprehensive view for user details with business unit and organization information
-- This view will be used by the API to efficiently retrieve user data with all related information

-- Drop view if exists (for development/updates)
DROP VIEW IF EXISTS vw_user_details;

-- Create the comprehensive user details view
CREATE VIEW vw_user_details AS
SELECT 
    p.id as user_id,
    p.email,
    p.first_name,
    p.middle_name, 
    p.last_name,
    p.is_admin,
    p.mfa_secret,
    p.mfa_method,
    p.created_at as user_created_at,
    p.updated_at as user_updated_at,
    
    -- Business Unit Information
    ub.business_unit_id,
    bu.name as business_unit_name,
    bu.code as business_unit_code,
    bu.description as business_unit_description,
    bu.location as business_unit_location,
    bu.is_active as business_unit_active,
    
    -- Organization Information  
    bu.organization_id,
    o.company_name as organization_name,
    o.email as organization_email,
    o.phone_number as organization_phone,
    o.city_town as organization_city,
    o.country as organization_country,
    
    -- Manager Information (if available)
    bu.manager_id as business_unit_manager_id,
    CONCAT(mgr.first_name, ' ', mgr.last_name) as business_unit_manager_name,
    
    -- Parent Business Unit Information (if available)
    bu.parent_unit_id,
    pbu.name as parent_business_unit_name,
    
    -- Assignment metadata
    ub.assigned_at as business_unit_assigned_at,
    ub.assigned_by as business_unit_assigned_by,
    ub.is_active as assignment_active

FROM aaa_profiles p
LEFT JOIN aaa_user_business_units ub ON p.id = ub.user_id AND ub.is_active = TRUE
LEFT JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
LEFT JOIN aaa_profiles mgr ON bu.manager_id = mgr.id
LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id;

-- Add helpful comments
COMMENT ON VIEW vw_user_details IS 'Comprehensive view of users with their business unit and organization details';

-- Create indexes on the underlying tables for better view performance (if not already exists)
-- Note: These are on the base tables, not the view itself

-- Index on user_business_units for faster joins
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_user_active 
ON aaa_user_business_units(user_id, is_active) WHERE is_active = TRUE;

-- Index on business_units for organization lookups
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_org_id 
ON aaa_business_units(organization_id);

-- Index on business_units for parent lookups  
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_parent_id 
ON aaa_business_units(parent_unit_id);

-- Index on business_units for manager lookups
CREATE INDEX IF NOT EXISTS idx_aaa_business_units_manager_id 
ON aaa_business_units(manager_id);