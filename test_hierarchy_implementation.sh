#!/bin/bash

# Test script for the updated hierarchical functional roles implementation
# This tests the API endpoints without database functions/triggers

API_BASE="http://localhost:8001"

echo "🧪 Testing Hierarchical Functional Roles Implementation (No DB Functions)"
echo "=================================================================="

# Test 1: Check if API is running
echo "1️⃣ Testing API availability..."
if curl -s "$API_BASE/" | grep -q "User Management API"; then
    echo "✅ API is running"
else
    echo "❌ API is not running on $API_BASE"
    exit 1
fi

# Test 2: Check if new endpoints are registered
echo ""
echo "2️⃣ Testing functional-roles-hierarchy endpoints registration..."
if curl -s "$API_BASE/openapi.json" | grep -q "functional-roles-hierarchy"; then
    echo "✅ Hierarchical functional roles endpoints are registered"
else
    echo "❌ Hierarchical functional roles endpoints not found"
fi

# Test 3: Test hierarchy overview endpoint (without auth for basic check)
echo ""
echo "3️⃣ Testing hierarchy overview endpoint (expect auth error)..."
response=$(curl -s -w "HTTP_STATUS:%{http_code}" "$API_BASE/functional-roles-hierarchy/hierarchy")
http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)

if [ "$http_status" = "401" ] || [ "$http_status" = "403" ]; then
    echo "✅ Hierarchy endpoint exists and requires authentication (status: $http_status)"
else
    echo "❌ Unexpected response from hierarchy endpoint (status: $http_status)"
    echo "Response: $(echo "$response" | sed 's/HTTP_STATUS:[0-9]*//')"
fi

# Test 4: Check available endpoints
echo ""
echo "4️⃣ Available hierarchical functional roles endpoints:"
curl -s "$API_BASE/openapi.json" | grep -o '"[^"]*functional-roles-hierarchy[^"]*"' | head -10

echo ""
echo "🔄 Manual Testing Steps:"
echo "======================"
echo "1. Run the views creation SQL:"
echo "   - Execute: Api/migrations/create_hierarchical_functional_roles_views_only.sql"
echo ""
echo "2. Test with admin authentication:"
echo "   curl -X GET '$API_BASE/functional-roles-hierarchy/hierarchy' \\"
echo "        -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'"
echo ""
echo "3. Test organization role assignment:"
echo "   curl -X POST '$API_BASE/functional-roles-hierarchy/organizations/{org_id}/roles/bulk' \\"
echo "        -H 'Authorization: Bearer YOUR_ADMIN_TOKEN' \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"organization_id\": \"{org_id}\", \"functional_role_names\": [\"fleet_manager\"], \"is_enabled\": true}'"
echo ""
echo "4. Test business unit available roles:"
echo "   curl -X GET '$API_BASE/functional-roles-hierarchy/business-units/{bu_id}/available-roles' \\"
echo "        -H 'Authorization: Bearer YOUR_ADMIN_TOKEN'"
echo ""
echo "5. Test constraint validation:"
echo "   - Try to assign a role to BU that's not enabled at org level (should fail)"
echo "   - Try to assign a role to user that's not enabled at BU level (should fail)"
echo ""
echo "✨ Implementation Summary:"
echo "========================="
echo "✅ Database views created instead of functions"
echo "✅ API constraint checking in Python code"
echo "✅ Hierarchical role availability checking"
echo "✅ Usage validation for role removal"
echo "✅ Frontend component remains unchanged"
echo ""
echo "The hierarchy constraints are now enforced in the API layer:"
echo "- Organization → Business Unit constraint checking"
echo "- Business Unit → User constraint checking"
echo "- Role removal usage validation"
echo "- All using database views for efficient querying"