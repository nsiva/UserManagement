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
        """Get user by ID."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT id, email, first_name, middle_name, last_name, is_admin, mfa_secret
                    FROM aaa_profiles WHERE id = $1 LIMIT 1
                """
                result = await conn.fetchrow(query, str(user_id))
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"Failed to get user by ID {user_id}: {e}")
                return None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all user profiles."""
        pool = await self.get_connection_pool()
        async with pool.acquire() as conn:
            try:
                query = """
                    SELECT id, email, first_name, middle_name, last_name, is_admin, mfa_secret
                    FROM aaa_profiles
                """
                results = await conn.fetch(query)
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"Failed to get all users: {e}")
                return []
    
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