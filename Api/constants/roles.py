"""
Role constants for the User Management API.

This module defines all role constants used throughout the application
to avoid hardcoded strings and ensure consistency.
"""

# Role Constants
ADMIN = "admin"
ORGANIZATION_ADMIN = "firm_admin"
BUSINESS_UNIT_ADMIN = "group_admin"
SUPER_USER = "super_user"

# Role Groups for easier permission checking
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