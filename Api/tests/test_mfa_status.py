#!/usr/bin/env python3

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("🔍 Checking user MFA status in database...\n")

try:
    # Get all users with MFA information
    response = supabase.from_('aaa_profiles').select('id, email, first_name, last_name, is_admin, mfa_secret').execute()
    
    if not response.data:
        print("❌ No users found in database")
        exit(1)
    
    print(f"Found {len(response.data)} users:")
    print("-" * 80)
    
    for user in response.data:
        mfa_enabled = bool(user.get('mfa_secret'))
        mfa_status = "✅ ENABLED" if mfa_enabled else "❌ NOT SETUP"
        
        print(f"Email: {user['email']}")
        print(f"Name: {user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}")
        print(f"Admin: {'Yes' if user.get('is_admin') else 'No'}")
        print(f"MFA: {mfa_status}")
        print(f"MFA Secret Present: {bool(user.get('mfa_secret'))}")
        print("-" * 80)
    
    print(f"\n✅ Database query successful. MFA data is available.")
    
except Exception as e:
    print(f"❌ Error querying database: {e}")
    exit(1)