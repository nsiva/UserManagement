from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from database import get_repository
from routers.auth import get_current_admin_user, get_current_client
from models import (
    UserInDB, 
    OrganizationFunctionalRoleCreate,
    OrganizationFunctionalRoleUpdate, 
    OrganizationFunctionalRoleInDB,
    BusinessUnitFunctionalRoleCreate,
    BusinessUnitFunctionalRoleUpdate,
    BusinessUnitFunctionalRoleInDB,
    AvailableFunctionalRolesResponse,
    AvailableFunctionalRole,
    BulkOrganizationFunctionalRoleAssignment,
    BulkBusinessUnitFunctionalRoleAssignment,
    FunctionalRoleHierarchyResponse,
    FunctionalRoleHierarchyItem
)

router = APIRouter(prefix="/functional-roles-hierarchy", tags=["functional-roles-hierarchy"])
logger = logging.getLogger("functional_roles_hierarchy")

# Helper functions
async def get_business_unit_enabled_functional_roles(repo, business_unit_id: UUID):
    """
    Get functional roles that are enabled for a specific business unit.
    This uses the vw_business_unit_available_roles view to get only enabled roles.
    """
    try:
        # Check if repository supports connection pool (PostgreSQL)
        if hasattr(repo, 'get_connection_pool'):
            pool = await repo.get_connection_pool()
            async with pool.acquire() as conn:
                # Query to get roles enabled ONLY at the business unit level (not just organization level)
                # We need to filter vw_business_unit_available_roles to only show enabled_at_bu = TRUE
                query = """
                SELECT DISTINCT
                    functional_role_id,
                    functional_role_name as name,
                    functional_role_label as label,
                    functional_role_description as description,
                    functional_role_category as category,
                    enabled_at_bu as is_enabled
                FROM vw_business_unit_available_roles 
                WHERE business_unit_id = $1 AND enabled_at_bu = TRUE
                ORDER BY functional_role_category, functional_role_name
                """
                
                rows = await conn.fetch(query, business_unit_id)
                
                enabled_roles = []
                for row in rows:
                    enabled_roles.append({
                        'functional_role_id': row['functional_role_id'],
                        'name': row['name'],
                        'label': row['label'],
                        'description': row['description'],
                        'category': row['category'],
                        'is_enabled': row['is_enabled']
                    })
                
                logger.info(f"Found {len(enabled_roles)} roles enabled at business unit level for business unit {business_unit_id}")
                return enabled_roles
        else:
            # Fallback for Supabase - use the supabase client
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Query the view through Supabase, filtering for business unit enabled roles only
            response = supabase.table("vw_business_unit_available_roles").select(
                "functional_role_id, functional_role_name, functional_role_label, "
                "functional_role_description, functional_role_category, enabled_at_bu"
            ).eq("business_unit_id", str(business_unit_id)).eq("enabled_at_bu", True).execute()
            
            enabled_roles = []
            for row in response.data:
                enabled_roles.append({
                    'functional_role_id': row['functional_role_id'],
                    'name': row['functional_role_name'],
                    'label': row['functional_role_label'],
                    'description': row['functional_role_description'],
                    'category': row['functional_role_category'],
                    'is_enabled': row['enabled_at_bu']
                })
            
            logger.info(f"Found {len(enabled_roles)} roles enabled at business unit level for business unit {business_unit_id}")
            return enabled_roles
        
    except Exception as e:
        logger.error(f"Error getting business unit enabled roles: {str(e)}")
        return []


# Placeholder implementations to prevent 500 errors while using PostgreSQL directly
# These need full implementation with proper SQL queries for production use

@router.post("/organizations/{organization_id}/roles", response_model=Dict[str, Any])
async def assign_functional_role_to_organization(
    organization_id: UUID,
    role_assignment: OrganizationFunctionalRoleCreate,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Assign a functional role to an organization (placeholder)"""
    try:
        repo = get_repository()
        
        # Verify organization exists
        org = await repo.get_organization_by_id(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        logger.warning(f"Organization functional role assignment not yet implemented - would assign role {role_assignment.functional_role_id} to organization {organization_id}")
        
        return {
            "message": "Functional role assignment completed (placeholder)",
            "organization_id": str(organization_id),
            "functional_role_id": str(role_assignment.functional_role_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning functional role to organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assigning role: {str(e)}")

@router.put("/organizations/{organization_id}/roles/{role_id}", response_model=Dict[str, Any])
async def update_organization_functional_role(
    organization_id: UUID,
    role_id: UUID,
    role_update: OrganizationFunctionalRoleUpdate,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Update a functional role assignment for an organization (placeholder)"""
    try:
        logger.warning(f"Organization functional role update not yet implemented - would update role {role_id} for organization {organization_id}")
        
        return {
            "message": "Functional role update completed (placeholder)",
            "organization_id": str(organization_id),
            "role_id": str(role_id)
        }
        
    except Exception as e:
        logger.error(f"Error updating organization functional role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")

@router.delete("/organizations/{organization_id}/roles/{role_id}")
async def remove_functional_role_from_organization(
    organization_id: UUID,
    role_id: UUID,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Remove a functional role from an organization (placeholder)"""
    try:
        logger.warning(f"Organization functional role removal not yet implemented - would remove role {role_id} from organization {organization_id}")
        
        return {
            "message": "Functional role removal completed (placeholder)"
        }
        
    except Exception as e:
        logger.error(f"Error removing functional role from organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error removing role: {str(e)}")

@router.post("/organizations/{organization_id}/roles/bulk", response_model=Dict[str, Any])
async def bulk_assign_functional_roles_to_organization(
    organization_id: UUID,
    bulk_assignment: BulkOrganizationFunctionalRoleAssignment,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Bulk assign functional roles to an organization"""
    try:
        repo = get_repository()
        
        # Verify organization exists using repository
        org = await repo.get_organization_by_id(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get functional role IDs by names using repository
        all_roles = await repo.get_functional_roles()
        role_map = {role.name: role.id for role in all_roles}
        
        missing_roles = [name for name in bulk_assignment.functional_role_names if name not in role_map]
        if missing_roles:
            raise HTTPException(status_code=404, detail=f"Functional roles not found: {missing_roles}")
        
        # Get the connection pool for direct SQL operations
        if hasattr(repo, 'get_connection_pool'):
            pool = await repo.get_connection_pool()
            async with pool.acquire() as conn:
                # Start a transaction
                async with conn.transaction():
                    # Clear existing assignments if replace_existing is True (default behavior)
                    if getattr(bulk_assignment, 'replace_existing', True):
                        await conn.execute(
                            "DELETE FROM aaa_organization_functional_roles WHERE organization_id = $1",
                            str(organization_id)
                        )
                    
                    # Insert new assignments
                    assigned_count = 0
                    for role_name in bulk_assignment.functional_role_names:
                        role_id = role_map[role_name]
                        try:
                            await conn.execute(
                                """INSERT INTO aaa_organization_functional_roles 
                                   (organization_id, functional_role_id, is_enabled, assigned_by, notes)
                                   VALUES ($1, $2, $3, $4, $5)
                                   ON CONFLICT (organization_id, functional_role_id) 
                                   DO UPDATE SET is_enabled = $3, assigned_by = $4, notes = $5, assigned_at = NOW()""",
                                str(organization_id), str(role_id), bulk_assignment.is_enabled, 
                                str(current_user.user_id), bulk_assignment.notes
                            )
                            assigned_count += 1
                        except Exception as e:
                            logger.error(f"Error assigning role {role_name} to organization: {e}")
                            continue
                    
                    logger.info(f"Successfully assigned {assigned_count} functional roles to organization {organization_id}")
                    
                    return {
                        "message": f"Bulk assignment completed for organization",
                        "assigned_roles": bulk_assignment.functional_role_names,
                        "total_assigned": assigned_count
                    }
        else:
            # Fallback for non-PostgreSQL repositories
            logger.warning(f"Repository doesn't support direct SQL - bulk assignment not implemented for organization {organization_id}")
            return {
                "message": f"Bulk assignment not supported by current database configuration",
                "assigned_roles": [],
                "total_assigned": 0
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk assigning functional roles to organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in bulk assignment: {str(e)}")

# Business Unit endpoints - similar placeholder implementations

@router.post("/business-units/{business_unit_id}/roles", response_model=Dict[str, Any])
async def assign_functional_role_to_business_unit(
    business_unit_id: UUID,
    role_assignment: BusinessUnitFunctionalRoleCreate,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Assign a functional role to a business unit (placeholder)"""
    try:
        repo = get_repository()
        
        # Verify business unit exists
        bu = await repo.get_business_unit_by_id(business_unit_id)
        if not bu:
            raise HTTPException(status_code=404, detail="Business unit not found")
        
        logger.warning(f"Business unit functional role assignment not yet implemented - would assign role {role_assignment.functional_role_id} to business unit {business_unit_id}")
        
        return {
            "message": "Functional role assignment completed (placeholder)",
            "business_unit_id": str(business_unit_id),
            "functional_role_id": str(role_assignment.functional_role_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning functional role to business unit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assigning role: {str(e)}")

@router.post("/business-units/{business_unit_id}/roles/bulk", response_model=Dict[str, Any])
async def bulk_assign_functional_roles_to_business_unit(
    business_unit_id: UUID,
    bulk_assignment: BulkBusinessUnitFunctionalRoleAssignment,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Bulk assign functional roles to a business unit (placeholder)"""
    try:
        repo = get_repository()
        
        # Verify business unit exists
        bu = await repo.get_business_unit_by_id(business_unit_id)
        if not bu:
            raise HTTPException(status_code=404, detail="Business unit not found")
        
        # Get functional role IDs by names using repository
        all_roles = await repo.get_functional_roles()
        role_map = {role.name: role.id for role in all_roles}
        
        missing_roles = [name for name in bulk_assignment.functional_role_names if name not in role_map]
        if missing_roles:
            raise HTTPException(status_code=404, detail=f"Functional roles not found: {missing_roles}")
        
        # Verify that the roles are enabled at the organization level first
        if hasattr(repo, 'get_connection_pool'):
            pool = await repo.get_connection_pool()
            async with pool.acquire() as conn:
                # Get business unit's organization
                org_result = await conn.fetchrow(
                    "SELECT organization_id FROM aaa_business_units WHERE id = $1",
                    str(business_unit_id)
                )
                if not org_result:
                    raise HTTPException(status_code=404, detail="Business unit not found")
                
                organization_id = org_result['organization_id']
                
                # Check which roles are enabled at organization level
                enabled_org_roles = await conn.fetch(
                    """SELECT functional_role_id, fr.name 
                       FROM aaa_organization_functional_roles ofr
                       JOIN aaa_functional_roles fr ON ofr.functional_role_id = fr.id
                       WHERE ofr.organization_id = $1 AND ofr.is_enabled = TRUE""",
                    str(organization_id)
                )
                
                enabled_role_names = {row['name'] for row in enabled_org_roles}
                
                # Check that all requested roles are enabled at organization level
                invalid_roles = [name for name in bulk_assignment.functional_role_names if name not in enabled_role_names]
                if invalid_roles:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"These roles must be enabled at organization level first: {invalid_roles}"
                    )
                
                # Start a transaction
                async with conn.transaction():
                    # For business units, we need to handle all org-enabled roles
                    # Selected roles get explicit enabled=true, unselected get explicit enabled=false
                    
                    selected_role_ids = [str(role_map[name]) for name in bulk_assignment.functional_role_names]
                    enabled_org_role_ids = [row['functional_role_id'] for row in enabled_org_roles]
                    
                    # Process all organization-enabled roles
                    assigned_count = 0
                    for role_row in enabled_org_roles:
                        role_id = str(role_row['functional_role_id'])
                        role_name = role_row['name']
                        
                        # Determine if this role should be enabled at BU level
                        is_enabled = role_id in selected_role_ids
                        
                        try:
                            await conn.execute(
                                """INSERT INTO aaa_business_unit_functional_roles 
                                   (business_unit_id, functional_role_id, is_enabled, assigned_by, notes)
                                   VALUES ($1, $2, $3, $4, $5)
                                   ON CONFLICT (business_unit_id, functional_role_id) 
                                   DO UPDATE SET is_enabled = $3, assigned_by = $4, notes = $5, assigned_at = NOW()""",
                                str(business_unit_id), role_id, is_enabled, 
                                str(current_user.user_id), bulk_assignment.notes
                            )
                            if is_enabled:
                                assigned_count += 1
                        except Exception as e:
                            logger.error(f"Error setting role {role_name} for business unit: {e}")
                            continue
                    
                    logger.info(f"Successfully assigned {assigned_count} functional roles to business unit {business_unit_id}")
                    
                    return {
                        "message": f"Bulk assignment completed for business unit",
                        "assigned_roles": bulk_assignment.functional_role_names,
                        "total_assigned": assigned_count
                    }
        else:
            # Fallback for non-PostgreSQL repositories
            logger.warning(f"Repository doesn't support direct SQL - bulk assignment not implemented for business unit {business_unit_id}")
            return {
                "message": f"Bulk assignment not supported by current database configuration",
                "assigned_roles": [],
                "total_assigned": 0
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk assigning functional roles to business unit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in bulk assignment: {str(e)}")

# Hierarchy and availability endpoints

@router.get("/organizations/{organization_id}/roles", response_model=List[AvailableFunctionalRole])
async def get_organization_functional_roles(
    organization_id: UUID,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Get functional roles assigned to an organization (placeholder)"""
    try:
        repo = get_repository()
        
        # Verify organization exists
        org = await repo.get_organization_by_id(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get organization functional roles from database
        if hasattr(repo, 'get_connection_pool'):
            pool = await repo.get_connection_pool()
            async with pool.acquire() as conn:
                # Query to get functional roles assigned to the organization
                rows = await conn.fetch(
                    """SELECT 
                        fr.id as functional_role_id,
                        fr.name,
                        fr.label,
                        fr.description,
                        fr.category,
                        fr.permissions,
                        ofr.is_enabled as is_currently_enabled,
                        TRUE as is_currently_assigned,
                        ofr.assigned_at,
                        NULL as expires_at
                    FROM aaa_organization_functional_roles ofr
                    JOIN aaa_functional_roles fr ON ofr.functional_role_id = fr.id
                    WHERE ofr.organization_id = $1 AND fr.is_active = TRUE
                    ORDER BY fr.category, fr.name""",
                    str(organization_id)
                )
                
                # Convert to AvailableFunctionalRole objects
                roles = []
                for row in rows:
                    role = AvailableFunctionalRole(
                        functional_role_id=str(row['functional_role_id']),
                        name=row['name'],
                        label=row['label'],
                        description=row['description'] or '',
                        category=row['category'] or 'general',
                        permissions=row['permissions'] or [],
                        is_currently_assigned=row['is_currently_assigned'],
                        is_currently_enabled=row['is_currently_enabled'],
                        assigned_at=row['assigned_at'],
                        expires_at=row['expires_at']
                    )
                    roles.append(role)
                
                logger.info(f"Retrieved {len(roles)} functional roles for organization {organization_id}")
                return roles
        else:
            logger.warning(f"Repository doesn't support direct SQL - returning empty list for organization {organization_id}")
            return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching organization functional roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching roles: {str(e)}")

@router.get("/business-units/{business_unit_id}/available-roles", response_model=AvailableFunctionalRolesResponse)
async def get_available_functional_roles_for_business_unit(
    business_unit_id: UUID,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Get available functional roles for a business unit (placeholder)"""
    try:
        repo = get_repository()
        
        # Verify business unit exists
        bu = await repo.get_business_unit_by_id(business_unit_id)
        if not bu:
            raise HTTPException(status_code=404, detail="Business unit not found")
        
        # Get roles available for this business unit (only roles enabled at organization level)
        if hasattr(repo, 'get_connection_pool'):
            pool = await repo.get_connection_pool()
            async with pool.acquire() as conn:
                # Query to get ALL functional roles enabled at organization level for this business unit
                # Show which ones are specifically enabled at business unit level
                rows = await conn.fetch(
                    """SELECT 
                        fr.id as functional_role_id,
                        fr.name,
                        fr.label,
                        fr.description,
                        fr.category,
                        fr.permissions,
                        TRUE as organization_enabled,
                        COALESCE(bufr.is_enabled, FALSE) as business_unit_enabled,
                        -- Only show as enabled if explicitly assigned and enabled at BU level
                        COALESCE(bufr.is_enabled, FALSE) as is_currently_enabled,
                        -- Only show as assigned if there's an explicit BU record AND it's enabled
                        COALESCE(bufr.is_enabled, FALSE) as is_currently_assigned,
                        bufr.assigned_at,
                        NULL as expires_at
                    FROM aaa_business_units bu
                    JOIN aaa_organization_functional_roles ofr ON bu.organization_id = ofr.organization_id 
                        AND ofr.is_enabled = TRUE
                    JOIN aaa_functional_roles fr ON ofr.functional_role_id = fr.id 
                        AND fr.is_active = TRUE
                    LEFT JOIN aaa_business_unit_functional_roles bufr ON bu.id = bufr.business_unit_id 
                        AND fr.id = bufr.functional_role_id
                    WHERE bu.id = $1
                    ORDER BY fr.category, fr.name""",
                    str(business_unit_id)
                )
                
                # Convert to AvailableFunctionalRole objects
                roles = []
                for row in rows:
                    role = AvailableFunctionalRole(
                        functional_role_id=str(row['functional_role_id']),
                        name=row['name'],
                        label=row['label'],
                        description=row['description'] or '',
                        category=row['category'] or 'general',
                        permissions=row['permissions'] or [],
                        is_currently_assigned=row['is_currently_assigned'],
                        is_currently_enabled=row['is_currently_enabled'],
                        assigned_at=row['assigned_at'],
                        expires_at=row['expires_at']
                    )
                    roles.append(role)
                
                logger.info(f"Retrieved {len(roles)} available functional roles for business unit {business_unit_id}")
                
                return AvailableFunctionalRolesResponse(
                    roles=roles,
                    total_count=len(roles),
                    context="business_unit"
                )
        else:
            logger.warning(f"Repository doesn't support direct SQL - returning empty list for business unit {business_unit_id}")
            return AvailableFunctionalRolesResponse(
                roles=[],
                total_count=0,
                context="business_unit"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available roles for business unit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching available roles: {str(e)}")

@router.get("/business-units/{business_unit_id}/roles", response_model=List[AvailableFunctionalRole])
async def get_business_unit_functional_roles(
    business_unit_id: UUID,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Get functional roles assigned to a business unit (placeholder)"""
    try:
        repo = get_repository()
        
        # Verify business unit exists
        bu = await repo.get_business_unit_by_id(business_unit_id)
        if not bu:
            raise HTTPException(status_code=404, detail="Business unit not found")
        
        logger.warning(f"Business unit functional roles retrieval not yet implemented - returning empty list for business unit {business_unit_id}")
        return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching business unit functional roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching roles: {str(e)}")

@router.get("/users/{user_id}/available-roles", response_model=AvailableFunctionalRolesResponse)
async def get_available_functional_roles_for_user(
    user_id: UUID,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Get available functional roles for a user based on their business unit"""
    try:
        repo = get_repository()
        
        # Verify user exists and get their organizational context
        user = await repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's organizational context (includes business_unit_id)
        user_context = await repo.get_user_organizational_context(user_id)
        if not user_context or not user_context.get('business_unit_id'):
            logger.warning(f"User {user_id} has no business unit assigned")
            return AvailableFunctionalRolesResponse(
                roles=[],
                total_count=0,
                context="user"
            )
        
        business_unit_id = user_context['business_unit_id']
        
        # Get functional roles that are enabled for the user's business unit
        # This should only return roles that are available at the business unit level
        business_unit_enabled_roles = await get_business_unit_enabled_functional_roles(repo, business_unit_id)
        
        if not business_unit_enabled_roles:
            logger.info(f"No functional roles enabled for business unit {business_unit_id}")
            return AvailableFunctionalRolesResponse(
                roles=[],
                total_count=0,
                context="user"
            )
        
        # Get user's currently assigned functional roles
        user_assigned_roles = await repo.get_user_functional_roles(user_id)
        assigned_role_ids = {role.id for role in user_assigned_roles}
        
        # Only show roles that are enabled at the business unit level
        roles = []
        for role in business_unit_enabled_roles:
            is_assigned = role['functional_role_id'] in assigned_role_ids
            roles.append(AvailableFunctionalRole(
                functional_role_id=role['functional_role_id'],
                name=role['name'],
                label=role['label'],
                description=role['description'],
                category=role['category'],
                is_currently_enabled=role.get('is_enabled', True),  # True if enabled at BU level
                is_currently_assigned=is_assigned,
                business_unit_name=user_context.get('business_unit_name', 'Unknown'),
                assigned_at=None,
                expires_at=None
            ))
        
        logger.info(f"Found {len(roles)} functional roles for user {user_id} in business unit {business_unit_id}")
        
        return AvailableFunctionalRolesResponse(
            roles=roles,
            total_count=len(roles),
            context="user"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available roles for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching available roles: {str(e)}")

@router.get("/hierarchy", response_model=FunctionalRoleHierarchyResponse)
async def get_functional_role_hierarchy(
    organization_id: Optional[UUID] = None,
    business_unit_id: Optional[UUID] = None,
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Get functional role hierarchy overview (placeholder)"""
    try:
        logger.warning("Functional role hierarchy not yet implemented - returning empty hierarchy")
        
        return FunctionalRoleHierarchyResponse(
            hierarchy=[],
            total_organizations=0,
            total_business_units=0,
            total_functional_roles=0
        )
        
    except Exception as e:
        logger.error(f"Error fetching functional role hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching hierarchy: {str(e)}")