-- Database Export Generated on 2025-09-05 08:57:47.458027
-- Schema: aaa_test

-- Begin Transaction
BEGIN;

CREATE SCHEMA IF NOT EXISTS aaa_test;
SET search_path TO aaa_test;

-- Drop existing tables (in reverse dependency order)
DROP TABLE IF EXISTS aaa_test.aaa_password_reset_tokens CASCADE;
DROP TABLE IF EXISTS aaa_test.aaa_user_roles CASCADE;
DROP TABLE IF EXISTS aaa_test.aaa_clients CASCADE;
DROP TABLE IF EXISTS aaa_test.aaa_profiles CASCADE;
DROP TABLE IF EXISTS aaa_test.aaa_roles CASCADE;

-- Create tables
-- Table: aaa_roles
CREATE TABLE aaa_test.aaa_roles (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id)
);

-- Table: aaa_profiles
CREATE TABLE aaa_test.aaa_profiles (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT false,
    mfa_secret TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id)
);

-- Table: aaa_clients
CREATE TABLE aaa_test.aaa_clients (
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    name TEXT,
    scopes TEXT[],
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (client_id)
);

-- Table: aaa_user_roles
CREATE TABLE aaa_test.aaa_user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES aaa_test.aaa_profiles(id),
    FOREIGN KEY (role_id) REFERENCES aaa_test.aaa_roles(id)
);

-- Table: aaa_password_reset_tokens
CREATE TABLE aaa_test.aaa_password_reset_tokens (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES aaa_test.aaa_profiles(id)
);

-- Insert data
-- Data for table: aaa_roles (9 rows)
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('05766212-c660-478d-8a97-4a0668e374a7', 'manager', '2025-08-29T09:10:39.699215-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('1b7af0fb-fe6d-407d-b38c-545dae07dfdd', 'editor', '2025-08-29T09:10:39.699215-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('2d99be35-8b19-4870-a95d-44a5a31f7bb8', 'viewer', '2025-08-29T09:10:39.699215-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('d86b86aa-03f2-4208-96f5-9fd88d0f6336', 'group_admin', '2025-08-23T08:43:57.212975-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('1b591fc8-ac4d-48fb-bf62-bcba424a235b', 'firm_admin', '2025-08-23T08:43:57.212975-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('e7064b56-f331-4d93-89d0-a51eaa532503', 'super_user', '2025-08-23T08:43:57.212975-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('c94ad0d0-c5da-4fed-93e0-72059519f0ad', 'user', '2025-08-23T08:43:57.212975-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('f582e367-72dd-4f57-92b0-73c2e2e755ed', 'admin', '2025-08-23T08:44:27.747919-04:00');
INSERT INTO aaa_test.aaa_roles (id, name, created_at) VALUES ('fc026ba0-d094-4a57-a2e2-51ca3e6ba08b', 'account_admin', '2025-08-24T10:11:25.980111-04:00');

-- Data for table: aaa_profiles (5 rows)
INSERT INTO aaa_test.aaa_profiles (id, email, password_hash, first_name, middle_name, last_name, is_admin, mfa_secret, created_at, updated_at) VALUES ('d11ba7c1-5f3b-4906-a728-983364e7b12c', 'n_sivakumar@yahoo.com', '$2b$12$tWufgbsd4UFKvJAg21xTyuT6osZvZr.53U4uWyEWBey1g0vHpI74m', 'Sivakumar', 'Natarajan', 'Natarajan', TRUE, 'DIMYV5YF5GGECOPCCOZPTC5BDCZJJZEF', '2025-08-23T09:11:34.856828-04:00', '2025-08-23T09:11:34.856828-04:00');
INSERT INTO aaa_test.aaa_profiles (id, email, password_hash, first_name, middle_name, last_name, is_admin, mfa_secret, created_at, updated_at) VALUES ('07b72580-1b61-473b-a5b8-9bcd1b666034', 'sivakumarnatar@gmail.com', '$2b$12$F2QFD1Ez7egZN.n.vptcXedOU8.beiW.lCawDdLatVRqHvxbqrS7i', 'siva2', NULL, 'natarajan_updated_test', FALSE, NULL, '2025-08-27T23:11:15.315851-04:00', '2025-09-04T22:24:15.320849-04:00');
INSERT INTO aaa_test.aaa_profiles (id, email, password_hash, first_name, middle_name, last_name, is_admin, mfa_secret, created_at, updated_at) VALUES ('10f36d26-7346-47df-902b-1b4ac7374361', 'first.last@xc.co', '$2b$12$MWersTpIvDg5jL5LrRukF.abKAL4DB0JisTSGVE6ZNct9y3uxY9eG', 'first', NULL, 'last', FALSE, 'NU3CXUBNNGXJDVGR4YTAW3WKSJGA5F6Q', '2025-09-04T19:22:46.184213-04:00', '2025-09-04T22:24:19.297037-04:00');
INSERT INTO aaa_test.aaa_profiles (id, email, password_hash, first_name, middle_name, last_name, is_admin, mfa_secret, created_at, updated_at) VALUES ('2d53c6b4-0996-4348-94ac-936502a98844', 'sriramh@gmail.com', '$2b$12$A3AbwudD2oSSCES96CZzdeUbRYXxkedvPvv/IrhiHvVAnkDjNktcK', 'sriram', NULL, 'hariram', FALSE, NULL, '2025-09-04T07:55:07.196621-04:00', '2025-09-04T22:24:40.587300-04:00');
INSERT INTO aaa_test.aaa_profiles (id, email, password_hash, first_name, middle_name, last_name, is_admin, mfa_secret, created_at, updated_at) VALUES ('d027cdcd-d024-4343-87e4-9877c0239eba', 'ai.tools.test.2000@gmail.com', '$2b$12$Xl7igt6pDKpTxyfy.3Ya.Of4ADgW6uMU9dG8rcDVKE3tcp.OEq0Ra', 'ai tools', NULL, 'real local test5', FALSE, NULL, '2025-08-28T17:07:02.226524-04:00', '2025-09-04T19:03:43.083448-04:00');

-- Data for table: aaa_clients (1 rows)
INSERT INTO aaa_test.aaa_clients (client_id, client_secret, name, scopes, is_active, created_at, updated_at) VALUES ('my_test_client_id', 'my_test_client_secret', 'My Test Application', ARRAY['read:users', 'manage:users']::TEXT[], TRUE, '2025-08-23T08:46:00.298407-04:00', '2025-08-23T08:46:00.298407-04:00');

-- Data for table: aaa_user_roles (5 rows)
INSERT INTO aaa_test.aaa_user_roles (user_id, role_id, assigned_at) VALUES ('d11ba7c1-5f3b-4906-a728-983364e7b12c', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-08-24T10:54:06.682291-04:00');
INSERT INTO aaa_test.aaa_user_roles (user_id, role_id, assigned_at) VALUES ('2d53c6b4-0996-4348-94ac-936502a98844', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-09-04T07:55:07.202664-04:00');
INSERT INTO aaa_test.aaa_user_roles (user_id, role_id, assigned_at) VALUES ('d027cdcd-d024-4343-87e4-9877c0239eba', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-04T19:03:43.098971-04:00');
INSERT INTO aaa_test.aaa_user_roles (user_id, role_id, assigned_at) VALUES ('10f36d26-7346-47df-902b-1b4ac7374361', 'c94ad0d0-c5da-4fed-93e0-72059519f0ad', '2025-09-04T19:22:46.186668-04:00');
INSERT INTO aaa_test.aaa_user_roles (user_id, role_id, assigned_at) VALUES ('07b72580-1b61-473b-a5b8-9bcd1b666034', 'f582e367-72dd-4f57-92b0-73c2e2e755ed', '2025-09-04T21:43:39.003727-04:00');

-- Data for table: aaa_password_reset_tokens (5 rows)
INSERT INTO aaa_test.aaa_password_reset_tokens (id, user_id, token, expires_at, used, created_at) VALUES ('09ad7cda-d00d-4f40-a96b-560b8a01f9aa', 'd027cdcd-d024-4343-87e4-9877c0239eba', 'x8G2J-ZJFcriGnfBikNmj3rLltlByt6SagBHYZAahWo', '2025-09-02T18:06:45.797381-04:00', FALSE, '2025-09-02T17:36:45.797475-04:00');
INSERT INTO aaa_test.aaa_password_reset_tokens (id, user_id, token, expires_at, used, created_at) VALUES ('76e55e17-1da7-41cc-bd22-337042180ecf', 'd027cdcd-d024-4343-87e4-9877c0239eba', 'N2yg1ggCafw4iRm_B-tq3f34NaKVwlLUQMgd52E1fms', '2025-09-02T18:12:22.907998-04:00', TRUE, '2025-09-02T17:42:22.909032-04:00');
INSERT INTO aaa_test.aaa_password_reset_tokens (id, user_id, token, expires_at, used, created_at) VALUES ('ea12ed9e-c0ba-4a07-90d3-e5e01b3cc94a', 'd027cdcd-d024-4343-87e4-9877c0239eba', 'mJT4tqufHxrAY5axOuD_t458NEvwgZv4n_0RgfdUPDY', '2025-09-04T13:49:46.546140-04:00', TRUE, '2025-09-04T13:19:46.548073-04:00');
INSERT INTO aaa_test.aaa_password_reset_tokens (id, user_id, token, expires_at, used, created_at) VALUES ('cca13b90-edc2-4c40-b79b-3a75a141b9c2', 'd027cdcd-d024-4343-87e4-9877c0239eba', '-7aRGXsv1ONwQTvm9gA8ijMTYeM6885vydYqQ64rgcw', '2025-09-04T22:27:47.469567-04:00', FALSE, '2025-09-04T21:57:47.469696-04:00');
INSERT INTO aaa_test.aaa_password_reset_tokens (id, user_id, token, expires_at, used, created_at) VALUES ('bc52e72c-8d20-4733-b468-48558a972c61', 'd027cdcd-d024-4343-87e4-9877c0239eba', 'AKNzSpYCdPJvVriJOxhu6r18PzojMyjQEOi8L58Ff-0', '2025-09-04T22:55:20.956094-04:00', FALSE, '2025-09-04T22:25:20.957392-04:00');

-- Commit Transaction
COMMIT;

-- Export completed: 5 tables, 25 total rows