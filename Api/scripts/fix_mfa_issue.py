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

def get_user_info(email):
    """Get current user information"""
    try:
        response = supabase.from_('aaa_profiles').select('*').eq('email', email).limit(1).execute()
        
        if response.data:
            user = response.data[0]
            print(f"=== Current Status for {email} ===")
            print(f"User ID: {user['id']}")
            print(f"Email: {user['email']}")
            print(f"Is Admin: {user['is_admin']}")
            print(f"MFA Secret: {user['mfa_secret']}")
            print(f"Created: {user.get('created_at', 'N/A')}")
            return user
        else:
            print(f"❌ User {email} not found!")
            return None
            
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
        return None

def disable_mfa_direct(email):
    """Disable MFA using direct SQL-like approach"""
    try:
        # Get user first
        user_response = supabase.from_('aaa_profiles').select('id').eq('email', email).limit(1).execute()
        
        if not user_response.data:
            print(f"❌ User {email} not found!")
            return False
            
        user_id = user_response.data[0]['id']
        
        # Update MFA secret to null
        update_response = supabase.from_('aaa_profiles').update({
            'mfa_secret': None
        }).eq('id', user_id).execute()
        
        print(f"Update response: {update_response}")
        
        # Check if update was successful by querying again
        verify_response = supabase.from_('aaa_profiles').select('mfa_secret').eq('email', email).limit(1).execute()
        
        if verify_response.data:
            mfa_secret = verify_response.data[0]['mfa_secret']
            if mfa_secret is None:
                print(f"✅ MFA successfully disabled for {email}")
                return True
            else:
                print(f"❌ MFA still enabled. Secret: {mfa_secret}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error disabling MFA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    email = "n_sivakumar@yahoo.com"
    
    print("Getting current user info...")
    user = get_user_info(email)
    
    if user and user['mfa_secret']:
        print(f"\n🔑 IMPORTANT - Save this MFA secret: {user['mfa_secret']}")
        print("\nYou have two options:")
        print("1. Use this secret in your authenticator app NOW (recommended)")
        print("2. Disable MFA temporarily to get a new QR code")
        
        print("\nTrying to disable MFA temporarily...")
        success = disable_mfa_direct(email)
        
        if success:
            print("\n" + "="*70)
            print("SUCCESS! MFA has been temporarily disabled.")
            print("="*70)
            print("Now you can login normally:")
            print("")
            print(f'curl -X POST "http://localhost:8001/auth/login" \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{"email": "{email}", "password": "password@1"}}\'')
            print("")
            print("After login, you can re-setup MFA with a QR code.")
        else:
            print("\n" + "="*70)
            print("MFA DISABLE FAILED - But you can still use the secret!")
            print("="*70)
            print("Manual setup in authenticator app:")
            print(f"1. Open your authenticator app")
            print(f"2. Choose 'Enter a setup key' or 'Manual entry'")
            print(f"3. Account name: {email}")
            print(f"4. Secret key: {user['mfa_secret']}")
            print(f"5. Type: Time-based")
            print(f"6. Test with MFA verification endpoint")
    else:
        print("✅ MFA is not enabled for this user.")