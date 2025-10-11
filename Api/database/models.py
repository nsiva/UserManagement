from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr


class DBUser(BaseModel):
    """Database user entity model."""
    id: UUID
    email: EmailStr
    password_hash: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = False
    mfa_secret: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DBRole(BaseModel):
    """Database role entity model."""
    id: UUID
    name: str
    created_at: datetime


class DBUserRole(BaseModel):
    """Database user-role relationship entity model."""
    user_id: UUID
    role_id: UUID
    assigned_at: datetime


class DBClient(BaseModel):
    """Database client entity model."""
    client_id: str
    client_secret: str
    name: str
    scopes: List[str]
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class DBPasswordResetToken(BaseModel):
    """Database password reset token entity model."""
    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime


class DBEmailOtp(BaseModel):
    """Database email OTP entity model."""
    id: UUID
    user_id: UUID
    email: EmailStr
    otp: str
    purpose: str  # 'setup' or 'login'
    expires_at: datetime
    used: bool = False
    created_at: datetime


class DBOrganization(BaseModel):
    """Database organization entity model."""
    id: UUID
    company_name: str
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city_town: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DBOAuthClient(BaseModel):
    """Database OAuth client entity model (unified with DBClient)."""
    client_id: str  # Primary key in unified table
    name: str
    client_type: str = "oauth_pkce"
    client_secret: Optional[str] = None  # Not used for PKCE clients
    redirect_uris: Optional[List[str]] = None
    scopes: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class DBAuthorizationCode(BaseModel):
    """Database authorization code entity model."""
    id: UUID
    code: str
    client_id: str
    user_id: UUID
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str
    expires_at: datetime
    used: bool = False
    created_at: datetime