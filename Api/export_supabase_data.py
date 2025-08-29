#!/usr/bin/env python3

"""
Supabase Data Export Script for User Management System

This script connects to your Supabase database and exports all data from the
aaa_* tables, generating INSERT statements that can be used to populate a 
local PostgreSQL database.

Tables exported:
- aaa_profiles (users)
- aaa_roles (role definitions) 
- aaa_user_roles (user-role assignments)
- aaa_clients (API clients)
- aaa_password_reset_tokens (password reset tokens)

Usage:
    python3 export_supabase_data.py
    
The script will create SQL files in the exports/ directory.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseDataExporter:
    """Export data from Supabase tables to SQL INSERT statements."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.service_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.service_key)
        self.export_dir = "exports"
        
        # Create export directory if it doesn't exist
        os.makedirs(self.export_dir, exist_ok=True)
        
    def export_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Export all data from a specific table."""
        try:
            print(f"📊 Exporting data from {table_name}...")
            response = self.client.from_(table_name).select('*').execute()
            
            if response.data:
                print(f"✅ Found {len(response.data)} records in {table_name}")
                return response.data
            else:
                print(f"⚠️  No data found in {table_name}")
                return []
                
        except Exception as e:
            print(f"❌ Error exporting {table_name}: {e}")
            return []
    
    def format_sql_value(self, value: Any) -> str:
        """Format a Python value for SQL insertion."""
        if value is None:
            return 'NULL'
        elif isinstance(value, str):
            # Escape single quotes in strings
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            # Handle PostgreSQL arrays (like scopes in aaa_clients)
            if not value:
                return "ARRAY[]::text[]"
            formatted_items = [self.format_sql_value(item) for item in value]
            return f"ARRAY[{', '.join(formatted_items)}]"
        elif isinstance(value, dict):
            # Handle JSON fields
            return f"'{json.dumps(value)}'"
        else:
            # For datetime and other types, convert to string
            return f"'{str(value)}'"
    
    def generate_insert_statements(self, table_name: str, data: List[Dict[str, Any]]) -> str:
        """Generate SQL INSERT statements for table data."""
        if not data:
            return f"-- No data to insert for {table_name}\n"
        
        sql_statements = []
        sql_statements.append(f"-- Data export for {table_name}")
        sql_statements.append(f"-- Generated on: {datetime.now()}")
        sql_statements.append(f"-- Record count: {len(data)}")
        sql_statements.append("")
        
        # Get column names from first record
        columns = list(data[0].keys())
        
        # Generate INSERT statements
        for record in data:
            values = []
            for column in columns:
                value = record.get(column)
                values.append(self.format_sql_value(value))
            
            values_str = ', '.join(values)
            columns_str = ', '.join(columns)
            
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
            sql_statements.append(insert_sql)
        
        sql_statements.append("")
        return '\n'.join(sql_statements)
    
    def export_all_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export data from all aaa_* tables."""
        tables = [
            'aaa_profiles',
            'aaa_roles', 
            'aaa_user_roles',
            'aaa_clients',
            'aaa_password_reset_tokens'
        ]
        
        all_data = {}
        
        print("🚀 Starting Supabase data export...")
        print("=" * 60)
        
        for table in tables:
            data = self.export_table_data(table)
            all_data[table] = data
            
            # Generate and save SQL file for each table
            sql_content = self.generate_insert_statements(table, data)
            sql_file = os.path.join(self.export_dir, f"{table}_data.sql")
            
            with open(sql_file, 'w') as f:
                f.write(sql_content)
            
            print(f"💾 Saved SQL to: {sql_file}")
            print("-" * 40)
        
        return all_data
    
    def generate_complete_export_file(self, all_data: Dict[str, List[Dict[str, Any]]]):
        """Generate a complete SQL file with all table data."""
        complete_sql = []
        
        # Add header
        complete_sql.append("-- Complete Supabase Data Export")
        complete_sql.append(f"-- Generated on: {datetime.now()}")
        complete_sql.append("-- User Management System Database Export")
        complete_sql.append("")
        complete_sql.append("-- IMPORTANT: Run these INSERT statements in the correct order:")
        complete_sql.append("-- 1. aaa_roles (referenced by aaa_user_roles)")
        complete_sql.append("-- 2. aaa_profiles (referenced by aaa_user_roles and aaa_password_reset_tokens)")  
        complete_sql.append("-- 3. aaa_user_roles (depends on both aaa_profiles and aaa_roles)")
        complete_sql.append("-- 4. aaa_clients (independent)")
        complete_sql.append("-- 5. aaa_password_reset_tokens (depends on aaa_profiles)")
        complete_sql.append("")
        complete_sql.append("=" * 80)
        complete_sql.append("")
        
        # Add data for each table in dependency order
        table_order = [
            'aaa_roles',
            'aaa_profiles', 
            'aaa_user_roles',
            'aaa_clients',
            'aaa_password_reset_tokens'
        ]
        
        for table in table_order:
            if table in all_data:
                table_sql = self.generate_insert_statements(table, all_data[table])
                complete_sql.append(table_sql)
                complete_sql.append("=" * 80)
                complete_sql.append("")
        
        # Save complete export file
        complete_file = os.path.join(self.export_dir, "complete_data_export.sql")
        with open(complete_file, 'w') as f:
            f.write('\n'.join(complete_sql))
        
        print(f"📄 Complete export saved to: {complete_file}")
        
    def print_summary(self, all_data: Dict[str, List[Dict[str, Any]]]):
        """Print a summary of exported data."""
        print("\n" + "=" * 60)
        print("📈 EXPORT SUMMARY")
        print("=" * 60)
        
        total_records = 0
        for table, data in all_data.items():
            count = len(data)
            total_records += count
            print(f"{table:<25}: {count:>6} records")
        
        print("-" * 40)
        print(f"{'TOTAL':<25}: {total_records:>6} records")
        print("")
        
        # Print some sample data for verification
        print("🔍 SAMPLE DATA PREVIEW:")
        print("-" * 40)
        
        for table, data in all_data.items():
            if data:
                print(f"\n{table} (first record):")
                sample = data[0]
                for key, value in sample.items():
                    # Truncate long values for display
                    display_value = str(value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    print(f"  {key}: {display_value}")
        
        print("\n" + "=" * 60)
        print("✅ Export completed successfully!")
        print(f"📁 Files saved in: {os.path.abspath(self.export_dir)}")
        print("=" * 60)


def main():
    """Main function to run the export."""
    try:
        exporter = SupabaseDataExporter()
        
        # Export all table data
        all_data = exporter.export_all_tables()
        
        # Generate complete export file
        exporter.generate_complete_export_file(all_data)
        
        # Print summary
        exporter.print_summary(all_data)
        
        print("\n🎉 Next Steps:")
        print("1. Review the generated SQL files in the exports/ directory")
        print("2. Update connection strings and environment variables for local PostgreSQL")
        print("3. Run the complete_data_export.sql file against your local PostgreSQL database")
        print("4. Test your application with the migrated data")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in your .env file")
        print("2. Check your network connection to Supabase")
        print("3. Verify your service key has read access to the aaa_* tables")


if __name__ == "__main__":
    main()