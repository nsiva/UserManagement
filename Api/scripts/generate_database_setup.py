#!/usr/bin/env python3
"""
Database Setup Generator for User Management System

This script generates a complete SQL setup file that includes:
- All table definitions with constraints and indexes
- Functions and triggers
- Sample data for roles, organizations, business units, and users
- Database views
- Essential configuration

Usage:
    python generate_database_setup.py [output_file]

If no output file is specified, it will create 'complete_database_setup.sql'
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class DatabaseSetupGenerator:
    def __init__(self, schema: str = "public", export_data: bool = False, connection_string: Optional[str] = None, source_schema: Optional[str] = None, inspect_schema: bool = False):
        self.output_lines: List[str] = []
        self.schema = schema  # Target schema where objects will be created
        self.source_schema = source_schema or schema  # Source schema where data will be exported from
        self.export_data = export_data
        self.connection_string = connection_string
        self.inspect_schema = inspect_schema  # Whether to inspect actual database schema
        self.exported_data: Dict[str, List[Dict[str, Any]]] = {}
        self.inspected_schema: Dict[str, Any] = {}  # Store inspected schema information
    
    def load_environment(self):
        """Load environment variables from .env file"""
        if DOTENV_AVAILABLE:
            # Look for .env file in current directory or parent directories
            env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                return True
            
            # Try current directory
            if os.path.exists('.env'):
                load_dotenv('.env')
                return True
        return False
    
    def get_connection_string(self) -> Optional[str]:
        """Get database connection string from environment or parameter"""
        if self.connection_string:
            return self.connection_string
        
        # Try to load from environment
        self.load_environment()
        
        # Check for various connection string formats
        conn_str = os.getenv('POSTGRES_CONNECTION_STRING')
        if conn_str:
            return conn_str
        
        # Try to build from individual components
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', '')
        database = os.getenv('POSTGRES_DB', 'postgres')
        schema = os.getenv('POSTGRES_SCHEMA', 'public')
        
        if any([host, port, user, database]):
            password_part = f":{password}" if password else ""
            options_part = f"?options=-csearch_path%3D{schema}" if schema != 'public' else ""
            return f"postgresql://{user}{password_part}@{host}:{port}/{database}{options_part}"
        
        return None
    
    def connect_to_database(self):
        """Connect to the database and return connection"""
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for database connectivity. Install with: pip install psycopg2-binary")
        
        conn_str = self.get_connection_string()
        if not conn_str:
            raise ValueError("No database connection string found. Set POSTGRES_CONNECTION_STRING in .env or provide --connection-string")
        
        try:
            # For PostgreSQL URIs with options, we need to handle them properly
            if "options=" in conn_str:
                # Extract the base URI without options and parse options separately
                base_uri = conn_str.split('?')[0]
                import urllib.parse
                parsed = urllib.parse.urlparse(conn_str)
                
                # Parse the query parameters
                query_params = urllib.parse.parse_qs(parsed.query)
                options = query_params.get('options', [])
                
                # Connect to base URI
                conn = psycopg2.connect(base_uri)
                
                # Set search_path if specified in options
                if options:
                    for option in options:
                        if option.startswith('-csearch_path='):
                            search_path = option.replace('-csearch_path=', '')
                            cursor = conn.cursor()
                            cursor.execute(f"SET search_path TO {search_path}, public")
                            cursor.close()
                            break
                
                return conn
            else:
                conn = psycopg2.connect(conn_str)
                return conn
        except Exception as e:
            raise Exception(f"Failed to connect to database: {e}")
    
    def export_table_data(self, table_name: str, connection) -> List[Dict[str, Any]]:
        """Export data from a specific table"""
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            # Start a new transaction for each table
            connection.rollback()  # Clear any previous transaction state
            # Check if table exists in the source schema
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                ) as table_exists
            """, (self.source_schema, table_name))
            
            result = cursor.fetchone()
            if not result['table_exists']:
                print(f"⚠️  Table {self.source_schema}.{table_name} does not exist, skipping...")
                return []
            
            # Get all data from the table in source schema
            # Try ordering by created_at, but fall back to no ordering if column doesn't exist
            try:
                cursor.execute(f"SELECT * FROM {self.source_schema}.{table_name} ORDER BY created_at")
                rows = cursor.fetchall()
            except Exception:
                # Fall back to no ordering if created_at column doesn't exist
                cursor.execute(f"SELECT * FROM {self.source_schema}.{table_name}")
                rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"⚠️  Error exporting data from {table_name}: {e}")
            return []
        finally:
            cursor.close()
    
    def export_all_data(self):
        """Export data from all relevant tables"""
        if not self.export_data:
            return
        
        print(f"📊 Connecting to database to export existing data from '{self.source_schema}' schema...")
        
        try:
            connection = self.connect_to_database()
            print(f"✅ Connected to database successfully")
            print(f"📍 Source schema: {self.source_schema}")
            print(f"🎯 Target schema: {self.schema}")
            
            # List of tables to export (in dependency order)
            tables_to_export = [
                'aaa_roles',
                'aaa_organizations', 
                'aaa_profiles',
                'aaa_clients',
                'aaa_business_units',
                'aaa_user_roles',
                'aaa_user_business_units',
                'aaa_email_otps',
                'aaa_password_reset_tokens'
            ]
            
            for table in tables_to_export:
                print(f"📋 Exporting data from {self.source_schema}.{table}...")
                data = self.export_table_data(table, connection)
                self.exported_data[table] = data
                print(f"   📊 Exported {len(data)} rows")
            
            connection.close()
            print("🔐 Database connection closed")
            
        except Exception as e:
            print(f"❌ Error during data export: {e}")
            # Continue with script generation even if data export fails
    
    def inspect_database_schema(self):
        """Inspect the actual database schema and store table definitions"""
        if not self.inspect_schema:
            return
            
        print(f"🔍 Inspecting database schema from '{self.source_schema}' schema...")
        
        try:
            connection = self.connect_to_database()
            print(f"✅ Connected to database for schema inspection")
            
            # Get all tables in the source schema
            tables = self.get_schema_tables(connection)
            print(f"📋 Found {len(tables)} tables to inspect")
            
            for table_name in tables:
                print(f"🔍 Inspecting table: {table_name}")
                table_info = self.inspect_table_structure(connection, table_name)
                self.inspected_schema[table_name] = table_info
                
            connection.close()
            print("🔐 Schema inspection completed")
            
        except Exception as e:
            print(f"❌ Error during schema inspection: {e}")
            import traceback
            print(f"   Debug: {traceback.format_exc()}")
            print("⚠️  Falling back to default table definitions")
    
    def get_schema_tables(self, connection) -> List[str]:
        """Get list of all tables in the source schema"""
        cursor = connection.cursor()
        try:
            # Get all aaa_* tables in the source schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name LIKE 'aaa_%'
                ORDER BY table_name
            """, (self.source_schema,))
            
            result = cursor.fetchall()
            tables = [row[0] if isinstance(row, tuple) else row for row in result]
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
        finally:
            cursor.close()
    
    def inspect_table_structure(self, connection, table_name: str) -> Dict[str, Any]:
        """Inspect the structure of a specific table"""
        cursor = connection.cursor()
        table_info = {
            'columns': [],
            'constraints': [],
            'indexes': [],
            'triggers': []
        }
        
        try:
            # Get column information
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    udt_name
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (self.source_schema, table_name))
            
            for row in cursor.fetchall():
                column_info = {
                    'name': row[0],
                    'data_type': row[1],
                    'is_nullable': row[2] == 'YES',
                    'default': row[3],
                    'char_max_length': row[4],
                    'numeric_precision': row[5],
                    'numeric_scale': row[6],
                    'udt_name': row[7]
                }
                table_info['columns'].append(column_info)
            
            # Get constraints (primary key, foreign key, unique, check)
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    cc.check_clause
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    AND tc.table_schema = ccu.table_schema
                LEFT JOIN information_schema.check_constraints cc
                    ON tc.constraint_name = cc.constraint_name
                    AND tc.table_schema = cc.constraint_schema
                WHERE tc.table_schema = %s AND tc.table_name = %s
            """, (self.source_schema, table_name))
            
            for row in cursor.fetchall():
                constraint_info = {
                    'name': row[0],
                    'type': row[1],
                    'column_name': row[2],
                    'foreign_table_schema': row[3],
                    'foreign_table_name': row[4],
                    'foreign_column_name': row[5],
                    'check_clause': row[6]
                }
                table_info['constraints'].append(constraint_info)
            
            # Get indexes
            cursor.execute("""
                SELECT 
                    i.indexname,
                    i.indexdef
                FROM pg_indexes i
                WHERE i.schemaname = %s AND i.tablename = %s
                AND i.indexname NOT LIKE '%_pkey'
            """, (self.source_schema, table_name))
            
            for row in cursor.fetchall():
                index_info = {
                    'name': row[0],
                    'definition': row[1]
                }
                table_info['indexes'].append(index_info)
                
            return table_info
            
        finally:
            cursor.close()
    
    def generate_table_ddl(self, table_name: str, table_info: Dict[str, Any]) -> List[str]:
        """Generate CREATE TABLE statement from inspected table info"""
        lines = []
        lines.append(f"-- {table_name} table (inspected from source database)")
        lines.append(f"CREATE TABLE IF NOT EXISTS {self.schema}.{table_name} (")
        
        # Generate column definitions
        column_lines = []
        primary_key_columns = []
        
        # Find primary key columns
        for constraint in table_info['constraints']:
            if constraint['type'] == 'PRIMARY KEY':
                primary_key_columns.append(constraint['column_name'])
        
        for col in table_info['columns']:
            col_def = f"    {col['name']} "
            
            # Handle different data types
            if col['udt_name'] == 'uuid':
                col_def += "UUID"
            elif col['data_type'] == 'character varying':
                if col['char_max_length']:
                    col_def += f"VARCHAR({col['char_max_length']})"
                else:
                    col_def += "TEXT"
            elif col['data_type'] == 'text':
                col_def += "TEXT"
            elif col['data_type'] == 'boolean':
                col_def += "BOOLEAN"
            elif col['data_type'] == 'integer':
                col_def += "INTEGER"
            elif col['data_type'] == 'bigint':
                col_def += "BIGINT"
            elif col['data_type'] == 'timestamp with time zone':
                col_def += "TIMESTAMP WITH TIME ZONE"
            elif col['data_type'] == 'timestamp without time zone':
                col_def += "TIMESTAMP"
            elif col['data_type'] == 'numeric':
                if col['numeric_precision'] and col['numeric_scale']:
                    col_def += f"NUMERIC({col['numeric_precision']},{col['numeric_scale']})"
                else:
                    col_def += "NUMERIC"
            elif col['data_type'] == 'ARRAY':
                col_def += "TEXT[]"
            else:
                col_def += col['data_type'].upper()
            
            # Add constraints
            if col['name'] in primary_key_columns:
                col_def += " PRIMARY KEY"
            
            if col['default']:
                if 'gen_random_uuid()' in col['default']:
                    col_def += " DEFAULT gen_random_uuid()"
                elif 'CURRENT_TIMESTAMP' in col['default'] or 'now()' in col['default']:
                    col_def += " DEFAULT NOW()"
                elif col['default'] == 'true':
                    col_def += " DEFAULT TRUE"
                elif col['default'] == 'false':
                    col_def += " DEFAULT FALSE"
                else:
                    col_def += f" DEFAULT {col['default']}"
            
            if not col['is_nullable']:
                col_def += " NOT NULL"
            
            column_lines.append(col_def)
        
        # Add column definitions
        for i, col_line in enumerate(column_lines):
            suffix = "," if i < len(column_lines) - 1 else ""
            lines.append(f"{col_line}{suffix}")
        
        lines.append(");")
        lines.append("")
        
        return lines
    
    def generate_table_constraints(self, table_name: str, table_info: Dict[str, Any]) -> List[str]:
        """Generate ALTER TABLE statements for foreign keys and other constraints"""
        lines = []
        
        # Group constraints by type
        foreign_keys = []
        unique_constraints = []
        check_constraints = []
        
        for constraint in table_info['constraints']:
            if constraint['type'] == 'FOREIGN KEY':
                foreign_keys.append(constraint)
            elif constraint['type'] == 'UNIQUE':
                unique_constraints.append(constraint)
            elif constraint['type'] == 'CHECK':
                check_constraints.append(constraint)
        
        # Generate foreign key constraints
        for fk in foreign_keys:
            if fk['foreign_table_name'] and fk['column_name']:
                lines.append(f"ALTER TABLE {self.schema}.{table_name}")
                lines.append(f"    ADD CONSTRAINT {fk['name']}")
                lines.append(f"    FOREIGN KEY ({fk['column_name']}) REFERENCES {self.schema}.{fk['foreign_table_name']}({fk['foreign_column_name']}) ON DELETE CASCADE;")
                lines.append("")
        
        return lines
        
    def add_header(self):
        """Add header with metadata"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.output_lines.extend([
            "-- =====================================================",
            "-- User Management System - Complete Database Setup",
            f"-- Generated on: {timestamp}",
            f"-- Target schema: {self.schema}",
            "-- =====================================================",
            "",
            "-- This script creates the complete database structure for the User Management System.",
            "-- It includes all tables, indexes, constraints, functions, triggers, views, and sample data.",
            "",
            "-- Prerequisites:",
            "-- 1. PostgreSQL 12+ database",
            "-- 2. UUID extension (usually available by default)",
            "-- 3. Sufficient privileges to create schema, tables, functions, and triggers",
            "",
            "-- Usage:",
            "-- psql -U your_username -d your_database_name -f complete_database_setup.sql",
            "",
            "BEGIN;",
            "",
            "-- Enable UUID extension if not already enabled",
            "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
            "",
            f"-- Create schema if it doesn't exist",
            f"CREATE SCHEMA IF NOT EXISTS {self.schema};",
            "",
            f"-- Set search path to target schema",
            f"SET search_path TO {self.schema}, public;",
            "",
        ])
    
    def add_core_tables(self):
        """Add core authentication and user management tables"""
        if self.inspect_schema and self.inspected_schema:
            # Use inspected schema definitions
            self.output_lines.extend([
                "-- =====================================================",
                "-- CORE TABLES (Inspected from source database)",
                "-- =====================================================",
                "",
            ])
            
            # Generate tables in dependency order
            table_order = ['aaa_roles', 'aaa_profiles', 'aaa_clients', 'aaa_organizations']
            for table_name in table_order:
                if table_name in self.inspected_schema:
                    table_ddl = self.generate_table_ddl(table_name, self.inspected_schema[table_name])
                    self.output_lines.extend(table_ddl)
        else:
            # Use default hardcoded schema
            self.output_lines.extend([
                "-- =====================================================",
                "-- CORE TABLES",
                "-- =====================================================",
                "",
                "-- User profiles table (main user data with authentication)",
                f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_profiles (",
                "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
                "    email TEXT UNIQUE NOT NULL,",
                "    password_hash TEXT NOT NULL,",
                "    first_name TEXT,",
                "    middle_name TEXT,",
                "    last_name TEXT,",
                "    is_admin BOOLEAN DEFAULT FALSE NOT NULL,",
                "    mfa_secret TEXT,",
                "    mfa_method TEXT CHECK (mfa_method IN ('totp', 'email')),",
                "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
                "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                ");",
                "",
                "-- Roles definition table",
                f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_roles (",
                "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
                "    name TEXT UNIQUE NOT NULL,",
                "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                ");",
                "",
                "-- User-Role junction table (many-to-many relationship)",
                f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_user_roles (",
                f"    user_id UUID NOT NULL REFERENCES {self.schema}.aaa_profiles(id) ON DELETE CASCADE,",
                f"    role_id UUID NOT NULL REFERENCES {self.schema}.aaa_roles(id) ON DELETE CASCADE,",
                "    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
                "    PRIMARY KEY (user_id, role_id)",
                ");",
                "",
                "-- API clients for client credentials flow",
                f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_clients (",
                "    client_id TEXT PRIMARY KEY,",
                "    client_secret TEXT NOT NULL,",
                "    name TEXT,",
                "    scopes TEXT[],",
                "    is_active BOOLEAN DEFAULT TRUE NOT NULL,",
                "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
                "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                ");",
                "",
            ])
    
    def add_organizational_tables(self):
        """Add organizations and business units tables"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- ORGANIZATIONAL STRUCTURE TABLES",
            "-- =====================================================",
            "",
            "-- Organizations table for company/organization management",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_organizations (",
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
            "    company_name TEXT NOT NULL,",
            "    address_1 TEXT,",
            "    address_2 TEXT,",
            "    city_town TEXT,",
            "    state TEXT,",
            "    zip TEXT,",
            "    country TEXT,",
            "    email TEXT,",
            "    phone_number TEXT,",
            "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
            "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
            ");",
            "",
            "-- Business Units table for organizational structure management",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_business_units (",
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
            "    name TEXT NOT NULL,",
            "    description TEXT,",
            "    code TEXT,",
            "    organization_id UUID NOT NULL,",
            "    parent_unit_id UUID,",
            "    manager_id UUID,",
            "    location TEXT,",
            "    country TEXT,",
            "    region TEXT,",
            "    email TEXT,",
            "    phone_number TEXT,",
            "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
            "    created_by UUID,",
            "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
            "    updated_by UUID,",
            "    is_active BOOLEAN DEFAULT TRUE NOT NULL,",
            "    ",
            "    -- Foreign key constraints",
            "    CONSTRAINT fk_business_unit_organization",
            f"        FOREIGN KEY (organization_id) REFERENCES {self.schema}.aaa_organizations(id) ON DELETE CASCADE,",
            "    CONSTRAINT fk_business_unit_parent",
            f"        FOREIGN KEY (parent_unit_id) REFERENCES {self.schema}.aaa_business_units(id) ON DELETE SET NULL,",
            "    CONSTRAINT fk_business_unit_manager",
            f"        FOREIGN KEY (manager_id) REFERENCES {self.schema}.aaa_profiles(id) ON DELETE SET NULL,",
            "    CONSTRAINT fk_business_unit_created_by",
            f"        FOREIGN KEY (created_by) REFERENCES {self.schema}.aaa_profiles(id) ON DELETE SET NULL,",
            "    CONSTRAINT fk_business_unit_updated_by",
            f"        FOREIGN KEY (updated_by) REFERENCES {self.schema}.aaa_profiles(id) ON DELETE SET NULL,",
            "    ",
            "    -- Business logic constraints",
            "    CONSTRAINT chk_business_unit_not_self_parent",
            "        CHECK (parent_unit_id != id),",
            "    CONSTRAINT chk_business_unit_name_length",
            "        CHECK (LENGTH(TRIM(name)) >= 2),",
            "    CONSTRAINT chk_business_unit_code_format",
            "        CHECK (code IS NULL OR (LENGTH(TRIM(code)) >= 2 AND code ~ '^[A-Z0-9_-]+$')),",
            "    CONSTRAINT chk_business_unit_email_format",
            "        CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')",
            ");",
            "",
            "-- User-Business Unit junction table",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_user_business_units (",
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
            f"    user_id UUID NOT NULL REFERENCES {self.schema}.aaa_profiles(id) ON DELETE CASCADE,",
            f"    business_unit_id UUID NOT NULL REFERENCES {self.schema}.aaa_business_units(id) ON DELETE CASCADE,",
            "    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
            f"    assigned_by UUID REFERENCES {self.schema}.aaa_profiles(id),",
            "    is_active BOOLEAN DEFAULT TRUE NOT NULL,",
            "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
            "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
            "    UNIQUE (user_id, business_unit_id)",
            ");",
            "",
        ])
    
    def add_security_tables(self):
        """Add security-related tables (MFA, password reset, etc.)"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- SECURITY TABLES",
            "-- =====================================================",
            "",
            "-- Email OTP table for email-based MFA",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_email_otps (",
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
            f"    user_id UUID NOT NULL REFERENCES {self.schema}.aaa_profiles(id) ON DELETE CASCADE,",
            "    email TEXT NOT NULL,",
            "    otp TEXT NOT NULL,",
            "    purpose TEXT NOT NULL,",
            "    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,",
            "    used BOOLEAN DEFAULT FALSE NOT NULL,",
            "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
            ");",
            "",
            "-- Password reset tokens table",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.aaa_password_reset_tokens (",
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
            f"    user_id UUID NOT NULL REFERENCES {self.schema}.aaa_profiles(id) ON DELETE CASCADE,",
            "    token TEXT UNIQUE NOT NULL,",
            "    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,",
            "    used BOOLEAN DEFAULT FALSE NOT NULL,",
            "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
            ");",
            "",
        ])
    
    def add_rls_disabling(self):
        """Disable Row Level Security on all tables"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- DISABLE ROW LEVEL SECURITY",
            "-- =====================================================",
            "",
            "-- Disable RLS on all tables for direct API access",
            f"ALTER TABLE {self.schema}.aaa_profiles DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_roles DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_user_roles DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_clients DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_organizations DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_business_units DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_user_business_units DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_email_otps DISABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE {self.schema}.aaa_password_reset_tokens DISABLE ROW LEVEL SECURITY;",
            "",
        ])
    
    def add_indexes(self):
        """Add performance indexes"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- INDEXES FOR PERFORMANCE",
            "-- =====================================================",
            "",
            "-- Core table indexes",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_profiles_email ON {self.schema}.aaa_profiles(email);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_profiles_mfa_method ON {self.schema}.aaa_profiles(mfa_method) WHERE mfa_method IS NOT NULL;",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_user_roles_user_id ON {self.schema}.aaa_user_roles(user_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_user_roles_role_id ON {self.schema}.aaa_user_roles(role_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_clients_active ON {self.schema}.aaa_clients(is_active) WHERE is_active = TRUE;",
            "",
            "-- Organizational indexes",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_organizations_company_name ON {self.schema}.aaa_organizations(company_name);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_organizations_email ON {self.schema}.aaa_organizations(email);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_business_units_organization_id ON {self.schema}.aaa_business_units(organization_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_business_units_parent_unit_id ON {self.schema}.aaa_business_units(parent_unit_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_business_units_manager_id ON {self.schema}.aaa_business_units(manager_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_business_units_name ON {self.schema}.aaa_business_units(name);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_business_units_code ON {self.schema}.aaa_business_units(code) WHERE code IS NOT NULL;",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_business_units_is_active ON {self.schema}.aaa_business_units(is_active);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_user_id ON {self.schema}.aaa_user_business_units(user_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_business_unit_id ON {self.schema}.aaa_user_business_units(business_unit_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_assigned_by ON {self.schema}.aaa_user_business_units(assigned_by);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_active ON {self.schema}.aaa_user_business_units(is_active);",
            "",
            "-- Security table indexes",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_user_id ON {self.schema}.aaa_email_otps(user_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_expires_at ON {self.schema}.aaa_email_otps(expires_at);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_used ON {self.schema}.aaa_email_otps(used);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_user_id ON {self.schema}.aaa_password_reset_tokens(user_id);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_token ON {self.schema}.aaa_password_reset_tokens(token);",
            f"CREATE INDEX IF NOT EXISTS idx_aaa_password_reset_tokens_expires_at ON {self.schema}.aaa_password_reset_tokens(expires_at);",
            "",
            "-- Unique constraints",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_business_units_unique_code_per_org",
            f"    ON {self.schema}.aaa_business_units(organization_id, code)",
            "    WHERE code IS NOT NULL;",
            "",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_business_units_unique_name_per_parent",
            f"    ON {self.schema}.aaa_business_units(organization_id, COALESCE(parent_unit_id, '00000000-0000-0000-0000-000000000000'), name);",
            "",
        ])
    
    def add_functions_and_triggers(self):
        """Add database functions and triggers"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- FUNCTIONS AND TRIGGERS",
            "-- =====================================================",
            "",
            "-- Function to update updated_at timestamp",
            f"CREATE OR REPLACE FUNCTION {self.schema}.update_aaa_business_units_updated_at()",
            "RETURNS TRIGGER AS $$",
            "BEGIN",
            "    NEW.updated_at = NOW();",
            "    RETURN NEW;",
            "END;",
            "$$ LANGUAGE plpgsql;",
            "",
            "-- Trigger to automatically update updated_at timestamp",
            f"DROP TRIGGER IF EXISTS trigger_update_aaa_business_units_updated_at ON {self.schema}.aaa_business_units;",
            "CREATE TRIGGER trigger_update_aaa_business_units_updated_at",
            f"    BEFORE UPDATE ON {self.schema}.aaa_business_units",
            "    FOR EACH ROW",
            f"    EXECUTE FUNCTION {self.schema}.update_aaa_business_units_updated_at();",
            "",
            "-- Function to prevent circular hierarchy",
            f"CREATE OR REPLACE FUNCTION {self.schema}.check_business_unit_hierarchy()",
            "RETURNS TRIGGER AS $$",
            "BEGIN",
            "    -- Only check if parent_unit_id is being set",
            "    IF NEW.parent_unit_id IS NOT NULL THEN",
            "        -- Check if the new parent would create a circular reference",
            "        WITH RECURSIVE hierarchy_check AS (",
            "            -- Start with the proposed parent",
            "            SELECT parent_unit_id, 1 as level",
            f"            FROM {self.schema}.aaa_business_units",
            "            WHERE id = NEW.parent_unit_id",
            "            ",
            "            UNION ALL",
            "            ",
            "            -- Follow the hierarchy up",
            "            SELECT bu.parent_unit_id, hc.level + 1",
            f"            FROM {self.schema}.aaa_business_units bu",
            "            JOIN hierarchy_check hc ON bu.id = hc.parent_unit_id",
            "            WHERE hc.level < 10 -- Prevent infinite recursion",
            "        )",
            "        SELECT 1 FROM hierarchy_check",
            "        WHERE parent_unit_id = NEW.id",
            "        LIMIT 1;",
            "        ",
            "        -- If we found the current record in its own ancestry, it's circular",
            "        IF FOUND THEN",
            "            RAISE EXCEPTION 'Cannot create circular hierarchy: Business unit cannot be an ancestor of itself';",
            "        END IF;",
            "        ",
            "        -- Also check that parent belongs to same organization",
            "        IF EXISTS (",
            f"            SELECT 1 FROM {self.schema}.aaa_business_units",
            "            WHERE id = NEW.parent_unit_id",
            "            AND organization_id != NEW.organization_id",
            "        ) THEN",
            "            RAISE EXCEPTION 'Parent business unit must belong to the same organization';",
            "        END IF;",
            "    END IF;",
            "    ",
            "    RETURN NEW;",
            "END;",
            "$$ LANGUAGE plpgsql;",
            "",
            "-- Trigger to enforce hierarchy constraints",
            f"DROP TRIGGER IF EXISTS trigger_check_business_unit_hierarchy ON {self.schema}.aaa_business_units;",
            "CREATE TRIGGER trigger_check_business_unit_hierarchy",
            f"    BEFORE INSERT OR UPDATE ON {self.schema}.aaa_business_units",
            "    FOR EACH ROW",
            f"    EXECUTE FUNCTION {self.schema}.check_business_unit_hierarchy();",
            "",
        ])
    
    def add_views(self):
        """Add database views for reporting and convenience"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- DATABASE VIEWS",
            "-- =====================================================",
            "",
            "-- User details view with organizational context",
            f"CREATE OR REPLACE VIEW {self.schema}.vw_user_details AS",
            "SELECT",
            "    p.id,",
            "    p.email,",
            "    p.first_name,",
            "    p.middle_name,",
            "    p.last_name,",
            "    p.is_admin,",
            "    p.mfa_secret,",
            "    p.mfa_method,",
            "    p.created_at,",
            "    p.updated_at,",
            "    -- Role information",
            "    ARRAY_AGG(DISTINCT r.name ORDER BY r.name) FILTER (WHERE r.name IS NOT NULL) as roles,",
            "    -- Business unit information",
            "    bu.id as business_unit_id,",
            "    bu.name as business_unit_name,",
            "    -- Organization information",
            "    org.id as organization_id,",
            "    org.company_name as organization_name",
            f"FROM {self.schema}.aaa_profiles p",
            f"LEFT JOIN {self.schema}.aaa_user_roles ur ON p.id = ur.user_id",
            f"LEFT JOIN {self.schema}.aaa_roles r ON ur.role_id = r.id",
            f"LEFT JOIN {self.schema}.aaa_user_business_units ubu ON p.id = ubu.user_id AND ubu.is_active = true",
            f"LEFT JOIN {self.schema}.aaa_business_units bu ON ubu.business_unit_id = bu.id AND bu.is_active = true",
            f"LEFT JOIN {self.schema}.aaa_organizations org ON bu.organization_id = org.id",
            "GROUP BY p.id, p.email, p.first_name, p.middle_name, p.last_name, p.is_admin,",
            "         p.mfa_secret, p.mfa_method, p.created_at, p.updated_at,",
            "         bu.id, bu.name, org.id, org.company_name;",
            "",
            "-- Business unit hierarchy view",
            f"CREATE OR REPLACE VIEW {self.schema}.vw_business_unit_hierarchy AS",
            "WITH RECURSIVE hierarchy AS (",
            "    -- Root business units (no parent)",
            "    SELECT",
            "        bu.id,",
            "        bu.name,",
            "        bu.organization_id,",
            "        org.company_name as organization_name,",
            "        bu.parent_unit_id,",
            "        NULL::TEXT as parent_name,",
            "        bu.manager_id,",
            "        CONCAT(p.first_name, ' ', p.last_name) as manager_name,",
            "        bu.location,",
            "        bu.email,",
            "        bu.phone_number,",
            "        bu.is_active,",
            "        1 as level,",
            "        ARRAY[bu.name] as path",
            f"    FROM {self.schema}.aaa_business_units bu",
            f"    LEFT JOIN {self.schema}.aaa_organizations org ON bu.organization_id = org.id",
            f"    LEFT JOIN {self.schema}.aaa_profiles p ON bu.manager_id = p.id",
            "    WHERE bu.parent_unit_id IS NULL",
            "    ",
            "    UNION ALL",
            "    ",
            "    -- Child business units",
            "    SELECT",
            "        bu.id,",
            "        bu.name,",
            "        bu.organization_id,",
            "        h.organization_name,",
            "        bu.parent_unit_id,",
            "        h.name as parent_name,",
            "        bu.manager_id,",
            "        CONCAT(p.first_name, ' ', p.last_name) as manager_name,",
            "        bu.location,",
            "        bu.email,",
            "        bu.phone_number,",
            "        bu.is_active,",
            "        h.level + 1,",
            "        h.path || bu.name",
            f"    FROM {self.schema}.aaa_business_units bu",
            "    JOIN hierarchy h ON bu.parent_unit_id = h.id",
            f"    LEFT JOIN {self.schema}.aaa_profiles p ON bu.manager_id = p.id",
            ")",
            "SELECT * FROM hierarchy;",
            "",
        ])
    
    def format_sql_value(self, value) -> str:
        """Format a Python value for SQL insertion"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            # Escape single quotes and wrap in quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            # Handle arrays (like scopes)
            formatted_items = [self.format_sql_value(item) for item in value]
            return f"ARRAY[{', '.join(formatted_items)}]"
        elif hasattr(value, 'isoformat'):
            # Handle datetime objects
            return f"'{value.isoformat()}'"
        else:
            # Convert to string and escape
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
    
    def generate_insert_statements(self, table_name: str, data: List[Dict[str, Any]]) -> List[str]:
        """Generate INSERT statements for exported data"""
        if not data:
            return []
        
        statements = []
        
        # Get all unique columns from the data
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        columns = sorted(list(all_columns))
        
        # Generate INSERT statement
        statements.append(f"-- Data exported from {table_name}")
        
        if len(data) == 1:
            # Single row insert
            row = data[0]
            values = [self.format_sql_value(row.get(col)) for col in columns]
            statements.append(f"INSERT INTO {self.schema}.{table_name} ({', '.join(columns)}) VALUES")
            statements.append(f"    ({', '.join(values)})")
            statements.append("ON CONFLICT DO NOTHING;")
        else:
            # Multi-row insert
            statements.append(f"INSERT INTO {self.schema}.{table_name} ({', '.join(columns)}) VALUES")
            
            for i, row in enumerate(data):
                values = [self.format_sql_value(row.get(col)) for col in columns]
                prefix = "    "
                suffix = "," if i < len(data) - 1 else ""
                statements.append(f"{prefix}({', '.join(values)}){suffix}")
            
            statements.append("ON CONFLICT DO NOTHING;")
        
        statements.append("")
        return statements

    def add_sample_data(self):
        """Add sample data for testing and initial setup"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- SAMPLE DATA",
            "-- =====================================================",
            "",
        ])
        
        if self.export_data and self.exported_data:
            # Use exported data
            self.output_lines.append("-- Data exported from existing database")
            self.output_lines.append("")
            
            # Tables in dependency order
            table_order = [
                'aaa_roles',
                'aaa_organizations',
                'aaa_profiles', 
                'aaa_clients',
                'aaa_business_units',
                'aaa_user_roles',
                'aaa_user_business_units',
                'aaa_email_otps',
                'aaa_password_reset_tokens'
            ]
            
            for table in table_order:
                if table in self.exported_data and self.exported_data[table]:
                    statements = self.generate_insert_statements(table, self.exported_data[table])
                    self.output_lines.extend(statements)
        else:
            # Use default sample data
            self.output_lines.extend([
                "-- Default sample data (use --export-data to use actual database data)",
                "",
                "-- Insert default roles",
                f"INSERT INTO {self.schema}.aaa_roles (name) VALUES",
                "    ('admin'),",
                "    ('super_user'),",
                "    ('firm_admin'),",
                "    ('group_admin'),",
                "    ('user')",
                "ON CONFLICT (name) DO NOTHING;",
                "",
                "-- Insert sample API client",
                f"INSERT INTO {self.schema}.aaa_clients (client_id, client_secret, name, scopes) VALUES",
                "    ('sample_client_id', 'sample_client_secret_change_in_production', 'Sample API Client', ARRAY['read:users', 'manage:users'])",
                "ON CONFLICT (client_id) DO NOTHING;",
                "",
                "-- Insert sample organizations",
                f"INSERT INTO {self.schema}.aaa_organizations (id, company_name, address_1, city_town, state, zip, country, email, phone_number) VALUES",
                "    ('11111111-1111-1111-1111-111111111111', 'Tech Solutions Inc', '123 Innovation Drive', 'San Francisco', 'CA', '94105', 'USA', 'contact@techsolutions.com', '+1-555-0101'),",
                "    ('22222222-2222-2222-2222-222222222222', 'Global Manufacturing Corp', '456 Industrial Blvd', 'Detroit', 'MI', '48201', 'USA', 'info@globalmanufacturing.com', '+1-555-0202')",
                "ON CONFLICT (id) DO NOTHING;",
                "",
                "-- Insert sample business units",
                f"INSERT INTO {self.schema}.aaa_business_units (id, name, description, code, organization_id, location, email, phone_number) VALUES",
                "    ('33333333-3333-3333-3333-333333333333', 'Engineering', 'Software Development Team', 'ENG', '11111111-1111-1111-1111-111111111111', 'San Francisco, CA', 'engineering@techsolutions.com', '+1-555-0301'),",
                "    ('44444444-4444-4444-4444-444444444444', 'Sales', 'Sales and Marketing Department', 'SALES', '11111111-1111-1111-1111-111111111111', 'San Francisco, CA', 'sales@techsolutions.com', '+1-555-0302'),",
                "    ('55555555-5555-5555-5555-555555555555', 'Production', 'Manufacturing Production Line', 'PROD', '22222222-2222-2222-2222-222222222222', 'Detroit, MI', 'production@globalmanufacturing.com', '+1-555-0303'),",
                "    ('66666666-6666-6666-6666-666666666666', 'Quality Assurance', 'Quality Control Department', 'QA', '22222222-2222-2222-2222-222222222222', 'Detroit, MI', 'qa@globalmanufacturing.com', '+1-555-0304')",
                "ON CONFLICT (id) DO NOTHING;",
                "",
                "-- Insert sample admin user (password: admin123)",
                "-- Note: In production, use proper password hashing and change default passwords",
                f"INSERT INTO {self.schema}.aaa_profiles (id, email, password_hash, first_name, last_name, is_admin) VALUES",
                "    ('77777777-7777-7777-7777-777777777777', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj7fKnKw82cO', 'System', 'Administrator', true)",
                "ON CONFLICT (email) DO NOTHING;",
                "",
                "-- Assign admin role to admin user",
                "DO $$",
                "DECLARE",
                "    admin_role_id UUID;",
                "    admin_user_id UUID := '77777777-7777-7777-7777-777777777777';",
                "BEGIN",
                f"    SELECT id INTO admin_role_id FROM {self.schema}.aaa_roles WHERE name = 'admin';",
                "    ",
                "    IF admin_role_id IS NOT NULL THEN",
                f"        INSERT INTO {self.schema}.aaa_user_roles (user_id, role_id) VALUES",
                "            (admin_user_id, admin_role_id)",
                "        ON CONFLICT (user_id, role_id) DO NOTHING;",
                "    END IF;",
                "END $$;",
                "",
            ])
    
    def add_comments(self):
        """Add helpful table and column comments"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- TABLE AND COLUMN COMMENTS",
            "-- =====================================================",
            "",
            "-- Core table comments",
            f"COMMENT ON TABLE {self.schema}.aaa_profiles IS 'User profiles with authentication data';",
            f"COMMENT ON TABLE {self.schema}.aaa_roles IS 'System roles for authorization';",
            f"COMMENT ON TABLE {self.schema}.aaa_user_roles IS 'Many-to-many relationship between users and roles';",
            f"COMMENT ON TABLE {self.schema}.aaa_clients IS 'API clients for machine-to-machine authentication';",
            "",
            "-- Organizational table comments",
            f"COMMENT ON TABLE {self.schema}.aaa_organizations IS 'Organizations/companies in the system';",
            f"COMMENT ON TABLE {self.schema}.aaa_business_units IS 'Business units within organizations supporting hierarchical structure';",
            f"COMMENT ON TABLE {self.schema}.aaa_user_business_units IS 'Assignment of users to business units';",
            "",
            "-- Security table comments",
            f"COMMENT ON TABLE {self.schema}.aaa_email_otps IS 'Email-based one-time passwords for MFA';",
            f"COMMENT ON TABLE {self.schema}.aaa_password_reset_tokens IS 'Tokens for password reset functionality';",
            "",
            "-- Key column comments",
            f"COMMENT ON COLUMN {self.schema}.aaa_profiles.mfa_method IS 'MFA method: totp (authenticator app) or email';",
            f"COMMENT ON COLUMN {self.schema}.aaa_business_units.parent_unit_id IS 'Parent business unit for hierarchical structure';",
            f"COMMENT ON COLUMN {self.schema}.aaa_business_units.code IS 'Internal reference code (alphanumeric, unique per organization)';",
            "",
        ])
    
    def add_footer(self):
        """Add footer with completion and verification steps"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- VERIFICATION AND COMPLETION",
            "-- =====================================================",
            "",
            "-- Verify table creation",
            "DO $$",
            "DECLARE",
            "    table_count INTEGER;",
            "BEGIN",
            "    SELECT COUNT(*) INTO table_count",
            "    FROM information_schema.tables",
            f"    WHERE table_schema = '{self.schema}'",
            "    AND table_name LIKE 'aaa_%';",
            "    ",
            f"    RAISE NOTICE 'Created % AAA tables in schema {self.schema}', table_count;",
            "    ",
            "    IF table_count < 9 THEN",
            "        RAISE WARNING 'Expected at least 9 AAA tables, but found %', table_count;",
            "    ELSE",
            f"        RAISE NOTICE 'Database setup completed successfully in schema {self.schema}!';",
            "    END IF;",
            "END $$;",
            "",
            "-- Display sample data counts",
            "SELECT",
            "    'Roles' as entity,",
            "    COUNT(*) as count",
            f"FROM {self.schema}.aaa_roles",
            "UNION ALL",
            "SELECT",
            "    'Organizations' as entity,",
            "    COUNT(*) as count",
            f"FROM {self.schema}.aaa_organizations",
            "UNION ALL",
            "SELECT",
            "    'Business Units' as entity,",
            "    COUNT(*) as count",
            f"FROM {self.schema}.aaa_business_units",
            "UNION ALL",
            "SELECT",
            "    'Users' as entity,",
            "    COUNT(*) as count",
            f"FROM {self.schema}.aaa_profiles;",
            "",
            "COMMIT;",
            "",
            "-- =====================================================",
            "-- SETUP COMPLETE",
            "-- =====================================================",
            "",
            "-- The database setup is now complete. You can:",
            "-- 1. Create additional users via the API or admin interface",
            "-- 2. Add more organizations and business units as needed",
            "-- 3. Configure MFA for users",
            "-- 4. Set up API clients for external integrations",
            "",
            "-- Default admin credentials:",
            "-- Email: admin@example.com",
            "-- Password: admin123",
            "-- IMPORTANT: Change the default password immediately in production!",
            "",
            f"-- Generated by User Management System Database Setup Generator",
            f"-- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ])
    
    def generate(self) -> str:
        """Generate the complete database setup script"""
        # Inspect schema first if requested
        if self.inspect_schema:
            self.inspect_database_schema()
        
        # Export data if requested
        if self.export_data:
            self.export_all_data()
        
        self.add_header()
        
        if self.inspect_schema and self.inspected_schema:
            # Use inspected schema to generate all tables
            self.add_inspected_tables()
            self.add_inspected_constraints()
        else:
            # Use hardcoded schema definitions
            self.add_core_tables()
            self.add_organizational_tables()
            self.add_security_tables()
        
        self.add_rls_disabling()
        self.add_indexes()
        self.add_functions_and_triggers()
        self.add_views()
        self.add_sample_data()
        self.add_comments()
        self.add_footer()
        
        return "\n".join(self.output_lines)
    
    def add_inspected_tables(self):
        """Add all tables based on inspected schema"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- ALL TABLES (Inspected from source database)",
            "-- =====================================================",
            "",
        ])
        
        # Generate all tables
        for table_name, table_info in self.inspected_schema.items():
            table_ddl = self.generate_table_ddl(table_name, table_info)
            self.output_lines.extend(table_ddl)
    
    def add_inspected_constraints(self):
        """Add foreign key constraints for inspected tables"""
        self.output_lines.extend([
            "-- =====================================================",
            "-- FOREIGN KEY CONSTRAINTS (Inspected from source database)", 
            "-- =====================================================",
            "",
        ])
        
        # Generate constraints for all tables
        for table_name, table_info in self.inspected_schema.items():
            constraints = self.generate_table_constraints(table_name, table_info)
            if constraints:
                self.output_lines.extend(constraints)


def main():
    """Main function to generate the database setup file"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate complete database setup for User Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate with sample data
  python generate_database_setup.py --schema user_mgmt
  
  # Export from aaa schema to new test_schema with inspected schema
  python generate_database_setup.py --export-data --inspect-schema --source-schema aaa --schema test_schema
  
  # Export with exact schema inspection (recommended)
  python generate_database_setup.py --export-data --inspect-schema --source-schema aaa --schema user_mgmt
  
  # Export with custom connection string and schema inspection
  python generate_database_setup.py --export-data --inspect-schema --source-schema aaa --schema new_schema --connection-string "postgresql://user:pass@host:port/db"
        '''
    )
    
    parser.add_argument('output_file', nargs='?', 
                        default='complete_database_setup.sql',
                        help='Output SQL filename (default: complete_database_setup.sql)')
    parser.add_argument('--schema', '-s', 
                        default='public',
                        help='Target database schema (default: public)')
    parser.add_argument('--output', '-o',
                        help='Output filename (alternative to positional argument)')
    parser.add_argument('--export-data', '--export', 
                        action='store_true',
                        help='Export existing data from database instead of using sample data')
    parser.add_argument('--source-schema', '--from-schema',
                        help='Source schema to export data from (default: same as target schema)')
    parser.add_argument('--inspect-schema', '--inspect',
                        action='store_true',
                        help='Inspect actual database schema instead of using templates')
    parser.add_argument('--connection-string', '--conn',
                        help='Database connection string (overrides .env file)')
    
    args = parser.parse_args()
    
    # Use --output if provided, otherwise use positional argument
    output_file = args.output if args.output else args.output_file
    
    # Validate schema name (basic validation)
    if not args.schema.replace('_', '').replace('-', '').isalnum():
        print(f"❌ Invalid schema name: {args.schema}")
        print("   Schema names should contain only letters, numbers, underscores, and hyphens")
        sys.exit(1)
    
    # Check dependencies for data export
    if args.export_data:
        if not PSYCOPG2_AVAILABLE:
            print("❌ Data export requires psycopg2. Install with:")
            print("   pip install psycopg2-binary")
            sys.exit(1)
        
        if not DOTENV_AVAILABLE:
            print("⚠️  python-dotenv not available. Environment variables will be read from system only.")
            print("   Install with: pip install python-dotenv")
    
    # Generate the setup script
    try:
        generator = DatabaseSetupGenerator(
            schema=args.schema, 
            export_data=args.export_data,
            connection_string=args.connection_string,
            source_schema=args.source_schema,
            inspect_schema=args.inspect_schema
        )
        setup_script = generator.generate()
    except Exception as e:
        print(f"❌ Error generating setup script: {e}")
        sys.exit(1)
    
    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(setup_script)
        
        print(f"✅ Database setup script generated successfully: {output_file}")
        print(f"📊 Script length: {len(setup_script.splitlines())} lines")
        print(f"📁 File size: {len(setup_script.encode('utf-8'))} bytes")
        print(f"🗂️  Target schema: {args.schema}")
        if args.export_data:
            source_schema = args.source_schema or args.schema
            print(f"📤 Data source: Exported from '{source_schema}' schema")
        else:
            print(f"📝 Data source: Default sample data")
        print()
        print("🚀 To use this script:")
        print(f"   psql -U your_username -d your_database_name -f {output_file}")
        print()
        if args.schema != 'public':
            print("📋 Schema-specific notes:")
            print(f"   • Tables will be created in '{args.schema}' schema")
            print(f"   • Make sure your application connects to the correct schema")
            print(f"   • Update your connection string or search_path as needed")
            print()
        print("⚠️  Remember to:")
        print("   1. Change default passwords in production")
        if args.export_data:
            print("   2. Review exported data for sensitive information")
        else:
            print("   2. Review and customize sample data")
        print("   3. Set appropriate database permissions")
        print("   4. Configure environment variables for your application")
        if args.schema != 'public':
            print(f"   5. Update application to use schema '{args.schema}'")
        
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()