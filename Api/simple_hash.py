#!/usr/bin/env python3

# Simple password hasher using just bcrypt (should be available)
import bcrypt
import uuid

def generate_admin_data():
    print("=== Admin User Generator ===")
    
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required")
        return
    
    # Generate UUID
    user_id = str(uuid.uuid4())
    
    # Generate bcrypt hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    hashed_string = hashed.decode('utf-8')
    
    print("\n" + "="*50)
    print("GENERATED ADMIN USER DATA:")
    print("="*50)
    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Password Hash: {hashed_string}")
    
    print("\n" + "="*50)
    print("SQL STATEMENTS TO RUN:")
    print("="*50)
    
    # Generate SQL statements
    sql = f"""-- Step 1: Create admin role (if not exists)
INSERT INTO aaa_roles (name) VALUES ('admin') ON CONFLICT (name) DO NOTHING;

-- Step 2: Create admin user
INSERT INTO aaa_profiles (id, email, password_hash, is_admin, mfa_secret)
VALUES (
    '{user_id}',
    '{email}',
    '{hashed_string}',
    true,
    NULL
);

-- Step 3: Assign admin role to user
INSERT INTO aaa_user_roles (user_id, role_id)
SELECT 
    '{user_id}',
    id
FROM aaa_roles 
WHERE name = 'admin';"""

    print(sql)
    
    # Verify the hash
    print("\n" + "="*50)
    print("VERIFICATION:")
    print("="*50)
    is_valid = bcrypt.checkpw(password_bytes, hashed)
    print(f"Password verification: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    
    print("\n" + "="*50)
    print("INSTRUCTIONS:")
    print("="*50)
    print("1. Copy the SQL statements above")
    print("2. Run them in your Supabase SQL Editor")
    print("3. Test login with:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print("="*50)

if __name__ == "__main__":
    generate_admin_data()