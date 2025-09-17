#!/usr/bin/env python3
"""
Database Data Export for User Management System

This script exports data from the User Management System database in various formats:
- SQL INSERT statements
- JSON format
- CSV files
- Summary statistics

Usage:
    python export_database_data.py [options]

Options:
    --format {sql,json,csv,all}     Export format (default: sql)
    --output OUTPUT_DIR             Output directory (default: exports/)
    --include-sensitive             Include sensitive data like password hashes
    --sample-only                   Export only sample/test data
    --connection CONNECTION_STRING  Database connection string

Examples:
    python export_database_data.py --format json
    python export_database_data.py --format all --output /tmp/exports
    python export_database_data.py --sample-only --format sql
"""

import sys
import os
import json
import csv
import argparse
import asyncio
import asyncpg
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


class DatabaseExporter:
    def __init__(self, connection_string: str, include_sensitive: bool = False):
        self.connection_string = connection_string
        self.include_sensitive = include_sensitive
        self.conn = None
        self.export_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    async def connect(self):
        """Connect to the database"""
        try:
            self.conn = await asyncpg.connect(self.connection_string)
            print("✅ Connected to database successfully")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            await self.conn.close()
    
    async def get_table_data(self, table_name: str, sample_only: bool = False) -> List[Dict[str, Any]]:
        """Get data from a specific table"""
        # Exclude sensitive columns unless explicitly requested
        sensitive_columns = ['password_hash', 'client_secret', 'mfa_secret']
        
        # Get column information
        columns_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = $1 AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        columns = await self.conn.fetch(columns_query, table_name)
        
        # Filter out sensitive columns if not requested
        if not self.include_sensitive:
            columns = [col for col in columns if col['column_name'] not in sensitive_columns]
        
        column_names = [col['column_name'] for col in columns]
        
        if not column_names:
            return []
        
        # Build query
        query = f"SELECT {', '.join(column_names)} FROM {table_name}"
        
        if sample_only:
            # Only export sample/test data
            if table_name == 'aaa_profiles':
                query += " WHERE email LIKE '%@example.com' OR email LIKE '%@test.com'"
            elif table_name == 'aaa_organizations':
                query += " WHERE company_name LIKE '%Sample%' OR company_name LIKE '%Test%' OR company_name LIKE '%Tech Solutions%' OR company_name LIKE '%Global Manufacturing%'"
        
        query += " ORDER BY created_at"
        
        try:
            rows = await self.conn.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️  Error exporting {table_name}: {e}")
            return []
    
    async def export_to_sql(self, output_dir: Path, sample_only: bool = False):
        """Export data as SQL INSERT statements"""
        print("📄 Exporting to SQL format...")
        
        tables = [
            'aaa_roles',
            'aaa_organizations',
            'aaa_profiles',
            'aaa_business_units',
            'aaa_user_roles',
            'aaa_user_business_units',
            'aaa_clients',
            'aaa_email_otps',
            'aaa_password_reset_tokens'
        ]
        
        filename = f"data_export_{self.export_timestamp}.sql"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"-- User Management System Data Export\\n")
            f.write(f"-- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\\n")
            f.write(f"-- Sample Only: {sample_only}\\n")
            f.write(f"-- Include Sensitive: {self.include_sensitive}\\n\\n")
            
            f.write("BEGIN;\\n\\n")
            
            for table_name in tables:
                data = await self.get_table_data(table_name, sample_only)
                
                if not data:
                    f.write(f"-- No data found for {table_name}\\n\\n")
                    continue
                
                f.write(f"-- Data for table: {table_name}\\n")
                f.write(f"-- Records: {len(data)}\\n")
                
                if data:
                    columns = list(data[0].keys())
                    f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\\n")
                    
                    for i, row in enumerate(data):
                        values = []
                        for col in columns:
                            value = row[col]
                            if value is None:
                                values.append('NULL')
                            elif isinstance(value, str):
                                # Escape single quotes
                                escaped = value.replace("'", "''")
                                values.append(f"'{escaped}'")
                            elif isinstance(value, (list, dict)):
                                # Handle arrays and JSON
                                values.append(f"'{json.dumps(value)}'")
                            elif isinstance(value, bool):
                                values.append('TRUE' if value else 'FALSE')
                            else:
                                values.append(str(value))
                        
                        line_end = ',' if i < len(data) - 1 else ';'
                        f.write(f"    ({', '.join(values)}){line_end}\\n")
                
                f.write("\\n")
            
            f.write("COMMIT;\\n")
        
        print(f"✅ SQL export completed: {filepath}")
        return filepath
    
    async def export_to_json(self, output_dir: Path, sample_only: bool = False):
        """Export data as JSON"""
        print("📄 Exporting to JSON format...")
        
        tables = [
            'aaa_roles', 'aaa_organizations', 'aaa_profiles', 'aaa_business_units',
            'aaa_user_roles', 'aaa_user_business_units', 'aaa_clients',
            'aaa_email_otps', 'aaa_password_reset_tokens'
        ]
        
        export_data = {
            'metadata': {
                'export_timestamp': self.export_timestamp,
                'export_time_utc': datetime.now(timezone.utc).isoformat(),
                'sample_only': sample_only,
                'include_sensitive': self.include_sensitive,
                'tables_exported': []
            },
            'data': {}
        }
        
        for table_name in tables:
            data = await self.get_table_data(table_name, sample_only)
            export_data['data'][table_name] = data
            export_data['metadata']['tables_exported'].append({
                'table': table_name,
                'record_count': len(data)
            })
        
        filename = f"data_export_{self.export_timestamp}.json"
        filepath = output_dir / filename
        
        # Custom JSON encoder for dates and UUIDs
        def json_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            elif hasattr(obj, '__str__'):
                return str(obj)
            return obj
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=json_serializer, ensure_ascii=False)
        
        print(f"✅ JSON export completed: {filepath}")
        return filepath
    
    async def export_to_csv(self, output_dir: Path, sample_only: bool = False):
        """Export data as CSV files (one per table)"""
        print("📄 Exporting to CSV format...")
        
        tables = [
            'aaa_roles', 'aaa_organizations', 'aaa_profiles', 'aaa_business_units',
            'aaa_user_roles', 'aaa_user_business_units', 'aaa_clients',
            'aaa_email_otps', 'aaa_password_reset_tokens'
        ]
        
        csv_dir = output_dir / f"csv_export_{self.export_timestamp}"
        csv_dir.mkdir(exist_ok=True)
        
        exported_files = []
        
        for table_name in tables:
            data = await self.get_table_data(table_name, sample_only)
            
            if not data:
                print(f"  ⚠️  No data for {table_name}")
                continue
            
            filename = f"{table_name}.csv"
            filepath = csv_dir / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    # Convert complex types to strings
                    csv_row = {}
                    for key, value in row.items():
                        if isinstance(value, (list, dict)):
                            csv_row[key] = json.dumps(value)
                        elif value is None:
                            csv_row[key] = ''
                        else:
                            csv_row[key] = str(value)
                    writer.writerow(csv_row)
            
            exported_files.append(filepath)
            print(f"  ✅ {table_name}: {len(data)} records → {filename}")
        
        print(f"✅ CSV export completed: {csv_dir}")
        return csv_dir
    
    async def generate_summary(self, output_dir: Path, sample_only: bool = False):
        """Generate export summary statistics"""
        print("📊 Generating export summary...")
        
        tables = [
            'aaa_roles', 'aaa_organizations', 'aaa_profiles', 'aaa_business_units',
            'aaa_user_roles', 'aaa_user_business_units', 'aaa_clients',
            'aaa_email_otps', 'aaa_password_reset_tokens'
        ]
        
        summary = {
            'export_info': {
                'timestamp': self.export_timestamp,
                'export_time_utc': datetime.now(timezone.utc).isoformat(),
                'sample_only': sample_only,
                'include_sensitive': self.include_sensitive
            },
            'table_summary': [],
            'totals': {
                'total_tables': 0,
                'total_records': 0,
                'tables_with_data': 0
            }
        }
        
        total_records = 0
        tables_with_data = 0
        
        for table_name in tables:
            data = await self.get_table_data(table_name, sample_only)
            record_count = len(data)
            
            summary['table_summary'].append({
                'table_name': table_name,
                'record_count': record_count,
                'has_data': record_count > 0
            })
            
            total_records += record_count
            if record_count > 0:
                tables_with_data += 1
        
        summary['totals'] = {
            'total_tables': len(tables),
            'total_records': total_records,
            'tables_with_data': tables_with_data
        }
        
        filename = f"export_summary_{self.export_timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Also print summary to console
        print(f"\\n📈 Export Summary:")
        print(f"   Total tables: {summary['totals']['total_tables']}")
        print(f"   Tables with data: {summary['totals']['tables_with_data']}")
        print(f"   Total records: {summary['totals']['total_records']}")
        print(f"   Sample only: {sample_only}")
        print(f"   Include sensitive: {self.include_sensitive}")
        
        print(f"\\n✅ Summary saved: {filepath}")
        return filepath


async def main():
    """Main export function"""
    parser = argparse.ArgumentParser(description='Export User Management System database data')
    parser.add_argument('--format', choices=['sql', 'json', 'csv', 'all'], default='sql',
                        help='Export format (default: sql)')
    parser.add_argument('--output', default='exports',
                        help='Output directory (default: exports/)')
    parser.add_argument('--include-sensitive', action='store_true',
                        help='Include sensitive data like password hashes')
    parser.add_argument('--sample-only', action='store_true',
                        help='Export only sample/test data')
    parser.add_argument('--connection',
                        help='Database connection string')
    
    args = parser.parse_args()
    
    # Get connection string
    connection_string = args.connection
    if not connection_string:
        connection_string = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_URL')
        if not connection_string:
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', '')
            database = os.getenv('DB_NAME', 'postgres')
            
            if password:
                connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                connection_string = f"postgresql://{user}@{host}:{port}/{database}"
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("📤 User Management System - Database Data Export")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"📊 Format: {args.format}")
    print(f"🔒 Include sensitive: {args.include_sensitive}")
    print(f"🧪 Sample only: {args.sample_only}")
    
    try:
        exporter = DatabaseExporter(connection_string, args.include_sensitive)
        await exporter.connect()
        
        exported_files = []
        
        if args.format in ['sql', 'all']:
            filepath = await exporter.export_to_sql(output_dir, args.sample_only)
            exported_files.append(filepath)
        
        if args.format in ['json', 'all']:
            filepath = await exporter.export_to_json(output_dir, args.sample_only)
            exported_files.append(filepath)
        
        if args.format in ['csv', 'all']:
            filepath = await exporter.export_to_csv(output_dir, args.sample_only)
            exported_files.append(filepath)
        
        # Always generate summary
        summary_path = await exporter.generate_summary(output_dir, args.sample_only)
        exported_files.append(summary_path)
        
        await exporter.disconnect()
        
        print(f"\\n🎉 Export completed successfully!")
        print(f"📁 Files created in: {output_dir.absolute()}")
        
    except KeyboardInterrupt:
        print("\\n❌ Export cancelled by user")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if asyncpg is available
    try:
        import asyncpg
    except ImportError:
        print("❌ Required dependency 'asyncpg' not found.")
        print("   Install with: pip install asyncpg")
        sys.exit(1)
    
    asyncio.run(main())