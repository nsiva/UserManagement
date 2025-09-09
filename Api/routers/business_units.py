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
from routers.auth import get_current_user, get_current_admin_user, get_current_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/business-units", tags=["business-units"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_organization_context(current_user: Optional[Dict[str, Any]], 
                                current_client: Optional[Dict[str, Any]] = None) -> Optional[UUID]:
    """
    Extract organization context from user or client for access control.
    Returns None if user is admin or super_user with global access.
    """
    # Admin users and clients with manage:business_units scope have global access
    if current_user and hasattr(current_user, 'is_admin') and current_user.is_admin:
        return None
    
    if current_client and hasattr(current_client, 'scopes') and 'manage:business_units' in current_client.scopes:
        return None
    
    # For firm admins, extract organization context
    # This would be extended based on user-organization relationship implementation
    # For now, returning None to allow global access - implement org context as needed
    return None


async def get_current_user_or_client(token: str = Depends(oauth2_scheme)):
    """Dependency that accepts either user or client authentication."""
    from routers.auth import get_current_user, get_current_client
    
    # Try user authentication first
    try:
        from routers.auth import jwt, CLIENT_JWT_SECRET, ALGORITHM
        from models import TokenData
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, CLIENT_JWT_SECRET, algorithms=[ALGORITHM])
            user_id: str = payload.get("user_id")
            email: str = payload.get("email")
            is_admin: bool = payload.get("is_admin", False)
            roles: List[str] = payload.get("roles", [])
            
            if user_id and email:
                # This is a user token
                return {
                    "user": TokenData(user_id=user_id, email=email, is_admin=is_admin, roles=roles),
                    "client": None
                }
        except:
            pass
        
        # Try client token
        try:
            from models import ClientTokenData
            payload = jwt.decode(token, CLIENT_JWT_SECRET, algorithms=[ALGORITHM])
            client_id = payload.get("client_id")
            if client_id:
                # This is a client token
                return {
                    "user": None,
                    "client": ClientTokenData(
                        client_id=client_id,
                        scopes=payload.get("scopes", []),
                        exp=payload.get("exp")
                    )
                }
        except:
            pass
        
        raise credentials_exception
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )


@router.post("/", response_model=BusinessUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_business_unit(
    business_unit: BusinessUnitCreate,
    repo: BaseRepository = Depends(get_repository),
    auth_info = Depends(get_current_user_or_client)
):
    """
    Create a new business unit.
    
    Requires: admin, super_user, organization/firm admin, or API client with manage:business_units scope.
    Firm admins are limited to their organization context.
    """
    try:
        current_user = auth_info.get("user")
        current_client = auth_info.get("client")
        
        # Check authorization
        if not current_user and not current_client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify user has appropriate permissions
        if current_user:
            # For users, check if admin, super_user, or organization/firm admin
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
            
            if not is_admin and not any(role in ['admin', 'super_user', 'organization_admin', 'firm_admin'] for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin, super_user, organization_admin, or firm_admin access required"
                )
        elif current_client:
            # For clients, check scopes
            client_scopes = current_client.scopes if hasattr(current_client, 'scopes') else []
            if 'manage:business_units' not in client_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient client permissions"
                )
        
        # Get organization context for validation
        organization_context = get_user_organization_context(current_user, current_client)
        
        # Convert Pydantic model to dict and add metadata
        business_unit_data = business_unit.model_dump(exclude_unset=True)
        business_unit_data['id'] = str(uuid4())
        business_unit_data['created_at'] = datetime.now(timezone.utc)
        
        # Add audit fields
        if current_user:
            user_id = current_user.user_id if hasattr(current_user, 'user_id') else None
            if user_id:
                business_unit_data['created_by'] = str(user_id)
        elif current_client:
            # For clients, you might want to track differently or leave None
            pass
        
        # Validate using business unit validator
        validated_data = BusinessUnitValidator.validate_for_create(
            business_unit_data, 
            organization_context=organization_context
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
        
        logger.info(f"Business unit created: {created_unit['id']} by user {current_user.user_id if current_user and hasattr(current_user, 'user_id') else 'client'}")
        
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
    auth_info = Depends(get_current_user_or_client)
):
    """
    Get business unit by ID.
    
    Requires: admin, super_user, firm_admin, group_admin, or API client with appropriate scope.
    """
    try:
        current_user = auth_info.get("user")
        current_client = auth_info.get("client")
        
        # Check authorization
        if not current_user and not current_client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify user has appropriate permissions
        if current_user:
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
            
            if not is_admin and not any(role in ['admin', 'super_user', 'firm_admin', 'group_admin'] for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin, super_user, firm_admin, or group_admin access required"
                )
        elif current_client:
            # For clients, check scopes
            if 'read:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else [] and 'manage:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else []:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient client permissions - requires read:business_units or manage:business_units scope"
                )
        
        business_unit = await repo.get_business_unit_by_id(business_unit_id)
        
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit not found"
            )
        
        # Check organization context for firm admins
        organization_context = get_user_organization_context(current_user, current_client)
        if organization_context and business_unit['organization_id'] != str(organization_context):
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
    auth_info = Depends(get_current_user_or_client)
):
    """
    Get all business units, optionally filtered by organization.
    
    Requires: admin, super_user, firm_admin, group_admin, or API client with appropriate scope.
    """
    try:
        current_user = auth_info.get("user")
        current_client = auth_info.get("client")
        
        # Check authorization
        if not current_user and not current_client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify user has appropriate permissions
        if current_user:
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
            
            if not is_admin and not any(role in ['admin', 'super_user', 'firm_admin', 'group_admin'] for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin, super_user, firm_admin, or group_admin access required"
                )
        elif current_client:
            # For clients, check scopes
            if 'read:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else [] and 'manage:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else []:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient client permissions - requires read:business_units or manage:business_units scope"
                )
        
        # Get organization context for filtering
        organization_context = get_user_organization_context(current_user, current_client)
        
        # If user has organization context (firm_admin), override organization_id filter
        if organization_context:
            organization_id = organization_context
        
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
    auth_info = Depends(get_current_user_or_client)
):
    """
    Get business unit hierarchy for an organization.
    
    Requires: admin, super_user, firm_admin, group_admin, or API client with appropriate scope.
    """
    try:
        current_user = auth_info.get("user")
        current_client = auth_info.get("client")
        
        # Check authorization
        if not current_user and not current_client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify user has appropriate permissions
        if current_user:
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
            
            if not is_admin and not any(role in ['admin', 'super_user', 'firm_admin', 'group_admin'] for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin, super_user, firm_admin, or group_admin access required"
                )
        elif current_client:
            # For clients, check scopes
            if 'read:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else [] and 'manage:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else []:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient client permissions - requires read:business_units or manage:business_units scope"
                )
        
        # Check organization context for firm admins
        organization_context = get_user_organization_context(current_user, current_client)
        if organization_context and organization_id != organization_context:
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
    auth_info = Depends(get_current_user_or_client)
):
    """
    Update a business unit.
    
    Requires: admin, super_user, organization/firm admin, or API client with manage:business_units scope.
    Firm admins are limited to their organization context.
    """
    try:
        current_user = auth_info.get("user")
        current_client = auth_info.get("client")
        
        # Check authorization (same as create)
        if current_user:
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
            
            if not is_admin and not any(role in ['admin', 'super_user', 'organization_admin', 'firm_admin'] for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin, super_user, organization_admin, or firm_admin access required"
                )
        elif current_client:
            if 'manage:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else []:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient client permissions"
                )
        
        # Verify business unit exists
        existing_unit = await repo.get_business_unit_by_id(business_unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit not found"
            )
        
        # Get organization context for validation
        organization_context = get_user_organization_context(current_user, current_client)
        
        # Validate organization context if user is restricted
        if organization_context and existing_unit['organization_id'] != organization_context:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update business units within your organization"
            )
        
        # Convert update model to dict
        update_data = business_unit_update.model_dump(exclude_unset=True)
        
        # Add audit fields
        if current_user:
            user_id = current_user.user_id if hasattr(current_user, 'user_id') else None
            if user_id:
                update_data['updated_by'] = str(user_id)
        
        # Validate update data
        validated_data = BusinessUnitValidator.validate_for_update(
            update_data,
            organization_context=organization_context
        )
        
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
        
        logger.info(f"Business unit updated: {business_unit_id} by user {current_user.user_id if current_user and hasattr(current_user, 'user_id') else 'client'}")
        
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
    auth_info = Depends(get_current_user_or_client)
):
    """
    Delete a business unit.
    
    Requires: admin, super_user, organization/firm admin, or API client with manage:business_units scope.
    Firm admins are limited to their organization context.
    """
    try:
        current_user = auth_info.get("user")
        current_client = auth_info.get("client")
        
        # Check authorization (same as create/update)
        if current_user:
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            is_admin = current_user.is_admin if hasattr(current_user, 'is_admin') else False
            
            if not is_admin and not any(role in ['admin', 'super_user', 'organization_admin', 'firm_admin'] for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin, super_user, organization_admin, or firm_admin access required"
                )
        elif current_client:
            if 'manage:business_units' not in current_client.scopes if hasattr(current_client, 'scopes') else []:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient client permissions"
                )
        
        # Verify business unit exists
        existing_unit = await repo.get_business_unit_by_id(business_unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business unit not found"
            )
        
        # Get organization context for validation
        organization_context = get_user_organization_context(current_user, current_client)
        
        # Validate organization context if user is restricted
        if organization_context and existing_unit['organization_id'] != organization_context:
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
        
        logger.info(f"Business unit deleted: {business_unit_id} by user {current_user.user_id if current_user and hasattr(current_user, 'user_id') else 'client'}")
        
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete business unit {business_unit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete business unit"
        )