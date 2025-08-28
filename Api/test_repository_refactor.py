#!/usr/bin/env python3
"""
Test script to verify the database repository refactoring.
This script tests that the repository pattern is working correctly.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


async def test_repository_factory():
    """Test that the repository factory works correctly."""
    try:
        from database import get_repository, RepositoryFactory
        
        print("✅ Successfully imported repository factory")
        
        # Test that we can get a repository instance
        repo = get_repository()
        print(f"✅ Successfully created repository instance: {type(repo).__name__}")
        
        # Test that it's a valid repository with required methods
        required_methods = [
            'create_user', 'get_user_by_email', 'get_user_by_id', 'get_all_users',
            'update_user', 'delete_user', 'create_role', 'get_all_roles',
            'update_role', 'delete_role', 'get_user_roles', 'assign_user_roles',
            'update_mfa_secret', 'get_client_by_id', 'create_reset_token',
            'validate_reset_token', 'mark_token_used'
        ]
        
        for method in required_methods:
            if hasattr(repo, method):
                print(f"✅ Repository has method: {method}")
            else:
                print(f"❌ Repository missing method: {method}")
                return False
        
        print("\n✅ All repository methods are present!")
        
        # Test provider switching
        original_provider = os.environ.get("DATABASE_PROVIDER", "supabase")
        
        # Test Supabase provider
        os.environ["DATABASE_PROVIDER"] = "supabase"
        RepositoryFactory.reset()
        supabase_repo = get_repository()
        print(f"✅ Supabase repository: {type(supabase_repo).__name__}")
        
        # Test PostgreSQL provider (if connection string is available)
        if os.environ.get("POSTGRES_CONNECTION_STRING"):
            os.environ["DATABASE_PROVIDER"] = "postgres"
            RepositoryFactory.reset()
            postgres_repo = get_repository()
            print(f"✅ PostgreSQL repository: {type(postgres_repo).__name__}")
        else:
            print("ℹ️  PostgreSQL connection string not found, skipping PostgreSQL test")
        
        # Restore original provider
        if original_provider:
            os.environ["DATABASE_PROVIDER"] = original_provider
        else:
            os.environ.pop("DATABASE_PROVIDER", None)
        RepositoryFactory.reset()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_backward_compatibility():
    """Test that backward compatibility is maintained."""
    try:
        # Test old import style still works (with deprecation warning)
        import database
        print("✅ Old database module import still works")
        
        if hasattr(database, 'supabase'):
            print("✅ Old supabase client is still available")
        else:
            print("❌ Old supabase client not available")
            return False
        
        if hasattr(database, 'get_supabase_client'):
            print("✅ Old get_supabase_client function is still available")
        else:
            print("❌ Old get_supabase_client function not available")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def test_environment_variables():
    """Test that required environment variables are present."""
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "JWT_SECRET_KEY"]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are present")
        return True


async def main():
    """Main test function."""
    print("🧪 Testing Database Repository Refactoring\n")
    
    tests = [
        ("Environment Variables", test_environment_variables()),
        ("Repository Factory", await test_repository_factory()),
        ("Backward Compatibility", await test_backward_compatibility())
    ]
    
    passed = 0
    total = len(tests)
    
    print("\n📊 Test Results:")
    print("=" * 50)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Repository refactoring is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)