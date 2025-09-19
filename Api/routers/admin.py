# admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Response # Import Response
from typing import List, Dict, Optional, Union # Import Union for the auth_identity
from uuid import UUID
import logging
from datetime import datetime, timezone, timedelta
import os
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
from routers.auth import get_current_admin_user, get_user_roles, get_current_client, get_password_hash, send_password_setup_email, generate_reset_token
from constants import (
    ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN, USER,
    ADMIN_ROLES, has_admin_access, has_organization_admin_access, has_business_unit_admin_access,
    validate_role_categories_legacy, get_administrative_role, get_functional_roles,
    ADMINISTRATIVE_ROLES
)

admin_router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("admin")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

def validate_role_assignment(current_user_roles: List[str], roles_to_assign: List[str], current_user_id: Optional[str] = None, target_user_id: Optional[str] = None) -> None:
    """
    Validate that the current user can assign the requested roles.
    Role hierarchy restrictions:
    - group_admin: cannot assign super_user, admin, firm_admin, group_admin
    - firm_admin: cannot assign super_user, admin, firm_admin
    - admin: cannot assign super_user
    - super_user: can assign any role
    - No user can change their own role (security restriction)
    
    Args:
        current_user_roles: Roles of the current user performing the assignment
        roles_to_assign: Roles to be assigned to the target user
        current_user_id: ID of the user performing the assignment (optional)
        target_user_id: ID of the user receiving the role assignment (optional)
    
    Raises:
        HTTPException: If the current user cannot assign one or more of the requested roles
    """
    # Prevent users from changing their own roles
    if current_user_id and target_user_id and current_user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot change their own roles for security reasons"
        )
    # Super user can assign any role
    if SUPER_USER in current_user_roles:
        return
    
    restricted_roles = []
    
    # Admin cannot assign super_user
    if ADMIN in current_user_roles:
        restricted_roles = [SUPER_USER]
    
    # Firm admin cannot assign super_user, admin, firm_admin
    elif ORGANIZATION_ADMIN in current_user_roles:
        restricted_roles = [SUPER_USER, ADMIN, ORGANIZATION_ADMIN]
    
    # Group admin cannot assign super_user, admin, firm_admin, group_admin
    elif BUSINESS_UNIT_ADMIN in current_user_roles:
        restricted_roles = [SUPER_USER, ADMIN, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN]
    
    else:
        # User has no role assignment privileges
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to assign roles to users"
        )
    
    # Check if any of the roles to assign are restricted
    forbidden_roles = [role for role in roles_to_assign if role in restricted_roles]
    
    if forbidden_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to assign the following roles: {', '.join(forbidden_roles)}"
        )

def validate_user_edit_permission(current_user_roles: List[str], target_user_roles: List[str], current_user_id: Optional[str] = None, target_user_id: Optional[str] = None) -> None:
    """
    Validate that the current user can edit the target user based on role hierarchy.
    - super_user: Can edit anyone
    - admin: Can edit anyone except super_user
    - firm_admin: Can edit users except super_user, admin, firm_admin
    - group_admin: Can edit users except super_user, admin, firm_admin, group_admin
    - All users can edit their own profile (first name, last name only)
    
    Args:
        current_user_roles: Roles of the current user performing the edit
        target_user_roles: Roles of the user being edited
        current_user_id: ID of the user performing the edit (optional)
        target_user_id: ID of the user being edited (optional)
        
    Raises:
        HTTPException: If the current user cannot edit the target user
    """
    # Allow users to edit their own profile
    logger.info(f"validate_user_edit_permission: current_user_id={current_user_id} (type: {type(current_user_id)}), target_user_id={target_user_id} (type: {type(target_user_id)}), current_user_roles={current_user_roles}, target_user_roles={target_user_roles}")
    
    # Ensure both IDs are strings for proper comparison
    current_user_id_str = str(current_user_id).lower().strip() if current_user_id else None
    target_user_id_str = str(target_user_id).lower().strip() if target_user_id else None
    
    # Check for self-editing with robust comparison
    is_self_editing = (current_user_id_str and target_user_id_str and 
                      current_user_id_str == target_user_id_str)
    
    if is_self_editing:
        logger.info(f"Self-editing detected: user {current_user_id_str} editing own profile")
        return  # Users can always edit their own profile
    
    logger.info(f"Not self-editing: current_user_id_str='{current_user_id_str}' != target_user_id_str='{target_user_id_str}'")
    # Super user can edit anyone
    if SUPER_USER in current_user_roles:
        return
    
    # Admin can edit anyone except super_user
    if ADMIN in current_user_roles:
        if SUPER_USER in target_user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot edit super_user accounts"
            )
        return
    
    # Firm admin can edit users except super_user, admin, firm_admin
    if ORGANIZATION_ADMIN in current_user_roles:
        restricted_roles = [SUPER_USER, ADMIN, ORGANIZATION_ADMIN]
        forbidden_roles = [role for role in target_user_roles if role in restricted_roles]
        if forbidden_roles:
            logger.warning(f"Firm admin edit permission denied: current_user_id={current_user_id}, target_user_id={target_user_id}, forbidden_roles={forbidden_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Firm admins cannot edit users with roles: {', '.join(forbidden_roles)}"
            )
        return
    
    # Group admin can only edit users with lower roles
    if BUSINESS_UNIT_ADMIN in current_user_roles:
        restricted_roles = [SUPER_USER, ADMIN, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN]
        forbidden_roles = [role for role in target_user_roles if role in restricted_roles]
        if forbidden_roles:
            logger.warning(f"Group admin edit permission denied: current_user_id={current_user_id}, target_user_id={target_user_id}, forbidden_roles={forbidden_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Group admins cannot edit users with roles: {', '.join(forbidden_roles)}"
            )
        return
    
    # Default: no edit permission
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to edit users"
    )

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
        
        # Validate role categories BEFORE creating user to prevent inconsistent states
        if user_data.roles:
            is_valid, error_message = validate_role_categories_legacy(user_data.roles)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role combination: {error_message}"
                )
            
            # Validate role assignment permissions 
            if current_admin_user:
                # Generate temporary user ID for validation (we'll use the same ID for actual creation)
                import uuid
                temp_user_id = str(uuid.uuid4())
                validate_role_assignment(
                    current_admin_user.roles, 
                    user_data.roles, 
                    current_admin_user.user_id, 
                    temp_user_id
                )
                user_id = temp_user_id  # Use the validated ID for creation
        else:
            # Generate UUID for new user
            import uuid
            user_id = str(uuid.uuid4())
        
        # Handle password based on selected option
        password_setup_sent = False
        if user_data.password_option == "generate_now":
            # Validate that password is provided
            if not user_data.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password is required when 'generate_now' option is selected."
                )
            password_hash = get_password_hash(user_data.password)
        elif user_data.password_option == "send_link":
            # Create a temporary password hash (user will set real password via email)
            import secrets
            temp_password = secrets.token_urlsafe(32)
            password_hash = get_password_hash(temp_password)
            
            # Generate reset token for password setup
            reset_token = generate_reset_token()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", 30)))
            
            password_setup_sent = True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password_option. Must be 'generate_now' or 'send_link'."
            )
        
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
        assigned_by = current_admin_user.user_id if current_admin_user else None
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
        # Role validation was already done earlier in the function for admin users
        # For clients, we allow full permissions for now but this could be enhanced
        await assign_roles_to_user_by_names(user_id, user_data.roles)

    roles = await get_user_roles(str(user_id))
    
    # Get business unit info for response
    business_unit_info = await repo.get_user_business_unit(UUID(user_id))
    
    # Handle password setup email if needed
    success_message = f"User created successfully"
    if password_setup_sent:
        # Store reset token and send email
        token_stored = await repo.create_reset_token({
            'user_id': user_id,
            'token': reset_token,
            'expires_at': expires_at,
            'used': False
        })
        if token_stored:
            email_sent = await send_password_setup_email(user_data.email, reset_token)
            if email_sent:
                success_message = f"User created successfully. Password setup email sent to {user_data.email}"
                logger.info(f"Password setup email sent for user: {user_data.email}")
            else:
                success_message = f"User created successfully. Warning: Failed to send password setup email"
                logger.warning(f"Failed to send password setup email for user: {user_data.email}")
        else:
            success_message = f"User created successfully. Warning: Failed to store password setup token"
            logger.error(f"Failed to store password setup token for user: {user_data.email}")
    
    logger.info(f"User created: {user_data.email} with roles: {roles}")
    # Get organization name for response
    business_unit_details = await repo.get_business_unit_by_id(user_data.business_unit_id) if business_unit_info else None
    
    # Create response with custom message
    response = UserWithRoles(
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
        organization_id=business_unit_details['organization_id'] if business_unit_details and business_unit_details.get('organization_id') else None,
        organization_name=business_unit_details.get('organization_name') if business_unit_details else None,
        organization_city=None,  # Would need to fetch organization details separately
        organization_country=None,  # Would need to fetch organization details separately
        # Additional Information  
        business_unit_manager_name=business_unit_details.get('manager_name') if business_unit_details else None,
        parent_business_unit_name=business_unit_details.get('parent_name') if business_unit_details else None
    )
    
    # Log success message for admin reference
    logger.info(success_message)
    return response


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
        if has_admin_access(current_user_roles):
            # Admin and super_user see all users
            users_data = await repo.get_all_users()
            logger.info(f"Admin/Super user {current_admin_user.email} accessing all users")
        else:
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                return []
            
            if has_organization_admin_access(current_user_roles):
                # Firm admin sees users in their organization
                users_data = await repo.get_users_by_organization(user_context['organization_id'])
                logger.info(f"Firm admin {current_admin_user.email} accessing organization {user_context['organization_name']} users")
            elif has_business_unit_admin_access(current_user_roles):
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
            mfa_enabled = bool(user_profile.get('mfa_secret') or user_profile.get('mfa_method'))
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
    # Get the user first to check their roles
    user = await get_user_by_id(user_id)
    
    # Validate that current user can edit the target user
    validate_user_edit_permission(current_admin_user.roles, user.roles, current_admin_user.user_id, str(user_id))
    
    return user


@admin_router.put("/users/{user_id}", response_model=UserWithRoles)
async def update_user(user_id: UUID, user_data: UserUpdate, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Updates an existing user's details (email, password, admin status, first name, last name, roles, business unit). (Admin only)
    """
    repo = get_repository()
    
    # Get the current user's roles to validate edit permission
    existing_user = await get_user_by_id(user_id)
    logger.info(f"About to validate edit permission for user {user_id}")
    validate_user_edit_permission(current_user.roles, existing_user.roles, current_user.user_id, str(user_id))
    logger.info(f"Edit permission validation passed for user {user_id}")
    
    # Validate business unit if provided
    if user_data.business_unit_id is not None:
        if not await repo.validate_business_unit_exists(user_data.business_unit_id):
            logger.warning(f"Invalid business unit ID: {user_data.business_unit_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid business unit ID. Business unit does not exist or is inactive."
            )
    
    profile_update_data = {}
    password_reset_sent = False
    reset_token = None
    user_email = existing_user.email  # Store email for password reset
    
    if user_data.email:
        profile_update_data["email"] = user_data.email
        user_email = user_data.email  # Update email if provided
    if user_data.first_name is not None:
        profile_update_data["first_name"] = user_data.first_name
    if user_data.middle_name is not None:
        profile_update_data["middle_name"] = user_data.middle_name
    if user_data.last_name is not None:
        profile_update_data["last_name"] = user_data.last_name
        
    # Handle password update options
    if user_data.send_password_reset:
        # Generate password reset token instead of directly updating password
        reset_token = generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", 30)))
        password_reset_sent = True
    elif user_data.password:
        # Direct password update if provided and not sending reset link
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
        logger.info(f"Processing role assignment for user {user_id}: {user_data.roles}")
        # Validate role assignment permissions
        if user_data.roles:  # Only validate if roles are being assigned (not when clearing roles)
            logger.info(f"Roles are being assigned, validating permissions")
            # Check if user is editing their own profile
            current_user_id_str = str(current_user.user_id)
            target_user_id_str = str(user_id)
            logger.info(f"Role assignment self-edit check: current_user_id_str='{current_user_id_str}' vs target_user_id_str='{target_user_id_str}'")
            if current_user_id_str == target_user_id_str:
                logger.info(f"Self-editing detected in role assignment section for user {current_user.user_id}")
                # For self-editing, get the current user's administrative role level
                repo = get_repository()
                current_administrative_roles = await get_user_roles(str(user_id))
                
                # Find current user's administrative role
                current_admin_role = None
                for role in current_administrative_roles:
                    if role in ADMINISTRATIVE_ROLES:
                        current_admin_role = role
                        break
                
                # Find new administrative role in the submitted roles
                new_admin_role = None
                for role in user_data.roles:
                    if role in ADMINISTRATIVE_ROLES:
                        new_admin_role = role
                        break
                
                logger.info(f"Self-editing role validation: current_admin_role={current_admin_role}, new_admin_role={new_admin_role}, submitted_roles={user_data.roles}")
                
                # Check if the administrative role is changing
                if current_admin_role != new_admin_role:
                    logger.warning(f"Administrative role change attempt for self-editing user {current_user.user_id}: {current_admin_role} -> {new_admin_role}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Users cannot change their own administrative role for security reasons"
                    )
                
                # Allow the role assignment to proceed (administrative role unchanged, functional roles can change)
                logger.info(f"User {current_user.user_id} editing own profile - administrative role unchanged: {current_admin_role}")
            else:
                # Normal role assignment validation for other users
                validate_role_assignment(
                    current_user.roles, 
                    user_data.roles, 
                    current_user.user_id, 
                    str(user_id)
                )
        logger.info(f"About to assign roles to user {user_id}: {user_data.roles}")
        await assign_roles_to_user_by_names(user_id, user_data.roles)
        logger.info(f"Successfully assigned roles to user {user_id}")
    
    # Update business unit assignment if provided
    if user_data.business_unit_id is not None:
        try:
            assigned_by = current_user.user_id
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

    # Handle password reset email if requested
    if password_reset_sent and reset_token:
        # Store reset token and send email
        user_id_for_token = str(existing_user.id) if hasattr(existing_user, 'id') else str(user_id)
        token_stored = await repo.create_reset_token({
            'user_id': user_id_for_token,
            'token': reset_token,
            'expires_at': expires_at,
            'used': False
        })
        if token_stored:
            email_sent = await send_password_setup_email(user_email, reset_token)
            if email_sent:
                logger.info(f"Password reset email sent for user: {user_email}")
            else:
                logger.warning(f"Failed to send password reset email for user: {user_email}")
        else:
            logger.error(f"Failed to store password reset token for user: {user_email}")

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
        # Get both administrative and functional roles
        administrative_roles = await get_user_roles(str(user_id))
        functional_roles_db = await repo.get_user_functional_roles(user_id, is_active=True)
        functional_role_names = [role.name for role in functional_roles_db]
        
        # Combine all roles
        roles = administrative_roles + functional_role_names
        logger.info(f"Fetched user {user_id} with administrative roles: {administrative_roles}, functional roles: {functional_role_names}")
        mfa_enabled = bool(user_profile.get('mfa_secret') or user_profile.get('mfa_method'))
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
    Helper function to assign both administrative and functional roles to a user.
    Separates role names into administrative and functional roles, then assigns them separately.
    """
    try:
        repo = get_repository()
        
        # Get functional roles from database to separate them from administrative roles
        functional_roles_db = await repo.get_functional_roles(is_active=True)
        functional_role_names = {role.name for role in functional_roles_db}
        
        # Separate administrative and functional roles
        administrative_roles = []
        functional_roles = []
        
        for role_name in role_names:
            if role_name in functional_role_names:
                functional_roles.append(role_name)
            else:
                administrative_roles.append(role_name)
        
        # Assign administrative roles (these go to aaa_user_roles)
        if administrative_roles:
            admin_success = await repo.assign_user_roles(user_id, administrative_roles)
            if not admin_success:
                logger.error(f"Failed to assign administrative roles {administrative_roles} to user {user_id}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign administrative roles")
        else:
            # If no administrative roles, clear existing ones
            await repo.delete_user_roles(user_id)
        
        # Assign functional roles (these go to aaa_user_functional_roles)
        # Always call this to either assign new roles or clear existing ones
        current_user_id = str(user_id)  # For now, use the same user ID - this should be updated to track who made the assignment
        functional_success = await repo.assign_functional_roles_to_user(
            user_id, 
            functional_roles,  # Empty list will clear existing roles
            current_user_id, 
            replace_existing=True
        )
        if not functional_success:
            logger.error(f"Failed to assign functional roles {functional_roles} to user {user_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign functional roles")
        
        if role_names:
            logger.info(f"Roles assigned to user {user_id} - Administrative: {administrative_roles}, Functional: {functional_roles}")
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
        
        # Validate role categories (exactly one administrative role + optional functional roles)
        if assignment.role_names:  # Only validate if roles are being assigned (not when clearing roles)
            is_valid, error_message = validate_role_categories_legacy(assignment.role_names)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role combination: {error_message}"
                )
            
            # Validate role assignment permissions before making changes
            validate_role_assignment(
                current_user.roles, 
                assignment.role_names, 
                current_user.user_id, 
                str(user_id)
            )
        
        await assign_roles_to_user_by_names(user_id, assignment.role_names)
        logger.info(f"User roles updated for user {user_id}")
        return {"message": "User roles updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing user roles for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@admin_router.get("/role-categories")
async def get_role_categories(
    current_user: TokenData = Depends(get_current_admin_user),
    self_edit: bool = False
):
    """
    Get role categories for frontend role selection UI.
    Returns administrative roles and functional roles separately.
    Administrative roles are filtered based on current user's permissions.
    Functional roles are loaded from database.
    """
    try:
        repo = get_repository()
        
        # Get functional roles from database
        functional_roles_db = await repo.get_functional_roles(is_active=True)
        
        # Convert to frontend format
        functional_roles = []
        for role in functional_roles_db:
            functional_roles.append({
                "value": role.name,
                "label": role.label,
                "description": role.description or f"{role.label} role",
                "category": role.category,
                "permissions": role.permissions
            })
        
        # Define role hierarchy - users can assign roles lower than their own
        all_administrative_roles = [
            {"value": "user", "label": "User", "description": "Basic user with limited access"},
            {"value": "group_admin", "label": "Group Admin", "description": "Manages users within business unit"},
            {"value": "firm_admin", "label": "Firm Admin", "description": "Manages users across organization"},
            {"value": "admin", "label": "System Admin", "description": "Full system administration access"},
            {"value": "super_user", "label": "Super User", "description": "Highest level access with all permissions"}
        ]
        
        # Filter available roles based on current user's role
        current_user_role = current_user.roles[0] if current_user.roles else "user"
        available_roles = []
        
        # Role hierarchy: super_user > admin > firm_admin > group_admin > user
        role_hierarchy = ["user", "group_admin", "firm_admin", "admin", "super_user"]
        
        try:
            current_user_level = role_hierarchy.index(current_user_role)
            # Users can assign roles below their level, and their own level only for self-editing
            for role in all_administrative_roles:
                role_level = role_hierarchy.index(role["value"])
                if role_level < current_user_level:  # Can assign lower level roles
                    available_roles.append(role)
                elif role_level == current_user_level and self_edit:  # Include own level only for self-editing
                    # Add current user's role so they can see it when editing themselves
                    # (though it will be disabled in frontend)
                    available_roles.append(role)
        except ValueError:
            # If current user's role is not in hierarchy, default to allowing only "user"
            available_roles = [{"value": "user", "label": "User", "description": "Basic user with limited access"}]
        
        return {
            "administrative": {
                "name": "Administrative Level",
                "description": "User's access level and organizational permissions",
                "required": True,
                "multiple_selection": False,
                "roles": available_roles
            },
            "functional": {
                "name": "Functional Roles",
                "description": "Job-specific roles defining what the user can do",
                "required": False,
                "multiple_selection": True,
                "roles": functional_roles
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting role categories: {e}", exc_info=True)
        # Return minimal structure if database fails
        return {
            "administrative": {
                "name": "Administrative Level",
                "description": "User's access level and organizational permissions",
                "required": True,
                "multiple_selection": False,
                "roles": [
                    {"value": "user", "label": "User", "description": "Basic user with limited access"},
                    {"value": "group_admin", "label": "Group Admin", "description": "Manages users within business unit"},
                    {"value": "firm_admin", "label": "Firm Admin", "description": "Manages users across organization"},
                    {"value": "admin", "label": "System Admin", "description": "Full system administration access"},
                    {"value": "super_user", "label": "Super User", "description": "Highest level access with all permissions"}
                ]
            },
            "functional": {
                "name": "Functional Roles",
                "description": "Job-specific roles defining what the user can do",
                "required": False,
                "multiple_selection": True,
                "roles": []
            }
        }