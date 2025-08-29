# Manual Supabase Data Export Guide

Generated on: 2025-08-29 08:36:43.061411

## Overview

This guide helps you manually export data from your Supabase database tables:
- aaa_profiles (users)
- aaa_roles (role definitions)
- aaa_user_roles (user-role assignments)
- aaa_clients (API clients)
- aaa_password_reset_tokens (password reset tokens)

## Quick Start

### Option 1: Automated Export (Recommended)
```bash
cd /Users/siva/projects/UserManagement/Api
python3 query_current_data.py     # Inspect current data
python3 export_supabase_data.py   # Generate INSERT statements
```

### Option 2: Manual Export
1. Open Supabase Dashboard → SQL Editor
2. Run queries from: sql_queries/export_queries.sql
3. Export results as CSV or copy data
4. Convert to INSERT statements manually

## Database Schema Reference

### Table Dependencies (Import Order)
1. **aaa_roles** - No dependencies
2. **aaa_profiles** - No dependencies
3. **aaa_user_roles** - Depends on aaa_profiles, aaa_roles
4. **aaa_clients** - No dependencies
5. **aaa_password_reset_tokens** - Depends on aaa_profiles

### Column Information

#### aaa_profiles
- id: UUID (Primary Key)
- email: TEXT (Unique)
- password_hash: TEXT (bcrypt hash)
- first_name, middle_name, last_name: TEXT (Optional)
- is_admin: BOOLEAN
- mfa_secret: TEXT (Optional TOTP secret)
- created_at, updated_at: TIMESTAMP

#### aaa_roles
- id: UUID (Primary Key)
- name: TEXT (Unique - e.g., 'admin', 'user', 'manager')
- created_at: TIMESTAMP

#### aaa_user_roles
- user_id: UUID (Foreign Key → aaa_profiles.id)
- role_id: UUID (Foreign Key → aaa_roles.id)
- assigned_at: TIMESTAMP

#### aaa_clients
- client_id: TEXT (Primary Key)
- client_secret: TEXT
- name: TEXT (Optional)
- scopes: TEXT[] (PostgreSQL array)
- is_active: BOOLEAN
- created_at, updated_at: TIMESTAMP

#### aaa_password_reset_tokens
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key → aaa_profiles.id)
- token: TEXT (Unique)
- expires_at: TIMESTAMP
- used: BOOLEAN
- created_at: TIMESTAMP

## Sample INSERT Statements

Here are examples of the INSERT statement format you'll need:

```sql
-- Sample role
INSERT INTO aaa_roles (id, name, created_at) VALUES 
('550e8400-e29b-41d4-a716-446655440000', 'admin', '2024-01-01 00:00:00+00');

-- Sample user
INSERT INTO aaa_profiles (id, email, password_hash, is_admin, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'admin@example.com', '$2b$12$...', true, '2024-01-01 00:00:00+00');

-- Sample user-role assignment
INSERT INTO aaa_user_roles (user_id, role_id, assigned_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', '2024-01-01 00:00:00+00');
```

## Troubleshooting

### Common Issues
1. **UUID Format**: Ensure UUIDs are properly formatted strings
2. **Password Hashes**: Don't modify bcrypt hashes during export
3. **Timestamps**: Use ISO format with timezone (YYYY-MM-DD HH:MM:SS+00)
4. **Arrays**: PostgreSQL arrays use ARRAY['item1', 'item2'] syntax
5. **Foreign Keys**: Import parent tables (roles, profiles) before child tables

### Verification Queries
After importing, run these to verify:

```sql
-- Check record counts match
SELECT COUNT(*) FROM aaa_profiles;
SELECT COUNT(*) FROM aaa_roles;
SELECT COUNT(*) FROM aaa_user_roles;

-- Verify relationships
SELECT p.email, r.name
FROM aaa_profiles p
JOIN aaa_user_roles ur ON p.id = ur.user_id
JOIN aaa_roles r ON ur.role_id = r.id;
```
