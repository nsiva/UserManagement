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
from models import ProfileResponse, UserWithRoles # Import the new ProfileResponse model

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
        
        # Determine if MFA is enabled (mfa_secret exists and is not null/empty)
        mfa_enabled = bool(profile_data.get('mfa_secret'))
        
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
        
        roles = await get_user_roles(str(current_user.user_id))
        logger.info(f"Fetched user {current_user.user_id} with roles: {roles}")
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