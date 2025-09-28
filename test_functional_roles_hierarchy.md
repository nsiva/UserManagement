# Functional Roles Hierarchy Testing Guide

This document provides a comprehensive guide to test the newly implemented hierarchical functional roles system.

## Overview

The hierarchical functional roles system implements the following structure:
- **Organization Level**: Functional roles can be enabled for the entire organization
- **Business Unit Level**: Only organization-enabled roles can be enabled for business units  
- **User Level**: Only business unit-enabled roles can be assigned to users

## Required Database Changes

Before testing, run the following SQL migration:

```sql
-- Run this in your Supabase SQL Editor or via database client
-- File: Api/migrations/create_hierarchical_functional_roles.sql
```

## Test Scenarios

### 1. Database Setup Test

First, verify the database schema is properly set up:

**SQL to verify tables exist:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN (
    'aaa_organization_functional_roles', 
    'aaa_business_unit_functional_roles',
    'aaa_functional_roles',
    'aaa_organizations',
    'aaa_business_units'
);
```

**Expected Result:** All 5 tables should be present.

### 2. API Endpoint Testing

#### 2.1 Test Organization-Level Role Management

**Prerequisites:**
- Have at least one organization in the system
- Have admin authentication token

**Get Organization Functional Roles:**
```bash
curl -X GET "http://localhost:8001/functional-roles-hierarchy/organizations/{org_id}/roles" \
  -H "Authorization: Bearer {your_token}"
```

**Bulk Assign Roles to Organization:**
```bash
curl -X POST "http://localhost:8001/functional-roles-hierarchy/organizations/{org_id}/roles/bulk" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "{org_id}",
    "functional_role_names": ["fleet_manager", "accountant", "dispatcher"],
    "is_enabled": true,
    "notes": "Initial setup for organization"
  }'
```

**Expected Result:** Roles successfully assigned at organization level.

#### 2.2 Test Business Unit-Level Role Management

**Get Available Roles for Business Unit:**
```bash
curl -X GET "http://localhost:8001/functional-roles-hierarchy/business-units/{bu_id}/available-roles" \
  -H "Authorization: Bearer {your_token}"
```

**Expected Result:** Only roles enabled at organization level should appear.

**Assign Roles to Business Unit:**
```bash
curl -X POST "http://localhost:8001/functional-roles-hierarchy/business-units/{bu_id}/roles/bulk" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "business_unit_id": "{bu_id}",
    "functional_role_names": ["fleet_manager", "dispatcher"],
    "is_enabled": true,
    "notes": "Roles for this business unit"
  }'
```

**Expected Result:** Roles successfully assigned to business unit.

**Test Constraint: Try to Assign Non-Org Role:**
```bash
curl -X POST "http://localhost:8001/functional-roles-hierarchy/business-units/{bu_id}/roles/bulk" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "business_unit_id": "{bu_id}",
    "functional_role_names": ["mechanic"],
    "is_enabled": true
  }'
```

**Expected Result:** Should fail if "mechanic" is not enabled at organization level.

#### 2.3 Test User-Level Role Availability

**Get Available Roles for User:**
```bash
curl -X GET "http://localhost:8001/functional-roles-hierarchy/users/{user_id}/available-roles" \
  -H "Authorization: Bearer {your_token}"
```

**Expected Result:** Only roles enabled at the user's business unit level should appear.

#### 2.4 Test Hierarchy View

**Get Complete Hierarchy:**
```bash
curl -X GET "http://localhost:8001/functional-roles-hierarchy/hierarchy" \
  -H "Authorization: Bearer {your_token}"
```

**Get Hierarchy for Specific Organization:**
```bash
curl -X GET "http://localhost:8001/functional-roles-hierarchy/hierarchy?organization_id={org_id}" \
  -H "Authorization: Bearer {your_token}"
```

**Expected Result:** Comprehensive view showing role assignments across the hierarchy.

### 3. Database Constraint Testing

#### 3.1 Test Organization-Level Constraint

Try to enable a business unit role without organization-level enablement:

```sql
-- This should fail due to trigger constraint
INSERT INTO aaa_business_unit_functional_roles 
  (business_unit_id, functional_role_id, is_enabled)
VALUES 
  ('{bu_id}', '{role_id_not_enabled_at_org}', true);
```

**Expected Result:** Should fail with constraint error.

#### 3.2 Test User-Level Constraint

Try to assign a functional role to a user without business unit enablement:

```sql
-- This should fail due to trigger constraint  
INSERT INTO aaa_user_functional_roles 
  (user_id, functional_role_id, is_active)
VALUES 
  ('{user_id}', '{role_id_not_enabled_at_bu}', true);
```

**Expected Result:** Should fail with constraint error.

### 4. Frontend Component Testing

#### 4.1 Test Functional Roles Manager Component

**Organization Context:**
```html
<app-functional-roles-manager 
  context="organization"
  [organizationId]="organizationId">
</app-functional-roles-manager>
```

**Business Unit Context:**
```html
<app-functional-roles-manager 
  context="business_unit" 
  [businessUnitId]="businessUnitId">
</app-functional-roles-manager>
```

**User Context (Read-only):**
```html
<app-functional-roles-manager 
  context="user"
  [userId]="userId"
  [readonly]="true">
</app-functional-roles-manager>
```

### 5. Integration Testing

#### 5.1 Complete Workflow Test

1. **Enable roles at organization level**
2. **Enable subset of roles at business unit level**
3. **Verify user can only be assigned business unit roles**
4. **Try to remove organization role that's used by business unit** (should fail)
5. **Try to remove business unit role that's assigned to user** (should fail)

#### 5.2 User Assignment Test

Using existing functional roles endpoints:

```bash
curl -X POST "http://localhost:8001/functional-roles/users/{user_id}/assign" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{user_id}",
    "functional_role_names": ["fleet_manager"],
    "replace_existing": false
  }'
```

**Expected Result:** Should succeed only if user is in a business unit that has "fleet_manager" enabled.

## Error Scenarios to Test

### 1. Hierarchy Violation Errors
- **Assigning BU role without org enablement**
- **Assigning user role without BU enablement**
- **User not in any business unit with required role**

### 2. Cascade Deletion Errors
- **Removing org role when BU has it enabled**
- **Removing BU role when user has it assigned**
- **Deleting business unit with active functional role assignments**

## Expected Results Summary

| Test Case | Expected Outcome |
|-----------|------------------|
| Assign org-level roles | Success |
| View BU available roles | Only org-enabled roles shown |
| Assign BU roles from available | Success |
| Assign BU roles not org-enabled | Constraint error |
| View user available roles | Only BU-enabled roles shown |
| Assign user roles from available | Success (via existing endpoint) |
| Hierarchy view | Complete role assignments displayed |
| Remove org role with BU usage | Prevention error |
| Remove BU role with user assignment | Prevention error |

## Database Functions to Test

The migration creates several PostgreSQL functions:

1. **`get_available_functional_roles_for_business_unit(bu_id)`**
2. **`get_available_functional_roles_for_user(user_id)`**
3. **`check_business_unit_functional_role_allowed()`** (trigger function)
4. **`check_user_functional_role_allowed()`** (trigger function)

Test these functions work correctly by calling them directly or through the API endpoints.

## Monitoring and Logging

During testing, monitor the API logs for:
- Constraint violation errors
- Successful role assignments
- Database trigger executions
- Authentication/authorization checks

## Frontend Integration

The functional roles manager component should:
1. Load available roles based on context
2. Show current assignments/enablements
3. Allow toggling roles on/off
4. Save changes via bulk assignment APIs
5. Display appropriate error messages for constraint violations
6. Show role categories and descriptions clearly

## Success Criteria

The implementation is successful when:
1. ✅ All database tables and constraints are created
2. ✅ API endpoints respond correctly
3. ✅ Hierarchy constraints are enforced
4. ✅ Frontend component displays and manages roles
5. ✅ User assignments respect the hierarchy
6. ✅ Error handling provides clear feedback
7. ✅ Performance is acceptable for typical organization sizes

## Troubleshooting Common Issues

### API Returns Empty Results
- Check database connection
- Verify authentication token
- Ensure test data exists (organizations, business units, users)

### Constraint Violations Not Working
- Check if migration ran successfully
- Verify trigger functions were created
- Test triggers manually with direct SQL

### Frontend Component Issues
- Check browser console for TypeScript errors
- Verify service injection and HTTP client setup
- Test API endpoints directly first

### Authentication Errors
- Ensure admin token is valid and not expired
- Check API endpoint security decorators
- Verify user has required permissions

This comprehensive testing approach ensures the hierarchical functional roles system works correctly across all levels of the organization structure.