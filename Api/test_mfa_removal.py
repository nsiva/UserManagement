#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test MFA removal endpoint
api_url = "http://localhost:8001"

def test_mfa_removal():
    print("🔍 Testing MFA Removal for Email MFA user...\n")
    
    # Test user with email MFA (from database export)
    test_email = "ai.tools.test.2000@gmail.com"
    
    print(f"Testing MFA removal for: {test_email}")
    print("This user should have email MFA enabled (mfa_method='email', mfa_secret=NULL)")
    
    # We'll need an admin token - let's use client credentials for testing
    try:
        # Get admin access via client credentials (if configured)
        client_data = {
            "client_id": "admin_client", 
            "client_secret": "admin_secret"
        }
        
        client_response = requests.post(f"{api_url}/auth/token", json=client_data)
        
        if client_response.status_code == 200:
            token = client_response.json().get("access_token")
            print(f"✅ Got admin token: {token[:20]}...")
            
            # Test MFA removal
            headers = {"Authorization": f"Bearer {token}"}
            removal_response = requests.delete(f"{api_url}/auth/mfa/remove?email={test_email}", headers=headers)
            
            print(f"\n📡 MFA Removal Response Status: {removal_response.status_code}")
            print(f"Response: {removal_response.text}")
            
            if removal_response.status_code == 200:
                print("✅ MFA removal succeeded!")
                
                # Now test that login no longer requires MFA
                login_data = {
                    "email": test_email,
                    "password": "test123"  # Assuming this is the password
                }
                
                login_response = requests.post(f"{api_url}/auth/login", json=login_data)
                print(f"\n📡 Login Response Status: {login_response.status_code}")
                print(f"Login Response: {login_response.text}")
                
                if login_response.status_code == 200:
                    print("✅ Login succeeded without MFA - MFA successfully removed!")
                elif login_response.status_code == 402:
                    print("❌ Login still requires MFA - removal may have failed")
                else:
                    print(f"⚠️ Login failed with different error: {login_response.status_code}")
            else:
                print("❌ MFA removal failed")
                
        else:
            print(f"❌ Failed to get admin token: {client_response.status_code}")
            print(f"Response: {client_response.text}")
            print("\nNote: You can manually test in the frontend admin panel.")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("\nNote: You can manually test in the frontend admin panel.")

if __name__ == "__main__":
    test_mfa_removal()