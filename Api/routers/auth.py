from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
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

from database import supabase
from models import LoginRequest, MFARequest, TokenResponse, TokenData, UserInDB, ClientTokenRequest, ClientTokenResponse, ClientTokenData

load_dotenv()

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
CLIENT_JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

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
        response = supabase.from_('aaa_profiles').select('*').eq('email', email).limit(1).execute()
        if response.data:
            logger.info(f"User found for email: {email}")
            return UserInDB(**response.data[0])
        logger.warning(f"No user found for email: {email}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user by email {email}: {e}")
        return None

async def get_user_roles(user_id: str) -> List[str]:
    try:
        response = supabase.from_('aaa_user_roles').select('role_id,aaa_roles(name)').eq('user_id', user_id).execute()
        if response.data:
            roles = [item['aaa_roles']['name'] for item in response.data if item['aaa_roles']]
            logger.info(f"Roles for user_id {user_id}: {roles}")
            return roles
        logger.warning(f"No roles found for user_id: {user_id}")
        return []
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
        if not current_user.is_admin:
            logger.warning(f"User {current_user.email} does not have admin permissions.")
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
        response = supabase.from_('aaa_clients').select('*').eq('client_id', request.client_id).limit(1).execute()
        if not response.data:
            logger.warning(f"Client not found: {request.client_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client ID or secret",
                headers={"WWW-Authenticate": "Bearer"},
            )
        client_in_db = response.data[0]
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
        if user.mfa_secret:
            logger.info(f"MFA required for user {user.email}")
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
        if not user or not user.mfa_secret:
            logger.warning(f"MFA verification failed: No MFA setup for {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not set up for this user or invalid email.")
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(request.mfa_code):
            logger.warning(f"Invalid MFA code for user {request.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code.")
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
        update_response = supabase.from_('aaa_profiles').update({'mfa_secret': secret}).eq('id', str(user.id)).execute()
        if update_response.count == 0:
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
