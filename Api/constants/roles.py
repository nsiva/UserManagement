"""
Role constants for the User Management API.

This module defines all role constants used throughout the application
to avoid hardcoded strings and ensure consistency.
"""

# Administrative Role Constants
ADMIN = "admin"
ORGANIZATION_ADMIN = "firm_admin"
BUSINESS_UNIT_ADMIN = "group_admin"
SUPER_USER = "super_user"
USER = "user"

# Role Categories
ADMINISTRATIVE_ROLES = [USER, BUSINESS_UNIT_ADMIN, ORGANIZATION_ADMIN, ADMIN, SUPER_USER]
# Note: FUNCTIONAL_ROLES are now dynamically loaded from database

# Legacy Role Groups (for backward compatibility)
ADMIN_ROLES = [ADMIN, SUPER_USER]
ORGANIZATIONAL_ROLES = [ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN]
ALL_ADMIN_ROLES = [ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN]

# Permission checking utilities
def has_admin_access(user_roles: list) -> bool:
    """Check if user has admin or super_user access."""
    return any(role in user_roles for role in ADMIN_ROLES)

def has_organizational_access(user_roles: list) -> bool:
    """Check if user has organizational admin access (firm_admin or group_admin)."""
    return any(role in user_roles for role in ORGANIZATIONAL_ROLES)

def has_any_admin_access(user_roles: list) -> bool:
    """Check if user has any type of admin access."""
    return any(role in user_roles for role in ALL_ADMIN_ROLES)

def has_organization_admin_access(user_roles: list) -> bool:
    """Check if user has organization admin (firm_admin) access."""
    return ORGANIZATION_ADMIN in user_roles

def has_business_unit_admin_access(user_roles: list) -> bool:
    """Check if user has business unit admin (group_admin) access."""
    return BUSINESS_UNIT_ADMIN in user_roles

# Role Category Validation Functions
async def validate_role_categories(administrative_role: str, functional_role_names: list = None) -> tuple[bool, str]:
    """
    Validate that user has exactly one administrative role and valid functional roles.
    
    Args:
        administrative_role: The administrative role name
        functional_role_names: List of functional role names (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not administrative_role:
        return False, "Administrative role is required"
    
    # Validate administrative role
    if administrative_role not in ADMINISTRATIVE_ROLES:
        return False, f"Invalid administrative role: {administrative_role}"
    
    # Functional roles are optional, but if provided, must be validated against database
    if functional_role_names:
        from database import get_repository
        try:
            repo = get_repository()
            for role_name in functional_role_names:
                role = await repo.get_functional_role_by_name(role_name)
                if not role:
                    return False, f"Functional role '{role_name}' does not exist"
                if not role.is_active:
                    return False, f"Functional role '{role_name}' is not active"
        except Exception as e:
            return False, f"Error validating functional roles: {str(e)}"
    
    return True, ""

def validate_role_categories_legacy(roles: list) -> tuple[bool, str]:
    """
    Legacy validation function for backward compatibility.
    Validates that roles contain exactly one administrative role.
    
    Args:
        roles: List of role names to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not roles:
        return False, "At least one role must be assigned"
    
    admin_roles_count = len([role for role in roles if role in ADMINISTRATIVE_ROLES])
    
    # Must have exactly one administrative role
    if admin_roles_count == 0:
        return False, "Exactly one administrative role (user, group_admin, firm_admin, admin, or super_user) must be assigned"
    elif admin_roles_count > 1:
        admin_roles_in_list = [role for role in roles if role in ADMINISTRATIVE_ROLES]
        return False, f"Only one administrative role allowed. Found: {', '.join(admin_roles_in_list)}"
    
    return True, ""

def get_administrative_role(roles: list) -> str:
    """Get the administrative role from a list of roles."""
    admin_roles = [role for role in roles if role in ADMINISTRATIVE_ROLES]
    return admin_roles[0] if admin_roles else ""

async def get_functional_roles(roles: list) -> list:
    """Get the functional roles from a list of roles by checking database."""
    from database import get_repository
    try:
        repo = get_repository()
        db_functional_roles = await repo.get_functional_roles(is_active=True)
        functional_role_names = [role.name for role in db_functional_roles]
        return [role for role in roles if role in functional_role_names]
    except Exception:
        return []

def is_administrative_role(role: str) -> bool:
    """Check if a role is an administrative role."""
    return role in ADMINISTRATIVE_ROLES

async def is_functional_role(role: str) -> bool:
    """Check if a role is a functional role by querying database."""
    from database import get_repository
    try:
        repo = get_repository()
        functional_role = await repo.get_functional_role_by_name(role)
        return functional_role is not None and functional_role.is_active
    except Exception:
        return False