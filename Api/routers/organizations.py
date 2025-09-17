from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
import logging
from pydantic import ValidationError

from database import get_repository
from organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from models import TokenData
from routers.auth import get_current_user
from validators.organization_validator import OrganizationValidator, OrganizationValidationError
from constants import (
    ADMIN, SUPER_USER, ORGANIZATION_ADMIN, BUSINESS_UNIT_ADMIN,
    ADMIN_ROLES, has_admin_access, has_organization_admin_access, has_business_unit_admin_access
)

organizations_router = APIRouter(prefix="/organizations", tags=["organizations"])
logger = logging.getLogger("organizations")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)


async def get_current_admin_or_superuser(current_user: TokenData = Depends(get_current_user)):
    """Dependency to ensure current user has admin or superuser role."""
    try:
        if 'super_user' not in current_user.roles and 'admin' not in current_user.roles:
            logger.warning(f"User {current_user.email} does not have admin or super_user permissions.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or super user access required")
        logger.info(f"Admin/Super user authenticated: {current_user.email}")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking admin/super user permissions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@organizations_router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    current_admin_user: TokenData = Depends(get_current_admin_or_superuser)
):
    """Create a new organization. Accessible to admin and super users."""
    try:
        repo = get_repository()
        
        # Create organization data dict
        organization_dict = organization_data.dict()
        
        # Additional custom validation using our validator
        try:
            validated_data = OrganizationValidator.validate_for_create(organization_dict)
        except OrganizationValidationError as validation_error:
            logger.warning(f"Organization validation failed: {validation_error.errors}")
            # Format validation errors for user-friendly response
            error_messages = []
            for field, errors in validation_error.errors.items():
                error_messages.extend([f"{field}: {error}" for error in errors])
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail={"message": "Validation failed", "errors": validation_error.errors}
            )
        
        # Use validated data for creation
        created_organization = await repo.create_organization(validated_data)
        if not created_organization:
            logger.error(f"Failed to create organization: {organization_data.company_name}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create organization")
        
        logger.info(f"Organization created successfully: {created_organization.get('company_name')} by user {current_admin_user.email}")
        return OrganizationResponse(**created_organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@organizations_router.get("/", response_model=List[OrganizationResponse])
async def get_all_organizations(current_user: TokenData = Depends(get_current_user)):
    """Get organizations with role-based filtering:
    - admin/super_user: See all organizations
    - firm_admin: See only their organization
    - group_admin: See only their organization
    - Other roles: Access denied
    """
    try:
        repo = get_repository()
        current_user_roles = current_user.roles
        
        # Check if user has appropriate role
        if not (has_admin_access(current_user_roles) or has_organization_admin_access(current_user_roles) or has_business_unit_admin_access(current_user_roles)):
            logger.warning(f"User {current_user.email} with roles {current_user_roles} attempted to access organizations")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Admin, super_user, {ORGANIZATION_ADMIN}, or {BUSINESS_UNIT_ADMIN} access required"
            )
        
        # Determine filtering based on user role
        if has_admin_access(current_user_roles):
            # Admin and super_user see all organizations
            organizations = await repo.get_all_organizations()
            logger.info(f"Admin/Super user {current_user.email} accessing all organizations")
        else:
            # Get current user's organizational context for filtering
            user_context = await repo.get_user_organizational_context(current_user.user_id)
            
            if not user_context:
                logger.warning(f"No organizational context found for user {current_user.email}")
                return []
            
            if has_organization_admin_access(current_user_roles):
                # Firm admin sees only their organization
                user_org_id = user_context['organization_id']
                organization = await repo.get_organization_by_id(user_org_id)
                organizations = [organization] if organization else []
                logger.info(f"Firm admin {current_user.email} accessing their organization {user_context['organization_name']}")
            elif has_business_unit_admin_access(current_user_roles):
                # Business unit admin sees only their organization
                user_org_id = user_context['organization_id']
                organization = await repo.get_organization_by_id(user_org_id)
                organizations = [organization] if organization else []
                logger.info(f"Business unit admin {current_user.email} accessing their organization {user_context['organization_name']}")
            else:
                logger.warning(f"User {current_user.email} with roles {current_user_roles} has no organization access permissions")
                return []
        
        # Add counts to each organization
        organizations_with_counts = []
        for organization in organizations:
            try:
                business_units_count = await repo.count_business_units_by_organization(organization['id'])
                users_count = await repo.count_users_by_organization(organization['id'])
                
                org_data = {**organization}
                org_data['business_units_count'] = business_units_count
                org_data['users_count'] = users_count
                
                organizations_with_counts.append(OrganizationResponse(**org_data))
                
            except Exception as e:
                logger.error(f"Error getting counts for organization {organization['id']}: {e}")
                # Include organization without counts if count fetch fails
                org_data = {**organization}
                org_data['business_units_count'] = 0
                org_data['users_count'] = 0
                organizations_with_counts.append(OrganizationResponse(**org_data))
        
        logger.info(f"Retrieved {len(organizations_with_counts)} organizations with counts for user {current_user.email}")
        return organizations_with_counts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving organizations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@organizations_router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    current_user: TokenData = Depends(get_current_user)
):
    """Get a specific organization by ID. Accessible to any authenticated user."""
    try:
        repo = get_repository()
        organization = await repo.get_organization_by_id(organization_id)
        
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
        logger.info(f"Retrieved organization {organization_id} for user {current_user.email}")
        return OrganizationResponse(**organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving organization {organization_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")




@organizations_router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    organization_data: OrganizationUpdate,
    current_admin_user: TokenData = Depends(get_current_admin_or_superuser)
):
    """Update an organization. Accessible to admin and super users."""
    try:
        repo = get_repository()
        
        # Check if organization exists
        existing_organization = await repo.get_organization_by_id(organization_id)
        if not existing_organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
        # Only include non-None values in update
        update_dict = {k: v for k, v in organization_data.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields provided for update")
        
        # Additional custom validation using our validator
        try:
            validated_data = OrganizationValidator.validate_for_update(update_dict)
        except OrganizationValidationError as validation_error:
            logger.warning(f"Organization update validation failed: {validation_error.errors}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail={"message": "Validation failed", "errors": validation_error.errors}
            )
        
        success = await repo.update_organization(organization_id, validated_data)
        if not success:
            logger.error(f"Failed to update organization {organization_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update organization")
        
        # Return updated organization
        updated_organization = await repo.get_organization_by_id(organization_id)
        logger.info(f"Organization {organization_id} updated successfully by user {current_admin_user.email}")
        return OrganizationResponse(**updated_organization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization {organization_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@organizations_router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    current_admin_user: TokenData = Depends(get_current_admin_or_superuser)
):
    """Delete an organization. Accessible to admin and super users."""
    try:
        repo = get_repository()
        
        # Check if organization exists
        existing_organization = await repo.get_organization_by_id(organization_id)
        if not existing_organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
        success = await repo.delete_organization(organization_id)
        if not success:
            logger.error(f"Failed to delete organization {organization_id}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete organization")
        
        logger.info(f"Organization {organization_id} deleted successfully by user {current_admin_user.email}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization {organization_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")