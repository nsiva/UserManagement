#!/usr/bin/env python3

import psycopg2
import os
from datetime import datetime
from typing import List, Dict, Any


class PostgresDBExporter:
    """
    A utility class to connect to PostgreSQL database and generate SQL statements
    that can be used to recreate the database structure and data.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the exporter with a PostgreSQL connection string.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            print(f"✓ Connected to PostgreSQL database successfully")
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✓ Database connection closed")
    
    def get_tables(self, schema_name: str = 'aaa') -> List[str]:
        """
        Get all tables in the specified schema.
        
        Args:
            schema_name: Database schema name (default: 'aaa')
            
        Returns:
            List of table names
        """
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        self.cursor.execute(query, (schema_name,))
        tables = [row[0] for row in self.cursor.fetchall()]
        print(f"✓ Found {len(tables)} tables in schema '{schema_name}': {', '.join(tables)}")
        return tables
    
    def get_table_structure(self, table_name: str, schema_name: str = 'aaa') -> str:
        """
        Generate CREATE TABLE statement for the given table.
        
        Args:
            table_name: Name of the table
            schema_name: Database schema name (default: 'aaa')
            
        Returns:
            CREATE TABLE SQL statement
        """
        # Get column information
        columns_query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        self.cursor.execute(columns_query, (schema_name, table_name))
        columns = self.cursor.fetchall()
        
        # Get primary key information
        pk_query = """
        SELECT column_name
        FROM information_schema.key_column_usage k
        JOIN information_schema.table_constraints t
        ON k.constraint_name = t.constraint_name
        WHERE t.table_schema = %s 
        AND t.table_name = %s 
        AND t.constraint_type = 'PRIMARY KEY'
        ORDER BY k.ordinal_position;
        """
        
        self.cursor.execute(pk_query, (schema_name, table_name))
        primary_keys = [row[0] for row in self.cursor.fetchall()]
        
        # Get foreign key information
        fk_query = """
        SELECT 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema = %s
        AND tc.table_name = %s;
        """
        
        self.cursor.execute(fk_query, (schema_name, table_name))
        foreign_keys = self.cursor.fetchall()
        
        # Build CREATE TABLE statement
        create_sql = f"CREATE TABLE {schema_name}.{table_name} (\n"
        
        column_definitions = []
        for col in columns:
            col_name, data_type, is_nullable, default, max_length, precision, scale = col
            
            # Build column definition
            col_def = f"    {col_name} {data_type.upper()}"
            
            # Add length/precision info
            if data_type.upper() in ['VARCHAR', 'CHAR'] and max_length:
                col_def += f"({max_length})"
            elif data_type.upper() in ['NUMERIC', 'DECIMAL'] and precision:
                if scale:
                    col_def += f"({precision},{scale})"
                else:
                    col_def += f"({precision})"
            
            # Add NOT NULL constraint
            if is_nullable == 'NO':
                col_def += " NOT NULL"
            
            # Add default value
            if default:
                col_def += f" DEFAULT {default}"
                
            column_definitions.append(col_def)
        
        create_sql += ",\n".join(column_definitions)
        
        # Add primary key constraint
        if primary_keys:
            create_sql += f",\n    PRIMARY KEY ({', '.join(primary_keys)})"
        
        # Add foreign key constraints
        for fk in foreign_keys:
            col_name, ref_table, ref_column = fk
            create_sql += f",\n    FOREIGN KEY ({col_name}) REFERENCES {schema_name}.{ref_table}({ref_column})"
        
        create_sql += "\n);"
        
        return create_sql
    
    def get_table_data(self, table_name: str, schema_name: str = 'aaa') -> List[str]:
        """
        Generate INSERT statements for all data in the given table.
        
        Args:
            table_name: Name of the table
            schema_name: Database schema name (default: 'aaa')
            
        Returns:
            List of INSERT SQL statements
        """
        # Get all data from table
        self.cursor.execute(f"SELECT * FROM {schema_name}.{table_name}")
        rows = self.cursor.fetchall()
        
        if not rows:
            return []
        
        # Get column names
        self.cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """, (schema_name, table_name))
        
        columns = [row[0] for row in self.cursor.fetchall()]
        
        insert_statements = []
        
        # Generate INSERT statements
        for row in rows:
            values = []
            for value in row:
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    # Escape single quotes in strings
                    escaped_value = value.replace("'", "''")
                    values.append(f"'{escaped_value}'")
                elif isinstance(value, bool):
                    values.append("TRUE" if value else "FALSE")
                elif isinstance(value, list):
                    # Handle PostgreSQL arrays
                    if not value:
                        values.append("ARRAY[]::TEXT[]")
                    else:
                        array_values = [f"'{str(v)}'" for v in value]
                        values.append(f"ARRAY[{', '.join(array_values)}]::TEXT[]")
                elif hasattr(value, 'strftime'):
                    # Handle datetime objects - format as ISO string with quotes
                    values.append(f"'{value.isoformat()}'")
                else:
                    # For any other type, quote it as string
                    values.append(f"'{str(value)}'")
            
            columns_str = ', '.join(columns)
            values_str = ', '.join(values)
            insert_sql = f"INSERT INTO {schema_name}.{table_name} ({columns_str}) VALUES ({values_str});"
            insert_statements.append(insert_sql)
        
        return insert_statements
    
    def export_database(self, output_file: str = None, schema_name: str = 'aaa') -> str:
        """
        Export the entire database structure and data to SQL file.
        
        Args:
            output_file: Output file path (optional)
            schema_name: Database schema name (default: 'aaa')
            
        Returns:
            Generated SQL content as string
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"database_export_{timestamp}.sql"
        
        sql_content = []
        
        # Header
        sql_content.append(f"-- Database Export Generated on {datetime.now()}")
        sql_content.append(f"-- Schema: {schema_name}")
        sql_content.append("")
        sql_content.append("-- Begin Transaction")
        sql_content.append("BEGIN;")
        sql_content.append("")
        
        # Create schema if not exists
        sql_content.append(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        sql_content.append(f"SET search_path TO {schema_name};")
        sql_content.append("")
        
        try:
            # Get all tables
            tables = self.get_tables(schema_name)
            
            # Table creation order (based on dependencies from EXPORT_GUIDE.md)
            table_order = [
                'aaa_roles',
                'aaa_profiles', 
                'aaa_clients',
                'aaa_user_roles',
                'aaa_password_reset_tokens'
            ]
            
            # Add any additional tables not in the predefined order
            remaining_tables = [t for t in tables if t not in table_order]
            ordered_tables = [t for t in table_order if t in tables] + remaining_tables
            
            # Generate DROP and CREATE statements
            sql_content.append("-- Drop existing tables (in reverse dependency order)")
            for table in reversed(ordered_tables):
                sql_content.append(f"DROP TABLE IF EXISTS {schema_name}.{table} CASCADE;")
            sql_content.append("")
            
            # Generate CREATE TABLE statements
            sql_content.append("-- Create tables")
            for table in ordered_tables:
                print(f"Generating structure for table: {table}")
                create_sql = self.get_table_structure(table, schema_name)
                sql_content.append(f"-- Table: {table}")
                sql_content.append(create_sql)
                sql_content.append("")
            
            # Generate INSERT statements
            sql_content.append("-- Insert data")
            total_rows = 0
            for table in ordered_tables:
                print(f"Generating data for table: {table}")
                insert_statements = self.get_table_data(table, schema_name)
                if insert_statements:
                    sql_content.append(f"-- Data for table: {table} ({len(insert_statements)} rows)")
                    sql_content.extend(insert_statements)
                    sql_content.append("")
                    total_rows += len(insert_statements)
                else:
                    sql_content.append(f"-- No data for table: {table}")
                    sql_content.append("")
            
            # Footer
            sql_content.append("-- Commit Transaction")
            sql_content.append("COMMIT;")
            sql_content.append("")
            sql_content.append(f"-- Export completed: {len(ordered_tables)} tables, {total_rows} total rows")
            
        except Exception as e:
            sql_content.append("-- Error occurred during export")
            sql_content.append("ROLLBACK;")
            print(f"✗ Error during export: {e}")
            raise
        
        # Write to file
        final_sql = '\n'.join(sql_content)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_sql)
        
        print(f"✓ Database export completed: {output_file}")
        return final_sql


def main():
    """Main function to run the database export."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get connection string from environment
    connection_string = os.getenv('POSTGRES_CONNECTION_STRING')
    
    if not connection_string:
        print("✗ Error: POSTGRES_CONNECTION_STRING environment variable not found")
        print("Please check your .env file")
        return
    
    # Fix connection string format for psycopg2
    if 'options=-csearch_path=' in connection_string:
        # Extract schema from options and create a proper psycopg2 connection string
        base_conn = connection_string.split('?')[0]
        schema_part = connection_string.split('options=-csearch_path=')[1]
        connection_string = base_conn
        print(f"Using schema: {schema_part}")
    
    print("PostgreSQL Database Exporter")
    print("=" * 50)
    print(f"Connection string: {connection_string.replace('postgresql://postgres:@', 'postgresql://postgres:***@')}")
    print()
    
    # Create exporter instance
    exporter = PostgresDBExporter(connection_string)
    
    try:
        # Connect to database
        exporter.connect()
        
        # Export database
        output_file = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        sql_content = exporter.export_database(output_file)
        
        print()
        print("Export Summary:")
        print(f"- Output file: {output_file}")
        print(f"- File size: {len(sql_content)} characters")
        print()
        print("You can now use this SQL file to recreate the database on another PostgreSQL instance:")
        print(f"  psql -d target_database -f {output_file}")
        
    except Exception as e:
        print(f"✗ Export failed: {e}")
    finally:
        exporter.disconnect()


if __name__ == "__main__":
    main()