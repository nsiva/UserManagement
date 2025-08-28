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