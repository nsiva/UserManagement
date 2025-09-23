from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
import logging
from supabase import Client

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SupabaseRepository(BaseRepository):
    """Supabase implementation of the repository pattern."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile."""
        try:
            response = self.client.from_('aaa_profiles').insert(user_data).execute()
            if not response.data:
                raise Exception("Failed to create user profile")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            response = self.client.from_('aaa_profiles').select('*').eq('email', email).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = self.client.from_('aaa_profiles').select(
                'id, email, first_name, middle_name, last_name, is_admin, mfa_secret, mfa_method'
            ).eq('id', str(user_id)).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all user profiles."""
        try:
            response = self.client.from_('aaa_profiles').select(
                'id, email, first_name, middle_name, last_name, is_admin, mfa_secret, mfa_method'
            ).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []
    
    async def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update user profile. Returns True if successful."""
        try:
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            response = self.client.from_('aaa_profiles').update(update_data).eq('id', str(user_id)).execute()
            # Check if response has data (successful update) since count might be None
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user profile. Returns True if successful."""
        try:
            # First delete user_roles entries
            self.client.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute()
            
            # Delete the user profile
            response = self.client.from_('aaa_profiles').delete().eq('id', str(user_id)).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    async def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        try:
            response = self.client.from_('aaa_roles').insert(role_data).execute()
            if not response.data:
                raise Exception("Failed to create role")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create role: {e}")
            raise
    
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles."""
        try:
            response = self.client.from_('aaa_roles').select('*').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get all roles: {e}")
            return []
    
    async def update_role(self, role_id: UUID, role_data: Dict[str, Any]) -> bool:
        """Update role. Returns True if successful."""
        try:
            response = self.client.from_('aaa_roles').update(role_data).eq('id', str(role_id)).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to update role {role_id}: {e}")
            return False
    
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role. Returns True if successful."""
        try:
            response = self.client.from_('aaa_roles').delete().eq('id', str(role_id)).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete role {role_id}: {e}")
            return False
    
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """Get role names for a user."""
        try:
            response = self.client.from_('aaa_user_roles').select(
                'role_id,aaa_roles(name)'
            ).eq('user_id', str(user_id)).execute()
            
            if response.data:
                return [item['aaa_roles']['name'] for item in response.data if item['aaa_roles']]
            return []
        except Exception as e:
            logger.error(f"Failed to get user roles for {user_id}: {e}")
            return []
    
    async def assign_user_roles(self, user_id: UUID, role_names: List[str]) -> bool:
        """Assign roles to a user. Replaces existing roles."""
        try:
            if not role_names:
                # Delete all existing roles for the user
                self.client.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute()
                return True
            
            # Fetch role IDs for the given role names
            roles_response = self.client.from_('aaa_roles').select('id, name').in_('name', role_names).execute()
            
            if not roles_response.data or len(roles_response.data) != len(role_names):
                missing_roles = set(role_names) - {role['name'] for role in roles_response.data or []}
                raise Exception(f"Role(s) not found: {missing_roles}")
            
            role_ids = [role['id'] for role in roles_response.data]
            
            # Delete all existing roles for the user before assigning new ones
            self.client.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute()
            
            # Insert new role assignments
            insert_data = [{"user_id": str(user_id), "role_id": str(role_id)} for role_id in role_ids]
            if insert_data:
                self.client.from_('aaa_user_roles').insert(insert_data).execute()
            
            return True
        except Exception as e:
            logger.error(f"Failed to assign roles to user {user_id}: {e}")
            return False
    
    async def delete_user_roles(self, user_id: UUID) -> bool:
        """Delete all roles for a user."""
        try:
            self.client.from_('aaa_user_roles').delete().eq('user_id', str(user_id)).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete user roles for {user_id}: {e}")
            return False
    
    # --- Functional Roles Management ---
    
    async def create_functional_role(self, role_data, created_by: str) -> UUID:
        """Create a new functional role."""
        try:
            from uuid import uuid4
            role_id = uuid4()
            
            insert_data = {
                'id': str(role_id),
                'name': role_data.name,
                'label': role_data.label,
                'description': role_data.description,
                'category': role_data.category,
                'permissions': role_data.permissions,
                'is_active': role_data.is_active,
                'created_by': created_by
            }
            
            self.client.from_('aaa_functional_roles').insert(insert_data).execute()
            return role_id
            
        except Exception as e:
            logger.error(f"Failed to create functional role: {e}")
            raise e
    
    async def get_functional_role_by_id(self, role_id: UUID):
        """Get functional role by ID."""
        try:
            response = self.client.from_('aaa_functional_roles').select('*').eq('id', str(role_id)).execute()
            if response.data:
                from models import FunctionalRoleInDB
                return FunctionalRoleInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get functional role {role_id}: {e}")
            return None
    
    async def get_functional_role_by_name(self, name: str):
        """Get functional role by name."""
        try:
            response = self.client.from_('aaa_functional_roles').select('*').eq('name', name).execute()
            if response.data:
                from models import FunctionalRoleInDB
                return FunctionalRoleInDB(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get functional role by name {name}: {e}")
            return None
    
    async def get_functional_roles(self, category: Optional[str] = None, is_active: Optional[bool] = None):
        """Get functional roles with optional filtering."""
        try:
            query = self.client.from_('aaa_functional_roles').select('*')
            
            if category:
                query = query.eq('category', category)
            if is_active is not None:
                query = query.eq('is_active', is_active)
                
            response = query.order('category', desc=False).order('name', desc=False).execute()
            
            from models import FunctionalRoleInDB
            return [FunctionalRoleInDB(**role) for role in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get functional roles: {e}")
            return []
    
    async def update_functional_role(self, role_id: UUID, role_data, updated_by: str) -> bool:
        """Update a functional role."""
        try:
            update_data = {
                'updated_by': updated_by,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if role_data.label is not None:
                update_data['label'] = role_data.label
            if role_data.description is not None:
                update_data['description'] = role_data.description
            if role_data.category is not None:
                update_data['category'] = role_data.category
            if role_data.permissions is not None:
                update_data['permissions'] = role_data.permissions
            if role_data.is_active is not None:
                update_data['is_active'] = role_data.is_active
            
            self.client.from_('aaa_functional_roles').update(update_data).eq('id', str(role_id)).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update functional role {role_id}: {e}")
            return False
    
    async def delete_functional_role(self, role_id: UUID) -> bool:
        """Delete a functional role."""
        try:
            self.client.from_('aaa_functional_roles').delete().eq('id', str(role_id)).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete functional role {role_id}: {e}")
            return False
    
    async def assign_functional_roles_to_user(self, user_id: UUID, role_names: List[str], assigned_by: str, replace_existing: bool = True, notes: Optional[str] = None) -> bool:
        """Assign functional roles to a user."""
        try:
            # Get role IDs from names
            role_ids = []
            for role_name in role_names:
                role = await self.get_functional_role_by_name(role_name)
                if role:
                    role_ids.append(role.id)
            
            if replace_existing:
                # Remove existing assignments
                self.client.from_('aaa_user_functional_roles').delete().eq('user_id', str(user_id)).execute()
            
            # Add new assignments
            if role_ids:
                from uuid import uuid4
                assignments = []
                for role_id in role_ids:
                    assignments.append({
                        'id': str(uuid4()),
                        'user_id': str(user_id),
                        'functional_role_id': str(role_id),
                        'assigned_by': assigned_by,
                        'notes': notes
                    })
                
                self.client.from_('aaa_user_functional_roles').insert(assignments).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign functional roles to user {user_id}: {e}")
            return False
    
    async def get_user_functional_roles(self, user_id: UUID, is_active: bool = True):
        """Get functional roles assigned to a user."""
        try:
            query = (self.client
                    .from_('aaa_user_functional_roles')
                    .select('aaa_functional_roles(*)')
                    .eq('user_id', str(user_id)))
            
            if is_active:
                query = query.eq('is_active', True)
                
            response = query.execute()
            
            from models import FunctionalRoleInDB
            roles = []
            for assignment in response.data:
                if assignment.get('aaa_functional_roles'):
                    roles.append(FunctionalRoleInDB(**assignment['aaa_functional_roles']))
            
            return roles
            
        except Exception as e:
            logger.error(f"Failed to get user functional roles for {user_id}: {e}")
            return []
    
    async def remove_functional_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Remove a functional role from a user."""
        try:
            response = (self.client
                       .from_('aaa_user_functional_roles')
                       .delete()
                       .eq('user_id', str(user_id))
                       .eq('functional_role_id', str(role_id))
                       .execute())
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to remove functional role {role_id} from user {user_id}: {e}")
            return False
    
    async def check_user_functional_permission(self, user_id: UUID, permission: str) -> tuple[bool, List[str]]:
        """Check if user has permission through functional roles."""
        try:
            # Get user's functional roles with permissions
            query = (self.client
                    .from_('aaa_user_functional_roles')
                    .select('aaa_functional_roles(name, permissions)')
                    .eq('user_id', str(user_id))
                    .eq('is_active', True))
            
            response = query.execute()
            
            granted_by_roles = []
            for assignment in response.data:
                role_data = assignment.get('aaa_functional_roles')
                if role_data and role_data.get('permissions'):
                    if permission in role_data['permissions']:
                        granted_by_roles.append(role_data['name'])
            
            return len(granted_by_roles) > 0, granted_by_roles
            
        except Exception as e:
            logger.error(f"Failed to check user functional permission: {e}")
            return False, []
    
    async def update_mfa_secret(self, user_id: UUID, secret: Optional[str]) -> bool:
        """Update MFA secret for a user. None to disable MFA."""
        try:
            update_data = {
                'mfa_secret': secret,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            response = self.client.from_('aaa_profiles').update(update_data).eq('id', str(user_id)).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to update MFA secret for user {user_id}: {e}")
            return False
    
    async def create_email_otp(self, otp_data: Dict[str, Any]) -> bool:
        """Create an email OTP record."""
        try:
            # First, cleanup any existing unused OTPs for this user/purpose
            await self.cleanup_user_email_otps(otp_data['user_id'], otp_data['purpose'])
            
            response = self.client.from_('aaa_email_otps').insert(otp_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to create email OTP: {e}")
            return False
    
    async def get_email_otp(self, user_id: UUID, otp: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get email OTP by user_id, otp and purpose."""
        try:
            response = self.client.from_('aaa_email_otps').select('*').eq(
                'user_id', str(user_id)
            ).eq('otp', otp).eq('purpose', purpose).eq('used', False).gte(
                'expires_at', datetime.now(timezone.utc).isoformat()
            ).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get email OTP for user {user_id}: {e}")
            return None
    
    async def mark_email_otp_used(self, otp_id: UUID) -> bool:
        """Mark an email OTP as used."""
        try:
            update_data = {
                'used': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            response = self.client.from_('aaa_email_otps').update(update_data).eq('id', str(otp_id)).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to mark email OTP as used {otp_id}: {e}")
            return False
    
    async def cleanup_expired_email_otps(self) -> int:
        """Remove expired email OTPs. Returns number of deleted records."""
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            response = self.client.from_('aaa_email_otps').delete().lt('expires_at', current_time).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Failed to cleanup expired email OTPs: {e}")
            return 0
    
    async def cleanup_user_email_otps(self, user_id: UUID, purpose: str) -> bool:
        """Remove existing unused OTPs for a user/purpose combination."""
        try:
            response = self.client.from_('aaa_email_otps').delete().eq(
                'user_id', str(user_id)
            ).eq('purpose', purpose).eq('used', False).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup user email OTPs for {user_id}: {e}")
            return False
    
    async def update_user_mfa_method(self, user_id: UUID, mfa_method: Optional[str]) -> bool:
        """Update user's MFA method (totp or email). None to clear MFA method."""
        try:
            update_data = {
                'mfa_method': mfa_method,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            response = self.client.from_('aaa_profiles').update(update_data).eq('id', str(user_id)).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to update MFA method for user {user_id}: {e}")
            return False
    
    async def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client by client_id."""
        try:
            response = self.client.from_('aaa_clients').select('*').eq('client_id', client_id).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get client by ID {client_id}: {e}")
            return None
    
    async def create_reset_token(self, token_data: Dict[str, Any]) -> bool:
        """Create a password reset token."""
        try:
            response = self.client.from_('aaa_password_reset_tokens').insert(token_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to create reset token: {e}")
            return False
    
    async def validate_reset_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Validate reset token. Returns (is_valid, user_email)."""
        try:
            response = self.client.from_('aaa_password_reset_tokens').select(
                'user_id, expires_at, used, aaa_profiles(email)'
            ).eq('token', token).eq('used', False).limit(1).execute()
            
            if not response.data:
                return False, None
            
            token_data = response.data[0]
            
            # Check if token has expired
            expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                return False, None
            
            user_email = token_data['aaa_profiles']['email'] if token_data['aaa_profiles'] else None
            return True, user_email
            
        except Exception as e:
            logger.error(f"Failed to validate reset token: {e}")
            return False, None
    
    async def mark_token_used(self, token: str) -> bool:
        """Mark reset token as used."""
        try:
            response = self.client.from_('aaa_password_reset_tokens').update({
                'used': True
            }).eq('token', token).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to mark token as used: {e}")
            return False
    
    async def count_business_units_by_organization(self, organization_id: UUID) -> int:
        """Count business units in an organization."""
        try:
            response = self.client.from_('aaa_business_units')\
                .select('id', count='exact')\
                .eq('organization_id', str(organization_id))\
                .execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Failed to count business units for organization {organization_id}: {e}")
            return 0
    
    async def count_users_by_organization(self, organization_id: UUID) -> int:
        """Count users in an organization."""
        try:
            # Get all business units in the organization first
            bu_response = self.client.from_('aaa_business_units')\
                .select('id')\
                .eq('organization_id', str(organization_id))\
                .execute()
            
            if not bu_response.data:
                return 0
            
            business_unit_ids = [bu['id'] for bu in bu_response.data]
            
            # Count users in those business units
            user_response = self.client.from_('aaa_user_business_units')\
                .select('user_id', count='exact')\
                .in_('business_unit_id', business_unit_ids)\
                .eq('is_active', True)\
                .execute()
            
            return user_response.count or 0
        except Exception as e:
            logger.error(f"Failed to count users for organization {organization_id}: {e}")
            return 0
    
    async def count_users_by_business_unit(self, business_unit_id: UUID) -> int:
        """Count users in a business unit."""
        try:
            response = self.client.from_('aaa_user_business_units')\
                .select('user_id', count='exact')\
                .eq('business_unit_id', str(business_unit_id))\
                .eq('is_active', True)\
                .execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Failed to count users for business unit {business_unit_id}: {e}")
            return 0