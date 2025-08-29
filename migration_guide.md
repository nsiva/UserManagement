# Local PostgreSQL Migration Guide

This guide helps you migrate from Supabase to a local PostgreSQL setup while keeping all your data and maintaining the same schema structure.

## 🎯 Overview

Your User Management system will be migrated from Supabase to local PostgreSQL with:
- **Schema**: All tables moved to `aaa` schema for organization
- **Data**: Complete export/import of all existing users, roles, and settings
- **Features**: JWT authentication, MFA, role-based access, password reset functionality
- **Compatibility**: Your existing FastAPI application will work with minimal changes

## 📋 Prerequisites

### 1. Local PostgreSQL Setup
```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb usermanagement

# Connect to verify
psql usermanagement
```

### 2. Python Environment
```bash
cd /Users/siva/projects/UserManagement
pip install supabase python-dotenv psycopg2-binary
```

### 3. Environment Variables
Ensure your `/Users/siva/projects/UserManagement/Api/.env` has:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_service_role_key
```

## 🚀 Migration Steps

### Step 1: Preview Current Data (Optional)
```bash
cd /Users/siva/projects/UserManagement
python3 export_current_data.py preview
```

This shows you:
- How many users, roles, clients you have
- MFA status of users
- Sample data structure

### Step 2: Create Local Schema
```bash
cd /Users/siva/projects/UserManagement
psql usermanagement -f local_postgresql_setup.sql
```

This creates:
- ✅ `aaa` schema
- ✅ All 5 tables: `aaa_profiles`, `aaa_roles`, `aaa_user_roles`, `aaa_clients`, `aaa_password_reset_tokens`
- ✅ Proper indexes and constraints
- ✅ Default roles and test client
- ✅ Triggers for auto-updating timestamps

### Step 3: Export Your Current Data
```bash
cd /Users/siva/projects/UserManagement
python3 export_current_data.py
```

This generates:
- `exported_data.sql` with all your current Supabase data
- Proper SQL formatting with UUID handling
- Maintains referential integrity

### Step 4: Import Your Data
```bash
cd /Users/siva/projects/UserManagement
psql usermanagement -f exported_data.sql
```

### Step 5: Verify Migration
```sql
-- Connect to your database
psql usermanagement

-- Set search path
SET search_path TO aaa, public;

-- Check all your data is there
SELECT 'profiles' as table_name, COUNT(*) as count FROM aaa_profiles
UNION ALL
SELECT 'roles' as table_name, COUNT(*) as count FROM aaa_roles
UNION ALL
SELECT 'user_roles' as table_name, COUNT(*) as count FROM aaa_user_roles
UNION ALL
SELECT 'clients' as table_name, COUNT(*) as count FROM aaa_clients;

-- Test a specific user
SELECT p.email, p.is_admin, 
       CASE WHEN p.mfa_secret IS NOT NULL THEN 'MFA Enabled' ELSE 'MFA Disabled' END as mfa_status,
       STRING_AGG(r.name, ', ') as roles
FROM aaa_profiles p
LEFT JOIN aaa_user_roles ur ON p.id = ur.user_id
LEFT JOIN aaa_roles r ON ur.role_id = r.id
GROUP BY p.id, p.email, p.is_admin, p.mfa_secret;
```

## 🔧 Update Your Application

### Option 1: Use Schema in Connection String
Update your database connection:
```python
# In database.py or your connection config
DATABASE_URL = "postgresql://user:password@localhost:5432/usermanagement?search_path=aaa"
```

### Option 2: Update Table References
If you prefer to keep explicit schema names:
```python
# Update repository classes to use aaa.table_name
query = "SELECT * FROM aaa.aaa_profiles WHERE email = $1"
```

### Option 3: Set Default Schema
Add this to your application startup:
```python
# Set default schema for the session
await conn.execute("SET search_path TO aaa, public")
```

## 📁 Files Generated

1. **`local_postgresql_setup.sql`** - Complete schema creation script
   - Creates `aaa` schema
   - All tables with proper relationships
   - Indexes and constraints
   - Default data (roles, test client)

2. **`export_current_data.py`** - Data export script
   - Connects to your Supabase
   - Exports all current data
   - Generates PostgreSQL-compatible SQL

3. **`exported_data.sql`** - Your actual data (generated after running export)
   - All your users with encrypted passwords
   - MFA secrets preserved
   - Role assignments maintained
   - API client credentials

4. **`migration_guide.md`** - This guide

## 🛠 Database Features Included

### Tables Structure
- **aaa_profiles**: Users with bcrypt passwords, MFA secrets, profile info
- **aaa_roles**: Role definitions (admin, user, manager, etc.)
- **aaa_user_roles**: Many-to-many user-role relationships
- **aaa_clients**: API client credentials for OAuth-style auth
- **aaa_password_reset_tokens**: Secure password reset functionality

### Performance Features
- **Indexes**: All critical queries optimized
- **Constraints**: Email validation, business rule enforcement
- **Triggers**: Auto-updating timestamps
- **Foreign Keys**: Proper referential integrity with CASCADE deletes

### Security Features
- **Password Hashing**: Bcrypt-hashed passwords preserved exactly
- **MFA Secrets**: TOTP secrets maintained for existing users
- **API Clients**: Client credentials preserved
- **Row Security**: Proper access control patterns

## 🔒 Security Considerations

### Passwords
- ✅ All bcrypt password hashes are preserved exactly
- ✅ No plaintext passwords in the migration
- ✅ Users can continue logging in with existing passwords

### MFA (Multi-Factor Authentication)
- ✅ TOTP secrets preserved for users who have MFA enabled
- ✅ QR codes can be regenerated if needed
- ✅ MFA setup process remains identical

### API Authentication
- ✅ Client credentials preserved
- ✅ Scopes and permissions maintained
- ✅ JWT signing continues to work

## 🧪 Testing Your Migration

### 1. Test Database Connection
```bash
cd /Users/siva/projects/UserManagement/Api
python3 -c "
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
# Update this connection string for your PostgreSQL
conn = psycopg2.connect('postgresql://user:password@localhost:5432/usermanagement')
cur = conn.cursor()
cur.execute('SET search_path TO aaa, public')
cur.execute('SELECT COUNT(*) FROM aaa_profiles')
print(f'Users in database: {cur.fetchone()[0]}')
conn.close()
"
```

### 2. Test API Endpoints
```bash
cd /Users/siva/projects/UserManagement/Api

# Update database configuration to point to PostgreSQL
# Then start the API
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Test login with existing user
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your_existing_user@email.com", "password": "their_password"}'
```

### 3. Test MFA (if enabled)
```bash
# If user has MFA enabled, login will return 402 status
# Then verify with TOTP code:
curl -X POST "http://localhost:8001/auth/mfa/verify" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@email.com", "mfa_code": "123456"}'
```

## 🚨 Troubleshooting

### Common Issues

**1. Connection Error**
```
Error: connection to server at "localhost" (::1), port 5432 failed
```
**Solution**: Ensure PostgreSQL is running: `brew services start postgresql`

**2. Schema Not Found**
```
Error: schema "aaa" does not exist
```
**Solution**: Run `local_postgresql_setup.sql` first

**3. Permission Denied**
```
Error: permission denied for schema aaa
```
**Solution**: Ensure your PostgreSQL user has proper permissions:
```sql
GRANT ALL ON SCHEMA aaa TO your_username;
GRANT ALL ON ALL TABLES IN SCHEMA aaa TO your_username;
```

**4. Data Not Found After Migration**
```
Error: User not found in database
```
**Solution**: Check search path is set correctly:
```sql
SET search_path TO aaa, public;
SHOW search_path;
```

## 🎉 Migration Complete!

After successful migration, you'll have:

- ✅ Local PostgreSQL with all your data
- ✅ Same authentication system (JWT + MFA)
- ✅ All user passwords working
- ✅ Role-based access control preserved
- ✅ API client authentication working
- ✅ Password reset functionality ready
- ✅ Organized schema structure
- ✅ Optimized database performance

Your FastAPI application should work exactly the same, but now running on local PostgreSQL instead of Supabase!

## 📞 Need Help?

If you encounter issues:
1. Check the verification queries in Step 5
2. Review the troubleshooting section above
3. Examine the generated `exported_data.sql` for any obvious issues
4. Test individual components (auth, MFA, admin functions) separately