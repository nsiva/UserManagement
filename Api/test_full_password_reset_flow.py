#!/usr/bin/env python3
"""
Test script for the complete password reset flow.
This script tests the new /auth/reset_password endpoint with proper authentication.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_full_password_reset_flow():
    """Test the complete password reset flow"""
    
    print("=== Password Reset Flow Test ===")
    print()
    
    # Step 1: Login to get access token (you'll need valid credentials)
    print("1. Testing login to get access token...")
    
    # Replace with actual test user credentials
    test_email = "admin@example.com"  
    test_password = "admin123"  # Current password
    new_password = "newpassword123"
    
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"   ✓ Login successful for {test_email}")
            print(f"   ✓ Access token obtained")
        elif response.status_code == 402:
            print(f"   ⚠ MFA required for {test_email}")
            print("   Please complete MFA verification manually first")
            return False
        else:
            print(f"   ✗ Login failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Connection failed - make sure backend is running on {BASE_URL}")
        return False
    
    # Step 2: Test reset password endpoint
    print()
    print("2. Testing password reset endpoint...")
    
    reset_data = {
        "current_password": test_password,
        "new_password": new_password
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/reset_password", json=reset_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Password reset successful: {result.get('message', 'Success')}")
        else:
            print(f"   ✗ Password reset failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
        return False
    
    # Step 3: Test login with new password
    print()
    print("3. Testing login with new password...")
    
    new_login_data = {
        "email": test_email,
        "password": new_password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data)
        
        if response.status_code == 200:
            print(f"   ✓ Login successful with new password")
        elif response.status_code == 402:
            print(f"   ✓ Login requires MFA (password change successful)")
        else:
            print(f"   ✗ Login with new password failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
        return False
    
    # Step 4: Reset password back to original (cleanup)
    print()
    print("4. Resetting password back to original (cleanup)...")
    
    # Get new token first
    response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data)
    if response.status_code == 200:
        new_token = response.json()["access_token"]
        
        cleanup_data = {
            "current_password": new_password,
            "new_password": test_password
        }
        
        headers = {"Authorization": f"Bearer {new_token}"}
        response = requests.post(f"{BASE_URL}/auth/reset_password", json=cleanup_data, headers=headers)
        
        if response.status_code == 200:
            print(f"   ✓ Password restored to original value")
        else:
            print(f"   ⚠ Could not restore original password: {response.status_code}")
    
    print()
    print("=== Test completed successfully! ===")
    return True

def show_endpoint_info():
    """Show information about the reset password endpoint"""
    print("=== Password Reset Endpoint Information ===")
    print()
    print("Endpoint: POST /auth/reset_password")
    print("Authentication: Bearer token required")
    print()
    print("Request Body:")
    print(json.dumps({
        "current_password": "string",
        "new_password": "string"
    }, indent=2))
    print()
    print("Success Response (200):")
    print(json.dumps({"message": "Password reset successfully"}, indent=2))
    print()
    print("Error Responses:")
    print("- 400: Current password is incorrect")
    print("- 401: Unauthorized (invalid/missing token)")
    print("- 404: User not found")
    print("- 500: Internal server error")
    print()
    print("Frontend Integration:")
    print("- Profile page now displays password with asterisks")
    print("- Reset password button navigates to /reset-password")
    print("- Reset password page provides form and calls API")
    print("- Success redirects back to profile page")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        show_endpoint_info()
    else:
        print("WARNING: This test script uses hardcoded credentials.")
        print("Make sure you have a test user with email 'admin@example.com' and password 'admin123'")
        print("OR modify the credentials in the script.")
        print()
        choice = input("Continue with test? (y/N): ").lower()
        if choice == 'y':
            test_full_password_reset_flow()
        else:
            print("Test cancelled. Run with 'info' argument to see endpoint documentation.")
            show_endpoint_info()