#!/usr/bin/env python3

"""
Quick Data Query Script for Supabase Tables

This script provides a quick overview of what data currently exists in your 
Supabase aaa_* tables. Use this to understand your current data structure 
before running the full export.

Usage:
    python3 query_current_data.py
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Dict, Any, List

# Load environment variables
load_dotenv()


class DataInspector:
    """Inspect current data in Supabase tables."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.service_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.service_key)
    
    def get_table_count(self, table_name: str) -> int:
        """Get the count of records in a table."""
        try:
            response = self.client.from_(table_name).select('*', count='exact').limit(1).execute()
            return response.count if response.count is not None else 0
        except Exception as e:
            print(f"❌ Error counting {table_name}: {e}")
            return 0
    
    def get_sample_records(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample records from a table."""
        try:
            response = self.client.from_(table_name).select('*').limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Error getting samples from {table_name}: {e}")
            return []
    
    def inspect_profiles_table(self):
        """Detailed inspection of aaa_profiles table."""
        print("\n" + "=" * 50)
        print("👥 AAA_PROFILES TABLE ANALYSIS")
        print("=" * 50)
        
        count = self.get_table_count('aaa_profiles')
        print(f"Total users: {count}")
        
        if count > 0:
            # Get all users with key information
            try:
                response = self.client.from_('aaa_profiles').select(
                    'id, email, first_name, last_name, is_admin, mfa_secret'
                ).execute()
                
                if response.data:
                    print("\nUser Details:")
                    for user in response.data:
                        mfa_status = "✅ Enabled" if user.get('mfa_secret') else "❌ Disabled"
                        admin_status = "👑 Admin" if user.get('is_admin') else "👤 User"
                        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                        name_display = f" ({name})" if name else ""
                        
                        print(f"  • {user['email']}{name_display}")
                        print(f"    ID: {user['id']}")
                        print(f"    Status: {admin_status} | MFA: {mfa_status}")
                        print()
            except Exception as e:
                print(f"❌ Error getting user details: {e}")
    
    def inspect_roles_table(self):
        """Detailed inspection of aaa_roles table."""
        print("\n" + "=" * 50) 
        print("🛡️  AAA_ROLES TABLE ANALYSIS")
        print("=" * 50)
        
        try:
            response = self.client.from_('aaa_roles').select('*').execute()
            
            if response.data:
                print(f"Total roles: {len(response.data)}")
                print("\nRole Details:")
                for role in response.data:
                    print(f"  • {role['name']} (ID: {role['id']})")
                    print(f"    Created: {role.get('created_at', 'Unknown')}")
            else:
                print("No roles found")
                
        except Exception as e:
            print(f"❌ Error getting roles: {e}")
    
    def inspect_user_roles_table(self):
        """Detailed inspection of aaa_user_roles table."""
        print("\n" + "=" * 50)
        print("🔗 AAA_USER_ROLES TABLE ANALYSIS") 
        print("=" * 50)
        
        try:
            # Get user-role relationships with names
            response = self.client.from_('aaa_user_roles').select(
                'user_id, role_id, assigned_at, aaa_profiles(email), aaa_roles(name)'
            ).execute()
            
            if response.data:
                print(f"Total user-role assignments: {len(response.data)}")
                print("\nAssignments:")
                for assignment in response.data:
                    user_email = assignment['aaa_profiles']['email'] if assignment['aaa_profiles'] else 'Unknown'
                    role_name = assignment['aaa_roles']['name'] if assignment['aaa_roles'] else 'Unknown'
                    assigned_date = assignment.get('assigned_at', 'Unknown')
                    
                    print(f"  • {user_email} → {role_name}")
                    print(f"    Assigned: {assigned_date}")
            else:
                print("No user-role assignments found")
                
        except Exception as e:
            print(f"❌ Error getting user-role assignments: {e}")
    
    def inspect_clients_table(self):
        """Detailed inspection of aaa_clients table."""
        print("\n" + "=" * 50)
        print("🔑 AAA_CLIENTS TABLE ANALYSIS")
        print("=" * 50)
        
        try:
            response = self.client.from_('aaa_clients').select('*').execute()
            
            if response.data:
                print(f"Total API clients: {len(response.data)}")
                print("\nClient Details:")
                for client in response.data:
                    status = "✅ Active" if client.get('is_active') else "❌ Inactive"
                    scopes = client.get('scopes', [])
                    scopes_display = ", ".join(scopes) if scopes else "None"
                    
                    print(f"  • {client['name']} ({client['client_id']})")
                    print(f"    Status: {status}")
                    print(f"    Scopes: {scopes_display}")
                    print(f"    Created: {client.get('created_at', 'Unknown')}")
                    print()
            else:
                print("No API clients found")
                
        except Exception as e:
            print(f"❌ Error getting API clients: {e}")
    
    def inspect_reset_tokens_table(self):
        """Detailed inspection of aaa_password_reset_tokens table."""
        print("\n" + "=" * 50)
        print("🔐 AAA_PASSWORD_RESET_TOKENS TABLE ANALYSIS")
        print("=" * 50)
        
        try:
            response = self.client.from_('aaa_password_reset_tokens').select(
                'id, user_id, expires_at, used, created_at, aaa_profiles(email)'
            ).execute()
            
            if response.data:
                active_tokens = [t for t in response.data if not t['used']]
                expired_tokens = [t for t in response.data if t['used']]
                
                print(f"Total reset tokens: {len(response.data)}")
                print(f"Active tokens: {len(active_tokens)}")
                print(f"Used tokens: {len(expired_tokens)}")
                
                if active_tokens:
                    print("\nActive Reset Tokens:")
                    for token in active_tokens:
                        user_email = token['aaa_profiles']['email'] if token['aaa_profiles'] else 'Unknown'
                        print(f"  • User: {user_email}")
                        print(f"    Expires: {token['expires_at']}")
                        print(f"    Created: {token['created_at']}")
                        print()
            else:
                print("No password reset tokens found")
                
        except Exception as e:
            print(f"❌ Error getting reset tokens: {e}")
    
    def run_full_inspection(self):
        """Run complete data inspection."""
        print("🔍 SUPABASE DATA INSPECTION REPORT")
        print("=" * 60)
        
        # Get overview counts first
        tables = [
            'aaa_profiles',
            'aaa_roles', 
            'aaa_user_roles',
            'aaa_clients',
            'aaa_password_reset_tokens'
        ]
        
        print("📊 OVERVIEW:")
        total_records = 0
        for table in tables:
            count = self.get_table_count(table)
            total_records += count
            print(f"{table:<30}: {count:>6} records")
        
        print("-" * 40)
        print(f"{'TOTAL RECORDS':<30}: {total_records:>6}")
        
        # Detailed inspections
        self.inspect_profiles_table()
        self.inspect_roles_table()
        self.inspect_user_roles_table() 
        self.inspect_clients_table()
        self.inspect_reset_tokens_table()
        
        print("\n" + "=" * 60)
        print("✅ INSPECTION COMPLETED")
        print("=" * 60)
        print("\n💡 Next Steps:")
        print("1. If you see data you want to export, run: python3 export_supabase_data.py")
        print("2. The export script will create SQL INSERT statements for local PostgreSQL")
        print("3. Review the data structure to understand what will be migrated")


def main():
    """Main function to run the inspection."""
    try:
        inspector = DataInspector()
        inspector.run_full_inspection()
        
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in your .env file")
        print("2. Check your network connection to Supabase") 
        print("3. Verify your service key has read access to the aaa_* tables")


if __name__ == "__main__":
    main()