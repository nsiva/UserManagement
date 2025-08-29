-- Supabase Data Export Queries
-- Generated on: 2025-08-29 08:36:43.061303
-- Run these queries in Supabase SQL Editor to export your data

-- INSTRUCTIONS:
-- 1. Run each query in order (dependencies matter)
-- 2. Copy the results and format as INSERT statements
-- 3. Or use the Python export script for automatic formatting

================================================================================

-- 1. Export aaa_roles
-- Export all roles (run this first)
SELECT * FROM aaa_roles ORDER BY created_at;

------------------------------------------------------------

-- 2. Export aaa_profiles
-- Export all user profiles
SELECT * FROM aaa_profiles ORDER BY created_at;

------------------------------------------------------------

-- 3. Export aaa_user_roles
-- Export user-role relationships
SELECT * FROM aaa_user_roles ORDER BY assigned_at;

------------------------------------------------------------

-- 4. Export aaa_clients
-- Export API clients
SELECT * FROM aaa_clients ORDER BY created_at;

------------------------------------------------------------

-- 5. Export aaa_password_reset_tokens
-- Export password reset tokens
SELECT * FROM aaa_password_reset_tokens ORDER BY created_at;

------------------------------------------------------------
