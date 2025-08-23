#!/usr/bin/env python3

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_KEY")

if not supabase_url or not service_key:
    print("❌ Environment variables not found!")
    exit(1)

supabase = create_client(supabase_url, service_key)

def disable_mfa_temporarily(email):
    """Temporarily disable MFA so user can login and set up authenticator app"""
    try:
        # First, get current MFA secret to display it
        get_response = supabase.from_('aaa_profiles').select('mfa_secret').eq('email', email).limit(1).execute()
        
        if get_response.data and get_response.data[0]['mfa_secret']:
            current_secret = get_response.data[0]['mfa_secret']
            print(f"Current MFA Secret: {current_secret}")
            print("\n📱 You can use this secret to set up your authenticator app manually:")
            print(f"   Account: {email}")
            print(f"   Secret: {current_secret}")
            print("   Type: Time-based (TOTP)")
            print("   Digits: 6")
            print("   Period: 30 seconds")
        
        # Temporarily disable MFA
        response = supabase.from_('aaa_profiles').update({
            'mfa_secret': None
        }).eq('email', email).execute()
        
        if response.count > 0:
            print(f"\n✅ MFA temporarily disabled for {email}")
            print("\nYou can now:")
            print("1. Login normally to get an access token")
            print("2. Use the token to re-setup MFA with QR code")
            print("3. Or use the secret above to configure your authenticator app now")
            return True
        else:
            print(f"❌ Failed to disable MFA for {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error disabling MFA: {e}")
        return False

if __name__ == "__main__":
    email = "n_sivakumar@yahoo.com"
    
    print(f"Temporarily disabling MFA for {email}...")
    
    if disable_mfa_temporarily(email):
        print("\n" + "="*70)
        print("IMMEDIATE NEXT STEPS:")
        print("="*70)
        print("Option A - Login and re-setup MFA with QR code:")
        print(f'1. curl -X POST "http://localhost:8001/auth/login" \\')
        print(f'     -H "Content-Type: application/json" \\')
        print(f'     -d \'{{"email": "{email}", "password": "password@1"}}\'')
        print("")
        print("2. Copy the access_token from response")
        print("")
        print(f'3. curl -X POST "http://localhost:8001/auth/mfa/setup?email={email}" \\')
        print(f'     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"')
        print("")
        print("Option B - Use the existing secret above in your authenticator app now")
        print("="*70)
    else:
        print("❌ Failed to disable MFA. Check your database connection.")