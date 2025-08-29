import os
import uuid
from datetime import datetime
from passlib.context import CryptContext
from supabase import create_client
from dotenv import load_dotenv
import sys

load_dotenv()

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Service Key exists: {'Yes' if service_key else 'No'}")

if not supabase_url or not service_key:
    print("Error: Environment variables not found!")
    print("Make sure your .env file contains:")
    print("SUPABASE_URL=your_url")
    print("SUPABASE_SERVICE_KEY=your_key")
    sys.exit(1)

supabase = create_client(supabase_url, service_key)

def create_admin_user(email, password):
    try:
        print(f"Creating admin user with email: {email}")
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        print(f"Generated user ID: {user_id}")

        # Hash password
        password_hash = pwd_context.hash(password)
        print(f"Password hashed successfully")

        # Create user profile
        profile_data = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "is_admin": True,
            "mfa_secret": None
        }

        print("Inserting user profile...")
        # Insert user
        profile_response = supabase.from_('aaa_profiles').insert(profile_data).execute()
        print(f"Profile response: {profile_response}")
        
        if not profile_response.data:
            print("Failed to create admin user - no data returned")
            return False

        print(f"✅ Admin user created: {email}")

        # Ensure admin role exists
        print("Creating admin role...")
        role_data = {"name": "admin"}
        try:
            role_response = supabase.from_('aaa_roles').insert(role_data).execute()
            print(f"Role creation response: {role_response}")
        except Exception as role_error:
            print(f"Role creation error (might already exist): {role_error}")

        # Get role ID (whether just created or already exists)
        print("Fetching admin role...")
        role_query = supabase.from_('aaa_roles').select('id').eq('name', 'admin').limit(1).execute()
        print(f"Role query response: {role_query}")
        
        if not role_query.data:
            print("Failed to find/create admin role")
            return False

        role_id = role_query.data[0]['id']
        print(f"Found admin role ID: {role_id}")

        # Assign admin role to user
        print("Assigning admin role to user...")
        user_role_data = {
            "user_id": user_id,
            "role_id": role_id
        }

        user_role_response = supabase.from_('aaa_user_roles').insert(user_role_data).execute()
        print(f"User role assignment response: {user_role_response}")
        
        if not user_role_response.data:
            print("Failed to assign admin role - no data returned")
            return False

        print(f"✅ Admin role assigned to {email}")
        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # You can modify these values or make them interactive
    email = "n_sivakumar@yahoo.com"  # Change this to your desired email
    password = "password@1"        # Change this to your desired password
    
    print("=== Creating Admin User ===")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("="*30)
    
    if create_admin_user(email, password):
        print("\n🎉 Admin user created successfully!")
        print("\nYou can now:")
        print(f"1. Login with email: {email}")
        print(f"2. Password: {password}")
        print("3. Use the /auth/login endpoint")
        print("4. Create more users via /admin/users")
    else:
        print("\n❌ Failed to create admin user.")