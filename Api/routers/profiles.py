# routers/profiles.py (or integrated into your main router file)

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError, BaseModel
from postgrest.exceptions import APIError # Import Supabase specific errors
from io import BytesIO # Not needed for /profiles/me, but good to keep in mind for future image handling
import base64 # Not needed for /profiles/me
import qrcode # Not needed for /profiles/me
import pyotp # Not needed for /profiles/me
from typing import Optional

from database import get_repository # Updated to use repository pattern
from routers.auth import get_current_user, TokenData, get_user_roles # Import your authentication dependencies
from models import ProfileResponse, UserWithRoles, UserRolesResponse, UserFunctionalRoleDetail # Import the new ProfileResponse model

# Profile update model for self-editing
class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Configure logging
logging.basicConfig(level=logging.INFO) # Set to INFO for production, DEBUG for development
logger = logging.getLogger(__name__)

profiles_router = APIRouter(prefix="/profiles", tags=["Profiles"])

@profiles_router.get("/me", summary="Get the authenticated user's own profile", response_model=ProfileResponse)
async def get_my_profile(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieves the profile information for the currently authenticated user.
    """
    logger.info(f"Attempting to retrieve profile for user_id: {current_user.user_id}")

    try:
        # Query the profiles table for the current user's ID
        repo = get_repository()
        profile_data = await repo.get_user_by_id(current_user.user_id)

        if not profile_data:
            logger.warning(f"Profile not found for authenticated user_id: {current_user.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found."
            )
        
        # Determine if MFA is enabled (mfa_secret or mfa_method exists)
        mfa_enabled = bool(profile_data.get('mfa_secret') or profile_data.get('mfa_method'))
        
        # Prepare profile data without the sensitive mfa_secret
        safe_profile_data = {
            'id': profile_data['id'],
            'email': profile_data['email'],
            'first_name': profile_data.get('first_name'),
            'middle_name': profile_data.get('middle_name'),
            'last_name': profile_data.get('last_name'),
            'mfa_enabled': mfa_enabled
        }

        try:
            # Use Pydantic model for validation and structuring the response
            profile = ProfileResponse(**safe_profile_data)
            logger.info(f"Successfully retrieved profile for user_id: {current_user.user_id}, MFA enabled: {mfa_enabled}")
            return profile
        except ValidationError as e:
            logger.error(f"Data validation error for profile {current_user.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: Invalid profile data format. {e}"
            )

    except APIError as e:
        logger.error(f"Supabase API error retrieving profile for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred retrieving profile for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


@profiles_router.get("/me/full", summary="Get the authenticated user's full profile with roles and business unit", response_model=UserWithRoles)
async def get_my_full_profile(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieves the full profile information for the currently authenticated user, including roles and business unit info.
    Similar to the admin endpoint but for self-access only.
    """
    logger.info(f"Attempting to retrieve full profile for user_id: {current_user.user_id}")

    try:
        repo = get_repository()
        user_profile = await repo.get_user_by_id(current_user.user_id)
        if not user_profile:
            logger.warning(f"User profile not found for user_id: {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        # Get both administrative and functional roles
        administrative_roles = await get_user_roles(str(current_user.user_id))
        functional_roles_db = await repo.get_user_functional_roles(current_user.user_id, is_active=True)
        functional_role_names = [role.name for role in functional_roles_db]
        
        # Combine all roles
        roles = administrative_roles + functional_role_names
        logger.info(f"Fetched user {current_user.user_id} with administrative roles: {administrative_roles}, functional roles: {functional_role_names}")
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
        logger.error(f"Error fetching full profile for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@profiles_router.put("/me", summary="Update the authenticated user's profile", response_model=UserWithRoles)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Updates the authenticated user's own profile (first name and last name only).
    """
    logger.info(f"Attempting to update profile for user_id: {current_user.user_id}")

    try:
        repo = get_repository()
        
        # Prepare update data (only first_name and last_name allowed for self-update)
        profile_update_data = {}
        if profile_data.first_name is not None:
            profile_update_data["first_name"] = profile_data.first_name
        if profile_data.last_name is not None:
            profile_update_data["last_name"] = profile_data.last_name
        
        if not profile_update_data:
            logger.warning(f"No valid update data provided for user {current_user.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="No valid profile data provided for update."
            )

        # Update user profile
        success = await repo.update_user(current_user.user_id, profile_update_data)
        if not success:
            logger.error(f"Failed to update profile for user_id: {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        logger.info(f"Profile updated successfully for user_id: {current_user.user_id}")
        
        # Return updated profile
        return await get_my_full_profile(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile.")


@profiles_router.get("/me/roles", summary="Get the authenticated user's roles and permissions", response_model=UserRolesResponse)
async def get_my_roles(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieves the complete role information for the currently authenticated user,
    including organizational roles and functional roles with their sources.
    """
    logger.info(f"Attempting to retrieve roles for user_id: {current_user.user_id}")

    try:
        repo = get_repository()
        
        # Get user profile information
        user_profile = await repo.get_user_by_id(current_user.user_id)
        if not user_profile:
            logger.warning(f"User profile not found for user_id: {current_user.user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        # Get organizational roles (administrative roles)
        organizational_roles = await get_user_roles(str(current_user.user_id))
        logger.info(f"Found organizational roles for user {current_user.user_id}: {organizational_roles}")
        
        # Get functional roles with source information
        functional_roles = []
        
        # Get directly assigned functional roles
        direct_functional_roles = await repo.get_user_functional_roles(current_user.user_id, is_active=True)
        for role in direct_functional_roles:
            functional_roles.append(UserFunctionalRoleDetail(
                functional_role_id=str(role.id),
                functional_role_name=role.name,
                functional_role_label=role.label,
                functional_role_category=role.category,
                source="direct",
                source_name=None,
                assigned_at=role.created_at
            ))
        
        # Get functional roles inherited from business unit and organization using SQL query
        # This will use the existing views to get hierarchical functional roles
        try:
            if hasattr(repo, 'get_connection_pool'):
                pool = await repo.get_connection_pool()
                async with pool.acquire() as conn:
                    # Query to get all functional roles available to this user through hierarchy
                    hierarchy_query = """
                    SELECT DISTINCT
                        fr.id as functional_role_id,
                        fr.name as functional_role_name,
                        fr.label as functional_role_label,
                        fr.category as functional_role_category,
                        CASE 
                            WHEN bufr.functional_role_id IS NOT NULL THEN 'business_unit'
                            WHEN ofr.functional_role_id IS NOT NULL THEN 'organization'
                        END as source,
                        CASE 
                            WHEN bufr.functional_role_id IS NOT NULL THEN bu.name
                            WHEN ofr.functional_role_id IS NOT NULL THEN org.company_name
                        END as source_name,
                        CASE 
                            WHEN bufr.functional_role_id IS NOT NULL THEN bufr.assigned_at
                            WHEN ofr.functional_role_id IS NOT NULL THEN ofr.assigned_at
                        END as assigned_at
                    FROM aaa_profiles p
                    LEFT JOIN aaa_business_units bu ON p.business_unit_id = bu.id
                    LEFT JOIN aaa_organizations org ON bu.organization_id = org.id OR p.organization_id = org.id
                    LEFT JOIN aaa_business_unit_functional_roles bufr ON bu.id = bufr.business_unit_id AND bufr.is_enabled = true
                    LEFT JOIN aaa_organization_functional_roles ofr ON org.id = ofr.organization_id AND ofr.is_enabled = true
                    LEFT JOIN aaa_functional_roles fr ON (bufr.functional_role_id = fr.id OR ofr.functional_role_id = fr.id)
                    WHERE p.id = $1 AND fr.id IS NOT NULL
                    ORDER BY source, functional_role_category, functional_role_name
                    """
                    
                    result = await conn.fetch(hierarchy_query, current_user.user_id)
                    
                    for row in result:
                        # Check if this role is not already included from direct assignment
                        existing_role_ids = [fr.functional_role_id for fr in functional_roles]
                        if str(row['functional_role_id']) not in existing_role_ids:
                            functional_roles.append(UserFunctionalRoleDetail(
                                functional_role_id=str(row['functional_role_id']),
                                functional_role_name=row['functional_role_name'],
                                functional_role_label=row['functional_role_label'],
                                functional_role_category=row['functional_role_category'],
                                source=row['source'],
                                source_name=row['source_name'],
                                assigned_at=row['assigned_at']
                            ))
                            
        except Exception as e:
            logger.warning(f"Could not fetch hierarchical functional roles for user {current_user.user_id}: {e}")
            # Fallback to empty list if hierarchy query fails
            pass
        
        logger.info(f"Found {len(functional_roles)} functional roles for user {current_user.user_id}")
        
        # Prepare response
        response = UserRolesResponse(
            user_id=str(current_user.user_id),
            email=user_profile['email'],
            organizational_roles=organizational_roles,
            functional_roles=functional_roles,
            organization_name=user_profile.get('organization_name'),
            business_unit_name=user_profile.get('business_unit_name')
        )
        
        logger.info(f"Successfully retrieved roles for user_id: {current_user.user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roles for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user roles")