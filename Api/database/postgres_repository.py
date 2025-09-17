from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
import logging
import asyncpg
import json

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PostgresRepository(BaseRepository):
    """PostgreSQL implementation of the repository pattern."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool: Optional[asyncpg.Pool] = None
    
    async def get_connection_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.connection_string)
        return self._pool
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                # Convert UUID to string if present
                if 'id' in user_data and isinstance(user_data['id'], UUID):
                    user_data['id'] = str(user_data['id'])
                
                columns = ', '.join(user_data.keys())
                placeholders = ', '.join(f'${i+1}' for i in range(len(user_data)))
                values = list(user_data.values())
                
                query = f"""
                    INSERT INTO aaa_profiles ({columns})
                    VALUES ({placeholders})
                    RETURNING *
                """
                
                result = await conn.fetchrow(query, *values)
                return dict(result) if result else {}
                
            except Exception as e:
                logger.error(f"Failed to create user: {e}")
                raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT * FROM aaa_profiles WHERE email = $1 LIMIT 1"
                result = await conn.fetchrow(query, email)
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get user by email {email}: {e}")
                return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID with complete business unit and organization information."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT 
                        user_id as id,
                        email,
                        first_name,
                        middle_name,
                        last_name,
                        is_admin,
                        mfa_secret,
                        business_unit_id,
                        business_unit_name,
                        business_unit_code,
                        business_unit_location,
                        organization_id,
                        organization_name,
                        organization_city,
                        organization_country,
                        business_unit_manager_name,
                        parent_business_unit_name
                    FROM vw_user_details 
                    WHERE user_id = $1 
                    LIMIT 1
                """
                result = await conn.fetchrow(query, str(user_id))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get user by ID from view: {e}")
                # Fallback to original query if view doesn't exist
                logger.info("Falling back to original query for get_user_by_id")
                query_fallback = """
                    SELECT p.id, p.email, p.first_name, p.middle_name, p.last_name, 
                           p.is_admin, p.mfa_secret, p.mfa_method,
                           ub.business_unit_id, bu.name as business_unit_name,
                           o.company_name as organization_name, bu.organization_id,
                           bu.code as business_unit_code, bu.location as business_unit_location,
                           o.city_town as organization_city, o.country as organization_country,
                           CONCAT(mgr.first_name, ' ', mgr.last_name) as business_unit_manager_name,
                           pbu.name as parent_business_unit_name
                    FROM aaa_profiles p
                    LEFT JOIN aaa_user_business_units ub ON p.id = ub.user_id AND ub.is_active = TRUE
                    LEFT JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_profiles mgr ON bu.manager_id = mgr.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    WHERE p.id = $1 
                    LIMIT 1
                """
                result = await conn.fetchrow(query_fallback, str(user_id))
                return dict(result) if result else None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all user profiles with complete business unit and organization information."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT 
                        user_id as id,
                        email,
                        first_name,
                        middle_name,
                        last_name,
                        is_admin,
                        mfa_secret,
                        mfa_method,
                        business_unit_id,
                        business_unit_name,
                        business_unit_code,
                        business_unit_location,
                        organization_id,
                        organization_name,
                        organization_city,
                        organization_country,
                        business_unit_manager_name,
                        parent_business_unit_name
                    FROM vw_user_details
                    ORDER BY email
                """
                results = await conn.fetch(query)
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get all users from view: {e}")
                # Fallback to original query if view doesn't exist
                logger.info("Falling back to original query")
                query_fallback = """
                    SELECT p.id, p.email, p.first_name, p.middle_name, p.last_name, 
                           p.is_admin, p.mfa_secret, p.mfa_method,
                           ub.business_unit_id, bu.name as business_unit_name,
                           o.company_name as organization_name, bu.organization_id,
                           bu.code as business_unit_code, bu.location as business_unit_location,
                           o.city_town as organization_city, o.country as organization_country,
                           CONCAT(mgr.first_name, ' ', mgr.last_name) as business_unit_manager_name,
                           pbu.name as parent_business_unit_name
                    FROM aaa_profiles p
                    LEFT JOIN aaa_user_business_units ub ON p.id = ub.user_id AND ub.is_active = TRUE
                    LEFT JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_profiles mgr ON bu.manager_id = mgr.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    ORDER BY p.email
                """
                results = await conn.fetch(query_fallback)
                return [dict(row) for row in results]
    
    async def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update user profile. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                update_data['updated_at'] = datetime.now(timezone.utc)
                
                set_clause = ', '.join(f'{key} = ${i+2}' for i, key in enumerate(update_data.keys()))
                values = [str(user_id)] + list(update_data.values())
                
                query = f"UPDATE aaa_profiles SET {set_clause} WHERE id = $1"
                result = await conn.execute(query, *values)
                
                # Check if any rows were affected
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to update user {user_id}: {e}")
                return False
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user profile. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                try:
                    # First delete user_roles entries
                    await conn.execute("DELETE FROM aaa_user_roles WHERE user_id = $1", str(user_id))
                    
                    # Delete user-business unit relationships
                    await conn.execute("DELETE FROM aaa_user_business_units WHERE user_id = $1", str(user_id))
                    
                    # Delete the user profile
                    result = await conn.execute("DELETE FROM aaa_profiles WHERE id = $1", str(user_id))
                    
                    return "DELETE 1" in result
                except Exception as e:
                    logger.error(f"Failed to delete user {user_id}: {e}")
                    return False
    
    async def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                columns = ', '.join(role_data.keys())
                placeholders = ', '.join(f'${i+1}' for i in range(len(role_data)))
                values = list(role_data.values())
                
                query = f"""
                    INSERT INTO aaa_roles ({columns})
                    VALUES ({placeholders})
                    RETURNING *
                """
                
                result = await conn.fetchrow(query, *values)
                return dict(result) if result else {}
            except Exception as e:
                logger.error(f"Failed to create role: {e}")
                raise
    
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT * FROM aaa_roles"
                results = await conn.fetch(query)
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get all roles: {e}")
                return []
    
    async def update_role(self, role_id: UUID, role_data: Dict[str, Any]) -> bool:
        """Update role. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                set_clause = ', '.join(f'{key} = ${i+2}' for i, key in enumerate(role_data.keys()))
                values = [str(role_id)] + list(role_data.values())
                
                query = f"UPDATE aaa_roles SET {set_clause} WHERE id = $1"
                result = await conn.execute(query, *values)
                
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to update role {role_id}: {e}")
                return False
    
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                result = await conn.execute("DELETE FROM aaa_roles WHERE id = $1", str(role_id))
                return "DELETE 1" in result
            except Exception as e:
                logger.error(f"Failed to delete role {role_id}: {e}")
                return False
    
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """Get role names for a user."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT r.name FROM aaa_user_roles ur
                    JOIN aaa_roles r ON ur.role_id = r.id
                    WHERE ur.user_id = $1
                """
                results = await conn.fetch(query, str(user_id))
                return [row['name'] for row in results]
            except Exception as e:
                logger.error(f"Failed to get user roles for {user_id}: {e}")
                return []
    
    async def assign_user_roles(self, user_id: UUID, role_names: List[str]) -> bool:
        """Assign roles to a user. Replaces existing roles."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                try:
                    if not role_names:
                        # Delete all existing roles for the user
                        await conn.execute("DELETE FROM aaa_user_roles WHERE user_id = $1", str(user_id))
                        return True
                    
                    # Get role IDs for the given role names
                    placeholders = ', '.join(f'${i+1}' for i in range(len(role_names)))
                    query = f"SELECT id, name FROM aaa_roles WHERE name IN ({placeholders})"
                    roles = await conn.fetch(query, *role_names)
                    
                    if len(roles) != len(role_names):
                        found_roles = {role['name'] for role in roles}
                        missing_roles = set(role_names) - found_roles
                        raise Exception(f"Role(s) not found: {missing_roles}")
                    
                    # Delete existing roles for the user
                    await conn.execute("DELETE FROM aaa_user_roles WHERE user_id = $1", str(user_id))
                    
                    # Insert new role assignments
                    for role in roles:
                        await conn.execute(
                            "INSERT INTO aaa_user_roles (user_id, role_id) VALUES ($1, $2)",
                            str(user_id), str(role['id'])
                        )
                    
                    return True
                except Exception as e:
                    logger.error(f"Failed to assign roles to user {user_id}: {e}")
                    return False
    
    async def delete_user_roles(self, user_id: UUID) -> bool:
        """Delete all roles for a user."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute("DELETE FROM aaa_user_roles WHERE user_id = $1", str(user_id))
                return True
            except Exception as e:
                logger.error(f"Failed to delete user roles for {user_id}: {e}")
                return False
    
    async def update_mfa_secret(self, user_id: UUID, secret: Optional[str]) -> bool:
        """Update MFA secret for a user. None to disable MFA."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    UPDATE aaa_profiles 
                    SET mfa_secret = $2, updated_at = $3 
                    WHERE id = $1
                """
                result = await conn.execute(query, str(user_id), secret, datetime.now(timezone.utc))
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to update MFA secret for user {user_id}: {e}")
                return False
    
    async def create_email_otp(self, otp_data: Dict[str, Any]) -> bool:
        """Create an email OTP record."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                # First, cleanup any existing unused OTPs for this user/purpose
                await self.cleanup_user_email_otps(otp_data['user_id'], otp_data['purpose'])
                
                columns = ', '.join(otp_data.keys())
                placeholders = ', '.join(f'${i+1}' for i in range(len(otp_data)))
                values = list(otp_data.values())
                
                query = f"""
                    INSERT INTO aaa_email_otps ({columns})
                    VALUES ({placeholders})
                """
                
                result = await conn.execute(query, *values)
                return "INSERT" in result
            except Exception as e:
                logger.error(f"Failed to create email OTP: {e}")
                return False
    
    async def get_email_otp(self, user_id: UUID, otp: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get email OTP by user_id, otp and purpose."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM aaa_email_otps 
                    WHERE user_id = $1 AND otp = $2 AND purpose = $3 
                    AND used = FALSE AND expires_at > $4
                    LIMIT 1
                """
                result = await conn.fetchrow(query, str(user_id), otp, purpose, datetime.now(timezone.utc))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get email OTP for user {user_id}: {e}")
                return None
    
    async def mark_email_otp_used(self, otp_id: UUID) -> bool:
        """Mark an email OTP as used."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    UPDATE aaa_email_otps 
                    SET used = TRUE, updated_at = $2 
                    WHERE id = $1
                """
                result = await conn.execute(query, str(otp_id), datetime.now(timezone.utc))
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to mark email OTP as used {otp_id}: {e}")
                return False
    
    async def cleanup_expired_email_otps(self) -> int:
        """Remove expired email OTPs. Returns number of deleted records."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    DELETE FROM aaa_email_otps 
                    WHERE expires_at < $1
                """
                result = await conn.execute(query, datetime.now(timezone.utc))
                # Extract the number of deleted rows from the result
                if result.startswith("DELETE "):
                    return int(result.split()[1])
                return 0
            except Exception as e:
                logger.error(f"Failed to cleanup expired email OTPs: {e}")
                return 0
    
    async def cleanup_user_email_otps(self, user_id: UUID, purpose: str) -> bool:
        """Remove existing unused OTPs for a user/purpose combination."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    DELETE FROM aaa_email_otps 
                    WHERE user_id = $1 AND purpose = $2 AND used = FALSE
                """
                await conn.execute(query, str(user_id), purpose)
                return True
            except Exception as e:
                logger.error(f"Failed to cleanup user email OTPs for {user_id}: {e}")
                return False
    
    async def update_user_mfa_method(self, user_id: UUID, mfa_method: str) -> bool:
        """Update user's MFA method (totp or email)."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    UPDATE aaa_profiles 
                    SET mfa_method = $2, updated_at = $3 
                    WHERE id = $1
                """
                result = await conn.execute(query, str(user_id), mfa_method, datetime.now(timezone.utc))
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to update MFA method for user {user_id}: {e}")
                return False
    
    async def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client by client_id."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT * FROM aaa_clients WHERE client_id = $1 LIMIT 1"
                result = await conn.fetchrow(query, client_id)
                if result:
                    client_data = dict(result)
                    # Parse scopes JSON if it's stored as text
                    if 'scopes' in client_data and isinstance(client_data['scopes'], str):
                        try:
                            client_data['scopes'] = json.loads(client_data['scopes'])
                        except json.JSONDecodeError:
                            client_data['scopes'] = []
                    return client_data
                return None
            except Exception as e:
                logger.error(f"Failed to get client by ID {client_id}: {e}")
                return None
    
    async def create_reset_token(self, token_data: Dict[str, Any]) -> bool:
        """Create a password reset token."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                columns = ', '.join(token_data.keys())
                placeholders = ', '.join(f'${i+1}' for i in range(len(token_data)))
                values = list(token_data.values())
                
                query = f"INSERT INTO aaa_password_reset_tokens ({columns}) VALUES ({placeholders})"
                await conn.execute(query, *values)
                return True
            except Exception as e:
                logger.error(f"Failed to create reset token: {e}")
                return False
    
    async def validate_reset_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Validate reset token. Returns (is_valid, user_email)."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT t.user_id, t.expires_at, t.used, p.email
                    FROM aaa_password_reset_tokens t
                    JOIN aaa_profiles p ON t.user_id = p.id
                    WHERE t.token = $1 AND t.used = false
                    LIMIT 1
                """
                result = await conn.fetchrow(query, token)
                
                if not result:
                    return False, None
                
                # Check if token has expired
                expires_at = result['expires_at']
                if datetime.now(timezone.utc) > expires_at:
                    return False, None
                
                return True, result['email']
                
            except Exception as e:
                logger.error(f"Failed to validate reset token: {e}")
                return False, None
    
    async def mark_token_used(self, token: str) -> bool:
        """Mark reset token as used."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "UPDATE aaa_password_reset_tokens SET used = true WHERE token = $1"
                result = await conn.execute(query, token)
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to mark token as used: {e}")
                return False
    
    # Organization Management
    async def create_organization(self, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new organization."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                columns = ', '.join(organization_data.keys())
                placeholders = ', '.join(f'${i+1}' for i in range(len(organization_data)))
                values = list(organization_data.values())
                
                query = f"""
                    INSERT INTO aaa_organizations ({columns})
                    VALUES ({placeholders})
                    RETURNING *
                """
                
                result = await conn.fetchrow(query, *values)
                return dict(result) if result else {}
                
            except Exception as e:
                logger.error(f"Failed to create organization: {e}")
                raise
    
    async def get_organization_by_id(self, organization_id: UUID) -> Optional[Dict[str, Any]]:
        """Get organization by ID."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT * FROM aaa_organizations WHERE id = $1 LIMIT 1"
                result = await conn.fetchrow(query, str(organization_id))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get organization by ID {organization_id}: {e}")
                return None
    
    
    async def get_all_organizations(self) -> List[Dict[str, Any]]:
        """Get all organizations."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT * FROM aaa_organizations ORDER BY company_name"
                results = await conn.fetch(query)
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get all organizations: {e}")
                return []
    
    async def update_organization(self, organization_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update organization. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                update_data['updated_at'] = datetime.now(timezone.utc)
                
                set_clauses = ', '.join(f"{key} = ${i+2}" for i, key in enumerate(update_data.keys()))
                values = [str(organization_id)] + list(update_data.values())
                
                query = f"UPDATE aaa_organizations SET {set_clauses} WHERE id = $1"
                result = await conn.execute(query, *values)
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to update organization {organization_id}: {e}")
                return False
    
    async def delete_organization(self, organization_id: UUID) -> bool:
        """Delete organization. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "DELETE FROM aaa_organizations WHERE id = $1"
                result = await conn.execute(query, str(organization_id))
                return "DELETE 1" in result
            except Exception as e:
                logger.error(f"Failed to delete organization {organization_id}: {e}")
                return False
    
    # Business Unit Management
    async def create_business_unit(self, business_unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business unit."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                columns = ', '.join(business_unit_data.keys())
                placeholders = ', '.join(f'${i+1}' for i in range(len(business_unit_data)))
                values = list(business_unit_data.values())
                
                query = f"""
                    INSERT INTO aaa_business_units ({columns})
                    VALUES ({placeholders})
                    RETURNING *
                """
                
                result = await conn.fetchrow(query, *values)
                return dict(result) if result else {}
                
            except Exception as e:
                logger.error(f"Failed to create business unit: {e}")
                raise
    
    async def get_business_unit_by_id(self, business_unit_id: UUID) -> Optional[Dict[str, Any]]:
        """Get business unit by ID."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT bu.*, 
                           o.company_name as organization_name,
                           pbu.name as parent_name,
                           CONCAT(p.first_name, ' ', p.last_name) as manager_name
                    FROM aaa_business_units bu
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
                    WHERE bu.id = $1 
                    LIMIT 1
                """
                result = await conn.fetchrow(query, str(business_unit_id))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get business unit by ID {business_unit_id}: {e}")
                return None
    
    async def get_business_units_by_organization(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get all business units for an organization."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT bu.*, 
                           o.company_name as organization_name,
                           pbu.name as parent_name,
                           CONCAT(p.first_name, ' ', p.last_name) as manager_name
                    FROM aaa_business_units bu
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
                    WHERE bu.organization_id = $1
                    ORDER BY bu.name
                """
                results = await conn.fetch(query, str(organization_id))
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get business units for organization {organization_id}: {e}")
                return []
    
    async def get_all_business_units(self) -> List[Dict[str, Any]]:
        """Get all business units."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT bu.*, 
                           o.company_name as organization_name,
                           pbu.name as parent_name,
                           CONCAT(p.first_name, ' ', p.last_name) as manager_name
                    FROM aaa_business_units bu
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
                    ORDER BY o.company_name, bu.name
                """
                results = await conn.fetch(query)
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get all business units: {e}")
                return []
    
    async def update_business_unit(self, business_unit_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update business unit. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                update_data['updated_at'] = datetime.now(timezone.utc)
                
                # Debug logging for is_active field
                if 'is_active' in update_data:
                    logger.info(f"Updating business unit {business_unit_id} - is_active value: {update_data['is_active']} (type: {type(update_data['is_active'])})")
                
                set_clauses = ', '.join(f"{key} = ${i+2}" for i, key in enumerate(update_data.keys()))
                values = [str(business_unit_id)] + list(update_data.values())
                
                # Debug logging for SQL values
                logger.info(f"SQL Query: UPDATE aaa_business_units SET {set_clauses} WHERE id = $1")
                logger.info(f"SQL Values: {values}")
                
                query = f"UPDATE aaa_business_units SET {set_clauses} WHERE id = $1"
                result = await conn.execute(query, *values)
                return "UPDATE 1" in result
            except Exception as e:
                logger.error(f"Failed to update business unit {business_unit_id}: {e}")
                return False
    
    async def delete_business_unit(self, business_unit_id: UUID) -> bool:
        """Delete business unit. Returns True if successful."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "DELETE FROM aaa_business_units WHERE id = $1"
                result = await conn.execute(query, str(business_unit_id))
                return "DELETE 1" in result
            except Exception as e:
                logger.error(f"Failed to delete business unit {business_unit_id}: {e}")
                return False
    
    async def get_business_unit_hierarchy(self, organization_id: UUID, parent_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get business unit hierarchy for an organization."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                # Base query for hierarchy starting from parent_id
                if parent_id:
                    query = """
                        WITH RECURSIVE unit_hierarchy AS (
                            SELECT bu.*, 
                                   o.company_name as organization_name,
                                   pbu.name as parent_name,
                                   CONCAT(p.first_name, ' ', p.last_name) as manager_name,
                                   0 as level
                            FROM aaa_business_units bu
                            LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                            LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                            LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
                            WHERE bu.id = $2 AND bu.organization_id = $1
                            
                            UNION ALL
                            
                            SELECT child.*, 
                                   o.company_name as organization_name,
                                   pbu.name as parent_name,
                                   CONCAT(p.first_name, ' ', p.last_name) as manager_name,
                                   uh.level + 1
                            FROM aaa_business_units child
                            LEFT JOIN aaa_organizations o ON child.organization_id = o.id
                            LEFT JOIN aaa_business_units pbu ON child.parent_unit_id = pbu.id
                            LEFT JOIN aaa_profiles p ON child.manager_id = p.id
                            JOIN unit_hierarchy uh ON child.parent_unit_id = uh.id
                            WHERE child.organization_id = $1
                        )
                        SELECT * FROM unit_hierarchy ORDER BY level, name
                    """
                    results = await conn.fetch(query, str(organization_id), str(parent_id))
                else:
                    # Get all units for organization ordered hierarchically
                    query = """
                        WITH RECURSIVE unit_hierarchy AS (
                            -- Root nodes (no parent)
                            SELECT bu.*, 
                                   o.company_name as organization_name,
                                   NULL as parent_name,
                                   CONCAT(p.first_name, ' ', p.last_name) as manager_name,
                                   0 as level,
                                   ARRAY[bu.name] as path
                            FROM aaa_business_units bu
                            LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                            LEFT JOIN aaa_profiles p ON bu.manager_id = p.id
                            WHERE bu.parent_unit_id IS NULL AND bu.organization_id = $1
                            
                            UNION ALL
                            
                            -- Child nodes
                            SELECT child.*, 
                                   o.company_name as organization_name,
                                   parent.name as parent_name,
                                   CONCAT(p.first_name, ' ', p.last_name) as manager_name,
                                   uh.level + 1,
                                   uh.path || child.name
                            FROM aaa_business_units child
                            LEFT JOIN aaa_organizations o ON child.organization_id = o.id
                            LEFT JOIN aaa_business_units parent ON child.parent_unit_id = parent.id
                            LEFT JOIN aaa_profiles p ON child.manager_id = p.id
                            JOIN unit_hierarchy uh ON child.parent_unit_id = uh.id
                            WHERE child.organization_id = $1
                        )
                        SELECT * FROM unit_hierarchy ORDER BY path
                    """
                    results = await conn.fetch(query, str(organization_id))
                    
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get business unit hierarchy for organization {organization_id}: {e}")
                return []
    
    async def validate_business_unit_hierarchy(self, business_unit_id: UUID, parent_unit_id: UUID) -> bool:
        """Validate that parent-child relationship doesn't create circular dependency."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                # Check if parent_unit_id is a descendant of business_unit_id
                query = """
                    WITH RECURSIVE descendants AS (
                        SELECT id, parent_unit_id 
                        FROM aaa_business_units 
                        WHERE id = $1
                        
                        UNION ALL
                        
                        SELECT child.id, child.parent_unit_id
                        FROM aaa_business_units child
                        JOIN descendants d ON child.parent_unit_id = d.id
                    )
                    SELECT EXISTS(SELECT 1 FROM descendants WHERE id = $2) as would_create_cycle
                """
                
                result = await conn.fetchrow(query, str(business_unit_id), str(parent_unit_id))
                # Return False if it would create a cycle, True if valid
                return not result['would_create_cycle'] if result else True
                
            except Exception as e:
                logger.error(f"Failed to validate business unit hierarchy: {e}")
                return False
    
    async def count_business_units_by_organization(self, organization_id: UUID) -> int:
        """Count business units in an organization."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT COUNT(*) FROM aaa_business_units WHERE organization_id = $1"
                result = await conn.fetchval(query, str(organization_id))
                return result or 0
            except Exception as e:
                logger.error(f"Failed to count business units for organization {organization_id}: {e}")
                return 0
    
    async def count_users_by_organization(self, organization_id: UUID) -> int:
        """Count users in an organization."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT COUNT(DISTINCT ub.user_id) 
                    FROM aaa_user_business_units ub
                    JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    WHERE bu.organization_id = $1 AND ub.is_active = TRUE
                """
                result = await conn.fetchval(query, str(organization_id))
                return result or 0
            except Exception as e:
                logger.error(f"Failed to count users for organization {organization_id}: {e}")
                return 0
    
    async def count_users_by_business_unit(self, business_unit_id: UUID) -> int:
        """Count users in a business unit."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT COUNT(*) 
                    FROM aaa_user_business_units 
                    WHERE business_unit_id = $1 AND is_active = TRUE
                """
                result = await conn.fetchval(query, str(business_unit_id))
                return result or 0
            except Exception as e:
                logger.error(f"Failed to count users for business unit {business_unit_id}: {e}")
                return 0
    
    # User-Business Unit Relationship Management
    async def validate_business_unit_exists(self, business_unit_id: UUID) -> bool:
        """Validate that a business unit exists and is active."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "SELECT EXISTS(SELECT 1 FROM aaa_business_units WHERE id = $1 AND is_active = TRUE)"
                result = await conn.fetchrow(query, str(business_unit_id))
                return result['exists'] if result else False
            except Exception as e:
                logger.error(f"Failed to validate business unit exists {business_unit_id}: {e}")
                return False
    
    async def assign_user_to_business_unit(self, user_id: UUID, business_unit_id: UUID, assigned_by: Optional[UUID] = None) -> bool:
        """Assign user to a business unit. Replaces existing assignment."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                try:
                    # First validate that business unit exists
                    if not await self.validate_business_unit_exists(business_unit_id):
                        raise Exception(f"Business unit {business_unit_id} does not exist or is inactive")
                    
                    # Remove any existing assignment for this user
                    await conn.execute("DELETE FROM aaa_user_business_units WHERE user_id = $1", str(user_id))
                    
                    # Insert new assignment
                    query = """
                        INSERT INTO aaa_user_business_units (user_id, business_unit_id, assigned_by, is_active)
                        VALUES ($1, $2, $3, TRUE)
                    """
                    await conn.execute(query, str(user_id), str(business_unit_id), str(assigned_by) if assigned_by else None)
                    
                    return True
                except Exception as e:
                    logger.error(f"Failed to assign user {user_id} to business unit {business_unit_id}: {e}")
                    return False
    
    async def get_user_business_unit(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the active business unit assignment for a user."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT ub.business_unit_id, bu.name as business_unit_name, ub.assigned_at
                    FROM aaa_user_business_units ub
                    JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    WHERE ub.user_id = $1 AND ub.is_active = TRUE
                    LIMIT 1
                """
                result = await conn.fetchrow(query, str(user_id))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get user business unit for {user_id}: {e}")
                return None
    
    async def remove_user_from_business_unit(self, user_id: UUID) -> bool:
        """Remove user from all business unit assignments."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = "DELETE FROM aaa_user_business_units WHERE user_id = $1"
                await conn.execute(query, str(user_id))
                return True
            except Exception as e:
                logger.error(f"Failed to remove user {user_id} from business units: {e}")
                return False
    
    # User organizational context methods
    async def get_user_organizational_context(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user's organizational context (organization_id, business_unit_id)."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT bu.organization_id, ub.business_unit_id, bu.name as business_unit_name,
                           o.company_name as organization_name
                    FROM aaa_user_business_units ub
                    JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    JOIN aaa_organizations o ON bu.organization_id = o.id
                    WHERE ub.user_id = $1 AND ub.is_active = TRUE
                    LIMIT 1
                """
                result = await conn.fetchrow(query, str(user_id))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get user organizational context for {user_id}: {e}")
                return None
    
    async def get_users_by_organization(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get all users within a specific organization."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT 
                        user_id as id,
                        email,
                        first_name,
                        middle_name,
                        last_name,
                        is_admin,
                        mfa_secret,
                        business_unit_id,
                        business_unit_name,
                        business_unit_code,
                        business_unit_location,
                        organization_id,
                        organization_name,
                        organization_city,
                        organization_country,
                        business_unit_manager_name,
                        parent_business_unit_name
                    FROM vw_user_details 
                    WHERE organization_id = $1
                    ORDER BY email
                """
                results = await conn.fetch(query, str(organization_id))
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get users by organization from view: {e}")
                # Fallback to original query
                query_fallback = """
                    SELECT p.id, p.email, p.first_name, p.middle_name, p.last_name, 
                           p.is_admin, p.mfa_secret,
                           ub.business_unit_id, bu.name as business_unit_name,
                           o.company_name as organization_name, bu.organization_id,
                           bu.code as business_unit_code, bu.location as business_unit_location,
                           o.city_town as organization_city, o.country as organization_country,
                           CONCAT(mgr.first_name, ' ', mgr.last_name) as business_unit_manager_name,
                           pbu.name as parent_business_unit_name
                    FROM aaa_profiles p
                    LEFT JOIN aaa_user_business_units ub ON p.id = ub.user_id AND ub.is_active = TRUE
                    LEFT JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_profiles mgr ON bu.manager_id = mgr.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    WHERE bu.organization_id = $1
                    ORDER BY p.email
                """
                results = await conn.fetch(query_fallback, str(organization_id))
                return [dict(row) for row in results]
    
    async def get_users_by_business_unit(self, business_unit_id: UUID) -> List[Dict[str, Any]]:
        """Get all users within a specific business unit."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT 
                        user_id as id,
                        email,
                        first_name,
                        middle_name,
                        last_name,
                        is_admin,
                        mfa_secret,
                        business_unit_id,
                        business_unit_name,
                        business_unit_code,
                        business_unit_location,
                        organization_id,
                        organization_name,
                        organization_city,
                        organization_country,
                        business_unit_manager_name,
                        parent_business_unit_name
                    FROM vw_user_details 
                    WHERE business_unit_id = $1
                    ORDER BY email
                """
                results = await conn.fetch(query, str(business_unit_id))
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get users by business unit from view: {e}")
                # Fallback to original query
                query_fallback = """
                    SELECT p.id, p.email, p.first_name, p.middle_name, p.last_name, 
                           p.is_admin, p.mfa_secret,
                           ub.business_unit_id, bu.name as business_unit_name,
                           o.company_name as organization_name, bu.organization_id,
                           bu.code as business_unit_code, bu.location as business_unit_location,
                           o.city_town as organization_city, o.country as organization_country,
                           CONCAT(mgr.first_name, ' ', mgr.last_name) as business_unit_manager_name,
                           pbu.name as parent_business_unit_name
                    FROM aaa_profiles p
                    JOIN aaa_user_business_units ub ON p.id = ub.user_id AND ub.is_active = TRUE
                    JOIN aaa_business_units bu ON ub.business_unit_id = bu.id
                    LEFT JOIN aaa_organizations o ON bu.organization_id = o.id
                    LEFT JOIN aaa_profiles mgr ON bu.manager_id = mgr.id
                    LEFT JOIN aaa_business_units pbu ON bu.parent_unit_id = pbu.id
                    WHERE ub.business_unit_id = $1
                    ORDER BY p.email
                """
                results = await conn.fetch(query_fallback, str(business_unit_id))
                return [dict(row) for row in results]