#!/bin/bash

# MFA Testing Script
echo "=== MFA Setup and Testing Script ==="
echo ""

# Check if server is running
if ! curl -s http://localhost:8001/ > /dev/null; then
    echo "❌ Server not running. Please start it with: ./scripts/start.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Get user credentials
read -p "Enter admin email: " ADMIN_EMAIL
read -s -p "Enter admin password: " ADMIN_PASSWORD
echo ""

# Step 1: Login to get token
echo "Step 1: Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\"}")

# Extract token (basic extraction without jq)
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login failed. Response:"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Setup MFA
echo "Step 2: Setting up MFA..."
MFA_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/mfa/setup?email=$ADMIN_EMAIL" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Extract secret and QR code
SECRET=$(echo "$MFA_RESPONSE" | grep -o '"secret":"[^"]*' | cut -d'"' -f4)
QR_CODE=$(echo "$MFA_RESPONSE" | grep -o '"qr_code_base64":"[^"]*' | cut -d'"' -f4)

if [ -z "$SECRET" ]; then
    echo "❌ MFA setup failed. Response:"
    echo "$MFA_RESPONSE"
    exit 1
fi

echo "✅ MFA setup successful"
echo ""

# Step 3: Save QR code
echo "Step 3: Saving QR code..."
echo "$QR_CODE" | base64 -d > mfa-qr-code.png
echo "✅ QR code saved as: mfa-qr-code.png"
echo ""

# Step 4: Display setup information
echo "=== MFA Setup Information ==="
echo "Secret Key: $SECRET"
echo "Account: $ADMIN_EMAIL"
echo "Issuer: YourAppName"
echo ""
echo "Next steps:"
echo "1. Open your authenticator app"
echo "2. Scan the QR code (mfa-qr-code.png) OR manually enter the secret key above"
echo "3. Test login with MFA using:"
echo "   curl -X POST \"http://localhost:8001/auth/mfa/verify\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"email\": \"$ADMIN_EMAIL\", \"mfa_code\": \"XXXXXX\"}'"
echo ""
echo "Note: Regular login will now require MFA for this user."