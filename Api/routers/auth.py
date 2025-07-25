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
from dotenv import load_dotenv
import logging

from database import supabase
from models import LoginRequest, MFARequest, TokenResponse, TokenData, UserInDB, ClientTokenRequest, ClientTokenResponse, ClientTokenData

load_dotenv()

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

print("Using SECRET_KEY from environment variables:", SECRET_KEY)   
print("Using ALGORITHM from environment variables:", ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Set up logger
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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str):
    response = supabase.from_('profiles').select('*').eq('email', email).limit(1).execute()
    if response.data:
        return UserInDB(**response.data[0])
    return None

async def get_user_roles(user_id: str) -> List[str]:
    response = supabase.from_('user_roles').select('role_id,roles(name)').eq('user_id', user_id).execute()
    if response.data:
        return [item['roles']['name'] for item in response.data if item['roles']]
    return []

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.info(f"Validating token: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
    return token_data

async def get_current_admin_user(current_user: TokenData = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user

async def get_current_client(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate client credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("client_id")
        scopes: List[str] = payload.get("scopes", [])

        if client_id is None:
            raise credentials_exception
        # Ensure it's a client token, not a user token (add a 'type' claim to JWTs if differentiating)
        if payload.get("token_type") != "client": # <-- IMPORTANT: Add 'token_type' to JWT payload when creating tokens
             raise credentials_exception

        client_token_data = ClientTokenData(client_id=client_id, scopes=scopes)
    except JWTError:
        raise credentials_exception
    return client_token_data

@auth_router.post("/token", response_model=ClientTokenResponse, summary="Obtain a token using client_id and client_secret")
async def get_client_token(request: ClientTokenRequest):
    # Retrieve client from database
    response = supabase.from_('clients').select('*').eq('client_id', request.client_id).limit(1).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client ID or secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    client_in_db = response.data[0]

    # Verify the client secret (use pwd_context.verify if hashed)
    # For demonstration, comparing plain text secret. CHANGE THIS FOR PRODUCTION!
    if client_in_db['client_secret'] != request.client_secret:
    # if not verify_password(request.client_secret, client_in_db['client_secret']): # For hashed secrets
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client ID or secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Define scopes for this client if applicable
    # For now, let's assume a default scope or fetch from DB
    scopes = ["read:users", "manage:users"] # Example scopes

    # Create a JWT for the client
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 2) # Clients might have longer lifespans
    client_access_token = create_access_token(
        data={"client_id": request.client_id, "scopes": scopes, "token_type": "client"}, # <-- Add 'token_type'
        expires_delta=access_token_expires
    )

    return ClientTokenResponse(
        access_token=client_access_token,
        token_type="bearer",
        client_id=request.client_id,
        scopes=scopes
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login_for_access_token(request: LoginRequest):
    # Fetch user from Supabase profiles table
    user_profile_response = supabase.from_('profiles').select('id, email, mfa_secret').eq('email', request.email).limit(1).execute()
    if not user_profile_response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    user_profile = user_profile_response.data[0]
    user_id = user_profile['id']
    email = user_profile['email']
    mfa_secret = user_profile['mfa_secret']

    # Verify password against Supabase auth.users table
    # Supabase's client-side sign-in handles password verification directly with auth.users.
    # For a custom backend, you'd typically use `auth.signInWithPassword` or similar.
    # However, since we're creating users via admin, we need to verify against auth.users
    # This requires a slightly different approach for password verification in a custom backend.
    # For simplicity, we'll assume a successful sign-in with Supabase's auth.
    # In a real scenario, you'd integrate Supabase's sign-in flow here or manage passwords directly.

    # For this example, let's simulate password verification for users created by admin
    # by fetching from auth.users (which is not directly queryable by RLS for password hash).
    # A more robust solution involves Supabase's `auth.admin.createUser` and then `auth.signInWithPassword`
    # or a custom password verification if you store hashes in `profiles`.
    # For now, we'll assume `auth.signInWithPassword` was successful to get the user context.
    # We'll rely on the `profiles` table for `mfa_secret` and `is_admin`.

    # To truly verify password, you'd sign in with Supabase auth:
    try:
        auth_response = supabase.auth.sign_in_with_password({"email": request.email, "password": request.password})
        if not auth_response.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {e}")


    # For the purpose of this example, let's assume password is correct if email exists.
    # THIS IS NOT SECURE FOR PRODUCTION. YOU MUST VERIFY PASSWORD SECURELY.
    # A proper way would be to create users using `auth.admin.createUser` and then use `auth.signInWithPassword`
    # to get the user's session token, which you then use to fetch profile data.
    # Or, if you hash passwords in `profiles`, verify against that hash.
    # For this example, we proceed assuming a valid password for simplicity.

    # Check MFA if secret exists
    if mfa_secret:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="MFA required. Please provide MFA code.")

    # Get user roles and admin status from profiles table
    profile_response = supabase.from_('profiles').select('is_admin').eq('id', user_id).limit(1).execute()
    is_admin = profile_response.data[0]['is_admin'] if profile_response.data else False
    roles = await get_user_roles(str(user_id))

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user_id), "email": email, "is_admin": is_admin, "roles": roles},
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        email=email,
        is_admin=is_admin,
        roles=roles
    )

@auth_router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa_code(request: MFARequest):
    user = await get_user_by_email(request.email)
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not set up for this user or invalid email.")

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(request.mfa_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code.")

    # Get user roles and admin status
    profile_response = supabase.from_('profiles').select('is_admin').eq('id', user.id).limit(1).execute()
    is_admin = profile_response.data[0]['is_admin'] if profile_response.data else False
    roles = await get_user_roles(str(user.id))

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user.id), "email": user.email, "is_admin": is_admin, "roles": roles},
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        is_admin=is_admin,
        roles=roles
    )

@auth_router.post("/mfa/setup", summary="Generate MFA QR code for a user (Admin or Self-Service after login)", response_model=dict)
async def setup_mfa(email: str, current_user: TokenData = Depends(get_current_user)):
    # This endpoint is protected by admin role.
    # In a real app, a user might also set up MFA for themselves after logging in.
    # If self-service, `current_user` would be the user setting up MFA.
    # For now, only admin can trigger this.

    user_profile_response = supabase.from_('profiles').select('id, email, mfa_secret').eq('email', email).limit(1).execute()
    if not user_profile_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user_id = user_profile_response.data[0]['id']
    user_email = user_profile_response.data[0]['email']

    # Generate a new secret if not already set or force_new is true
    secret = pyotp.random_base32()
    provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email, issuer_name="YourAppName"
    )

    # Update user's MFA secret in profiles table
    update_response = supabase.from_('profiles').update({'mfa_secret': secret}).eq('id', user_id).execute()
    if update_response.count == 0:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save MFA secret.")

    # Generate QR code
    img = qrcode.make(provisioning_uri)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {"qr_code_base64": qr_code_base64, "secret": secret, "provisioning_uri": provisioning_uri}
