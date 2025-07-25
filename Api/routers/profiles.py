# routers/profiles.py (or integrated into your main router file)

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from postgrest.exceptions import APIError # Import Supabase specific errors
from io import BytesIO # Not needed for /profiles/me, but good to keep in mind for future image handling
import base64 # Not needed for /profiles/me
import qrcode # Not needed for /profiles/me
import pyotp # Not needed for /profiles/me

from database import supabase # Assuming your Supabase client is initialized here
from routers.auth import get_current_user, TokenData # Import your authentication dependencies
from models import ProfileResponse # Import the new ProfileResponse model

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
        response = supabase.from_('profiles').select(
            'id, email' # Select only non-sensitive fields
        ).eq('id', str(current_user.user_id)).limit(1).execute()

        if not response.data:
            logger.warning(f"Profile not found for authenticated user_id: {current_user.user_id}")
            # This case should ideally not happen if get_current_user correctly validates
            # the user against the database, but it's good for robustness.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found."
            )

        profile_data = response.data[0]

        try:
            # Use Pydantic model for validation and structuring the response
            profile = ProfileResponse(**profile_data)
            logger.info(f"Successfully retrieved profile for user_id: {current_user.user_id}")
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
    except Exception as e:
        logger.critical(f"An unexpected error occurred retrieving profile for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )