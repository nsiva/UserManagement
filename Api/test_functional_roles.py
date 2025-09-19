#!/usr/bin/env python3
"""
Test script for functional roles system.
"""

import asyncio
from database import get_repository
from models import FunctionalRoleCreate, BulkUserFunctionalRoleAssignment
from constants.roles import validate_role_categories, ADMINISTRATIVE_ROLES

async def test_functional_roles_system():
    """Test the complete functional roles system"""
    print("🧪 Testing Functional Roles System")
    print("=" * 50)
    
    repo = get_repository()
    
    # Test 1: Get all functional roles
    print("\n1. Testing get_functional_roles()")
    roles = await repo.get_functional_roles()
    print(f"   Found {len(roles)} functional roles:")
    for role in roles:
        print(f"   - {role.name} ({role.category}): {role.label}")
    
    # Test 2: Get role by name
    print("\n2. Testing get_functional_role_by_name()")
    fleet_manager = await repo.get_functional_role_by_name("fleet_manager")
    if fleet_manager:
        print(f"   ✅ Fleet Manager found: {fleet_manager.label}")
        print(f"   Permissions: {fleet_manager.permissions}")
    else:
        print("   ❌ Fleet Manager not found")
    
    # Test 3: Test role validation (now completely database-driven)
    print("\n3. Testing role validation (database-driven)")
    test_cases = [
        ("firm_admin", ["fleet_manager", "accountant"]),
        ("user", ["driver"]),
        ("invalid_admin", ["fleet_manager"]),
        ("firm_admin", ["invalid_functional"]),
    ]
    
    for admin_role, functional_roles in test_cases:
        is_valid, error = await validate_role_categories(admin_role, functional_roles)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {admin_role} + {functional_roles}")
        if not is_valid:
            print(f"     Error: {error}")
    
    # Test 4: Test dynamic functional role detection
    print("\n4. Testing dynamic functional role detection")
    from constants.roles import is_functional_role
    test_role_names = ["fleet_manager", "invalid_role", "driver", "accountant"]
    
    for role_name in test_role_names:
        is_functional = await is_functional_role(role_name)
        status = "✅" if is_functional else "❌"
        print(f"   {status} is_functional_role('{role_name}') = {is_functional}")
    
    # Test 5: Create a test functional role
    print("\n5. Testing create_functional_role()")
    try:
        test_role = FunctionalRoleCreate(
            name="test_role",
            label="Test Role",
            description="A test role for demonstration",
            category="test",
            permissions=["test:read", "test:write"],
            is_active=True
        )
        
        from uuid import uuid4
        test_user_id = str(uuid4())
        role_id = await repo.create_functional_role(test_role, test_user_id)
        print(f"   ✅ Test role created with ID: {role_id}")
        
        # Clean up
        await repo.delete_functional_role(role_id)
        print(f"   ✅ Test role deleted")
        
    except Exception as e:
        print(f"   ❌ Error creating test role: {e}")
    
    # Test 6: Test permission checking
    print("\n6. Testing check_user_functional_permission()")
    # This would need a real user ID, so we'll skip for now
    print("   ⏭️  Skipped (requires valid user ID)")
    
    print("\n" + "=" * 50)
    print("✅ Functional roles system tests completed!")

if __name__ == "__main__":
    asyncio.run(test_functional_roles_system())