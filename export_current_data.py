#!/usr/bin/env python3
"""
Export Current Supabase Data for Local PostgreSQL Migration

This script connects to your existing Supabase database and exports all data
from the aaa_* tables, generating SQL INSERT statements that can be run
on your local PostgreSQL setup with the 'aaa' schema.

Usage:
    python3 export_current_data.py

Output:
    - Creates 'exported_data.sql' with all your current data
    - Handles proper SQL escaping and UUID formatting
    - Maintains referential integrity order
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

try:
    from supabase import create_client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages. Install with:")
    print("pip install supabase python-dotenv")
    print(f"Error: {e}")
    sys.exit(1)

# Load environment variables - look for .env in Api directory
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(script_dir, 'Api')
env_path = os.path.join(api_dir, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to current directory
    load_dotenv()

class DataExporter:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")
            sys.exit(1)
            
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.output_file = "exported_data.sql"
        
    def safe_sql_value(self, value: Any) -> str:
        """Convert Python value to safe SQL string"""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return str(value).upper()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape single quotes by doubling them
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, list):
            # Handle PostgreSQL arrays (like scopes)
            if not value:
                return "ARRAY[]::TEXT[]"
            # Fix f-string backslash issue by using separate variable
            escaped_items = []
            for item in value:
                escaped_item = str(item).replace("'", "''")
                escaped_items.append(f"'{escaped_item}'")
            return f"ARRAY[{', '.join(escaped_items)}]"
        elif isinstance(value, dict):
            # Handle JSON fields if any
            json_str = json.dumps(value).replace("'", "''")
            return f"'{json_str}'::JSONB"
        else:
            # Convert to string and escape
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    def export_table(self, table_name: str) -> List[str]:
        """Export data from a single table and return SQL INSERT statements"""
        try:
            print(f"Exporting {table_name}...")
            response = self.client.from_(table_name).select("*").execute()
            
            if not response.data:
                print(f"  No data found in {table_name}")
                return []
                
            # Get column names from first row
            columns = list(response.data[0].keys())
            
            insert_statements = []
            
            for row in response.data:
                values = [self.safe_sql_value(row.get(col)) for col in columns]
                
                insert_sql = f"""INSERT INTO aaa.{table_name} ({', '.join(columns)}) 
VALUES ({', '.join(values)});"""
                
                insert_statements.append(insert_sql)
            
            print(f"  Exported {len(insert_statements)} rows from {table_name}")
            return insert_statements
            
        except Exception as e:
            print(f"Error exporting {table_name}: {e}")
            return []

    def export_all_data(self):
        """Export all data from aaa_* tables in dependency order"""
        
        # Tables in dependency order (tables with no dependencies first)
        tables_order = [
            "aaa_roles",           # No dependencies
            "aaa_profiles",        # No dependencies  
            "aaa_clients",         # No dependencies
            "aaa_user_roles",      # Depends on profiles and roles
            "aaa_password_reset_tokens"  # Depends on profiles
        ]
        
        all_sql_statements = []
        
        # Add header
        header = f"""-- ========================================================================
-- EXPORTED DATA FROM SUPABASE
-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================================================
-- This file contains all your current data from Supabase aaa_* tables
-- Run this AFTER creating the schema with local_postgresql_setup.sql
-- ========================================================================

-- Set search path to use the aaa schema
SET search_path TO aaa, public;

-- Disable triggers during bulk insert for better performance
SET session_replication_role = replica;

"""
        all_sql_statements.append(header)
        
        # Export each table
        for table_name in tables_order:
            table_statements = self.export_table(table_name)
            
            if table_statements:
                section_header = f"\n-- ========================================================================\n-- {table_name.upper()} DATA\n-- ========================================================================\n"
                all_sql_statements.append(section_header)
                all_sql_statements.extend(table_statements)
        
        # Add footer
        footer = f"""
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
"""
        all_sql_statements.append(footer)
        
        # Write to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_sql_statements))
        
        print(f"\n✅ Data export complete!")
        print(f"📄 Generated: {self.output_file}")
        print(f"\nTo use this export:")
        print(f"1. First run: local_postgresql_setup.sql (creates schema)")
        print(f"2. Then run: {self.output_file} (imports your data)")

    def preview_data(self):
        """Show a preview of current data without exporting"""
        print("🔍 PREVIEW: Current data in your Supabase database\n")
        
        tables = ["aaa_roles", "aaa_profiles", "aaa_clients", "aaa_user_roles", "aaa_password_reset_tokens"]
        
        for table_name in tables:
            try:
                response = self.client.from_(table_name).select("*", count="exact").limit(3).execute()
                count = response.count if hasattr(response, 'count') else len(response.data)
                
                print(f"📊 {table_name}: {count} total rows")
                
                if response.data:
                    print(f"   Sample columns: {', '.join(list(response.data[0].keys()))}")
                    
                    # Show specific info based on table
                    if table_name == "aaa_profiles":
                        for row in response.data[:2]:
                            mfa_status = "✅ Enabled" if row.get('mfa_secret') else "❌ Disabled"
                            admin_status = "👑 Admin" if row.get('is_admin') else "👤 User"
                            print(f"   - {row.get('email')} | {admin_status} | MFA: {mfa_status}")
                    
                    elif table_name == "aaa_roles":
                        roles = [row.get('name') for row in response.data]
                        print(f"   - Roles: {', '.join(roles)}")
                        
                    elif table_name == "aaa_clients":
                        for row in response.data[:2]:
                            status = "🟢 Active" if row.get('is_active') else "🔴 Inactive"
                            scopes = row.get('scopes', [])
                            print(f"   - {row.get('client_id')} | {status} | Scopes: {len(scopes)}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error accessing {table_name}: {e}\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        # Preview mode - just show current data
        exporter = DataExporter()
        exporter.preview_data()
    else:
        # Full export mode
        print("🚀 Starting Supabase data export for local PostgreSQL migration...\n")
        
        exporter = DataExporter()
        exporter.export_all_data()

if __name__ == "__main__":
    main()