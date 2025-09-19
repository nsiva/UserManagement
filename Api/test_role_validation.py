#!/usr/bin/env python3
"""
Test script for role category validation.
"""

from constants.roles import validate_role_categories, get_administrative_role, get_functional_roles

def test_role_validation():
    """Test various role combinations"""
    
    test_cases = [
        # Valid combinations
        (["user"], "✅ Valid: Basic user"),
        (["user", "driver"], "✅ Valid: User with driver role"),
        (["firm_admin", "fleet_manager", "accountant"], "✅ Valid: Firm admin with functional roles"),
        (["group_admin", "dispatcher"], "✅ Valid: Group admin with dispatcher role"),
        (["super_user", "fleet_manager", "accountant", "dispatcher"], "✅ Valid: Super user with all functional roles"),
        
        # Invalid combinations
        ([], "❌ Invalid: No roles"),
        (["fleet_manager", "accountant"], "❌ Invalid: No administrative role"),
        (["user", "firm_admin"], "❌ Invalid: Multiple administrative roles"),
        (["admin", "super_user", "fleet_manager"], "❌ Invalid: Multiple administrative roles"),
        (["invalid_role"], "❌ Invalid: Unknown role"),
        (["user", "invalid_role"], "❌ Invalid: Unknown functional role"),
    ]
    
    print("🧪 Testing Role Category Validation\n")
    print("=" * 60)
    
    for roles, description in test_cases:
        is_valid, error_message = validate_role_categories(roles)
        
        print(f"\nTest: {roles}")
        print(f"Expected: {description}")
        print(f"Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if not is_valid:
            print(f"Error: {error_message}")
        else:
            admin_role = get_administrative_role(roles)
            functional_roles = get_functional_roles(roles)
            print(f"Administrative: {admin_role}")
            print(f"Functional: {functional_roles}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_role_validation()