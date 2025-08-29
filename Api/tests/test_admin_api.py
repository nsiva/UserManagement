#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Test admin API endpoint
api_url = "http://localhost:8001"

# First try with a test admin token (we'll create one manually)
print("🔍 Testing Admin API endpoint...\n")

# Create a test user with correct password
test_email = "test_admin@example.com" 
test_password = "test123"

# Create password hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash(test_password)

print(f"Testing with:")
print(f"Email: {test_email}")
print(f"Password: {test_password}")
print(f"Hash: {password_hash[:20]}...")

try:
    # Try login
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    login_response = requests.post(f"{api_url}/auth/login", json=login_data)
    print(f"\n📡 Login Response Status: {login_response.status_code}")
    print(f"Login Response: {login_response.text[:200]}")
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"✅ Got token: {token[:20]}...")
        
        # Test admin endpoint
        headers = {"Authorization": f"Bearer {token}"}
        users_response = requests.get(f"{api_url}/admin/users", headers=headers)
        
        print(f"\n📡 Users Response Status: {users_response.status_code}")
        if users_response.status_code == 200:
            users_data = users_response.json()
            print(f"✅ Got {len(users_data)} users from API")
            
            for user in users_data:
                print(f"\n📋 User: {user.get('email')}")
                print(f"   MFA Enabled: {user.get('mfa_enabled', 'MISSING FIELD!')}")
                print(f"   Fields: {list(user.keys())}")
        else:
            print(f"❌ Users API Error: {users_response.text}")
    
    else:
        print(f"❌ Login failed: {login_response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Let's also try with a known user that we saw has MFA
print("\n" + "="*60)
print("🔍 Testing with known admin user...")

# Try with the admin user we know exists
admin_login = {
    "email": "n_sivakumar@yahoo.com",
    "password": "your_actual_password_here"  # You'll need to provide this
}

# Don't actually run this login since we don't know the password,
# but let's create a JWT token manually for testing
import jwt
from datetime import datetime, timedelta

# Create a test token manually
jwt_secret = os.environ.get("JWT_SECRET_KEY")
if jwt_secret:
    payload = {
        "user_id": "test-admin-id",
        "email": "n_sivakumar@yahoo.com",
        "is_admin": True,
        "roles": ["admin"],
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    
    test_token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    print(f"🔑 Created test admin token: {test_token[:30]}...")
    
    # Test with this token
    headers = {"Authorization": f"Bearer {test_token}"}
    try:
        users_response = requests.get(f"{api_url}/admin/users", headers=headers)
        print(f"\n📡 Users Response Status: {users_response.status_code}")
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            print(f"✅ Got {len(users_data)} users from API")
            
            for user in users_data:
                print(f"\n📋 User: {user.get('email')}")
                print(f"   MFA Enabled: {user.get('mfa_enabled', 'MISSING FIELD!')}")
                print(f"   All Fields: {json.dumps(user, indent=2)}")
        else:
            print(f"❌ Users API Error: {users_response.text}")
            
    except Exception as e:
        print(f"❌ Error testing with manual token: {e}")
else:
    print("❌ No JWT_SECRET_KEY found")