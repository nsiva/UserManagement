-- Supabase Data Inspection Queries
-- Generated on: 2025-08-29 08:36:43.061099
-- Run these queries in Supabase SQL Editor to inspect your data

-- IMPORTANT: These are READ-ONLY queries safe to run on production

================================================================================

-- Count all records in each table
-- Get overview of data volume
-- Get record counts from all tables
SELECT 'aaa_profiles' as table_name, COUNT(*) as record_count FROM aaa_profiles
UNION ALL
SELECT 'aaa_roles', COUNT(*) FROM aaa_roles  
UNION ALL
SELECT 'aaa_user_roles', COUNT(*) FROM aaa_user_roles
UNION ALL  
SELECT 'aaa_clients', COUNT(*) FROM aaa_clients
UNION ALL
SELECT 'aaa_password_reset_tokens', COUNT(*) FROM aaa_password_reset_tokens;

------------------------------------------------------------

-- User overview with roles
-- See all users with their roles and MFA status
-- Users with roles and MFA status
SELECT 
    p.email,
    p.first_name,
    p.last_name,
    p.is_admin,
    CASE WHEN p.mfa_secret IS NOT NULL THEN 'Enabled' ELSE 'Disabled' END as mfa_status,
    STRING_AGG(r.name, ', ') as roles,
    p.created_at
FROM aaa_profiles p
LEFT JOIN aaa_user_roles ur ON p.id = ur.user_id
LEFT JOIN aaa_roles r ON ur.role_id = r.id
GROUP BY p.id, p.email, p.first_name, p.last_name, p.is_admin, p.mfa_secret, p.created_at
ORDER BY p.created_at;

------------------------------------------------------------
