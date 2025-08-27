#!/usr/bin/env python3
"""
Quick test script for the /auth/reset_password endpoint.
This script demonstrates how to use the new password reset functionality.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_password_reset():
    """Test the password reset endpoint"""
    
    # Example usage - you'll need to provide valid credentials
    print("Password Reset Endpoint Test")
    print("=" * 40)
    
    # Step 1: Login to get a token (replace with actual user credentials)
    login_data = {
        "email": "admin@example.com",  # Replace with actual email
        "password": "current_password"  # Replace with actual password
    }
    
    print("1. Login to get access token...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"   ✓ Login successful, token obtained")
        elif response.status_code == 402:
            print(f"   ⚠ MFA required - you'll need to complete MFA verification first")
            return
        else:
            print(f"   ✗ Login failed: {response.status_code} - {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Connection failed - make sure the server is running on {BASE_URL}")
        return
    
    # Step 2: Reset password
    reset_data = {
        "current_password": "current_password",  # Replace with actual current password
        "new_password": "new_secure_password123"  # Replace with desired new password
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("2. Reset password...")
    try:
        response = requests.post(f"{BASE_URL}/auth/reset_password", json=reset_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Password reset successful: {result['message']}")
        else:
            print(f"   ✗ Password reset failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")

def show_usage():
    """Show how to use the endpoint"""
    print("Password Reset Endpoint Usage")
    print("=" * 40)
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

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "usage":
        show_usage()
    else:
        print("Note: This is a demonstration script.")
        print("Update the credentials in the script before running the actual test.")
        print("Run with 'usage' argument to see endpoint documentation.")
        print()
        show_usage()