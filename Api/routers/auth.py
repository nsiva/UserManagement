from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from passlib.context import CryptContext
import pyotp
import qrcode
from io import BytesIO
import base64
import os
import logging
from dotenv import load_dotenv
import logging
import secrets
import warnings

# Suppress bcrypt version warning from passlib
import passlib.handlers.bcrypt
warnings.filterwarnings("ignore", module="passlib.handlers.bcrypt")
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import get_repository
from models import LoginRequest, MFARequest, EmailOtpSetupRequest, EmailOtpVerifyRequest, PasswordResetRequest, TokenResponse, TokenData, UserInDB, ClientTokenRequest, ClientTokenResponse, ClientTokenData, ForgotPasswordRequest, SetNewPasswordRequest, VerifyResetTokenResponse

load_dotenv()

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
CLIENT_JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:4201")

print("Using SECRET_KEY from environment variables:", CLIENT_JWT_SECRET)   
print("Using ALGORITHM from environment variables:", ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

logger = logging.getLogger("auth")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USERNAME)
RESET_TOKEN_EXPIRE_MINUTES = int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", 30))

def generate_reset_token() -> str:
    """Generate a cryptographically secure reset token"""
    return secrets.token_urlsafe(32)

def mask_email(email: str) -> str:
    """Mask email address for security (show first char and domain)"""
    if "@" not in email:
        return email[:1] + "*" * (len(email) - 1)
    username, domain = email.split("@", 1)
    if len(username) <= 2:
        masked_username = username[0] + "*" * (len(username) - 1)
    else:
        masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
    return f"{masked_username}@{domain}"

async def send_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email"""
    try:
        if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD]):
            logger.error("Email configuration missing. Check SMTP environment variables.")
            return False
        
        # Create reset link (frontend should handle this route)
        reset_link = f"{FRONTEND_BASE_URL}/set-new-password?token={reset_token}"

        
        # Create email content
        subject = "Password Reset Request"
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your account.</p>
            <p>Click the link below to reset your password (this link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes):</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        You requested a password reset for your account.
        
        Click the link below to reset your password (this link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes):
        {reset_link}
        
        If you didn't request this, please ignore this email.
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = email
        
        # Add both plain text and HTML parts
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Password reset email sent to {mask_email(email)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send reset email to {mask_email(email)}: {e}")
        return False

async def send_password_setup_email(email: str, reset_token: str) -> bool:
    """Send password setup email for new users"""
    try:
        if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD]):
            logger.error("Email configuration missing. Check SMTP environment variables.")
            return False
        
        # Create password setup link (same as reset password)
        setup_link = f"{FRONTEND_BASE_URL}/set-new-password?token={reset_token}"
        # Create email content
        subject = "Set Your Password - Account Setup"
        html_body = f"""
        <html>
        <body>
            <h2>Welcome! Set Your Password</h2>
            <p>Your account has been created. Please set your password to complete the setup.</p>
            <p>Click the link below to set your password (this link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes):</p>
            <p><a href="{setup_link}">Set Password</a></p>
            <p>If you did not expect this email, please contact your administrator.</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome! Set Your Password
        
        Your account has been created. Please set your password to complete the setup.
        
        Click the link below to set your password (this link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes):
        {setup_link}
        
        If you did not expect this email, please contact your administrator.
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = email
        
        # Add both plain text and HTML parts
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Password setup email sent to {mask_email(email)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password setup email to {mask_email(email)}: {e}")
        return False

async def validate_reset_token(token: str) -> tuple[bool, Optional[str]]:
    """Validate reset token and return (is_valid, user_email)"""
    try:
        repo = get_repository()
        is_valid, user_email = await repo.validate_reset_token(token)
        return is_valid, user_email
    except Exception as e:
        logger.error(f"Error validating reset token: {e}")
        return False, None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CLIENT_JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str):
    try:
        repo = get_repository()
        user_data = await repo.get_user_by_email(email)
        if user_data:
            logger.info(f"User found for email: {email}")
            return UserInDB(**user_data)
        logger.warning(f"No user found for email: {email}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by email {email}: {e}")
        return None

async def get_user_roles(user_id: str) -> List[str]:
    try:
        from uuid import UUID
        repo = get_repository()
        roles = await repo.get_user_roles(UUID(user_id))
        logger.info(f"Roles for user_id {user_id}: {roles}")
        return roles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roles for user_id {user_id}: {e}")
        return []

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.info(f"Validating token: {token}")
    try:
        payload = jwt.decode(token, CLIENT_JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        is_admin: bool = payload.get("is_admin", False)
        roles: List[str] = payload.get("roles", [])

        logger.info(f"Decoded JWT payload: user_id={user_id}, email={email}, is_admin={is_admin}, roles={roles}")

        if user_id is None or email is None:
            logger.warning("Token missing user_id or email.")
            raise credentials_exception
        token_data = TokenData(user_id=user_id, email=email, is_admin=is_admin, roles=roles)
    except JWTError as e:
        logger.error(f"JWT Error during decoding: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise credentials_exception
    return token_data

async def get_current_admin_user(current_user: TokenData = Depends(get_current_user)):
    try:
        # Check if user has any admin role (admin, super_user, firm_admin, group_admin)
        admin_roles = ['admin', 'super_user', 'firm_admin', 'group_admin']
        has_admin_role = any(role in current_user.roles for role in admin_roles)
        
        if not current_user.is_admin and not has_admin_role:
            logger.warning(f"User {current_user.email} does not have admin permissions. Roles: {current_user.roles}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        logger.info(f"Admin user authenticated: {current_user.email}")
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_admin_user: {e}")
        raise

# In routers/auth.py or common_dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt # Assuming you use PyJWT for token validation
from pydantic import ValidationError # For catching Pydantic validation errors
import logging

# Define your secret key for client tokens (different from Supabase's JWT secret if applicable)
# It's crucial this matches how you *issue* client tokens.
#CLIENT_JWT_SECRET = "your_client_jwt_secret" # MAKE SURE THIS IS A STRONG SECRET FROM ENV VARS

CLIENT_JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
CLIENT_ALGORITHM = os.environ.get("ALGORITHM") # Or whatever algorithm you use for client tokens

# Initialize HTTPBearer to extract token from "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()
logger = logging.getLogger("auth") # Use your auth logger

async def get_current_client(
    token_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[ClientTokenData]: # Returns ClientTokenData or None
    """
    Dependency to get the current authenticated API client.
    Returns ClientTokenData if client is valid, otherwise None (as it's Optional).
    """
    if not token_credentials:
        # No Authorization header or no Bearer token provided for client.
        # This is fine for an Optional dependency.
        return None

    token = token_credentials.credentials # Extract the JWT string

    try:
        # Decode the token
        payload = jwt.decode(token, CLIENT_JWT_SECRET, algorithms=[CLIENT_ALGORITHM])

        # Validate essential claims for a client token
        if 'client_id' not in payload or not payload['client_id']:
            logger.warning("Client token provided but missing 'client_id' claim.")
            return None # Not a valid client token structure

        # Re-construct ClientTokenData from the payload
        # Ensure ClientTokenData Pydantic model can handle these fields
        client_data = ClientTokenData(
            client_id=payload['client_id'],
            scopes=payload.get('scopes', []), # Default to empty list if no scopes
            exp=payload.get('exp')
            # Add other client-specific claims if you have them
        )

        # You might add more checks here, e.g., if client_id exists in your database

        return client_data

    except jwt.ExpiredSignatureError:
        logger.warning("Client token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid client token: {e}")
        return None
    except ValidationError as e: # Catch Pydantic validation errors if ClientTokenData construction fails
        logger.warning(f"Client token payload validation error: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during token processing
        logger.error(f"Unexpected error during client token validation: {e}", exc_info=True)
        return None

@auth_router.post("/token", response_model=ClientTokenResponse, summary="Obtain a token using client_id and client_secret")
async def get_client_token(request: ClientTokenRequest):
    # Retrieve client from database
    try:
        repo = get_repository()
        client_in_db = await repo.get_client_by_id(request.client_id)
        if not client_in_db:
            logger.warning(f"Client not found: {request.client_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client ID or secret",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if client_in_db['client_secret'] != request.client_secret:
            logger.warning(f"Invalid client secret for client_id: {request.client_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client ID or secret",
                headers={"WWW-Authenticate": "Bearer"},
            )
        scopes = ["read:users", "manage:users"]
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 2)
        client_access_token = create_access_token(
            data={"client_id": request.client_id, "scopes": scopes, "token_type": "client"},
            expires_delta=access_token_expires
        )
        logger.info(f"Client token issued for client_id: {request.client_id}")
        return ClientTokenResponse(
            access_token=client_access_token,
            token_type="bearer",
            client_id=request.client_id,
            scopes=scopes
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_client_token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/login", response_model=TokenResponse)
async def login_for_access_token(request: LoginRequest):
    # Fetch user from profiles table and verify password
    try:
        user = await get_user_by_email(request.email)
        if not user:
            logger.warning(f"Login failed: User not found for {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
        
        # Verify password using bcrypt
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"Login failed: Incorrect password for {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
        
        # Check if MFA is required
        mfa_method = getattr(user, 'mfa_method', None)
        if user.mfa_secret or mfa_method:
            if mfa_method == 'email':
                # For email MFA, automatically send OTP
                otp = generate_otp()
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                
                repo = get_repository()
                otp_data = {
                    'user_id': str(user.id),
                    'email': user.email,
                    'otp': otp,
                    'purpose': 'login',
                    'expires_at': expires_at,
                    'created_at': datetime.now(timezone.utc)
                }
                
                otp_stored = await repo.create_email_otp(otp_data)
                if otp_stored:
                    email_sent = await send_otp_email(user.email, otp, 'login')
                    if email_sent:
                        logger.info(f"Email MFA required for user {user.email}, OTP sent")
                        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Email MFA required. Check your email for verification code.")
                    else:
                        logger.error(f"Failed to send email OTP for user {user.email}")
                        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email.")
                else:
                    logger.error(f"Failed to store email OTP for user {user.email}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process email verification.")
            else:
                # For TOTP MFA
                logger.info(f"TOTP MFA required for user {user.email}")
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="MFA required. Please provide MFA code.")
        
        # Get user roles
        roles = await get_user_roles(str(user.id))
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"user_id": str(user.id), "email": user.email, "is_admin": user.is_admin, "roles": roles},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Access token issued for user {user.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            roles=roles
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login_for_access_token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa_code(request: MFARequest):
    try:
        user = await get_user_by_email(request.email)
        if not user:
            logger.warning(f"MFA verification failed: User not found for {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or MFA code.")
        
        mfa_method = getattr(user, 'mfa_method', None)
        mfa_verified = False
        
        if mfa_method == 'email':
            # Verify email OTP
            repo = get_repository()
            otp_record = await repo.get_email_otp(user.id, request.mfa_code, 'login')
            
            if otp_record:
                # Mark OTP as used
                await repo.mark_email_otp_used(otp_record['id'])
                mfa_verified = True
                logger.info(f"Email OTP verified for user {user.email}")
            else:
                logger.warning(f"Invalid or expired email OTP for user {request.email}")
                
        elif user.mfa_secret:
            # Verify TOTP
            totp = pyotp.TOTP(user.mfa_secret)
            if totp.verify(request.mfa_code):
                mfa_verified = True
                logger.info(f"TOTP verified for user {user.email}")
            else:
                logger.warning(f"Invalid TOTP code for user {request.email}")
        else:
            logger.warning(f"MFA verification failed: No MFA setup for {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not set up for this user.")
        
        if not mfa_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code.")
        
        # Create access token
        roles = await get_user_roles(str(user.id))
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"user_id": str(user.id), "email": user.email, "is_admin": user.is_admin, "roles": roles},
            expires_delta=access_token_expires
        )
        logger.info(f"MFA verified and access token issued for user {user.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            roles=roles
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_mfa_code: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/mfa/setup", summary="Generate MFA QR code for a user (Admin or Self-Service after login)", response_model=dict)
async def setup_mfa(email: str, current_user: TokenData = Depends(get_current_user)):
    # This endpoint is protected by admin role.
    # In a real app, a user might also set up MFA for themselves after logging in.
    # If self-service, `current_user` would be the user setting up MFA.
    # For now, only admin can trigger this.

    try:
        user = await get_user_by_email(email)
        if not user:
            logger.warning(f"MFA setup failed: User not found for {email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        secret = pyotp.random_base32()
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name="YourAppName"
        )
        repo = get_repository()
        success = await repo.update_mfa_secret(user.id, secret)
        if not success:
            logger.error(f"Failed to save MFA secret for user {user.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save MFA secret.")
        img = qrcode.make(provisioning_uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        logger.info(f"MFA setup complete for user {user.email}")
        return {"qr_code_base64": qr_code_base64, "secret": secret, "provisioning_uri": provisioning_uri}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in setup_mfa: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.delete("/mfa/remove", summary="Remove MFA for a user (Admin only)")
async def remove_mfa(email: str, current_user: TokenData = Depends(get_current_admin_user)):
    """
    Remove MFA for a user by clearing both mfa_secret and mfa_method.
    Supports both TOTP (authenticator app) and email MFA removal.
    This endpoint is protected by admin role.
    """
    try:
        user = await get_user_by_email(email)
        if not user:
            logger.warning(f"MFA removal failed: User not found for {email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        # Check if user has any MFA enabled (either TOTP secret or email method)
        has_mfa = bool(user.mfa_secret or user.mfa_method)
        if not has_mfa:
            logger.info(f"MFA removal: User {email} already has no MFA setup")
            return {"message": "MFA is not enabled for this user."}
        
        repo = get_repository()
        
        # Remove both MFA secret (for TOTP) and MFA method (for email/TOTP)
        success_secret = await repo.update_mfa_secret(user.id, None)
        success_method = await repo.update_user_mfa_method(user.id, None)
        
        if not (success_secret and success_method):
            logger.error(f"Failed to remove MFA for user {user.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove MFA.")
        
        logger.info(f"MFA removed for user {user.email} (secret: {bool(user.mfa_secret)}, method: {user.mfa_method})")
        return {"message": "MFA has been successfully removed."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in remove_mfa: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/validate-token")
async def validate_token(
    current_user: TokenData = Depends(get_current_user)
):
    """Validate authentication token - used by callback page"""
    try:
        logger.info(f"Token validated for user: {current_user.email}")
        return {
            "valid": True,
            "user": {
                "id": current_user.user_id,
                "email": current_user.email
            }
        }
    except Exception as e:
        logger.error(f"Error in validate_token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/reset_password", summary="Reset password for authenticated user")
async def reset_password(
    request: PasswordResetRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Reset password for the currently authenticated user.
    Requires current password verification before allowing password change.
    """
    try:
        user = await get_user_by_email(current_user.email)
        if not user:
            logger.warning(f"Password reset failed: User not found for {current_user.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Verify current password
        if not verify_password(request.current_password, user.password_hash):
            logger.warning(f"Password reset failed: Incorrect current password for {current_user.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        
        # Hash new password
        new_password_hash = get_password_hash(request.new_password)
        
        # Update password in database
        repo = get_repository()
        success = await repo.update_user(user.id, {
            'password_hash': new_password_hash
        })
        
        if not success:
            logger.error(f"Failed to update password for user {current_user.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password")
        
        logger.info(f"Password reset successful for user: {current_user.email}")
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/forgot-password", summary="Request password reset via email")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Initiate password reset process by sending reset link to user's email.
    Always returns success to prevent email enumeration attacks.
    """
    try:
        # Check if user exists
        user = await get_user_by_email(request.email)
        if not user:
            # Return success even if user doesn't exist (security: prevent email enumeration)
            logger.info(f"Password reset requested for non-existent email: {mask_email(request.email)}")
            return {"message": "If the email exists in our system, a password reset link will be sent."}
        
        # Generate reset token
        reset_token = generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        
        # Store token in database
        repo = get_repository()
        success = await repo.create_reset_token({
            'user_id': str(user.id),
            'token': reset_token,
            'expires_at': expires_at,
            'used': False
        })
        
        if not success:
            logger.error(f"Failed to store reset token for user {mask_email(request.email)}")
            # Still return success to prevent information disclosure
            return {"message": "If the email exists in our system, a password reset link will be sent."}
        
        # Send reset email
        email_sent = await send_reset_email(request.email, reset_token)
        if not email_sent:
            logger.error(f"Failed to send reset email to {mask_email(request.email)}")
            # Don't reveal email sending failure to user for security
            
        logger.info(f"Password reset initiated for user: {mask_email(request.email)}")
        return {"message": "If the email exists in our system, a password reset link will be sent."}
        
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}")
        # Return success even on error to prevent information disclosure
        return {"message": "If the email exists in our system, a password reset link will be sent."}

@auth_router.get("/verify-reset-token/{token}", response_model=VerifyResetTokenResponse, summary="Verify reset token validity")
async def verify_reset_token_endpoint(token: str):
    """
    Verify if a password reset token is valid and not expired.
    Returns masked email for valid tokens.
    """
    try:
        is_valid, user_email = await validate_reset_token(token)
        
        if is_valid and user_email:
            masked_email = mask_email(user_email)
            logger.info(f"Reset token verified for user: {masked_email}")
            return VerifyResetTokenResponse(valid=True, email=masked_email)
        else:
            logger.warning("Invalid or expired reset token verification attempt")
            return VerifyResetTokenResponse(valid=False)
            
    except Exception as e:
        logger.error(f"Error in verify_reset_token: {e}")
        return VerifyResetTokenResponse(valid=False)

@auth_router.post("/set-new-password", summary="Set new password using reset token")
async def set_new_password(request: SetNewPasswordRequest):
    """
    Complete password reset process using a valid reset token.
    Sets new password and invalidates the token.
    """
    try:
        # Validate token
        is_valid, user_email = await validate_reset_token(request.token)
        if not is_valid or not user_email:
            logger.warning("Invalid or expired token used for password reset")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user by email
        user = await get_user_by_email(user_email)
        if not user:
            logger.error(f"User not found during password reset: {mask_email(user_email)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Hash new password
        new_password_hash = get_password_hash(request.new_password)
        
        # Update password in database
        repo = get_repository()
        success = await repo.update_user(user.id, {
            'password_hash': new_password_hash
        })
        
        if not success:
            logger.error(f"Failed to update password for user {mask_email(user_email)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        # Mark token as used
        repo = get_repository()
        success = await repo.mark_token_used(request.token)
        
        if not success:
            logger.warning(f"Failed to mark reset token as used for user {mask_email(user_email)}")
        
        logger.info(f"Password reset completed for user: {mask_email(user_email)}")
        return {"message": "Password has been reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in set_new_password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Email OTP Helper Functions
def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)

async def send_otp_email(email: str, otp: str, purpose: str) -> bool:
    """Send OTP via email."""
    try:
        # Email configuration
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_username = os.environ.get("SMTP_USERNAME")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        
        if not smtp_username or not smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        
        if purpose == 'setup':
            msg['Subject'] = "Multi-Factor Authentication Setup - Verification Code"
            body = f"""
            Your MFA setup verification code is: {otp}
            
            This code will expire in 10 minutes.
            
            If you did not request this code, please contact your administrator.
            """
        else:  # login
            msg['Subject'] = "Login Verification Code"
            body = f"""
            Your login verification code is: {otp}
            
            This code will expire in 5 minutes.
            
            If you did not request this code, please contact your administrator immediately.
            """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"OTP email sent to {email} for {purpose}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        return False

# Email OTP Endpoints
@auth_router.post("/mfa/email/setup", summary="Send email OTP for MFA setup")
async def setup_email_mfa(
    request: EmailOtpSetupRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Send email OTP for MFA setup verification."""
    try:
        user = await get_user_by_email(request.email)
        if not user:
            logger.warning(f"Email MFA setup failed: User not found for {request.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        # Generate OTP
        otp = generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Store OTP in database
        repo = get_repository()
        otp_data = {
            'user_id': str(user.id),
            'email': request.email,
            'otp': otp,
            'purpose': 'setup',
            'expires_at': expires_at,
            'created_at': datetime.now(timezone.utc)
        }
        
        success = await repo.create_email_otp(otp_data)
        if not success:
            logger.error(f"Failed to store email OTP for user {user.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create verification code.")
        
        # Send OTP email
        email_sent = await send_otp_email(request.email, otp, 'setup')
        if not email_sent:
            logger.error(f"Failed to send OTP email to {request.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email.")
        
        logger.info(f"Email MFA setup OTP sent to {request.email}")
        return {"message": "Verification code sent to your email", "expires_at": expires_at.isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in setup_email_mfa: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/mfa/email/verify", summary="Verify email OTP for MFA setup")
async def verify_email_mfa_setup(
    request: EmailOtpVerifyRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Verify email OTP and complete MFA setup."""
    try:
        user = await get_user_by_email(request.email)
        if not user:
            logger.warning(f"Email MFA verification failed: User not found for {request.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        # Get and validate OTP
        repo = get_repository()
        otp_record = await repo.get_email_otp(user.id, request.otp, 'setup')
        
        if not otp_record:
            logger.warning(f"Invalid or expired OTP for user {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code.")
        
        # Mark OTP as used
        otp_used = await repo.mark_email_otp_used(otp_record['id'])
        if not otp_used:
            logger.error(f"Failed to mark OTP as used for user {request.email}")
        
        # Enable email MFA for user
        mfa_enabled = await repo.update_user_mfa_method(user.id, 'email')
        if not mfa_enabled:
            logger.error(f"Failed to enable email MFA for user {request.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enable MFA.")
        
        logger.info(f"Email MFA setup completed for user {request.email}")
        return {"message": "Email MFA has been successfully enabled.", "mfa_enabled": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_email_mfa_setup: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@auth_router.post("/mfa/email/send", summary="Send email OTP for login")
async def send_login_email_otp(request: EmailOtpSetupRequest):
    """Send email OTP for login verification."""
    try:
        user = await get_user_by_email(request.email)
        if not user:
            # Don't reveal if user exists
            logger.warning(f"Login email OTP requested for non-existent user: {request.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        # Check if user has email MFA enabled
        if getattr(user, 'mfa_method', None) != 'email':
            logger.warning(f"Login email OTP requested for user without email MFA: {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email MFA is not enabled for this user.")
        
        # Generate OTP
        otp = generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)  # Shorter expiry for login
        
        # Store OTP in database
        repo = get_repository()
        otp_data = {
            'user_id': str(user.id),
            'email': request.email,
            'otp': otp,
            'purpose': 'login',
            'expires_at': expires_at,
            'created_at': datetime.now(timezone.utc)
        }
        
        success = await repo.create_email_otp(otp_data)
        if not success:
            logger.error(f"Failed to store login email OTP for user {user.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create verification code.")
        
        # Send OTP email
        email_sent = await send_otp_email(request.email, otp, 'login')
        if not email_sent:
            logger.error(f"Failed to send login OTP email to {request.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email.")
        
        logger.info(f"Login email OTP sent to {request.email}")
        return {"message": "Verification code sent to your email", "expires_at": expires_at.isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_login_email_otp: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
