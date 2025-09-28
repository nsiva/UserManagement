-- Migration: Create views for hierarchical functional roles system
-- This version uses only views and relies on API code for constraint enforcement

-- View to show available functional roles for business units
-- (only roles enabled at organization level)
CREATE OR REPLACE VIEW vw_business_unit_available_roles AS
SELECT 
    bu.id as business_unit_id,
    bu.name as business_unit_name,
    bu.organization_id,
    o.company_name as organization_name,
    fr.id as functional_role_id,
    fr.name as functional_role_name,
    fr.label as functional_role_label,
    fr.description as functional_role_description,
    fr.category as functional_role_category,
    fr.permissions as functional_role_permissions,
    ofr.is_enabled as enabled_at_org,
    COALESCE(bufr.is_enabled, FALSE) as enabled_at_bu,
    ofr.assigned_at as org_assigned_at,
    bufr.assigned_at as bu_assigned_at
FROM aaa_business_units bu
JOIN aaa_organizations o ON bu.organization_id = o.id
JOIN aaa_organization_functional_roles ofr ON o.id = ofr.organization_id AND ofr.is_enabled = TRUE
JOIN aaa_functional_roles fr ON ofr.functional_role_id = fr.id AND fr.is_active = TRUE
LEFT JOIN aaa_business_unit_functional_roles bufr ON bu.id = bufr.business_unit_id 
    AND fr.id = bufr.functional_role_id
ORDER BY bu.name, fr.category, fr.name;

-- View to show available functional roles for users
-- (only roles enabled at business unit level where user is assigned)
CREATE OR REPLACE VIEW vw_user_available_roles AS
SELECT DISTINCT
    ubu.user_id,
    p.email as user_email,
    p.first_name,
    p.last_name,
    bu.id as business_unit_id,
    bu.name as business_unit_name,
    bu.organization_id,
    o.company_name as organization_name,
    fr.id as functional_role_id,
    fr.name as functional_role_name,
    fr.label as functional_role_label,
    fr.description as functional_role_description,
    fr.category as functional_role_category,
    fr.permissions as functional_role_permissions,
    COALESCE(ufr.is_active, FALSE) as currently_assigned,
    ufr.assigned_at as assigned_at,
    ufr.expires_at as expires_at
FROM aaa_user_business_units ubu
JOIN aaa_profiles p ON ubu.user_id = p.id
JOIN aaa_business_units bu ON ubu.business_unit_id = bu.id AND ubu.is_active = TRUE
JOIN aaa_organizations o ON bu.organization_id = o.id
JOIN aaa_business_unit_functional_roles bufr ON bu.id = bufr.business_unit_id AND bufr.is_enabled = TRUE
JOIN aaa_functional_roles fr ON bufr.functional_role_id = fr.id AND fr.is_active = TRUE
LEFT JOIN aaa_user_functional_roles ufr ON ubu.user_id = ufr.user_id 
    AND fr.id = ufr.functional_role_id
ORDER BY p.email, bu.name, fr.category, fr.name;

-- Enhanced hierarchy view with more details
CREATE OR REPLACE VIEW vw_functional_role_hierarchy AS
SELECT 
    o.id as organization_id,
    o.company_name as organization_name,
    bu.id as business_unit_id,
    bu.name as business_unit_name,
    fr.id as functional_role_id,
    fr.name as functional_role_name,
    fr.label as functional_role_label,
    fr.category as functional_role_category,
    fr.description as functional_role_description,
    ofr.is_enabled as enabled_at_org,
    bufr.is_enabled as enabled_at_bu,
    ofr.assigned_at as org_assigned_at,
    bufr.assigned_at as bu_assigned_at,
    ofr.notes as org_notes,
    bufr.notes as bu_notes,
    COUNT(ufr.user_id) as users_with_role
FROM aaa_organizations o
LEFT JOIN aaa_organization_functional_roles ofr ON o.id = ofr.organization_id
LEFT JOIN aaa_functional_roles fr ON ofr.functional_role_id = fr.id
LEFT JOIN aaa_business_units bu ON o.id = bu.organization_id
LEFT JOIN aaa_business_unit_functional_roles bufr ON bu.id = bufr.business_unit_id 
    AND fr.id = bufr.functional_role_id
LEFT JOIN aaa_user_functional_roles ufr ON fr.id = ufr.functional_role_id AND ufr.is_active = TRUE
LEFT JOIN aaa_user_business_units ubu ON ufr.user_id = ubu.user_id 
    AND ubu.business_unit_id = bu.id AND ubu.is_active = TRUE
WHERE fr.id IS NOT NULL
GROUP BY o.id, o.company_name, bu.id, bu.name, fr.id, fr.name, fr.label, fr.category, 
         fr.description, ofr.is_enabled, bufr.is_enabled, ofr.assigned_at, bufr.assigned_at,
         ofr.notes, bufr.notes
ORDER BY o.company_name, bu.name, fr.category, fr.name;

-- View to check organization role usage (for deletion constraints)
CREATE OR REPLACE VIEW vw_organization_role_usage AS
SELECT 
    ofr.id as org_role_assignment_id,
    ofr.organization_id,
    ofr.functional_role_id,
    fr.name as role_name,
    o.company_name,
    COUNT(bufr.id) as business_unit_usage_count,
    COUNT(ufr.user_id) as total_user_assignments
FROM aaa_organization_functional_roles ofr
JOIN aaa_functional_roles fr ON ofr.functional_role_id = fr.id
JOIN aaa_organizations o ON ofr.organization_id = o.id
LEFT JOIN aaa_business_unit_functional_roles bufr ON ofr.functional_role_id = bufr.functional_role_id
    AND bufr.is_enabled = TRUE
LEFT JOIN aaa_business_units bu ON bufr.business_unit_id = bu.id 
    AND bu.organization_id = o.id
LEFT JOIN aaa_user_functional_roles ufr ON fr.id = ufr.functional_role_id AND ufr.is_active = TRUE
LEFT JOIN aaa_user_business_units ubu ON ufr.user_id = ubu.user_id 
    AND ubu.business_unit_id = bu.id AND ubu.is_active = TRUE
GROUP BY ofr.id, ofr.organization_id, ofr.functional_role_id, fr.name, o.company_name;

-- View to check business unit role usage (for deletion constraints)
CREATE OR REPLACE VIEW vw_business_unit_role_usage AS
SELECT 
    bufr.id as bu_role_assignment_id,
    bufr.business_unit_id,
    bufr.functional_role_id,
    fr.name as role_name,
    bu.name as business_unit_name,
    bu.organization_id,
    COUNT(ufr.user_id) as user_assignment_count
FROM aaa_business_unit_functional_roles bufr
JOIN aaa_functional_roles fr ON bufr.functional_role_id = fr.id
JOIN aaa_business_units bu ON bufr.business_unit_id = bu.id
LEFT JOIN aaa_user_functional_roles ufr ON fr.id = ufr.functional_role_id AND ufr.is_active = TRUE
LEFT JOIN aaa_user_business_units ubu ON ufr.user_id = ubu.user_id 
    AND ubu.business_unit_id = bu.id AND ubu.is_active = TRUE
WHERE bufr.is_enabled = TRUE
GROUP BY bufr.id, bufr.business_unit_id, bufr.functional_role_id, fr.name, bu.name, bu.organization_id;

-- Add table comments
COMMENT ON VIEW vw_business_unit_available_roles IS 'Shows functional roles available for business units (org-level enabled roles)';
COMMENT ON VIEW vw_user_available_roles IS 'Shows functional roles available for users (bu-level enabled roles)';
COMMENT ON VIEW vw_functional_role_hierarchy IS 'Complete hierarchical view of functional role assignments';
COMMENT ON VIEW vw_organization_role_usage IS 'Shows usage of organization-level roles for constraint checking';
COMMENT ON VIEW vw_business_unit_role_usage IS 'Shows usage of business unit-level roles for constraint checking';

-- Display setup confirmation
SELECT 'Hierarchical functional roles views created successfully' as status;