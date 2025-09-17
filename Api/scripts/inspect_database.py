#!/usr/bin/env python3
"""
Database Inspector for User Management System

This script connects to your database and provides detailed information about:
- Table structure and relationships
- Sample data counts
- Index status
- Constraint validation
- View definitions

Usage:
    python inspect_database.py [connection_string]

Examples:
    python inspect_database.py "postgresql://user:pass@localhost:5432/dbname"
    python inspect_database.py  # Uses environment variables

Environment Variables:
    DATABASE_URL or SUPABASE_URL
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME (if not using URL)
"""

import sys
import os
import asyncio
import asyncpg
from typing import Dict, List, Any
from urllib.parse import urlparse


class DatabaseInspector:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
    
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
    
    async def get_table_info(self) -> List[Dict[str, Any]]:
        """Get information about all AAA tables"""
        query = """
        SELECT 
            table_name,
            (SELECT COUNT(*) FROM information_schema.columns 
             WHERE table_name = t.table_name AND table_schema = 'public') as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
        AND table_name LIKE 'aaa_%'
        ORDER BY table_name;
        """
        return await self.conn.fetch(query)
    
    async def get_data_counts(self) -> Dict[str, int]:
        """Get record counts for all tables"""
        tables = await self.get_table_info()
        counts = {}
        
        for table in tables:
            table_name = table['table_name']
            try:
                count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                counts[table_name] = count
            except Exception as e:
                counts[table_name] = f"Error: {e}"
        
        return counts
    
    async def get_constraints(self) -> List[Dict[str, Any]]:
        """Get constraint information"""
        query = """
        SELECT 
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            CASE 
                WHEN tc.constraint_type = 'FOREIGN KEY' THEN
                    ccu.table_name || '(' || ccu.column_name || ')'
                ELSE NULL
            END as foreign_table
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_schema = 'public'
        AND tc.table_name LIKE 'aaa_%'
        ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;
        """
        return await self.conn.fetch(query)
    
    async def get_indexes(self) -> List[Dict[str, Any]]:
        """Get index information"""
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'aaa_%'
        ORDER BY tablename, indexname;
        """
        return await self.conn.fetch(query)
    
    async def get_views(self) -> List[Dict[str, Any]]:
        """Get view information"""
        query = """
        SELECT 
            table_name as view_name,
            view_definition
        FROM information_schema.views
        WHERE table_schema = 'public'
        AND table_name LIKE 'vw_%'
        ORDER BY table_name;
        """
        return await self.conn.fetch(query)
    
    async def get_functions(self) -> List[Dict[str, Any]]:
        """Get custom function information"""
        query = """
        SELECT 
            routine_name,
            routine_type,
            data_type,
            routine_definition
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name NOT LIKE 'pg_%'
        ORDER BY routine_name;
        """
        return await self.conn.fetch(query)
    
    async def check_sample_admin(self) -> Dict[str, Any]:
        """Check if sample admin user exists"""
        query = """
        SELECT 
            id,
            email,
            first_name,
            last_name,
            is_admin,
            mfa_method,
            created_at,
            (SELECT ARRAY_AGG(r.name) FROM aaa_user_roles ur 
             JOIN aaa_roles r ON ur.role_id = r.id 
             WHERE ur.user_id = p.id) as roles
        FROM aaa_profiles p
        WHERE email = 'admin@example.com';
        """
        result = await self.conn.fetchrow(query)
        return dict(result) if result else {}
    
    def print_separator(self, title: str):
        """Print a formatted separator"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    async def inspect(self):
        """Run complete database inspection"""
        await self.connect()
        
        try:
            # Table Overview
            self.print_separator("TABLE OVERVIEW")
            tables = await self.get_table_info()
            print(f"Found {len(tables)} AAA tables:\n")
            for table in tables:
                print(f"  📋 {table['table_name']:<30} ({table['column_count']} columns)")
            
            # Data Counts
            self.print_separator("DATA COUNTS")
            counts = await self.get_data_counts()
            total_records = 0
            for table_name, count in counts.items():
                if isinstance(count, int):
                    total_records += count
                    print(f"  📊 {table_name:<30} {count:>8} records")
                else:
                    print(f"  ❌ {table_name:<30} {count}")
            print(f"\n  📈 Total records across all tables: {total_records}")
            
            # Constraints
            self.print_separator("CONSTRAINTS")
            constraints = await self.get_constraints()
            constraint_types = {}
            for constraint in constraints:
                ctype = constraint['constraint_type']
                constraint_types[ctype] = constraint_types.get(ctype, 0) + 1
            
            print("Constraint summary:")
            for ctype, count in constraint_types.items():
                print(f"  🔒 {ctype:<20} {count:>3} constraints")
            
            print("\nForeign Key relationships:")
            for constraint in constraints:
                if constraint['constraint_type'] == 'FOREIGN KEY':
                    print(f"  🔗 {constraint['table_name']}.{constraint['column_name']} → {constraint['foreign_table']}")
            
            # Indexes
            self.print_separator("INDEXES")
            indexes = await self.get_indexes()
            print(f"Found {len(indexes)} indexes:\n")
            current_table = None
            for index in indexes:
                if index['tablename'] != current_table:
                    current_table = index['tablename']
                    print(f"\n  📋 {current_table}:")
                print(f"    🔍 {index['indexname']}")
            
            # Views
            self.print_separator("VIEWS")
            views = await self.get_views()
            if views:
                print(f"Found {len(views)} views:\n")
                for view in views:
                    print(f"  👁️  {view['view_name']}")
            else:
                print("  ⚠️  No views found")
            
            # Functions
            self.print_separator("CUSTOM FUNCTIONS")
            functions = await self.get_functions()
            if functions:
                print(f"Found {len(functions)} custom functions:\n")
                for func in functions:
                    print(f"  ⚙️  {func['routine_name']} ({func['routine_type']})")
            else:
                print("  ⚠️  No custom functions found")
            
            # Sample Admin Check
            self.print_separator("SAMPLE ADMIN USER")
            admin = await self.check_sample_admin()
            if admin:
                print(f"  ✅ Sample admin user found:")
                print(f"     Email: {admin['email']}")
                print(f"     Name: {admin['first_name']} {admin['last_name']}")
                print(f"     Admin: {admin['is_admin']}")
                print(f"     MFA: {admin.get('mfa_method', 'None')}")
                print(f"     Roles: {admin.get('roles', [])}")
                print(f"     Created: {admin['created_at']}")
                print(f"\n  ⚠️  Remember to change the default password!")
            else:
                print("  ⚠️  Sample admin user not found")
            
            # Health Check
            self.print_separator("HEALTH CHECK")
            issues = []
            
            if len(tables) < 9:
                issues.append(f"Expected at least 9 tables, found {len(tables)}")
            
            if not views:
                issues.append("No views found - may affect reporting functionality")
            
            if not functions:
                issues.append("No custom functions found - business logic may be missing")
            
            if not admin:
                issues.append("No default admin user found")
            
            if issues:
                print("  ⚠️  Issues found:")
                for issue in issues:
                    print(f"     • {issue}")
            else:
                print("  ✅ Database structure looks healthy!")
            
            print(f"\n{'='*60}")
            print(" INSPECTION COMPLETE")
            print(f"{'='*60}")
            
        finally:
            await self.disconnect()


def get_connection_string() -> str:
    """Get database connection string from arguments or environment"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # Try environment variables
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    
    if os.getenv('SUPABASE_URL'):
        return os.getenv('SUPABASE_URL')
    
    # Try individual components
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'postgres')
    
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        return f"postgresql://{user}@{host}:{port}/{database}"


async def main():
    """Main inspection function"""
    try:
        connection_string = get_connection_string()
        
        # Parse URL to hide password in output
        parsed = urlparse(connection_string)
        safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"
        
        print("🔍 User Management System - Database Inspector")
        print(f"🔗 Connecting to: {safe_url}")
        
        inspector = DatabaseInspector(connection_string)
        await inspector.inspect()
        
    except KeyboardInterrupt:
        print("\n❌ Inspection cancelled by user")
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
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