"""
Functional Roles API Router.

This router provides CRUD operations for functional roles and user assignments.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from database import get_repository
from models import (
    FunctionalRoleCreate, FunctionalRoleUpdate, FunctionalRoleInDB,
    UserFunctionalRoleAssignmentCreate, UserFunctionalRoleAssignmentUpdate, 
    UserFunctionalRoleAssignmentInDB, BulkUserFunctionalRoleAssignment,
    UserFunctionalRoleAssignmentResponse, FunctionalRoleCategoriesResponse,
    FunctionalRoleCategory, RolePermissionCheck, RolePermissionResponse,
    UserRolesSummary
)
from routers.auth import get_current_admin_user, get_current_user
from models import TokenData, UserWithRoles
from constants import has_admin_access, has_organization_admin_access

functional_roles_router = APIRouter(prefix="/functional-roles", tags=["functional-roles"])
logger = logging.getLogger("functional_roles")

# --- Functional Role CRUD Operations ---

@functional_roles_router.post("/", response_model=FunctionalRoleInDB, status_code=status.HTTP_201_CREATED)
async def create_functional_role(
    role_data: FunctionalRoleCreate,
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Create a new functional role. (Admin only)
    """
    try:
        repo = get_repository()
        
        # Check if role with same name already exists
        existing_role = await repo.get_functional_role_by_name(role_data.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Functional role with name '{role_data.name}' already exists"
            )
        
        # Create the role
        role_id = await repo.create_functional_role(role_data, current_user.user_id)
        created_role = await repo.get_functional_role_by_id(role_id)
        
        logger.info(f"Functional role created: {role_data.name} by user {current_user.user_id}")
        return created_role
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating functional role: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.get("/", response_model=List[FunctionalRoleInDB])
async def get_functional_roles(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all functional roles with optional filtering.
    """
    try:
        repo = get_repository()
        roles = await repo.get_functional_roles(category=category, is_active=is_active)
        return roles
        
    except Exception as e:
        logger.error(f"Error getting functional roles: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.get("/categories", response_model=FunctionalRoleCategoriesResponse)
async def get_functional_roles_by_category(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get functional roles grouped by category.
    """
    try:
        repo = get_repository()
        roles = await repo.get_functional_roles(is_active=True)
        
        # Group by category
        categories_dict = {}
        for role in roles:
            category = role.category or 'general'
            if category not in categories_dict:
                categories_dict[category] = []
            categories_dict[category].append(role)
        
        categories = [
            FunctionalRoleCategory(
                category=cat,
                roles=roles_list,
                count=len(roles_list)
            )
            for cat, roles_list in categories_dict.items()
        ]
        
        return FunctionalRoleCategoriesResponse(
            categories=categories,
            total_roles=len(roles)
        )
        
    except Exception as e:
        logger.error(f"Error getting functional roles by category: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.get("/{role_id}", response_model=FunctionalRoleInDB)
async def get_functional_role(
    role_id: UUID,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get a specific functional role by ID.
    """
    try:
        repo = get_repository()
        role = await repo.get_functional_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Functional role not found"
            )
        return role
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting functional role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.put("/{role_id}", response_model=FunctionalRoleInDB)
async def update_functional_role(
    role_id: UUID,
    role_data: FunctionalRoleUpdate,
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Update a functional role. (Admin only)
    """
    try:
        repo = get_repository()
        
        # Check if role exists
        existing_role = await repo.get_functional_role_by_id(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Functional role not found"
            )
        
        # Update the role
        success = await repo.update_functional_role(role_id, role_data, current_user.user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update functional role"
            )
        
        # Return updated role
        updated_role = await repo.get_functional_role_by_id(role_id)
        logger.info(f"Functional role updated: {role_id} by user {current_user.user_id}")
        return updated_role
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating functional role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_functional_role(
    role_id: UUID,
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Delete a functional role. (Admin only)
    This will also remove all user assignments to this role.
    """
    try:
        repo = get_repository()
        
        # Check if role exists
        existing_role = await repo.get_functional_role_by_id(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Functional role not found"
            )
        
        # Delete the role (cascade will handle user assignments)
        success = await repo.delete_functional_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete functional role"
            )
        
        logger.info(f"Functional role deleted: {role_id} by user {current_user.user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting functional role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# --- User Functional Role Assignment Operations ---

@functional_roles_router.post("/users/{user_id}/assign", response_model=UserFunctionalRoleAssignmentResponse)
async def assign_functional_roles_to_user(
    user_id: UUID,
    assignment: BulkUserFunctionalRoleAssignment,
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Assign functional roles to a user. (Admin only)
    """
    try:
        # Validate user_id matches
        if user_id != assignment.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID in path must match user ID in request body"
            )
        
        repo = get_repository()
        
        # Verify user exists
        user = await repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate functional roles exist and are available for this user (hierarchy check)
        from routers.functional_roles_hierarchy import get_available_functional_roles_for_user
        
        # Get available roles for this user from the hierarchy service
        try:
            available_roles_response = await get_available_functional_roles_for_user(user_id, current_user)
            available_role_names = [role.name for role in available_roles_response.roles]
        except Exception as hierarchy_error:
            logger.warning(f"Could not verify role hierarchy for user {user_id}: {hierarchy_error}")
            # Fallback to basic role validation without hierarchy check
            available_role_names = []
        
        for role_name in assignment.functional_role_names:
            role = await repo.get_functional_role_by_name(role_name)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Functional role '{role_name}' not found"
                )
            if not role.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Functional role '{role_name}' is not active"
                )
            # Check hierarchy constraint - role must be available for this user (if we have the data)
            if available_role_names and role_name not in available_role_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Functional role '{role_name}' is not available for this user. The role must be enabled at the user's business unit level."
                )
        
        # Assign roles
        success = await repo.assign_functional_roles_to_user(
            user_id, 
            assignment.functional_role_names, 
            current_user.user_id,
            assignment.replace_existing,
            assignment.notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign functional roles"
            )
        
        # Get updated user functional roles
        user_functional_roles = await repo.get_user_functional_roles(user_id)
        
        logger.info(f"Functional roles assigned to user {user_id}: {assignment.functional_role_names}")
        
        return UserFunctionalRoleAssignmentResponse(
            user_id=user_id,
            functional_roles=user_functional_roles,
            assigned_count=len(assignment.functional_role_names),
            message="Functional roles assigned successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning functional roles to user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.get("/users/{user_id}", response_model=List[FunctionalRoleInDB])
async def get_user_functional_roles(
    user_id: UUID,
    is_active: bool = Query(True, description="Filter by active assignments"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get functional roles assigned to a user.
    """
    try:
        repo = get_repository()
        
        # Check permission - users can see their own roles, admins can see any
        if str(user_id) != current_user.user_id and not has_admin_access(current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        roles = await repo.get_user_functional_roles(user_id, is_active=is_active)
        return roles
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user functional roles for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@functional_roles_router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_functional_role_from_user(
    user_id: UUID,
    role_id: UUID,
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Remove a functional role from a user. (Admin only)
    """
    try:
        repo = get_repository()
        
        success = await repo.remove_functional_role_from_user(user_id, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User functional role assignment not found"
            )
        
        logger.info(f"Functional role {role_id} removed from user {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing functional role {role_id} from user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# --- Permission Checking ---

@functional_roles_router.post("/check-permission", response_model=RolePermissionResponse)
async def check_user_permission(
    permission_check: RolePermissionCheck,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Check if a user has a specific permission through their functional roles.
    """
    try:
        # Check permission - users can check their own permissions, admins can check any
        if str(permission_check.user_id) != current_user.user_id and not has_admin_access(current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        repo = get_repository()
        has_permission, granted_by_roles = await repo.check_user_functional_permission(
            permission_check.user_id,
            permission_check.permission
        )
        
        return RolePermissionResponse(
            user_id=permission_check.user_id,
            permission=permission_check.permission,
            has_permission=has_permission,
            granted_by_roles=granted_by_roles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking permission: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")