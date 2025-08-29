#!/usr/bin/env python3

"""
Generate SQL Export Queries for Supabase

This script generates the SQL queries you can run directly in Supabase SQL Editor
to export your data. Use this if you prefer to manually run queries instead of 
using the Python export script.

Usage:
    python3 generate_export_queries.py
"""

import os
from datetime import datetime


def generate_export_queries():
    """Generate SQL queries for data export."""
    
    queries = {
        "inspection_queries": [
            {
                "name": "Count all records in each table",
                "description": "Get overview of data volume",
                "query": """
-- Get record counts from all tables
SELECT 'aaa_profiles' as table_name, COUNT(*) as record_count FROM aaa_profiles
UNION ALL
SELECT 'aaa_roles', COUNT(*) FROM aaa_roles  
UNION ALL
SELECT 'aaa_user_roles', COUNT(*) FROM aaa_user_roles
UNION ALL  
SELECT 'aaa_clients', COUNT(*) FROM aaa_clients
UNION ALL
SELECT 'aaa_password_reset_tokens', COUNT(*) FROM aaa_password_reset_tokens;"""
            },
            {
                "name": "User overview with roles",
                "description": "See all users with their roles and MFA status",
                "query": """
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
ORDER BY p.created_at;"""
            }
        ],
        
        "export_queries": [
            {
                "name": "Export aaa_roles",
                "description": "Export all roles (run this first)",
                "query": "SELECT * FROM aaa_roles ORDER BY created_at;"
            },
            {
                "name": "Export aaa_profiles", 
                "description": "Export all user profiles",
                "query": "SELECT * FROM aaa_profiles ORDER BY created_at;"
            },
            {
                "name": "Export aaa_user_roles",
                "description": "Export user-role relationships", 
                "query": "SELECT * FROM aaa_user_roles ORDER BY assigned_at;"
            },
            {
                "name": "Export aaa_clients",
                "description": "Export API clients",
                "query": "SELECT * FROM aaa_clients ORDER BY created_at;"
            },
            {
                "name": "Export aaa_password_reset_tokens",
                "description": "Export password reset tokens",
                "query": "SELECT * FROM aaa_password_reset_tokens ORDER BY created_at;"
            }
        ]
    }
    
    # Create queries directory
    queries_dir = "sql_queries"
    os.makedirs(queries_dir, exist_ok=True)
    
    print("🔧 GENERATING SUPABASE EXPORT QUERIES")
    print("=" * 60)
    
    # Generate inspection queries file
    inspection_content = [
        "-- Supabase Data Inspection Queries",
        f"-- Generated on: {datetime.now()}",
        "-- Run these queries in Supabase SQL Editor to inspect your data",
        "",
        "-- IMPORTANT: These are READ-ONLY queries safe to run on production",
        "",
        "=" * 80,
        ""
    ]
    
    for query_info in queries["inspection_queries"]:
        inspection_content.extend([
            f"-- {query_info['name']}",
            f"-- {query_info['description']}",
            query_info['query'].strip(),
            "",
            "-" * 60,
            ""
        ])
    
    inspection_file = os.path.join(queries_dir, "inspection_queries.sql")
    with open(inspection_file, 'w') as f:
        f.write('\n'.join(inspection_content))
    
    print(f"📋 Created inspection queries: {inspection_file}")
    
    # Generate export queries file
    export_content = [
        "-- Supabase Data Export Queries",
        f"-- Generated on: {datetime.now()}",
        "-- Run these queries in Supabase SQL Editor to export your data",
        "",
        "-- INSTRUCTIONS:",
        "-- 1. Run each query in order (dependencies matter)",
        "-- 2. Copy the results and format as INSERT statements",
        "-- 3. Or use the Python export script for automatic formatting",
        "",
        "=" * 80,
        ""
    ]
    
    for i, query_info in enumerate(queries["export_queries"], 1):
        export_content.extend([
            f"-- {i}. {query_info['name']}",
            f"-- {query_info['description']}",
            query_info['query'].strip(),
            "",
            "-" * 60,
            ""
        ])
    
    export_file = os.path.join(queries_dir, "export_queries.sql")
    with open(export_file, 'w') as f:
        f.write('\n'.join(export_content))
    
    print(f"📤 Created export queries: {export_file}")
    
    # Generate a comprehensive manual export guide
    guide_content = [
        "# Manual Supabase Data Export Guide",
        "",
        f"Generated on: {datetime.now()}",
        "",
        "## Overview",
        "",
        "This guide helps you manually export data from your Supabase database tables:",
        "- aaa_profiles (users)",
        "- aaa_roles (role definitions)",  
        "- aaa_user_roles (user-role assignments)",
        "- aaa_clients (API clients)",
        "- aaa_password_reset_tokens (password reset tokens)",
        "",
        "## Quick Start",
        "",
        "### Option 1: Automated Export (Recommended)",
        "```bash",
        "cd /Users/siva/projects/UserManagement/Api",
        "python3 query_current_data.py     # Inspect current data",
        "python3 export_supabase_data.py   # Generate INSERT statements",
        "```",
        "",
        "### Option 2: Manual Export",
        "1. Open Supabase Dashboard → SQL Editor",
        f"2. Run queries from: {export_file}",
        "3. Export results as CSV or copy data",
        "4. Convert to INSERT statements manually",
        "",
        "## Database Schema Reference",
        "",
        "### Table Dependencies (Import Order)",
        "1. **aaa_roles** - No dependencies",
        "2. **aaa_profiles** - No dependencies", 
        "3. **aaa_user_roles** - Depends on aaa_profiles, aaa_roles",
        "4. **aaa_clients** - No dependencies",
        "5. **aaa_password_reset_tokens** - Depends on aaa_profiles",
        "",
        "### Column Information",
        "",
        "#### aaa_profiles",
        "- id: UUID (Primary Key)",
        "- email: TEXT (Unique)",
        "- password_hash: TEXT (bcrypt hash)",
        "- first_name, middle_name, last_name: TEXT (Optional)",
        "- is_admin: BOOLEAN",
        "- mfa_secret: TEXT (Optional TOTP secret)",
        "- created_at, updated_at: TIMESTAMP",
        "",
        "#### aaa_roles", 
        "- id: UUID (Primary Key)",
        "- name: TEXT (Unique - e.g., 'admin', 'user', 'manager')",
        "- created_at: TIMESTAMP",
        "",
        "#### aaa_user_roles",
        "- user_id: UUID (Foreign Key → aaa_profiles.id)",
        "- role_id: UUID (Foreign Key → aaa_roles.id)", 
        "- assigned_at: TIMESTAMP",
        "",
        "#### aaa_clients",
        "- client_id: TEXT (Primary Key)",
        "- client_secret: TEXT",
        "- name: TEXT (Optional)",
        "- scopes: TEXT[] (PostgreSQL array)",
        "- is_active: BOOLEAN",
        "- created_at, updated_at: TIMESTAMP",
        "",
        "#### aaa_password_reset_tokens",
        "- id: UUID (Primary Key)",
        "- user_id: UUID (Foreign Key → aaa_profiles.id)",
        "- token: TEXT (Unique)",
        "- expires_at: TIMESTAMP",
        "- used: BOOLEAN", 
        "- created_at: TIMESTAMP",
        "",
        "## Sample INSERT Statements",
        "",
        "Here are examples of the INSERT statement format you'll need:",
        "",
        "```sql",
        "-- Sample role",
        "INSERT INTO aaa_roles (id, name, created_at) VALUES ",
        "('550e8400-e29b-41d4-a716-446655440000', 'admin', '2024-01-01 00:00:00+00');",
        "",
        "-- Sample user", 
        "INSERT INTO aaa_profiles (id, email, password_hash, is_admin, created_at) VALUES",
        "('550e8400-e29b-41d4-a716-446655440001', 'admin@example.com', '$2b$12$...', true, '2024-01-01 00:00:00+00');",
        "",
        "-- Sample user-role assignment",
        "INSERT INTO aaa_user_roles (user_id, role_id, assigned_at) VALUES",
        "('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', '2024-01-01 00:00:00+00');",
        "```",
        "",
        "## Troubleshooting",
        "",
        "### Common Issues",
        "1. **UUID Format**: Ensure UUIDs are properly formatted strings",
        "2. **Password Hashes**: Don't modify bcrypt hashes during export",
        "3. **Timestamps**: Use ISO format with timezone (YYYY-MM-DD HH:MM:SS+00)",
        "4. **Arrays**: PostgreSQL arrays use ARRAY['item1', 'item2'] syntax",
        "5. **Foreign Keys**: Import parent tables (roles, profiles) before child tables",
        "",
        "### Verification Queries",
        "After importing, run these to verify:",
        "",
        "```sql",
        "-- Check record counts match",
        "SELECT COUNT(*) FROM aaa_profiles;",
        "SELECT COUNT(*) FROM aaa_roles;",
        "SELECT COUNT(*) FROM aaa_user_roles;",
        "",
        "-- Verify relationships",
        "SELECT p.email, r.name",
        "FROM aaa_profiles p",
        "JOIN aaa_user_roles ur ON p.id = ur.user_id", 
        "JOIN aaa_roles r ON ur.role_id = r.id;",
        "```",
        ""
    ]
    
    guide_file = os.path.join(queries_dir, "EXPORT_GUIDE.md")
    with open(guide_file, 'w') as f:
        f.write('\n'.join(guide_content))
    
    print(f"📖 Created export guide: {guide_file}")
    
    print("\n" + "=" * 60)
    print("✅ QUERY GENERATION COMPLETED")
    print("=" * 60)
    print(f"📁 Files created in: {os.path.abspath(queries_dir)}")
    print("\n🚀 Next Steps:")
    print("1. Run inspection queries to see current data:")
    print(f"   Open {inspection_file} in Supabase SQL Editor")
    print("\n2. For automated export (recommended):")
    print("   python3 query_current_data.py")
    print("   python3 export_supabase_data.py")
    print("\n3. For manual export:")
    print(f"   Follow instructions in {guide_file}")


def main():
    """Main function."""
    generate_export_queries()


if __name__ == "__main__":
    main()