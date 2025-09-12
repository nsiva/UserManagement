"""
Constants package for the User Management API.
"""

from .roles import (
    ADMIN,
    ORGANIZATION_ADMIN,
    BUSINESS_UNIT_ADMIN,
    SUPER_USER,
    ADMIN_ROLES,
    ORGANIZATIONAL_ROLES,
    ALL_ADMIN_ROLES,
    has_admin_access,
    has_organizational_access,
    has_any_admin_access,
    has_organization_admin_access,
    has_business_unit_admin_access
)

__all__ = [
    "ADMIN",
    "ORGANIZATION_ADMIN", 
    "BUSINESS_UNIT_ADMIN",
    "SUPER_USER",
    "ADMIN_ROLES",
    "ORGANIZATIONAL_ROLES",
    "ALL_ADMIN_ROLES",
    "has_admin_access",
    "has_organizational_access", 
    "has_any_admin_access",
    "has_organization_admin_access",
    "has_business_unit_admin_access"
]