#!/usr/bin/env python3

# Generate admin user SQL statements with bcrypt hash
import bcrypt
import uuid

def generate_admin_sql(email="admin@example.com", password="admin123"):
    print("=== Admin User SQL Generator ===")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print()
    
    # Generate UUID
    user_id = str(uuid.uuid4())
    
    # Generate bcrypt hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    hashed_string = hashed.decode('utf-8')
    
    print("="*60)
    print("GENERATED DATA:")
    print("="*60)
    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Password Hash: {hashed_string}")
    
    print("\n" + "="*60)
    print("SQL STATEMENTS TO RUN IN SUPABASE:")
    print("="*60)
    
    # Generate SQL statements
    sql = f"""-- Create admin role (if not exists)
INSERT INTO aaa_roles (name) VALUES ('admin') 
ON CONFLICT (name) DO NOTHING;

-- Create admin user
INSERT INTO aaa_profiles (id, email, password_hash, is_admin, mfa_secret)
VALUES (
    '{user_id}',
    '{email}',
    '{hashed_string}',
    true,
    NULL
);

-- Assign admin role to user
INSERT INTO aaa_user_roles (user_id, role_id)
SELECT 
    '{user_id}' as user_id,
    id as role_id
FROM aaa_roles 
WHERE name = 'admin';

-- Verify the user was created (optional query to test)
SELECT 
    p.id,
    p.email,
    p.is_admin,
    r.name as role
FROM aaa_profiles p
LEFT JOIN aaa_user_roles ur ON p.id = ur.user_id
LEFT JOIN aaa_roles r ON ur.role_id = r.id
WHERE p.email = '{email}';"""

    print(sql)
    
    # Verify the hash
    print("\n" + "="*60)
    print("VERIFICATION:")
    print("="*60)
    is_valid = bcrypt.checkpw(password_bytes, hashed)
    print(f"Password hash verification: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("="*60)
    print("1. First, ensure your aaa_* tables are created in Supabase")
    print("2. Copy the SQL statements above")
    print("3. Run them in your Supabase SQL Editor")
    print("4. Test login with your FastAPI app using:")
    print(f"   POST /auth/login")
    print(f"   {{\"email\": \"{email}\", \"password\": \"{password}\"}}")
    print("="*60)

if __name__ == "__main__":
    # Default credentials - change these as needed
    EMAIL = "admin@yourdomain.com"
    PASSWORD = "SecureAdmin123!"
    
    generate_admin_sql(EMAIL, PASSWORD)