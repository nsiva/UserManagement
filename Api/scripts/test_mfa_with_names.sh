#!/bin/bash

# Test script for MFA endpoints with name fields
echo "=== Testing MFA endpoints with name fields ==="
echo ""

# Check if server is running
if ! curl -s http://localhost:8001/ > /dev/null; then
    echo "❌ Server not running. Please start it with: ./scripts/start.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Get user credentials
read -p "Enter user email (with MFA enabled): " USER_EMAIL
read -s -p "Enter user password: " USER_PASSWORD
echo ""

# Step 1: Try login (should require MFA)
echo "Step 1: Attempting login (should require MFA)..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$USER_EMAIL\", \"password\": \"$USER_PASSWORD\"}")

echo "Login Response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

# Check if MFA is required
if echo "$LOGIN_RESPONSE" | grep -q "MFA required"; then
    echo "✅ MFA is correctly required"
    echo ""
    
    # Step 2: Get MFA code from user
    read -p "Enter 6-digit MFA code from authenticator: " MFA_CODE
    
    # Step 3: Verify MFA
    echo "Step 3: Verifying MFA code..."
    MFA_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/mfa/verify" \
      -H "Content-Type: application/json" \
      -d "{\"email\": \"$USER_EMAIL\", \"mfa_code\": \"$MFA_CODE\"}")
    
    echo "✅ MFA Verification Response:"
    echo "$MFA_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MFA_RESPONSE"
    echo ""
    
    # Step 4: Check if name fields are present
    echo "Step 4: Checking name fields in token response..."
    if echo "$MFA_RESPONSE" | grep -q "first_name"; then
        echo "✅ first_name field is present"
    else
        echo "⚠️  first_name field is missing"
    fi
    
    if echo "$MFA_RESPONSE" | grep -q "middle_name"; then
        echo "✅ middle_name field is present"
    else
        echo "⚠️  middle_name field is missing"
    fi
    
    if echo "$MFA_RESPONSE" | grep -q "last_name"; then
        echo "✅ last_name field is present"
    else
        echo "⚠️  last_name field is missing"
    fi
    
    # Extract token for additional test
    ACCESS_TOKEN=$(echo "$MFA_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ ! -z "$ACCESS_TOKEN" ]; then
        echo ""
        echo "Step 5: Testing token with /profiles/me endpoint..."
        PROFILE_RESPONSE=$(curl -s -X GET "http://localhost:8001/profiles/me" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        echo "Profile Response:"
        echo "$PROFILE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PROFILE_RESPONSE"
    fi
    
else
    echo "⚠️  Login succeeded without MFA (user might not have MFA enabled)"
    echo "Response shows user logged in directly:"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
fi

echo ""
echo "🎉 MFA with names test completed!"