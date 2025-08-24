# admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Response # Import Response
from typing import List, Dict, Optional, Union # Import Union for the auth_identity
from uuid import UUID
import logging
# import pyotp # REMOVED: Not used in this file's functions

from database import supabase
from models import (
    UserCreate, UserUpdate, UserWithRoles, RoleCreate, RoleUpdate, RoleInDB,
    UserRoleAssignment, TokenData, ClientTokenData
)
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
        profile_response = supabase.from_('aaa_profiles').insert(profile_data).execute()
        if profile_response.count == 0:
            logger.error(f"Failed to create user profile for email: {user_data.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user profile.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation failed for {user_data.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User creation failed: {e}")

    if user_data.roles:
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    roles = await get_user_roles(str(user_id))
    logger.info(f"User created: {user_data.email} with roles: {roles}")
    return UserWithRoles(
        id=user_id, 
        email=user_data.email, 
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        is_admin=user_data.is_admin, 
        roles=roles
    )


@admin_router.get("/users", response_model=List[UserWithRoles])
async def get_all_users(current_admin_user: TokenData = Depends(get_current_admin_user)):
    """
    Retrieves all user profiles with their assigned roles. (Admin only)
    """
    try:
        response = supabase.from_('aaa_profiles').select('id, email, first_name, middle_name, last_name, is_admin').execute()
        if not response.data:
            logger.warning("No users found in profiles table.")
            return []
        users_with_roles = []
        for user_profile in response.data:
            roles = await get_user_roles(str(user_profile['id']))
            users_with_roles.append(UserWithRoles(
                id=user_profile['id'],
                email=user_profile['email'],
                first_name=user_profile.get('first_name'),
                middle_name=user_profile.get('middle_name'),
                last_name=user_profile.get('last_name'),
                is_admin=user_profile['is_admin'],
                roles=roles
            ))
        logger.info(f"Fetched {len(users_with_roles)} users.")
        return users_with_roles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all users: {e}", exc_info=True) # Added exc_info for full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@admin_router.put("/users/{user_id}", response_model=UserWithRoles)
async def update_user(user_id: UUID, user_data: UserUpdate, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Updates an existing user's details (email, password, admin status, first name, last name, roles). (Admin only)
    """
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
            profile_response = supabase.from_('aaa_profiles').update(profile_update_data).eq('id', str(user_id)).execute()
            if profile_response.count == 0:
                logger.error(f"Failed to update user profile for user_id: {user_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User profile update failed for user_id {user_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user profile.")

    if user_data.roles is not None: # `is not None` allows passing empty list to clear roles
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    logger.info(f"User updated: {user_id}")
    # Call get_user_by_id to return the updated user details
    return await get_user_by_id(user_id) # Removed unused current_user argument


async def get_user_by_id(user_id: UUID): # Removed unused current_user argument
    """
    Helper function to retrieve a single user's profile and roles by ID.
    (Internal use or can be exposed as a separate admin.get("/users/{user_id}") endpoint)
    """
    try:
        response = supabase.from_('aaa_profiles').select('id, email, first_name, middle_name, last_name, is_admin').eq('id', str(user_id)).limit(1).execute()
        if not response.data:
            logger.warning(f"User not found for user_id: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user_profile = response.data[0]
        roles = await get_user_roles(str(user_id))
        logger.info(f"Fetched user {user_id} with roles: {roles}")
        return UserWithRoles(
            id=user_profile['id'], 
            email=user_profile['email'], 
            first_name=user_profile.get('first_name'),
            middle_name=user_profile.get('middle_name'),
            last_name=user_profile.get('last_name'),
            is_admin=user_profile['is_admin'], 
            roles=roles
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
        # First delete user_roles entries
        supabase.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute()
        
        # Delete the user profile
        delete_response = supabase.from_('aaa_profiles').delete().eq('id', str(user_id)).execute()
        if delete_response.count == 0:
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
        response = supabase.from_('aaa_roles').insert(role_data.model_dump()).execute()
        if response.count == 0:
            logger.error(f"Failed to create role: {role_data.name}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create role.")
        logger.info(f"Role created: {role_data.name}")
        return RoleInDB(**response.data[0])
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
        response = supabase.from_('aaa_roles').select('*').execute()
        if not response.data:
            logger.warning("No roles found.")
            return []
        logger.info(f"Fetched {len(response.data)} roles.")
        return [RoleInDB(**item) for item in response.data]
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
        response = supabase.from_('aaa_roles').update(role_data.model_dump()).eq('id', str(role_id)).execute() # Convert UUID to str
        if response.count == 0:
            logger.error(f"Role not found or failed to update: {role_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found or failed to update.")
        logger.info(f"Role updated: {role_id}")
        return RoleInDB(**response.data[0])
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
        response = supabase.from_('aaa_roles').delete().eq('id', str(role_id)).execute() # Convert UUID to str
        if response.count == 0:
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
        if not role_names:
            # If no role names are provided, delete all existing roles for the user
            supabase.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute() # Convert UUID to str
            logger.info(f"All roles removed for user {user_id}")
            return

        # Fetch role IDs for the given role names
        roles_response = supabase.from_('aaa_roles').select('id, name').in_('name', role_names).execute()
        if not roles_response.data or len(roles_response.data) != len(role_names):
            # If some roles were not found, raise an error
            found_role_names = {item['name'] for item in roles_response.data}
            missing_roles = set(role_names) - found_role_names
            logger.warning(f"One or more specified roles not found for user {user_id}: {missing_roles}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"One or more specified roles not found: {', '.join(missing_roles)}.")

        role_ids = [item['id'] for item in roles_response.data]

        # Delete all existing roles for the user before assigning new ones
        supabase.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute() # Convert UUID to str

        insert_data = [{"user_id": str(user_id), "role_id": str(role_id)} for role_id in role_ids]
        if insert_data: # Only insert if there's data to insert
            supabase.from_('aaa_user_roles').insert(insert_data).execute()
            logger.info(f"Roles {role_names} assigned to user {user_id}")
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