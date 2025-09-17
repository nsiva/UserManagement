# Database Management Scripts

This directory contains comprehensive scripts for managing the User Management System database across different environments.

## Quick Start

```bash
cd Api/scripts

# Generate complete database setup
python3 generate_database_setup.py

# Inspect existing database
python3 inspect_database.py "postgresql://user:pass@host:port/db"

# Export database data
python3 export_database_data.py --format json
```

## Files

- **`generate_database_setup.py`** - Generates complete database setup SQL script
- **`inspect_database.py`** - Inspects and validates existing database structure  
- **`export_database_data.py`** - Exports database data in multiple formats
- **`complete_database_setup.sql`** - Generated complete setup file
- **`README.md`** - This documentation file

## Usage

### Database Setup Generation

```bash
# Generate with default filename (public schema)
python3 generate_database_setup.py

# Generate with custom filename  
python3 generate_database_setup.py my_database_setup.sql

# Generate with custom schema
python3 generate_database_setup.py --schema user_management

# Generate with custom filename and schema
python3 generate_database_setup.py --schema company_data --output my_setup.sql

# Using bash wrapper
./db-tools.sh setup --schema user_mgmt
./db-tools.sh setup my_file.sql --schema test_env
```

### Database Inspection

```bash
# Inspect using connection string
python3 inspect_database.py "postgresql://user:pass@host:port/db"

# Inspect using environment variables
export DATABASE_URL="postgresql://user:pass@host:port/db"
python3 inspect_database.py

# Inspect local database
python3 inspect_database.py "postgresql://localhost/usertest_dev"
```

### Data Export

```bash
# Export as SQL INSERT statements
python3 export_database_data.py --format sql

# Export as JSON
python3 export_database_data.py --format json

# Export as CSV files
python3 export_database_data.py --format csv

# Export all formats
python3 export_database_data.py --format all --output /tmp/exports

# Export only sample data
python3 export_database_data.py --sample-only --format sql

# Include sensitive data (password hashes, secrets)
python3 export_database_data.py --include-sensitive --format json
```

### Apply to Database

```bash
# Apply to PostgreSQL database
psql -U username -d database_name -f complete_database_setup.sql

# Apply to Supabase (via psql)
psql "postgresql://user:pass@host:port/database" -f complete_database_setup.sql
```

## What's Included

The generated SQL script includes:

### 🗄️ **Complete Database Schema**
- All tables with proper constraints and relationships
- Indexes for optimal performance  
- Foreign key relationships
- Check constraints for data validation

### 🔧 **Database Functions & Triggers**
- Automatic timestamp updates
- Business unit hierarchy validation
- Circular reference prevention

### 👁️ **Views for Reporting**
- `vw_user_details` - User information with organizational context
- `vw_business_unit_hierarchy` - Hierarchical business unit structure

### 🔒 **Security Configuration**
- Row Level Security disabled for API access
- Proper indexes for authentication queries
- MFA and password reset table structure

### 📊 **Sample Data**
- Default roles (admin, super_user, firm_admin, group_admin, user)
- Sample organizations and business units
- Default admin user (admin@example.com / admin123)
- Test API client credentials

### 📝 **Documentation**
- Table and column comments
- Verification queries
- Setup completion confirmation

## Database Tables

| Table | Purpose |
|-------|---------|
| `aaa_profiles` | User accounts and authentication |
| `aaa_roles` | System roles (admin, user, etc.) |
| `aaa_user_roles` | User-role assignments |
| `aaa_organizations` | Companies/organizations |
| `aaa_business_units` | Departments within organizations |
| `aaa_user_business_units` | User assignments to business units |
| `aaa_clients` | API client credentials |
| `aaa_email_otps` | Email-based MFA tokens |
| `aaa_password_reset_tokens` | Password reset functionality |

## Environment Setup Examples

### Local Development

```bash
# Create local PostgreSQL database
createdb usertest_dev

# Apply setup
python generate_database_setup.py local_dev_setup.sql
psql -d usertest_dev -f local_dev_setup.sql
```

### Production Deployment

```bash
# Generate production setup (review before applying!)
python generate_database_setup.py production_setup.sql

# Review the generated file first
less production_setup.sql

# Apply to production database
psql "postgresql://user:pass@prod-host:5432/prod_db" -f production_setup.sql
```

### Staging Environment

```bash
# Generate for staging
python generate_database_setup.py staging_setup.sql
psql "postgresql://user:pass@staging-host:5432/staging_db" -f staging_setup.sql
```

## Security Notes

⚠️ **Important**: The generated script includes default credentials:

- **Admin User**: admin@example.com / admin123
- **API Client**: sample_client_id / sample_client_secret_change_in_production

**Always change these in production environments!**

## Customization

You can modify `generate_database_setup.py` to:

- Add custom sample data
- Include additional tables
- Modify default configurations
- Add custom functions or triggers

## Verification

After running the setup, verify with:

```sql
-- Check table count
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'aaa_%';

-- Verify sample data
SELECT 'Roles' as entity, COUNT(*) as count FROM aaa_roles
UNION ALL
SELECT 'Organizations', COUNT(*) FROM aaa_organizations
UNION ALL  
SELECT 'Business Units', COUNT(*) FROM aaa_business_units
UNION ALL
SELECT 'Users', COUNT(*) FROM aaa_profiles;
```

## Troubleshooting

### Common Issues

**Permission denied**
```bash
# Make sure you have CREATE privileges
GRANT CREATE ON DATABASE your_db TO your_user;
```

**Extension not found**
```sql
-- Enable UUID extension manually if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

**Foreign key violations**
```sql
-- Check existing data that might conflict
SELECT table_name, constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY';
```

## Migration from Existing Database

If you have an existing database:

1. **Backup first**: `pg_dump your_db > backup.sql`
2. **Check for conflicts**: Review existing table names
3. **Modify script**: Remove conflicting `CREATE TABLE` statements
4. **Test on copy**: Always test on a database copy first

## Support

For issues with the database setup:

1. Check the generated SQL file for syntax errors
2. Verify PostgreSQL version compatibility (requires 12+)
3. Ensure proper database permissions
4. Review the application logs for connection issues

## Script Details

### 🔧 generate_database_setup.py

**Purpose**: Creates a complete SQL script for database setup across environments.

**Features**:
- All table definitions with constraints
- Indexes for performance optimization
- Functions and triggers for business logic
- Database views for reporting
- Sample data for testing
- Comprehensive comments and documentation

**Output**: Single SQL file that can recreate the entire database structure.

### 🔍 inspect_database.py

**Purpose**: Validates and reports on existing database structure.

**Features**:
- Table structure analysis
- Data count verification
- Constraint and index verification
- Function and view detection
- Sample admin user check
- Health check with issue reporting

**Requirements**: `pip install asyncpg`

**Output**: Detailed console report of database status.

### 📤 export_database_data.py

**Purpose**: Exports database data in multiple formats for backup or migration.

**Features**:
- SQL INSERT statements
- JSON format with metadata
- CSV files (one per table)
- Sample-only export option
- Sensitive data filtering
- Export statistics

**Requirements**: `pip install asyncpg`

**Output**: Data files in specified format(s).

## Dependencies

### Python Requirements

```bash
# For database inspection and export scripts
pip install asyncpg

# Optional: for enhanced JSON handling
pip install orjson
```

### Environment Variables

The inspection and export scripts support these environment variables:

```bash
# Primary connection (recommended)
export DATABASE_URL="postgresql://user:pass@host:port/database"

# Alternative: Supabase URL
export SUPABASE_URL="postgresql://postgres:pass@host:port/postgres"

# Individual components (fallback)
export DB_HOST="localhost"
export DB_PORT="5432"  
export DB_USER="postgres"
export DB_PASSWORD="password"
export DB_NAME="usertest_dev"
```

## Use Cases

### 🚀 New Environment Setup
```bash
# Generate setup script (public schema)
python3 generate_database_setup.py production_setup.sql

# Generate setup script (custom schema)
python3 generate_database_setup.py production_setup.sql --schema user_mgmt

# Review and apply
psql -d production_db -f production_setup.sql

# Verify setup
python3 inspect_database.py
```

### 🗂️ Schema-Specific Setup
```bash
# Development environment with custom schema
python3 generate_database_setup.py dev_setup.sql --schema dev_users
psql -d dev_db -f dev_setup.sql

# Production with company-specific schema
python3 generate_database_setup.py prod_setup.sql --schema company_users
psql -d prod_db -f prod_setup.sql

# Testing environment
./db-tools.sh setup test_setup.sql --schema test_env
psql -d test_db -f test_setup.sql
```

### 🔄 Environment Migration
```bash
# Export from source
python3 export_database_data.py --format all --output migration_data/

# Setup target environment  
python3 generate_database_setup.py target_setup.sql
psql -d target_db -f target_setup.sql

# Import data (manual step - review exported SQL)
```

### 🧪 Testing & Development
```bash
# Setup test database with sample data
python3 generate_database_setup.py test_setup.sql
psql -d test_db -f test_setup.sql

# Export sample data only
python3 export_database_data.py --sample-only --format json
```

### 📊 Audit & Compliance
```bash
# Full database inspection
python3 inspect_database.py > database_audit_$(date +%Y%m%d).txt

# Export all data (including sensitive) for backup
python3 export_database_data.py --include-sensitive --format all
```

## License

These scripts are part of the User Management System project.