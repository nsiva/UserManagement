"""
Business Unit management endpoints.
Provides CRUD operations with role-based access control and organizational context validation.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from database import get_repository
from database.base_repository import BaseRepository
from business_unit import (
    BusinessUnitCreate, BusinessUnitUpdate, BusinessUnitResponse, 
    BusinessUnitHierarchy, BusinessUnitListResponse
)
from validators import BusinessUnitValidator, BusinessUnitValidationError
from routers.auth import get_current_admin_user
from models import TokenData
from constants import (
    ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN,
    ADMIN_ROLES, ALL_ADMIN_ROLES, has_admin_access, has_any_admin_access
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/business-units", tags=["business-units"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")





@router.post("/", response_model=BusinessUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_business_unit(
    business_unit: BusinessUnitCreate,
    repo: BaseRepository = Depends(get_repository),
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    """
    Create a new business unit with role-based access control.
    - admin/super_user: Can create business units in any organization
    - firm_admin: Can only create business units in their organization
    """
    try:
        current_user_roles = current_admin_user.roles
        
        # Check if user has appropriate role
        if not (has_admin_access(current_user_roles) or ORGANIZATION_ADMIN in current_user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Admin, super_user, or {ORGANIZATION_ADMIN} access required"
            )
        
        # For firm_admin users, validate they can only create business units in their organization
        if ORGANIZATION_ADMIN in current_user_roles and not has_admin_access(current_user_roles):
            # Get current user's organizational context
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - no organizational context"
                )
            
            # Check if the business unit is being created in user's organization
            if str(business_unit.organization_id) != str(user_context['organization_id']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create business units within your organization"
                )
        
        # Convert Pydantic model to dict and add metadata
        business_unit_data = business_unit.model_dump(exclude_unset=True)
        business_unit_data['id'] = str(uuid4())
        business_unit_data['created_at'] = datetime.now(timezone.utc)
        
        # Add audit fields
        business_unit_data['created_by'] = str(current_admin_user.user_id)
        
        # Validate using business unit validator (no organization context for admin/super_user)
        validated_data = BusinessUnitValidator.validate_for_create(
            business_unit_data, 
            organization_context=None
        )
        
        # Validate parent-child hierarchy if parent is specified
        if validated_data.get('parent_unit_id'):
            # Verify parent exists and belongs to same organization
            parent = await repo.get_business_unit_by_id(validated_data['parent_unit_id'])
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent business unit not found"
                )
            
            if parent['organization_id'] != validated_data['organization_id']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent business unit must belong to the same organization"
                )
        
        # Create business unit
        created_unit = await repo.create_business_unit(validated_data)
        
        logger.info(f"Business unit created: {created_unit['id']} by user {current_admin_user.user_id}")
        
        return BusinessUnitResponse(**created_unit)
    
    except BusinessUnitValidationError as e:
        logger.warning(f"Business unit validation failed: {e.errors}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Validation failed",
                "errors": e.errors
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create business unit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create business unit"
        )


@router.get("/{business_unit_id}", response_model=BusinessUnitResponse)
async def get_business_unit(
    business_unit_id: UUID,
    repo: BaseRepository = Depends(get_repository),
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    """
    Get business unit by ID with role-based access control.
    - admin/super_user: Can access any business unit
    - firm_admin/group_admin: Can only access business units in their organization
    """
    try:
        current_user_roles = current_admin_user.roles
        
        # Basic role check
        if not has_any_admin_access(current_user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin, super_user, firm_admin, or group_admin access required"
            )
        
        business_unit = await repo.get_business_unit_by_id(business_unit_id)
        
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit not found"
            )
        
        # Check organization context for firm/group admins
        if not has_admin_access(current_user_roles):
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - no organizational context"
                )
            
            # Check if business unit belongs to user's organization
            if str(business_unit['organization_id']) != str(user_context['organization_id']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access business units within your organization"
                )
        
        return BusinessUnitResponse(**business_unit)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get business unit {business_unit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business unit"
        )


@router.get("/", response_model=BusinessUnitListResponse)
async def get_business_units(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    repo: BaseRepository = Depends(get_repository),
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    """
    Get all business units with organizational filtering based on user role.
    - admin/super_user: See all business units
    - firm_admin: See business units in their organization
    - group_admin: See only their specific business unit
    """
    try:
        current_user_roles = current_admin_user.roles
        
        # Determine filtering based on user role
        if has_admin_access(current_user_roles):
            # Admin and super_user see all business units
            organization_id = None
            logger.info(f"Admin/Super user {current_admin_user.email} accessing all business units")
        else:
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                return BusinessUnitListResponse(
                    business_units=[],
                    total_count=0,
                    organization_id=None,
                    organization_name=None
                )
            
            if ORGANIZATION_ADMIN in current_user_roles:
                # firm_admin sees all business units in their organization
                organization_id = user_context['organization_id']
                logger.info(f"Firm admin {current_admin_user.email} accessing organization {user_context['organization_name']} business units")
            elif BUSINESS_UNIT_ADMIN in current_user_roles:
                # group_admin sees only their specific business unit
                if user_context.get('business_unit_id'):
                    # Get only the user's specific business unit
                    business_unit = await repo.get_business_unit_by_id(user_context['business_unit_id'])
                    if business_unit:
                        business_unit_responses = [BusinessUnitResponse(**business_unit)]
                        return BusinessUnitListResponse(
                            business_units=business_unit_responses,
                            total_count=1,
                            organization_id=user_context['organization_id'],
                            organization_name=user_context['organization_name']
                        )
                    else:
                        logger.warning(f"Business unit {user_context['business_unit_id']} not found for group_admin {current_admin_user.email}")
                        return BusinessUnitListResponse(
                            business_units=[],
                            total_count=0,
                            organization_id=user_context['organization_id'],
                            organization_name=user_context['organization_name']
                        )
                else:
                    logger.warning(f"Group admin {current_admin_user.email} has no business unit context")
                    return BusinessUnitListResponse(
                        business_units=[],
                        total_count=0,
                        organization_id=user_context['organization_id'],
                        organization_name=user_context['organization_name']
                    )
            else:
                logger.warning(f"User {current_admin_user.email} with roles {current_user_roles} has no business unit access permissions")
                return BusinessUnitListResponse(
                    business_units=[],
                    total_count=0,
                    organization_id=None,
                    organization_name=None
                )
        
        if organization_id:
            business_units = await repo.get_business_units_by_organization(organization_id)
            
            # Get organization name for response
            organization = await repo.get_organization_by_id(organization_id)
            organization_name = organization['company_name'] if organization else None
        else:
            business_units = await repo.get_all_business_units()
            organization_name = None
        
        business_unit_responses = [BusinessUnitResponse(**unit) for unit in business_units]
        
        return BusinessUnitListResponse(
            business_units=business_unit_responses,
            total_count=len(business_unit_responses),
            organization_id=organization_id,
            organization_name=organization_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get business units: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business units"
        )


@router.get("/hierarchy/{organization_id}", response_model=List[BusinessUnitHierarchy])
async def get_business_unit_hierarchy(
    organization_id: UUID,
    parent_id: Optional[UUID] = Query(None, description="Start hierarchy from this parent unit"),
    repo: BaseRepository = Depends(get_repository),
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    """
    Get business unit hierarchy for an organization with role-based access control.
    - admin/super_user: Can access any organization's hierarchy
    - firm_admin/group_admin: Can only access their organization's hierarchy
    """
    try:
        current_user_roles = current_admin_user.roles
        
        # Basic role check
        if not has_any_admin_access(current_user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin, super_user, firm_admin, or group_admin access required"
            )
        
        # Check organization context for firm/group admins
        if not has_admin_access(current_user_roles):
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - no organizational context"
                )
            
            # Check if requested organization matches user's organization
            if str(organization_id) != str(user_context['organization_id']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access business unit hierarchy within your organization"
                )
        
        hierarchy_units = await repo.get_business_unit_hierarchy(organization_id, parent_id)
        
        # Convert to hierarchy response models
        hierarchy_responses = []
        for unit in hierarchy_units:
            hierarchy_response = BusinessUnitHierarchy(**unit)
            hierarchy_responses.append(hierarchy_response)
        
        return hierarchy_responses
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get business unit hierarchy for organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business unit hierarchy"
        )


@router.put("/{business_unit_id}", response_model=BusinessUnitResponse)
async def update_business_unit(
    business_unit_id: UUID,
    business_unit_update: BusinessUnitUpdate,
    repo: BaseRepository = Depends(get_repository),
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    """
    Update a business unit with role-based access control.
    - admin/super_user: Can update any business unit
    - firm_admin: Can only update business units in their organization
    """
    try:
        current_user_roles = current_admin_user.roles
        
        # Check if user has appropriate role
        if not any(role in current_user_roles for role in ['admin', 'super_user', 'firm_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin, super_user, or firm_admin access required for business unit updates"
            )
        
        # Verify business unit exists
        existing_unit = await repo.get_business_unit_by_id(business_unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit not found"
            )
        
        # Check organization context for firm_admin users
        if not has_admin_access(current_user_roles):
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - no organizational context"
                )
            
            # Check if business unit belongs to user's organization
            if str(existing_unit['organization_id']) != str(user_context['organization_id']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update business units within your organization"
                )
        
        # Convert update model to dict
        update_data = business_unit_update.model_dump(exclude_unset=True)
        
        # Debug logging for received data
        logger.info(f"Business unit update received - data: {update_data}")
        if 'is_active' in update_data:
            logger.info(f"is_active field received: {update_data['is_active']} (type: {type(update_data['is_active'])})")
        
        # Add audit fields
        update_data['updated_by'] = str(current_admin_user.user_id)
        
        # Validate update data (no organization context needed for admin/super_user)
        validated_data = BusinessUnitValidator.validate_for_update(
            update_data,
            organization_context=None
        )
        
        # Debug logging for validated data
        logger.info(f"Business unit update validated - data: {validated_data}")
        if 'is_active' in validated_data:
            logger.info(f"is_active field after validation: {validated_data['is_active']} (type: {type(validated_data['is_active'])})")
        
        # Validate parent-child hierarchy if parent is being changed
        if 'parent_unit_id' in validated_data and validated_data['parent_unit_id']:
            # Verify parent exists and belongs to same organization
            parent = await repo.get_business_unit_by_id(validated_data['parent_unit_id'])
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent business unit not found"
                )
            
            if parent['organization_id'] != existing_unit['organization_id']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent business unit must belong to the same organization"
                )
            
            # Check for circular dependency
            is_valid_hierarchy = await repo.validate_business_unit_hierarchy(
                business_unit_id, validated_data['parent_unit_id']
            )
            if not is_valid_hierarchy:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid hierarchy: would create circular dependency"
                )
        
        # Update business unit
        success = await repo.update_business_unit(business_unit_id, validated_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update business unit"
            )
        
        # Return updated business unit
        updated_unit = await repo.get_business_unit_by_id(business_unit_id)
        
        logger.info(f"Business unit updated: {business_unit_id} by user {current_admin_user.user_id}")
        
        return BusinessUnitResponse(**updated_unit)
    
    except BusinessUnitValidationError as e:
        logger.warning(f"Business unit validation failed: {e.errors}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Validation failed",
                "errors": e.errors
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update business unit {business_unit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business unit"
        )


@router.delete("/{business_unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_unit(
    business_unit_id: UUID,
    repo: BaseRepository = Depends(get_repository),
    current_admin_user: TokenData = Depends(get_current_admin_user)
):
    """
    Delete a business unit with role-based access control.
    - admin/super_user: Can delete any business unit
    - firm_admin: Can only delete business units in their organization
    """
    try:
        current_user_roles = current_admin_user.roles
        
        # Check if user has appropriate role
        if not any(role in current_user_roles for role in ['admin', 'super_user', 'firm_admin']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin, super_user, or firm_admin access required for business unit deletion"
            )
        
        # Verify business unit exists
        existing_unit = await repo.get_business_unit_by_id(business_unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit not found"
            )
        
        # Check organization context for firm_admin users
        if not has_admin_access(current_user_roles):
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_admin_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_admin_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - no organizational context"
                )
            
            # Check if business unit belongs to user's organization
            if str(existing_unit['organization_id']) != str(user_context['organization_id']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete business units within your organization"
                )
        
        # Check if business unit has children
        children = await repo.get_business_units_by_organization(existing_unit['organization_id'])
        has_children = any(child['parent_unit_id'] == str(business_unit_id) for child in children)
        
        if has_children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete business unit that has child units. Delete or reassign child units first."
            )
        
        # Delete business unit
        success = await repo.delete_business_unit(business_unit_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete business unit"
            )
        
        logger.info(f"Business unit deleted: {business_unit_id} by user {current_admin_user.user_id}")
        
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete business unit {business_unit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete business unit"
        )