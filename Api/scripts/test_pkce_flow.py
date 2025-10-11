#!/usr/bin/env python3
"""
Test script for OAuth 2.0 PKCE flow implementation.

This script demonstrates the complete PKCE flow:
1. External app generates code challenge and initiates OAuth flow
2. User authenticates (with or without MFA)
3. Authorization code is generated and returned to external app
4. External app exchanges code for access token using code verifier
5. External app uses access token to access user profile

Prerequisites:
- User Management API running on localhost:8001
- Database migrations applied (OAuth tables created)
- Test OAuth client registered in database
"""

import os
import sys
import json
import base64
import hashlib
import secrets
import requests
from urllib.parse import urlencode, parse_qs, urlparse
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8001"
CLIENT_ID = "test_external_app"
REDIRECT_URI = "http://localhost:3000/callback"

# Test user credentials (update these to match your test user)
TEST_USER_EMAIL = "admin@example.com"
TEST_USER_PASSWORD = "admin123"

class PKCEFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.code_verifier = None
        self.code_challenge = None
        self.authorization_code = None
        self.access_token = None
        self.state = None
        
    def generate_pkce_params(self):
        """Generate PKCE code verifier and challenge."""
        print("📝 Step 1: Generating PKCE parameters...")
        
        # Generate code verifier (43-128 characters)
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        print(f"   Code verifier: {self.code_verifier[:20]}...")
        
        # Generate code challenge (SHA256 hash of verifier)
        digest = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        print(f"   Code challenge: {self.code_challenge[:20]}...")
        
        # Generate state for CSRF protection
        self.state = secrets.token_urlsafe(16)
        print(f"   State: {self.state}")
        
        return True
    
    def create_authorization_url(self):
        """Create OAuth authorization URL that external app would redirect user to."""
        print("\n🌐 Step 2: Creating authorization URL...")
        
        params = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256',
            'state': self.state
        }
        
        auth_url = f"{API_BASE_URL}/oauth/authorize?{urlencode(params)}"
        print(f"   Authorization URL: {auth_url}")
        
        return auth_url
    
    def simulate_user_authentication(self, auth_url):
        """Simulate user going through authentication flow."""
        print("\n🔐 Step 3: Simulating user authentication...")
        
        # Follow the authorization URL (this would normally be done in a browser)
        print("   Following authorization URL...")
        try:
            response = self.session.get(auth_url, allow_redirects=False)
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 302:
                # User not logged in - redirected to login
                login_url = response.headers.get('Location')
                print(f"   Redirected to login: {login_url}")
                
                # Extract the return_url from login redirect
                parsed_login_url = urlparse(login_url)
                if parsed_login_url.path == '/login':
                    query_params = parse_qs(parsed_login_url.query)
                    return_url = query_params.get('return_url', [None])[0]
                    print(f"   Return URL: {return_url}")
                    
                    # Simulate user login
                    if self.login_user():
                        # After login, redirect back to OAuth authorization
                        if return_url:
                            return self.complete_authorization(return_url)
                
                return False
            
            elif response.status_code == 200:
                print("   User already authenticated, checking response...")
                # User already logged in, check if we got redirected to callback
                return self.extract_authorization_code(response.url)
                
        except Exception as e:
            print(f"   Error during authorization: {e}")
            return False
    
    def login_user(self):
        """Simulate user login."""
        print("   🔑 Logging in user...")
        
        login_data = {
            'email': TEST_USER_EMAIL,
            'password': TEST_USER_PASSWORD
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            print(f"   Login response status: {response.status_code}")
            
            if response.status_code == 200:
                # Login successful
                token_data = response.json()
                print(f"   Login successful for user: {token_data.get('email')}")
                return True
            elif response.status_code == 402:
                # MFA required
                print("   MFA required - simulating MFA verification...")
                return self.handle_mfa()
            else:
                print(f"   Login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   Login error: {e}")
            return False
    
    def handle_mfa(self):
        """Handle MFA verification (simulation)."""
        print("   📱 MFA verification required")
        print("   ⚠️  Note: This is a simulation. In a real scenario, user would:")
        print("      1. Receive MFA prompt in the frontend")
        print("      2. Enter their TOTP code or email OTP")
        print("      3. Get redirected back to OAuth authorization flow")
        print("   ✅ Assuming MFA verification succeeds...")
        return True
    
    def complete_authorization(self, return_url):
        """Complete the OAuth authorization after login."""
        print(f"   🔄 Completing authorization with return URL: {return_url}")
        
        try:
            # Follow the return URL to complete OAuth authorization
            response = self.session.get(return_url, allow_redirects=False)
            print(f"   Authorization completion status: {response.status_code}")
            
            if response.status_code == 302:
                # Should redirect to callback URL with authorization code
                callback_url = response.headers.get('Location')
                print(f"   Callback URL: {callback_url}")
                
                return self.extract_authorization_code(callback_url)
            
        except Exception as e:
            print(f"   Error completing authorization: {e}")
            return False
    
    def extract_authorization_code(self, callback_url):
        """Extract authorization code from callback URL."""
        print("   📋 Extracting authorization code...")
        
        try:
            parsed_url = urlparse(callback_url)
            query_params = parse_qs(parsed_url.query)
            
            # Check for error
            error = query_params.get('error', [None])[0]
            if error:
                print(f"   ❌ OAuth error: {error}")
                return False
            
            # Extract authorization code
            self.authorization_code = query_params.get('code', [None])[0]
            returned_state = query_params.get('state', [None])[0]
            
            if not self.authorization_code:
                print("   ❌ No authorization code received")
                return False
            
            # Verify state parameter
            if returned_state != self.state:
                print(f"   ❌ State mismatch: expected {self.state}, got {returned_state}")
                return False
            
            print(f"   ✅ Authorization code received: {self.authorization_code[:20]}...")
            print(f"   ✅ State verified: {returned_state}")
            return True
            
        except Exception as e:
            print(f"   Error extracting code: {e}")
            return False
    
    def exchange_code_for_token(self):
        """Exchange authorization code for access token."""
        print("\n🎫 Step 4: Exchanging authorization code for access token...")
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'code': self.authorization_code,
            'redirect_uri': REDIRECT_URI,
            'code_verifier': self.code_verifier
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/oauth/token", json=token_data)
            print(f"   Token exchange status: {response.status_code}")
            
            if response.status_code == 200:
                token_response = response.json()
                self.access_token = token_response.get('access_token')
                
                print(f"   ✅ Access token received: {self.access_token[:20]}...")
                print(f"   Token type: {token_response.get('token_type')}")
                print(f"   Expires in: {token_response.get('expires_in')} seconds")
                print(f"   User ID: {token_response.get('user_id')}")
                print(f"   Email: {token_response.get('email')}")
                print(f"   Roles: {token_response.get('roles')}")
                
                return True
            else:
                print(f"   ❌ Token exchange failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   Token exchange error: {e}")
            return False
    
    def test_access_token(self):
        """Test the access token by accessing user profile."""
        print("\n👤 Step 5: Testing access token with user profile...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(f"{API_BASE_URL}/profiles/me", headers=headers)
            print(f"   Profile access status: {response.status_code}")
            
            if response.status_code == 200:
                profile = response.json()
                print("   ✅ Profile access successful!")
                print(f"   User ID: {profile.get('id')}")
                print(f"   Email: {profile.get('email')}")
                print(f"   Name: {profile.get('first_name', '')} {profile.get('last_name', '')}")
                print(f"   MFA Enabled: {profile.get('mfa_enabled', False)}")
                return True
            else:
                print(f"   ❌ Profile access failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   Profile access error: {e}")
            return False
    
    def run_complete_flow(self):
        """Run the complete PKCE flow test."""
        print("🚀 Starting OAuth 2.0 PKCE Flow Test")
        print("=" * 50)
        
        try:
            # Step 1: Generate PKCE parameters
            if not self.generate_pkce_params():
                print("❌ Failed to generate PKCE parameters")
                return False
            
            # Step 2: Create authorization URL
            auth_url = self.create_authorization_url()
            
            # Step 3: Simulate user authentication
            if not self.simulate_user_authentication(auth_url):
                print("❌ User authentication failed")
                return False
            
            # Step 4: Exchange code for token
            if not self.exchange_code_for_token():
                print("❌ Token exchange failed")
                return False
            
            # Step 5: Test access token
            if not self.test_access_token():
                print("❌ Access token test failed")
                return False
            
            print("\n🎉 PKCE Flow Test Completed Successfully!")
            print("=" * 50)
            print("\nSummary:")
            print(f"✅ Client ID: {CLIENT_ID}")
            print(f"✅ Redirect URI: {REDIRECT_URI}")
            print(f"✅ User: {TEST_USER_EMAIL}")
            print(f"✅ Authorization Code: {self.authorization_code[:20]}...")
            print(f"✅ Access Token: {self.access_token[:20]}...")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            return False

def check_prerequisites():
    """Check if prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ User Management API is running")
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ User Management API is not accessible")
        print(f"   Please ensure the API is running on {API_BASE_URL}")
        return False
    
    # Check if OAuth client exists
    try:
        response = requests.get(f"{API_BASE_URL}/oauth/clients")
        if response.status_code == 401:
            print("⚠️  OAuth client check requires admin authentication")
            print("   Assuming aaa_clients table is extended and test client exists...")
        elif response.status_code == 200:
            print("✅ OAuth endpoints accessible")
        else:
            print(f"⚠️  OAuth endpoints returned status {response.status_code}")
    except requests.exceptions.RequestException:
        print("⚠️  Could not check OAuth client existence")
        print("   Please ensure aaa_clients table is extended for OAuth support")
    
    print("✅ Prerequisites check completed")
    return True

if __name__ == "__main__":
    print("OAuth 2.0 PKCE Flow Test Script")
    print("=" * 40)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        sys.exit(1)
    
    print(f"\n📋 Test Configuration:")
    print(f"   API URL: {API_BASE_URL}")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Redirect URI: {REDIRECT_URI}")
    print(f"   Test User: {TEST_USER_EMAIL}")
    
    input("\n⏸️  Press Enter to start the PKCE flow test...")
    
    tester = PKCEFlowTester()
    success = tester.run_complete_flow()
    
    if success:
        print("\n🎯 All tests passed! The PKCE flow is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        sys.exit(1)