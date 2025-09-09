from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
import logging

from database import get_repository
from firm import FirmCreate, FirmUpdate, FirmResponse
from models import TokenData
from routers.auth import get_current_user

firms_router = APIRouter(prefix="/firms", tags=["firms"])
logger = logging.getLogger("firms")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)


async def get_current_superuser(current_user: TokenData = Depends(get_current_user)):
    """Dependency to ensure current user has superuser role."""
    try:
        if 'super_user' not in current_user.roles:
            logger.warning(f"User {current_user.email} does not have super_user permissions.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super user access required")
        logger.info(f"Super user authenticated: {current_user.email}")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking super user permissions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@firms_router.post("/", response_model=FirmResponse, status_code=status.HTTP_201_CREATED)
async def create_firm(
    firm_data: FirmCreate,
    current_superuser: TokenData = Depends(get_current_superuser)
):
    """Create a new firm. Only accessible to super users."""
    try:
        repo = get_repository()
        
        # Create firm data dict
        firm_dict = firm_data.dict()
        
        created_firm = await repo.create_firm(firm_dict)
        if not created_firm:
            logger.error(f"Failed to create firm: {firm_data.company_name}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create firm")
        
        logger.info(f"Firm created successfully: {created_firm.get('company_name')} by user {current_superuser.email}")
        return FirmResponse(**created_firm)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating firm: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@firms_router.get("/", response_model=List[FirmResponse])
async def get_all_firms(current_superuser: TokenData = Depends(get_current_superuser)):
    """Get all firms. Only accessible to super users."""
    try:
        repo = get_repository()
        firms = await repo.get_all_firms()
        
        logger.info(f"Retrieved {len(firms)} firms for user {current_superuser.email}")
        return [FirmResponse(**firm) for firm in firms]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving firms: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@firms_router.get("/{firm_id}", response_model=FirmResponse)
async def get_firm(
    firm_id: UUID,
    current_superuser: TokenData = Depends(get_current_superuser)
):
    """Get a specific firm by ID. Only accessible to super users."""
    try:
        repo = get_repository()
        firm = await repo.get_firm_by_id(firm_id)
        
        if not firm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Firm not found")
        
        logger.info(f"Retrieved firm {firm_id} for user {current_superuser.email}")
        return FirmResponse(**firm)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving firm {firm_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")




@firms_router.put("/{firm_id}", response_model=FirmResponse)
async def update_firm(
    firm_id: UUID,
    firm_data: FirmUpdate,
    current_superuser: TokenData = Depends(get_current_superuser)
):
    """Update a firm. Only accessible to super users."""
    try:
        repo = get_repository()
        
        # Check if firm exists
        existing_firm = await repo.get_firm_by_id(firm_id)
        if not existing_firm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Firm not found")
        
        # Only include non-None values in update
        update_dict = {k: v for k, v in firm_data.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields provided for update")
        
        success = await repo.update_firm(firm_id, update_dict)
        if not success:
            logger.error(f"Failed to update firm {firm_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update firm")
        
        # Return updated firm
        updated_firm = await repo.get_firm_by_id(firm_id)
        logger.info(f"Firm {firm_id} updated successfully by user {current_superuser.email}")
        return FirmResponse(**updated_firm)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating firm {firm_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@firms_router.delete("/{firm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_firm(
    firm_id: UUID,
    current_superuser: TokenData = Depends(get_current_superuser)
):
    """Delete a firm. Only accessible to super users."""
    try:
        repo = get_repository()
        
        # Check if firm exists
        existing_firm = await repo.get_firm_by_id(firm_id)
        if not existing_firm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Firm not found")
        
        success = await repo.delete_firm(firm_id)
        if not success:
            logger.error(f"Failed to delete firm {firm_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete firm")
        
        logger.info(f"Firm {firm_id} deleted successfully by user {current_superuser.email}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting firm {firm_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")