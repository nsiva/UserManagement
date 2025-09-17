from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime


class BaseRepository(ABC):
    """Abstract base repository interface for database operations."""
    
    # User Management
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile."""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all user profiles."""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update user profile. Returns True if successful."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user profile. Returns True if successful."""
        pass
    
    # Role Management
    @abstractmethod
    async def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        pass
    
    @abstractmethod
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles."""
        pass
    
    @abstractmethod
    async def update_role(self, role_id: UUID, role_data: Dict[str, Any]) -> bool:
        """Update role. Returns True if successful."""
        pass
    
    @abstractmethod
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role. Returns True if successful."""
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """Get role names for a user."""
        pass
    
    @abstractmethod
    async def assign_user_roles(self, user_id: UUID, role_names: List[str]) -> bool:
        """Assign roles to a user. Replaces existing roles."""
        pass
    
    @abstractmethod
    async def delete_user_roles(self, user_id: UUID) -> bool:
        """Delete all roles for a user."""
        pass
    
    # MFA Management
    @abstractmethod
    async def update_mfa_secret(self, user_id: UUID, secret: Optional[str]) -> bool:
        """Update MFA secret for a user. None to disable MFA."""
        pass
    
    @abstractmethod
    async def create_email_otp(self, otp_data: Dict[str, Any]) -> bool:
        """Create an email OTP record."""
        pass
    
    @abstractmethod
    async def get_email_otp(self, user_id: UUID, otp: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get email OTP by user_id, otp and purpose."""
        pass
    
    @abstractmethod
    async def mark_email_otp_used(self, otp_id: UUID) -> bool:
        """Mark an email OTP as used."""
        pass
    
    @abstractmethod
    async def cleanup_expired_email_otps(self) -> int:
        """Remove expired email OTPs. Returns number of deleted records."""
        pass
    
    @abstractmethod
    async def update_user_mfa_method(self, user_id: UUID, mfa_method: str) -> bool:
        """Update user's MFA method (totp or email)."""
        pass
    
    # Client Management
    @abstractmethod
    async def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client by client_id."""
        pass
    
    # Password Reset
    @abstractmethod
    async def create_reset_token(self, token_data: Dict[str, Any]) -> bool:
        """Create a password reset token."""
        pass
    
    @abstractmethod
    async def validate_reset_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Validate reset token. Returns (is_valid, user_email)."""
        pass
    
    @abstractmethod
    async def mark_token_used(self, token: str) -> bool:
        """Mark reset token as used."""
        pass
    
    # Organization Management
    @abstractmethod
    async def create_organization(self, organization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new organization."""
        pass
    
    @abstractmethod
    async def get_organization_by_id(self, organization_id: UUID) -> Optional[Dict[str, Any]]:
        """Get organization by ID."""
        pass
    
    @abstractmethod
    async def get_all_organizations(self) -> List[Dict[str, Any]]:
        """Get all organizations."""
        pass
    
    @abstractmethod
    async def update_organization(self, organization_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update organization. Returns True if successful."""
        pass
    
    @abstractmethod
    async def delete_organization(self, organization_id: UUID) -> bool:
        """Delete organization. Returns True if successful."""
        pass
    
    # Business Unit Management
    @abstractmethod
    async def create_business_unit(self, business_unit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business unit."""
        pass
    
    @abstractmethod
    async def get_business_unit_by_id(self, business_unit_id: UUID) -> Optional[Dict[str, Any]]:
        """Get business unit by ID."""
        pass
    
    @abstractmethod
    async def get_business_units_by_organization(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get all business units for an organization."""
        pass
    
    @abstractmethod
    async def get_all_business_units(self) -> List[Dict[str, Any]]:
        """Get all business units."""
        pass
    
    @abstractmethod
    async def update_business_unit(self, business_unit_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update business unit. Returns True if successful."""
        pass
    
    @abstractmethod
    async def delete_business_unit(self, business_unit_id: UUID) -> bool:
        """Delete business unit. Returns True if successful."""
        pass
    
    @abstractmethod
    async def get_business_unit_hierarchy(self, organization_id: UUID, parent_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get business unit hierarchy for an organization."""
        pass
    
    @abstractmethod
    async def validate_business_unit_hierarchy(self, business_unit_id: UUID, parent_unit_id: UUID) -> bool:
        """Validate that parent-child relationship doesn't create circular dependency."""
        pass
    
    # User-Business Unit Relationship Management
    @abstractmethod
    async def validate_business_unit_exists(self, business_unit_id: UUID) -> bool:
        """Validate that a business unit exists and is active."""
        pass
    
    @abstractmethod
    async def assign_user_to_business_unit(self, user_id: UUID, business_unit_id: UUID, assigned_by: Optional[UUID] = None) -> bool:
        """Assign user to a business unit. Replaces existing assignment."""
        pass
    
    @abstractmethod
    async def get_user_business_unit(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the active business unit assignment for a user."""
        pass
    
    @abstractmethod
    async def remove_user_from_business_unit(self, user_id: UUID) -> bool:
        """Remove user from all business unit assignments."""
        pass
    
    @abstractmethod
    async def get_user_organizational_context(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user's organizational context (organization_id, business_unit_id)."""
        pass
    
    @abstractmethod
    async def get_users_by_organization(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """Get all users within a specific organization."""
        pass
    
    @abstractmethod
    async def get_users_by_business_unit(self, business_unit_id: UUID) -> List[Dict[str, Any]]:
        """Get all users within a specific business unit."""
        pass