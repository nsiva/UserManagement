from pydantic import BaseModel, EmailStr
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# --- Auth Models ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class MFARequest(BaseModel):
    email: EmailStr
    mfa_code: str

class EmailOtpSetupRequest(BaseModel):
    email: EmailStr

class EmailOtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class PasswordResetRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class SetNewPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyResetTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None  # Masked email for valid tokens

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool
    roles: List[str]

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    is_admin: bool = False
    roles: List[str] = []

# --- User Management Models ---
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None  # Made optional to support different password setup methods
    password_option: str = "generate_now"  # Options: "generate_now", "send_link"
    is_admin: Optional[bool] = False
    roles: Optional[List[str]] = [] # Roles by name
    business_unit_id: Optional[UUID] = None  # Optional for backward compatibility

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    send_password_reset: Optional[bool] = False  # Send password reset email if true
    is_admin: Optional[bool] = None
    roles: Optional[List[str]] = None # Roles by name
    business_unit_id: Optional[UUID] = None  # Optional business unit change

class UserInDB(UserBase):
    id: UUID
    is_admin: bool
    password_hash: str # Stored hashed password
    mfa_secret: Optional[str] = None # Only for backend use
    mfa_method: Optional[str] = None # MFA method: 'totp' or 'email'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserWithRoles(UserBase):
    id: UUID
    is_admin: bool
    roles: List[str] # List of role names
    mfa_enabled: bool = False  # Indicates whether MFA is set up
    
    # Business Unit Information
    business_unit_id: Optional[UUID] = None  # Current business unit assignment
    business_unit_name: Optional[str] = None  # Business unit name for display
    business_unit_code: Optional[str] = None  # Business unit code
    business_unit_location: Optional[str] = None  # Business unit location
    
    # Organization Information
    organization_id: Optional[UUID] = None  # Organization ID
    organization_name: Optional[str] = None  # Organization name for display
    organization_city: Optional[str] = None  # Organization city
    organization_country: Optional[str] = None  # Organization country
    
    # Manager Information (if available)
    business_unit_manager_name: Optional[str] = None  # Business unit manager name
    
    # Parent Business Unit (if available)
    parent_business_unit_name: Optional[str] = None  # Parent business unit name

    class Config:
        from_attributes = True


# --- User Role Assignment Model ---
class UserRoleAssignment(BaseModel):
    user_id: UUID
    role_names: List[str] # List of role names to assign/replace


# --- Client Credentials Models ---
class ClientTokenRequest(BaseModel):
    client_id: str
    client_secret: str

class ClientTokenResponse(BaseModel):
    access_token: str
    token_type: str
    client_id: str
    scopes: List[str] = [] # Optional: define scopes for different client permissions

# --- Token Data for Client (if you differentiate from user TokenData) ---
class ClientTokenData(BaseModel):
    client_id: str
    scopes: List[str] = []


# New: Profile Response Model (exclude sensitive data like mfa_secret)
class ProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mfa_enabled: bool = False  # Indicates whether MFA is set up (without exposing the secret)
    # Add any other non-sensitive profile fields you want to return
    # is_admin: bool # You might include this if you want the client to know their admin status


