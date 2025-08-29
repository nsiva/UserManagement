-- ========================================================================
-- EXPORTED DATA FROM SUPABASE
-- Generated on: 2025-08-29 09:17:51
-- ========================================================================
-- This file contains all your current data from Supabase aaa_* tables
-- Run this AFTER creating the schema with local_postgresql_setup.sql
-- ========================================================================

-- Set search path to use the aaa schema
SET search_path TO aaa, public;

-- Disable triggers during bulk insert for better performance
SET session_replication_role = replica;



-- ========================================================================
-- AAA_ROLES DATA
-- ========================================================================

INSERT INTO aaa.aaa_roles (id, name, created_at) 
VALUES ('d86b86aa-03f2-4208-96f5-9fd88d0f6336', 'group_admin', '2025-08-23T12:43:57.212975+00:00');
INSERT INTO aaa.aaa_roles (id, name, created_at) 
VALUES ('1b591fc8-ac4d-48fb-bf62-bcba424a235b', 'firm_admin', '2025-08-23T12:43:57.212975+00:00');
INSERT INTO aaa.aaa_roles (id, name, created_at) 
VALUES ('e7064b56-f331-4d93-89d0-a51eaa532503', 'super_user', '2025-08-23T12:43:57.212975+00:00');
INSERT INTO aaa.aaa_roles (id, name, created_at) 
VALUES ('c94ad0d0-c5da-4fed-93e0-72059519f0ad', 'user', '2025-08-23T12:43:57.212975+00:00');
INSERT INTO aaa.aaa_roles (id, name, created_at) 
VALUES ('f582e367-72dd-4f57-92b0-73c2e2e755ed', 'admin', '2025-08-23T12:44:27.747919+00:00');
INSERT INTO aaa.aaa_roles (id, name, created_at) 
VALUES ('fc026ba0-d094-4a57-a2e2-51ca3e6ba08b', 'account_admin', '2025-08-24T14:11:25.980111+00:00');

-- ========================================================================
-- AAA_PROFILES DATA
-- ========================================================================

INSERT INTO aaa.aaa_profiles (id, email, password_hash, is_admin, mfa_secret, created_at, updated_at, first_name, middle_name, last_name) 
VALUES ('07b72580-1b61-473b-a5b8-9bcd1b666034', 'sivakumarnatar@gmail.com', '$2b$12$F2QFD1Ez7egZN.n.vptcXedOU8.beiW.lCawDdLatVRqHvxbqrS7i', FALSE, 'BQ7LK4IFETMYGF3LAAATJ6T7C7SAZEKU', '2025-08-28T03:11:15.315851+00:00', '2025-08-28T21:03:06.739299+00:00', 'siva2', NULL, 'natarajan_updated_test');
INSERT INTO aaa.aaa_profiles (id, email, password_hash, is_admin, mfa_secret, created_at, updated_at, first_name, middle_name, last_name) 
VALUES ('d027cdcd-d024-4343-87e4-9877c0239eba', 'ai.tools.test.2000@gmail.com', '$2b$12$flrsrtPUNYQF.SLNYxTCxuRSIftq//6plVNAiRuolbfMIyndY9Mve', FALSE, NULL, '2025-08-28T21:07:02.226524+00:00', '2025-08-28T21:07:02.226524+00:00', 'ai tools', NULL, 'test');
INSERT INTO aaa.aaa_profiles (id, email, password_hash, is_admin, mfa_secret, created_at, updated_at, first_name, middle_name, last_name) 
VALUES ('d11ba7c1-5f3b-4906-a728-983364e7b12c', 'n_sivakumar@yahoo.com', '$2b$12$tWufgbsd4UFKvJAg21xTyuT6osZvZr.53U4uWyEWBey1g0vHpI74m', TRUE, 'DIMYV5YF5GGECOPCCOZPTC5BDCZJJZEF', '2025-08-23T13:11:34.856828+00:00', '2025-08-23T13:11:34.856828+00:00', 'Sivakumar', 'Natarajan', 'Natarajan');

-- ========================================================================
-- AAA_CLIENTS DATA
-- ========================================================================

INSERT INTO aaa.aaa_clients (client_id, client_secret, name, scopes, is_active, created_at, updated_at) 
VALUES ('my_test_client_id', 'my_test_client_secret', 'My Test Application', ARRAY['read:users', 'manage:users'], TRUE, '2025-08-23T12:46:00.298407+00:00', '2025-08-23T12:46:00.298407+00:00');

-- ========================================================================
-- AAA_USER_ROLES DATA
-- ========================================================================

INSERT INTO aaa.aaa_user_roles (user_id, role_id, assigned_at) 
VALUES ('d11ba7c1-5f3b-4906-a728-983364e7b12c', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-08-24T14:54:06.682291+00:00');
INSERT INTO aaa.aaa_user_roles (user_id, role_id, assigned_at) 
VALUES ('07b72580-1b61-473b-a5b8-9bcd1b666034', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-08-28T03:11:15.540481+00:00');
INSERT INTO aaa.aaa_user_roles (user_id, role_id, assigned_at) 
VALUES ('d027cdcd-d024-4343-87e4-9877c0239eba', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-08-28T21:07:02.482338+00:00');

-- ========================================================================
-- DATA EXPORT COMPLETE
-- ========================================================================

-- Re-enable triggers
SET session_replication_role = DEFAULT;

-- Update sequences to avoid ID conflicts (if using serial columns)
-- Note: This setup uses UUID with gen_random_uuid(), so no sequence updates needed

-- Verify data was imported correctly
SELECT 
    'aaa_profiles' as table_name, 
    COUNT(*) as row_count 
FROM aaa.aaa_profiles
UNION ALL
SELECT 
    'aaa_roles' as table_name, 
    COUNT(*) as row_count 
FROM aaa.aaa_roles
UNION ALL
SELECT 
    'aaa_user_roles' as table_name, 
    COUNT(*) as row_count 
FROM aaa.aaa_user_roles
UNION ALL
SELECT 
    'aaa_clients' as table_name, 
    COUNT(*) as row_count 
FROM aaa.aaa_clients
UNION ALL
SELECT 
    'aaa_password_reset_tokens' as table_name, 
    COUNT(*) as row_count 
FROM aaa.aaa_password_reset_tokens;

COMMIT;
