#!/bin/bash

# Test script for the updated /profiles/me endpoint
echo "=== Testing /profiles/me endpoint with name fields ==="
echo ""

# Check if server is running
if ! curl -s http://localhost:8001/ > /dev/null; then
    echo "❌ Server not running. Please start it with: ./scripts/start.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Get user credentials
read -p "Enter user email: " USER_EMAIL
read -s -p "Enter user password: " USER_PASSWORD
echo ""

# Step 1: Login to get token
echo "Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$USER_EMAIL\", \"password\": \"$USER_PASSWORD\"}")

# Extract token (basic extraction without jq)
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login failed. Response:"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Test /profiles/me endpoint
echo "Step 2: Getting profile information..."
PROFILE_RESPONSE=$(curl -s -X GET "http://localhost:8001/profiles/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "✅ Profile Response:"
echo "$PROFILE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PROFILE_RESPONSE"
echo ""

# Step 3: Check if name fields are present
echo "Step 3: Checking name fields..."
if echo "$PROFILE_RESPONSE" | grep -q "first_name"; then
    echo "✅ first_name field is present"
else
    echo "⚠️  first_name field is missing"
fi

if echo "$PROFILE_RESPONSE" | grep -q "middle_name"; then
    echo "✅ middle_name field is present"
else
    echo "⚠️  middle_name field is missing"
fi

if echo "$PROFILE_RESPONSE" | grep -q "last_name"; then
    echo "✅ last_name field is present"
else
    echo "⚠️  last_name field is missing"
fi

echo ""
echo "🎉 Profile endpoint test completed!"