#!/usr/bin/env python3
"""
Demo script showing how functional roles are now completely database-driven.
"""

import asyncio
from database import get_repository
from models import FunctionalRoleCreate

async def demo_dynamic_roles():
    """Demonstrate the dynamic role system"""
    print("🚀 Dynamic Functional Roles Demo")
    print("=" * 40)
    
    repo = get_repository()
    
    # Show current roles
    print("\n1. Current functional roles in database:")
    roles = await repo.get_functional_roles(is_active=True)
    for role in roles:
        print(f"   • {role.name} ({role.category}): {role.label}")
        print(f"     Permissions: {role.permissions[:3]}..." if len(role.permissions) > 3 else f"     Permissions: {role.permissions}")
    
    print(f"\n   Total: {len(roles)} functional roles")
    
    # Show how roles are categorized
    print("\n2. Roles by category:")
    categories = {}
    for role in roles:
        cat = role.category or 'general'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(role.name)
    
    for category, role_names in categories.items():
        print(f"   • {category.title()}: {', '.join(role_names)}")
    
    # Show validation works dynamically
    print("\n3. Dynamic validation examples:")
    from constants.roles import validate_role_categories
    
    test_cases = [
        ("user", ["driver"]),
        ("firm_admin", ["fleet_manager", "accountant"]),
        ("user", ["nonexistent_role"]),
    ]
    
    for admin, functional in test_cases:
        is_valid, error = await validate_role_categories(admin, functional)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {admin} + {functional}")
        if error:
            print(f"     → {error}")
    
    print("\n4. Key Benefits of Database-Driven Approach:")
    print("   ✅ No hardcoded role names in application code")
    print("   ✅ Add new roles through API/UI without code changes")
    print("   ✅ Permissions are stored with each role")
    print("   ✅ Categories help organize roles")
    print("   ✅ Roles can be activated/deactivated dynamically")
    print("   ✅ Full audit trail (created_by, updated_by, timestamps)")
    
    print("\n5. Example: Add new role through database:")
    print("   INSERT INTO aaa_functional_roles (name, label, category, permissions)")
    print("   VALUES ('security_officer', 'Security Officer', 'security',")
    print("          ARRAY['access_logs:read', 'cameras:view', 'incidents:write']);")
    
    print("\n" + "=" * 40)
    print("🎉 No more hardcoded functional role names!")
    print("   The system is now completely database-driven.")

if __name__ == "__main__":
    asyncio.run(demo_dynamic_roles())