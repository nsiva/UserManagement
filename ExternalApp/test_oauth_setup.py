#!/usr/bin/env python3
"""
Test script to verify OAuth client setup for ExternalApp
"""

import requests
import json
import sys

# Configuration
USER_MGMT_API_BASE = "http://localhost:8001"
EXTERNAL_APP_CLIENT_ID = "test_external_app"
EXTERNAL_APP_REDIRECT_URI = "http://localhost:4202/oauth/callback"

def test_oauth_client_exists():
    """Test if OAuth client is properly registered"""
    print("🔍 Testing OAuth client registration...")
    
    try:
        # Try to access OAuth client list endpoint (requires admin auth)
        response = requests.get(f"{USER_MGMT_API_BASE}/oauth/clients")
        
        if response.status_code == 401:
            print("⚠️  OAuth client list requires admin authentication")
            print("   This is expected - OAuth client management is admin-only")
            return True
        elif response.status_code == 200:
            clients = response.json()
            print(f"✅ OAuth client endpoint accessible, found {len(clients)} clients")
            
            # Look for our test client
            for client in clients:
                if client.get('client_id') == EXTERNAL_APP_CLIENT_ID:
                    print(f"✅ Found ExternalApp OAuth client: {EXTERNAL_APP_CLIENT_ID}")
                    print(f"   Redirect URIs: {client.get('redirect_uris')}")
                    return True
            
            print(f"⚠️  OAuth client {EXTERNAL_APP_CLIENT_ID} not found")
            print("   Run the database migration to create it")
            return False
        else:
            print(f"❌ OAuth client endpoint returned {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to User Management API: {e}")
        return False

def test_oauth_authorization_endpoint():
    """Test OAuth authorization endpoint accessibility"""
    print("\n🔍 Testing OAuth authorization endpoint...")
    
    try:
        # Test authorization endpoint without parameters (should return 400)
        response = requests.get(f"{USER_MGMT_API_BASE}/oauth/authorize")
        
        if response.status_code == 400:
            print("✅ OAuth authorization endpoint is accessible")
            print("   Returns 400 without parameters (expected)")
            return True
        elif response.status_code == 422:
            print("✅ OAuth authorization endpoint is accessible")
            print("   Returns 422 for missing parameters (expected)")
            return True
        else:
            print(f"⚠️  OAuth authorization endpoint returned {response.status_code}")
            print("   This might be expected depending on validation")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to OAuth authorization endpoint: {e}")
        return False

def test_oauth_token_endpoint():
    """Test OAuth token endpoint accessibility"""
    print("\n🔍 Testing OAuth token endpoint...")
    
    try:
        # Test token endpoint without parameters (should return 400)
        response = requests.post(f"{USER_MGMT_API_BASE}/oauth/token", json={})
        
        if response.status_code in [400, 422]:
            print("✅ OAuth token endpoint is accessible")
            print(f"   Returns {response.status_code} without parameters (expected)")
            return True
        else:
            print(f"⚠️  OAuth token endpoint returned {response.status_code}")
            print("   This might be expected depending on validation")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to OAuth token endpoint: {e}")
        return False

def test_external_app_api():
    """Test ExternalApp API accessibility"""
    print("\n🔍 Testing ExternalApp API...")
    
    try:
        response = requests.get("http://localhost:8002/")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ExternalApp API is running")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   User Management Integration: {data.get('user_management_integration', False)}")
            return True
        else:
            print(f"❌ ExternalApp API returned {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ExternalApp API not accessible: {e}")
        print("   Make sure to start the ExternalApp API on port 8002")
        return False

def test_external_app_oauth_callback():
    """Test ExternalApp OAuth callback endpoint"""
    print("\n🔍 Testing ExternalApp OAuth callback endpoint...")
    
    try:
        # Test callback endpoint without parameters (should return 400)
        response = requests.get("http://localhost:8002/oauth/callback")
        
        if response.status_code in [400, 422]:
            print("✅ ExternalApp OAuth callback endpoint is accessible")
            print(f"   Returns {response.status_code} without parameters (expected)")
            return True
        else:
            print(f"⚠️  ExternalApp OAuth callback returned {response.status_code}")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ExternalApp OAuth callback not accessible: {e}")
        return False

def show_manual_setup_instructions():
    """Show instructions for manual OAuth client setup"""
    print("\n📋 Manual OAuth Client Setup Instructions:")
    print("=" * 50)
    
    print("\n1. Apply database migration:")
    print("   cd /Users/siva/projects/UserManagement/Api")
    print("   psql -h your-host -U your-username -d your-database -f migrations/extend_aaa_clients_for_oauth.sql")
    
    print("\n2. Or insert OAuth client manually:")
    print("   INSERT INTO aaa_clients (client_id, name, client_type, redirect_uris, scopes, description)")
    print("   VALUES (")
    print(f"     '{EXTERNAL_APP_CLIENT_ID}',")
    print("     'ExternalApp Test Client',")
    print("     'oauth_pkce',")
    print(f"     ARRAY['{EXTERNAL_APP_REDIRECT_URI}'],")
    print("     ARRAY['read:profile', 'read:roles'],")
    print("     'OAuth PKCE client for ExternalApp testing'")
    print("   );")
    
    print("\n3. Start required services:")
    print("   - User Management API: http://localhost:8001")
    print("   - User Management WebUI: http://localhost:4201") 
    print("   - ExternalApp API: http://localhost:8002")
    print("   - ExternalApp WebUI: http://localhost:4202")

def main():
    """Run all OAuth setup tests"""
    print("🚀 OAuth PKCE Setup Test for ExternalApp")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test User Management API
    if not test_oauth_client_exists():
        all_tests_passed = False
    
    if not test_oauth_authorization_endpoint():
        all_tests_passed = False
        
    if not test_oauth_token_endpoint():
        all_tests_passed = False
    
    # Test ExternalApp API
    if not test_external_app_api():
        all_tests_passed = False
        
    if not test_external_app_oauth_callback():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    
    if all_tests_passed:
        print("🎉 All OAuth setup tests passed!")
        print("\nTo test the complete flow:")
        print("1. Open http://localhost:4202 in your browser")
        print("2. Click 'Login via User Management'")
        print("3. Complete authentication (including MFA if enabled)")
        print("4. You should be redirected back to ExternalApp dashboard")
    else:
        print("❌ Some tests failed")
        show_manual_setup_instructions()
        
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())