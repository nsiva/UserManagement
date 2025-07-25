from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from uuid import UUID
import pyotp

from database import supabase
from models import (
    UserCreate, UserUpdate, UserWithRoles, RoleCreate, RoleUpdate, RoleInDB,
    UserRoleAssignment, TokenData, ClientTokenData # NEW IMPORTS
)
from routers.auth import get_current_admin_user, get_password_hash, get_user_roles, get_current_client # NEW IMPORTS

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# --- User Management ---
@admin_router.post("/users", response_model=UserWithRoles, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_admin_user)):
    # 1. Create user in Supabase Auth (without signup)
    try:
        auth_response = supabase.auth.admin.create_user(
            {
                "email": user_data.email,
                "password": user_data.password,
                "email_confirm": True # Automatically confirm email
            }
        )
        if not auth_response.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user in Auth.")
        user_id = auth_response.user.id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Auth user creation failed: {e}")

    # 2. Create profile in public.profiles table
    profile_data = {
        "id": user_id,
        "email": user_data.email,
        "is_admin": user_data.is_admin,
        "mfa_secret": None # MFA secret is set separately
    }
    profile_response = supabase.from_('profiles').insert(profile_data).execute()
    if profile_response.count == 0:
        # If profile creation fails, try to delete auth user to prevent orphaned entries
        supabase.auth.admin.delete_user(user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user profile.")

    # 3. Assign roles
    if user_data.roles:
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    # Fetch and return the created user with their roles
    roles = await get_user_roles(str(user_id))
    return UserWithRoles(id=user_id, email=user_data.email, is_admin=user_data.is_admin, roles=roles)


@admin_router.post("/users", response_model=UserWithRoles, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    # Allow either an admin user OR a client token to access this endpoint
    current_admin_user: TokenData = Depends(get_current_admin_user), # User-based admin auth
    current_client: Optional[ClientTokenData] = Depends(get_current_client) # Client-based auth
):
    # Logic to ensure at least one authentication method is present and authorized
    if not current_admin_user and not current_client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # If a client is used, check for required scopes
    if current_client and "manage:users" not in current_client.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client lacks 'manage:users' scope")

    # If it's a user, get_current_admin_user already ensures admin role.
    # ... (rest of your create_user logic) ...
    try:
        auth_response = supabase.auth.admin.create_user(
            {
                "email": user_data.email,
                "password": user_data.password,
                "email_confirm": True
            }
        )
        if not auth_response.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user in Auth.")
        user_id = auth_response.user.id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Auth user creation failed: {e}")

    profile_data = {
        "id": user_id,
        "email": user_data.email,
        "is_admin": user_data.is_admin,
        "mfa_secret": None
    }
    profile_response = supabase.from_('profiles').insert(profile_data).execute()
    if profile_response.count == 0:
        supabase.auth.admin.delete_user(user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user profile.")

    if user_data.roles:
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    roles = await get_user_roles(str(user_id))
    return UserWithRoles(id=user_id, email=user_data.email, is_admin=user_data.is_admin, roles=roles)


@admin_router.get("/users", response_model=List[UserWithRoles])
async def get_all_users(
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    if not current_admin_user and not current_client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    #if current_client and "read:users" not in current_client.scopes:
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client lacks 'read:users' scope")

    # ... (rest of your get_all_users logic) ...
    response = supabase.from_('profiles').select('id, email, is_admin').execute()
    if not response.data:
        return []

    users_with_roles = []
    for user_profile in response.data:
        roles = await get_user_roles(str(user_profile['id']))
        users_with_roles.append(UserWithRoles(
            id=user_profile['id'],
            email=user_profile['email'],
            is_admin=user_profile['is_admin'],
            roles=roles
        ))
    return users_with_roles

@admin_router.put("/users/{user_id}", response_model=UserWithRoles)
async def update_user(user_id: UUID, user_data: UserUpdate, current_user: dict = Depends(get_current_admin_user)):
    # 1. Update user in Supabase Auth (email, password)
    auth_update_data = {}
    if user_data.email:
        auth_update_data["email"] = user_data.email
    if user_data.password:
        auth_update_data["password"] = user_data.password

    if auth_update_data:
        try:
            # Note: Supabase admin update user only changes email/password, not profile data.
            # It also doesn't return the updated user object directly.
            supabase.auth.admin.update_user_by_id(str(user_id), auth_update_data)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Auth user update failed: {e}")

    # 2. Update profile in public.profiles table
    profile_update_data = {}
    if user_data.email: # Update email in profiles if it changed
        profile_update_data["email"] = user_data.email
    if user_data.is_admin is not None:
        profile_update_data["is_admin"] = user_data.is_admin

    if profile_update_data:
        profile_response = supabase.from_('profiles').update(profile_update_data).eq('id', user_id).execute()
        if profile_response.count == 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user profile.")

    # 3. Update roles if provided
    if user_data.roles is not None: # Check if roles list was explicitly provided
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    # Fetch and return the updated user with their roles
    return await get_user_by_id(user_id, current_user) # Re-fetch to get latest state

@admin_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, current_user: dict = Depends(get_current_admin_user)):
    # Delete user from Supabase Auth (this cascades to profiles and user_roles due to CASCADE ON DELETE)
    try:
        supabase.auth.admin.delete_user(str(user_id))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to delete user: {e}")
    return {"message": "User deleted successfully"}

# --- Role Management ---
@admin_router.post("/roles", response_model=RoleInDB, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, current_user: dict = Depends(get_current_admin_user)):
    response = supabase.from_('roles').insert(role_data.model_dump()).execute()
    if response.count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create role.")
    return RoleInDB(**response.data[0])

@admin_router.get("/roles", response_model=List[RoleInDB])
async def get_all_roles(current_user: dict = Depends(get_current_admin_user)):
    response = supabase.from_('roles').select('*').execute()
    if not response.data:
        return []
    return [RoleInDB(**item) for item in response.data]

@admin_router.put("/roles/{role_id}", response_model=RoleInDB)
async def update_role(role_id: UUID, role_data: RoleUpdate, current_user: dict = Depends(get_current_admin_user)):
    response = supabase.from_('roles').update(role_data.model_dump()).eq('id', role_id).execute()
    if response.count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found or failed to update.")
    return RoleInDB(**response.data[0])

@admin_router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: UUID, current_user: dict = Depends(get_current_admin_user)):
    response = supabase.from_('roles').delete().eq('id', role_id).execute()
    if response.count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found or failed to delete.")
    return {"message": "Role deleted successfully"}

# --- User Role Assignment ---
async def assign_roles_to_user_by_names(user_id: UUID, role_names: List[str]):
    # Get role IDs from names
    if not role_names:
        # If no roles provided, delete all existing roles for the user
        supabase.from_('user_roles').delete().eq('user_id', user_id).execute()
        return

    roles_response = supabase.from_('roles').select('id, name').in_('name', role_names).execute()
    if not roles_response.data or len(roles_response.data) != len(role_names):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more specified roles not found.")

    role_ids = [item['id'] for item in roles_response.data]

    # Delete existing roles for the user
    supabase.from_('user_roles').delete().eq('user_id', user_id).execute()

    # Insert new roles
    insert_data = [{"user_id": str(user_id), "role_id": str(role_id)} for role_id in role_ids]
    if insert_data:
        supabase.from_('user_roles').insert(insert_data).execute()

@admin_router.post("/users/{user_id}/roles", status_code=status.HTTP_200_OK)
async def manage_user_roles(user_id: UUID, assignment: UserRoleAssignment, current_user: dict = Depends(get_current_admin_user)):
    if user_id != assignment.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID in path must match user ID in body.")

    await assign_roles_to_user_by_names(user_id, assignment.role_names)
    return {"message": "User roles updated successfully."}
