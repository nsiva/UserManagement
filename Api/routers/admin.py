# admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Response # Import Response
from typing import List, Dict, Optional, Union # Import Union for the auth_identity
from uuid import UUID
import logging
# import pyotp # REMOVED: Not used in this file's functions

from database import get_repository
from models import (
    UserCreate, UserUpdate, UserWithRoles,
    UserRoleAssignment, TokenData, ClientTokenData
)
from role import RoleCreate, RoleUpdate, RoleInDB
from exceptions import UserManagementError, DuplicateEmailError, ConstraintViolationError, DatabaseConnectionError, UserNotFoundError
# Assuming get_password_hash is not used directly in admin.py functions.
# get_current_admin_user, get_user_roles, get_current_client are needed.
from routers.auth import get_current_admin_user, get_user_roles, get_current_client, get_password_hash

admin_router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("admin")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# --- USER MANAGEMENT ---

# IMPORTANT: You need a custom dependency for "either/or" auth if you keep this endpoint as is.
# Example of such a custom dependency (can be placed in routers/auth.py or common_dependencies.py)
# You would need to ensure get_current_admin_user and get_current_client can be called with just 'token' if needed.
# For simplicity in this review, I'm assuming the existing dependencies just work as intended
# (i.e., get_current_admin_user raises if not admin, get_current_client raises if not valid client/scope).
# The current check `if not current_admin_user and not current_client:` then becomes relevant if BOTH
# dependencies returned None *without* raising an exception. This is less common.
# The most robust way is the custom dependency that combines them.

@admin_router.post("/users", response_model=UserWithRoles, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    # This setup means FastAPI calls *both* dependencies.
    # If get_current_admin_user raises HTTPException, this function won't be entered.
    # If get_current_admin_user passes, current_admin_user is set.
    # If get_current_client passes, current_client is set.
    # The current logic then checks for a client and its scope.
    current_admin_user: TokenData = Depends(get_current_admin_user), # User-based admin auth
    current_client: Optional[ClientTokenData] = Depends(get_current_client) # Client-based auth
):
    """
    Creates a new user account (FastAPI Admin or authorized API Client).
    Requires 'manage:users' scope for client authentication.
    """
    # Logic to ensure at least one authentication method is present and authorized
    if not current_admin_user and not current_client:
        # This case is usually reached if both dependencies return None, not if they raise.
        # If your dependencies raise HTTPExceptions on failure, this check might be redundant.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated by user or client.")

    # If a client is used, perform scope check (admin user implicitly has all access)
    if current_client and "manage:users" not in current_client.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client lacks 'manage:users' scope for user creation.")

    try:
        # Check if user with email already exists before attempting to create
        repo = get_repository()
        existing_user = await repo.get_user_by_email(user_data.email)
        if existing_user:
            logger.warning(f"Attempt to create user with existing email: {user_data.email}")
            raise DuplicateEmailError(user_data.email)
        
        # Validate business unit exists (if provided)
        if user_data.business_unit_id:
            if not await repo.validate_business_unit_exists(user_data.business_unit_id):
                logger.warning(f"Invalid business unit ID: {user_data.business_unit_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Invalid business unit ID. Business unit does not exist or is inactive."
                )
        
        # Generate UUID for new user
        import uuid
        user_id = str(uuid.uuid4())
        
        # Hash the password
        password_hash = get_password_hash(user_data.password)
        
        # Create user profile with hashed password
        profile_data = {
            "id": user_id,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "middle_name": user_data.middle_name,
            "last_name": user_data.last_name,
            "password_hash": password_hash,
            "is_admin": user_data.is_admin,
            "mfa_secret": None
        }
        created_user = await repo.create_user(profile_data)
        if not created_user:
            logger.error(f"Failed to create user profile for email: {user_data.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user profile.")
        
        # Assign user to business unit
        assigned_by = UUID(current_admin_user.user_id) if current_admin_user else None
        assignment_success = await repo.assign_user_to_business_unit(
            UUID(user_id), user_data.business_unit_id, assigned_by
        )
        if not assignment_success:
            logger.error(f"Failed to assign user {user_id} to business unit {user_data.business_unit_id}")
            # Note: User was created but business unit assignment failed
            # In a production system, you might want to rollback the user creation
    except HTTPException:
        raise
    except UserManagementError as e:
        # Custom user management exceptions - already logged in repository layer
        # Return user-friendly message to the client
        if isinstance(e, DuplicateEmailError):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.user_message)
        elif isinstance(e, ConstraintViolationError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.user_message)
        elif isinstance(e, DatabaseConnectionError):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.user_message)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.user_message)
    except Exception as e:
        # Unexpected errors - log with full details and return generic message
        logger.error(f"Unexpected error during user creation for {user_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred. Please try again later."
        )

    if user_data.roles:
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    roles = await get_user_roles(str(user_id))
    
    # Get business unit info for response
    business_unit_info = await repo.get_user_business_unit(UUID(user_id))
    
    logger.info(f"User created: {user_data.email} with roles: {roles}")
    # Get organization name for response
    business_unit_details = await repo.get_business_unit_by_id(user_data.business_unit_id) if business_unit_info else None
    
    return UserWithRoles(
        id=user_id, 
        email=user_data.email, 
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        is_admin=user_data.is_admin, 
        roles=roles,
        mfa_enabled=False,  # New users don't have MFA setup by default
        # Business Unit Information
        business_unit_id=business_unit_info['business_unit_id'] if business_unit_info else None,
        business_unit_name=business_unit_info['business_unit_name'] if business_unit_info else None,
        business_unit_code=business_unit_details.get('code') if business_unit_details else None,
        business_unit_location=business_unit_details.get('location') if business_unit_details else None,
        # Organization Information
        organization_id=UUID(business_unit_details['organization_id']) if business_unit_details and business_unit_details.get('organization_id') else None,
        organization_name=business_unit_details.get('organization_name') if business_unit_details else None,
        organization_city=None,  # Would need to fetch organization details separately
        organization_country=None,  # Would need to fetch organization details separately
        # Additional Information  
        business_unit_manager_name=business_unit_details.get('manager_name') if business_unit_details else None,
        parent_business_unit_name=business_unit_details.get('parent_name') if business_unit_details else None
    )


@admin_router.get("/users", response_model=List[UserWithRoles])
async def get_all_users(current_admin_user: TokenData = Depends(get_current_admin_user)):
    """
    Retrieves user profiles with organizational filtering based on user role.
    - admin/super_user: See all users
    - firm_admin: See users in their organization
    - group_admin: See users in their business unit only
    """
    try:
        repo = get_repository()
        current_user_roles = current_admin_user.roles
        
        # Determine filtering based on user role
        if any(role in current_user_roles for role in ['admin', 'super_user']):
            # Admin and super_user see all users
            users_data = await repo.get_all_users()
            logger.info(f"Admin/Super user {current_admin_user.email} accessing all users")
        else:
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                return []
            
            if 'firm_admin' in current_user_roles:
                # Firm admin sees users in their organization
                users_data = await repo.get_users_by_organization(user_context['organization_id'])
                logger.info(f"Firm admin {current_admin_user.email} accessing organization {user_context['organization_name']} users")
            elif 'group_admin' in current_user_roles:
                # Group admin sees users in their business unit only
                users_data = await repo.get_users_by_business_unit(user_context['business_unit_id'])
                logger.info(f"Group admin {current_admin_user.email} accessing business unit {user_context['business_unit_name']} users")
            else:
                logger.warning(f"User {current_admin_user.email} with roles {current_user_roles} has no user access permissions")
                return []
        
        if not users_data:
            logger.info("No users found for current user's scope.")
            return []
            
        users_with_roles = []
        for user_profile in users_data:
            roles = await get_user_roles(str(user_profile['id']))
            mfa_enabled = bool(user_profile.get('mfa_secret'))
            users_with_roles.append(UserWithRoles(
                id=user_profile['id'],
                email=user_profile['email'],
                first_name=user_profile.get('first_name'),
                middle_name=user_profile.get('middle_name'),
                last_name=user_profile.get('last_name'),
                is_admin=user_profile['is_admin'],
                roles=roles,
                mfa_enabled=mfa_enabled,
                # Business Unit Information
                business_unit_id=user_profile.get('business_unit_id'),
                business_unit_name=user_profile.get('business_unit_name'),
                business_unit_code=user_profile.get('business_unit_code'),
                business_unit_location=user_profile.get('business_unit_location'),
                # Organization Information
                organization_id=user_profile.get('organization_id'),
                organization_name=user_profile.get('organization_name'),
                organization_city=user_profile.get('organization_city'),
                organization_country=user_profile.get('organization_country'),
                # Additional Information
                business_unit_manager_name=user_profile.get('business_unit_manager_name'),
                parent_business_unit_name=user_profile.get('parent_business_unit_name')
            ))
        logger.info(f"Fetched {len(users_with_roles)} users for {current_admin_user.email}")
        return users_with_roles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all users: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.get("/users/{user_id}", response_model=UserWithRoles)
async def get_user(user_id: UUID, current_admin_user: TokenData = Depends(get_current_admin_user)):
    """
    Retrieves a single user's profile and roles by ID. (Admin only)
    """
    return await get_user_by_id(user_id)


@admin_router.put("/users/{user_id}", response_model=UserWithRoles)
async def update_user(user_id: UUID, user_data: UserUpdate, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Updates an existing user's details (email, password, admin status, first name, last name, roles, business unit). (Admin only)
    """
    repo = get_repository()
    
    # Validate business unit if provided
    if user_data.business_unit_id is not None:
        if not await repo.validate_business_unit_exists(user_data.business_unit_id):
            logger.warning(f"Invalid business unit ID: {user_data.business_unit_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid business unit ID. Business unit does not exist or is inactive."
            )
    
    profile_update_data = {}
    if user_data.email:
        profile_update_data["email"] = user_data.email
    if user_data.first_name is not None:
        profile_update_data["first_name"] = user_data.first_name
    if user_data.middle_name is not None:
        profile_update_data["middle_name"] = user_data.middle_name
    if user_data.last_name is not None:
        profile_update_data["last_name"] = user_data.last_name
    if user_data.password:
        profile_update_data["password_hash"] = get_password_hash(user_data.password)
    if user_data.is_admin is not None:
        profile_update_data["is_admin"] = user_data.is_admin

    if profile_update_data:
        try:
            success = await repo.update_user(user_id, profile_update_data)
            if not success:
                logger.error(f"Failed to update user profile for user_id: {user_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User profile update failed for user_id {user_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user profile.")

    if user_data.roles is not None: # `is not None` allows passing empty list to clear roles
        await assign_roles_to_user_by_names(user_id, user_data.roles)
    
    # Update business unit assignment if provided
    if user_data.business_unit_id is not None:
        try:
            assigned_by = UUID(current_user.user_id)
            assignment_success = await repo.assign_user_to_business_unit(
                user_id, user_data.business_unit_id, assigned_by
            )
            if not assignment_success:
                logger.error(f"Failed to update business unit assignment for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail="Failed to update business unit assignment."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Business unit assignment update failed for user_id {user_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update business unit assignment.")

    logger.info(f"User updated: {user_id}")
    # Call get_user_by_id to return the updated user details
    return await get_user_by_id(user_id) # Removed unused current_user argument


async def get_user_by_id(user_id: UUID): # Removed unused current_user argument
    """
    Helper function to retrieve a single user's profile and roles by ID.
    (Internal use or can be exposed as a separate admin.get("/users/{user_id}") endpoint)
    """
    try:
        repo = get_repository()
        user_profile = await repo.get_user_by_id(user_id)
        if not user_profile:
            logger.warning(f"User not found for user_id: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        roles = await get_user_roles(str(user_id))
        logger.info(f"Fetched user {user_id} with roles: {roles}")
        mfa_enabled = bool(user_profile.get('mfa_secret'))
        return UserWithRoles(
            id=user_profile['id'], 
            email=user_profile['email'], 
            first_name=user_profile.get('first_name'),
            middle_name=user_profile.get('middle_name'),
            last_name=user_profile.get('last_name'),
            is_admin=user_profile['is_admin'], 
            roles=roles,
            mfa_enabled=mfa_enabled,
            # Business Unit Information
            business_unit_id=user_profile.get('business_unit_id'),
            business_unit_name=user_profile.get('business_unit_name'),
            business_unit_code=user_profile.get('business_unit_code'),
            business_unit_location=user_profile.get('business_unit_location'),
            # Organization Information
            organization_id=user_profile.get('organization_id'),
            organization_name=user_profile.get('organization_name'),
            organization_city=user_profile.get('organization_city'),
            organization_country=user_profile.get('organization_country'),
            # Additional Information
            business_unit_manager_name=user_profile.get('business_unit_manager_name'),
            parent_business_unit_name=user_profile.get('parent_business_unit_name')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by id {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Deletes a user account and all related data. (Admin only)
    """
    try:
        # Delete the user profile (this will also handle user_roles deletion)
        repo = get_repository()
        success = await repo.delete_user(user_id)
        if not success:
            logger.warning(f"User not found for deletion: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
            
        logger.info(f"User deleted: {user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user.")
    # For 204 No Content, no response body should be returned
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- ROLE MANAGEMENT ---

@admin_router.post("/roles", response_model=RoleInDB, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Creates a new role entry in the database. (Admin only)
    """
    try:
        repo = get_repository()
        created_role = await repo.create_role(role_data.model_dump())
        if not created_role:
            logger.error(f"Failed to create role: {role_data.name}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create role.")
        logger.info(f"Role created: {role_data.name}")
        return RoleInDB(**created_role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating role {role_data.name}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.get("/roles", response_model=List[RoleInDB])
async def get_all_roles(current_user: TokenData = Depends(get_current_admin_user)):
    """
    Retrieves a list of all defined roles. (Admin only)
    """
    try:
        repo = get_repository()
        roles_data = await repo.get_all_roles()
        if not roles_data:
            logger.warning("No roles found.")
            return []
        logger.info(f"Fetched {len(roles_data)} roles.")
        return [RoleInDB(**item) for item in roles_data]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roles: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.put("/roles/{role_id}", response_model=RoleInDB)
async def update_role(role_id: UUID, role_data: RoleUpdate, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Updates an existing role by ID. (Admin only)
    """
    try:
        repo = get_repository()
        success = await repo.update_role(role_id, role_data.model_dump())
        if not success:
            logger.error(f"Role not found or failed to update: {role_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found or failed to update.")
        logger.info(f"Role updated: {role_id}")
        # Get updated role data to return
        updated_roles = await repo.get_all_roles()
        updated_role = next((r for r in updated_roles if str(r['id']) == str(role_id)), None)
        return RoleInDB(**updated_role) if updated_role else None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: UUID, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Deletes a role by ID. (Admin only)
    """
    try:
        repo = get_repository()
        success = await repo.delete_role(role_id)
        if not success:
            logger.error(f"Role not found or failed to delete: {role_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found or failed to delete.")
        logger.info(f"Role deleted: {role_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT) # No content for 204
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role {role_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# --- USER ROLE ASSIGNMENT ---

async def assign_roles_to_user_by_names(user_id: UUID, role_names: List[str]):
    """
    Helper function to assign roles to a user by role names.
    Deletes existing roles for the user and inserts the new set.
    """
    try:
        repo = get_repository()
        success = await repo.assign_user_roles(user_id, role_names)
        if not success:
            logger.error(f"Failed to assign roles to user {user_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign roles")
        
        if role_names:
            logger.info(f"Roles {role_names} assigned to user {user_id}")
        else:
            logger.info(f"All roles removed for user {user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning roles to user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.post("/users/{user_id}/roles", status_code=status.HTTP_200_OK)
async def manage_user_roles(user_id: UUID, assignment: UserRoleAssignment, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Manages roles for a specific user (assigns or removes roles). (Admin only)
    """
    try:
        if user_id != assignment.user_id:
            logger.warning(f"User ID mismatch in manage_user_roles: {user_id} != {assignment.user_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID in path must match user ID in body.")
        await assign_roles_to_user_by_names(user_id, assignment.role_names)
        logger.info(f"User roles updated for user {user_id}")
        return {"message": "User roles updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing user roles for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")