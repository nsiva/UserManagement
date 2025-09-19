"""
Constants package for the User Management API.
"""

from .roles import (
    ADMIN,
    ORGANIZATION_ADMIN,
    BUSINESS_UNIT_ADMIN,
    SUPER_USER,
    USER,
    ADMINISTRATIVE_ROLES,
    ADMIN_ROLES,
    ORGANIZATIONAL_ROLES,
    ALL_ADMIN_ROLES,
    has_admin_access,
    has_organizational_access,
    has_any_admin_access,
    has_organization_admin_access,
    has_business_unit_admin_access,
    validate_role_categories,
    validate_role_categories_legacy,
    get_administrative_role,
    get_functional_roles,
    is_administrative_role,
    is_functional_role
)

__all__ = [
    "ADMIN",
    "ORGANIZATION_ADMIN", 
    "BUSINESS_UNIT_ADMIN",
    "SUPER_USER",
    "USER",
    "ADMINISTRATIVE_ROLES",
    "ADMIN_ROLES",
    "ORGANIZATIONAL_ROLES",
    "ALL_ADMIN_ROLES",
    "has_admin_access",
    "has_organizational_access", 
    "has_any_admin_access",
    "has_organization_admin_access",
    "has_business_unit_admin_access",
    "validate_role_categories",
    "validate_role_categories_legacy",
    "get_administrative_role",
    "get_functional_roles",
    "is_administrative_role",
    "is_functional_role"
]