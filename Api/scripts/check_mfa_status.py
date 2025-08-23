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

def check_user_mfa_status(email):
    try:
        # Get user info
        response = supabase.from_('aaa_profiles').select('id, email, is_admin, mfa_secret').eq('email', email).limit(1).execute()
        
        if not response.data:
            print(f"❌ User {email} not found!")
            return False
            
        user = response.data[0]
        has_mfa = user['mfa_secret'] is not None
        
        print(f"=== User Status for {email} ===")
        print(f"User ID: {user['id']}")
        print(f"Email: {user['email']}")
        print(f"Is Admin: {user['is_admin']}")
        print(f"Has MFA: {'Yes' if has_mfa else 'No'}")
        
        if has_mfa:
            print(f"MFA Secret: {user['mfa_secret'][:10]}..." if user['mfa_secret'] else 'None')
            print("\n⚠️  MFA is enabled for this user!")
            print("This is why you're getting 'MFA required' when logging in.")
        else:
            print("\n✅ No MFA configured for this user.")
            
        return has_mfa
        
    except Exception as e:
        print(f"❌ Error checking MFA status: {e}")
        return False

def disable_mfa_temporarily(email):
    """Temporarily disable MFA so user can login and set up authenticator app"""
    try:
        response = supabase.from_('aaa_profiles').update({
            'mfa_secret': None
        }).eq('email', email).execute()
        
        if response.count > 0:
            print(f"✅ MFA temporarily disabled for {email}")
            print("You can now login normally to get an access token.")
            return True
        else:
            print(f"❌ Failed to disable MFA for {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error disabling MFA: {e}")
        return False

if __name__ == "__main__":
    email = "n_sivakumar@yahoo.com"
    
    print("Checking MFA status...")
    has_mfa = check_user_mfa_status(email)
    
    if has_mfa:
        print("\n" + "="*50)
        print("SOLUTION OPTIONS:")
        print("="*50)
        print("1. Temporarily disable MFA to get access token")
        print("2. Use the existing secret to set up your authenticator app")
        print("3. Create a new admin user without MFA")
        print("")
        
        choice = input("Choose option (1/2/3) or 'q' to quit: ").strip().lower()
        
        if choice == '1':
            print("\nDisabling MFA temporarily...")
            if disable_mfa_temporarily(email):
                print("\n" + "="*60)
                print("NEXT STEPS:")
                print("="*60)
                print("1. Login to get access token:")
                print(f'   curl -X POST "http://localhost:8001/auth/login" \\')
                print(f'     -H "Content-Type: application/json" \\')
                print(f'     -d \'{{"email": "{email}", "password": "password@1"}}\'')
                print("")
                print("2. Use the token to set up MFA:")
                print(f'   curl -X POST "http://localhost:8001/auth/mfa/setup?email={email}" \\')
                print(f'     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"')
                print("")
                print("3. Scan QR code or enter secret in authenticator app")
                print("4. Test MFA login")
                
        elif choice == '2':
            print("\nThe existing MFA secret is shown above.")
            print("You can manually enter this in your authenticator app:")
            print("1. Open Google Authenticator/Microsoft Authenticator/Authy")
            print("2. Choose 'Enter a setup key' or 'Manual entry'")
            print(f"3. Account name: {email}")
            print("4. Key: [Use the secret shown above]")
            print("5. Type: Time-based")
            
        elif choice == '3':
            print("\nTo create a new admin user, modify and run:")
            print("python3 sqls/create_admin.py")
            print("(Edit the email/password in the script first)")
            
        else:
            print("No action taken.")
    else:
        print("\n✅ User can login normally. MFA not enabled.")