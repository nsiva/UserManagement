from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import base64
import secrets
import logging
from uuid import UUID

from database import get_repository
from models import (
    AuthorizationRequest, TokenExchangeRequest, OAuthTokenResponse,
    TokenData, OAuthClientCreate, OAuthClientUpdate, OAuthClientInDB
)
from routers.auth import get_current_user, get_current_user_optional, create_access_token, get_user_roles, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)
oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])

def generate_authorization_code() -> str:
    """Generate a cryptographically secure authorization code."""
    return secrets.token_urlsafe(32)

def verify_code_challenge(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """Verify PKCE code challenge against code verifier."""
    if method == "S256":
        # Base64url-encode(SHA256(code_verifier))
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        return challenge == code_challenge
    elif method == "plain":
        return code_verifier == code_challenge
    else:
        return False

async def get_oauth_client(client_id: str):
    """Get OAuth client by client_id."""
    try:
        repo = get_repository()
        client_data = await repo.get_oauth_client_by_id(client_id)
        if client_data:
            return client_data
        return None
    except Exception as e:
        logger.error(f"Error fetching OAuth client {client_id}: {e}")
        return None

def is_redirect_uri_allowed(redirect_uri: str, allowed_uris: list) -> bool:
    """Check if redirect URI is in the allowed list."""
    return redirect_uri in allowed_uris

@oauth_router.get("/authorize")
async def authorize(
    request: Request,
    response_type: str = Query(..., description="Must be 'code'"),
    client_id: str = Query(..., description="OAuth client ID"),
    redirect_uri: str = Query(..., description="Callback URL"),
    code_challenge: str = Query(..., description="PKCE code challenge"),
    code_challenge_method: str = Query(default="S256", description="PKCE method"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    access_token: Optional[str] = Query(None, description="JWT access token from login")
):
    """
    OAuth 2.0 Authorization Endpoint with PKCE.
    
    This endpoint handles the authorization request from external applications.
    If user is not authenticated, redirects to login with return URL.
    If authenticated, generates authorization code and redirects back to client.
    """
    try:
        # Validate request parameters
        if response_type != "code":
            logger.warning(f"Invalid response_type: {response_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid response_type. Must be 'code'"
            )

        if code_challenge_method != "S256":
            logger.warning(f"Unsupported code_challenge_method: {code_challenge_method}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported code_challenge_method. Only S256 is supported"
            )

        # Validate client
        client = await get_oauth_client(client_id)
        if not client or not client.get('is_active', False):
            logger.warning(f"Invalid or inactive OAuth client: {client_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_id"
            )

        # Validate redirect URI
        if not is_redirect_uri_allowed(redirect_uri, client.get('redirect_uris', [])):
            logger.warning(f"Invalid redirect_uri {redirect_uri} for client {client_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect_uri"
            )

        # Check for authentication via access_token parameter or Authorization header
        current_user = None
        
        # First, try to get token from query parameter
        if access_token:
            logger.info(f"OAuth authorize - Found access_token parameter")
            try:
                # Import JWT here to avoid circular import
                from jose import jwt, JWTError
                from routers.auth import CLIENT_JWT_SECRET, ALGORITHM
                
                payload = jwt.decode(access_token, CLIENT_JWT_SECRET, algorithms=[ALGORITHM])
                user_id = payload.get("user_id")
                email = payload.get("email")
                is_admin = payload.get("is_admin", False)
                roles = payload.get("roles", [])
                
                if user_id and email:
                    current_user = TokenData(user_id=user_id, email=email, is_admin=is_admin, roles=roles)
                    logger.info(f"User authenticated via query parameter for OAuth: {email}")
            except (JWTError, ImportError) as e:
                logger.warning(f"Token validation failed in OAuth authorize (query param): {e}")
        
        # If no token in query parameter, try Authorization header
        if not current_user:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    from jose import jwt, JWTError
                    from routers.auth import CLIENT_JWT_SECRET, ALGORITHM
                    
                    payload = jwt.decode(token, CLIENT_JWT_SECRET, algorithms=[ALGORITHM])
                    user_id = payload.get("user_id")
                    email = payload.get("email")
                    is_admin = payload.get("is_admin", False)
                    roles = payload.get("roles", [])
                    
                    if user_id and email:
                        current_user = TokenData(user_id=user_id, email=email, is_admin=is_admin, roles=roles)
                        logger.info(f"User authenticated via Authorization header for OAuth: {email}")
                except (JWTError, ImportError) as e:
                    logger.warning(f"Token validation failed in OAuth authorize (header): {e}")

        logger.info(f"OAuth authorize - Current user: {current_user.email if current_user else 'None'}")

        # If user is not authenticated, redirect to login with return URL
        if not current_user:
            # Build the return URL to come back here after login
            query_params = {
                'response_type': response_type,
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'code_challenge': code_challenge,
                'code_challenge_method': code_challenge_method
            }
            if state:
                query_params['state'] = state
            
            return_url = f"http://localhost:8001/oauth/authorize?{urlencode(query_params)}"
            from urllib.parse import quote
            login_url = f"http://localhost:4201/login?return_url={quote(return_url)}"
            
            logger.info(f"User not authenticated, redirecting to login for client {client_id}")
            return RedirectResponse(url=login_url, status_code=302)

        # Generate authorization code
        auth_code = generate_authorization_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)  # 10 minute expiry

        # Store authorization code
        repo = get_repository()
        code_data = {
            'code': auth_code,
            'client_id': client_id,
            'user_id': str(current_user.user_id),
            'redirect_uri': redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
            'expires_at': expires_at,
            'used': False
        }

        success = await repo.create_authorization_code(code_data)
        if not success:
            logger.error(f"Failed to store authorization code for user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authorization code"
            )

        # Build callback URL
        callback_params = {'code': auth_code}
        if state:
            callback_params['state'] = state

        callback_url = f"{redirect_uri}?{urlencode(callback_params)}"
        
        logger.info(f"Authorization code generated for user {current_user.email}, client {client_id}")
        return RedirectResponse(url=callback_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in authorize endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@oauth_router.post("/token", response_model=OAuthTokenResponse)
async def token_exchange(request: TokenExchangeRequest):
    """
    OAuth 2.0 Token Exchange Endpoint with PKCE verification.
    
    External applications call this endpoint to exchange authorization code
    for access token using PKCE code verifier.
    """
    try:
        # Validate grant type
        if request.grant_type != "authorization_code":
            logger.warning(f"Invalid grant_type: {request.grant_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid grant_type. Must be 'authorization_code'"
            )

        # Validate client
        client = await get_oauth_client(request.client_id)
        if not client or not client.get('is_active', False):
            logger.warning(f"Invalid or inactive OAuth client: {request.client_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_id"
            )

        # Validate redirect URI
        if not is_redirect_uri_allowed(request.redirect_uri, client.get('redirect_uris', [])):
            logger.warning(f"Invalid redirect_uri {request.redirect_uri} for client {request.client_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect_uri"
            )

        # Get and validate authorization code
        repo = get_repository()
        code_record = await repo.get_authorization_code(request.code)
        
        if not code_record:
            logger.warning(f"Invalid authorization code: {request.code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired authorization code"
            )

        # Check if code is already used
        if code_record.get('used', False):
            logger.warning(f"Authorization code already used: {request.code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code already used"
            )

        # Check if code is expired
        expires_at = code_record.get('expires_at')
        if expires_at and datetime.now(timezone.utc) > expires_at:
            logger.warning(f"Authorization code expired: {request.code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code expired"
            )

        # Validate client_id matches
        if code_record.get('client_id') != request.client_id:
            logger.warning(f"Client ID mismatch for code {request.code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_id for this authorization code"
            )

        # Validate redirect_uri matches
        if code_record.get('redirect_uri') != request.redirect_uri:
            logger.warning(f"Redirect URI mismatch for code {request.code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect_uri for this authorization code"
            )

        # Verify PKCE code challenge
        code_challenge = code_record.get('code_challenge')
        code_challenge_method = code_record.get('code_challenge_method', 'S256')
        
        if not verify_code_challenge(request.code_verifier, code_challenge, code_challenge_method):
            logger.warning(f"PKCE verification failed for code {request.code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code_verifier"
            )

        # Mark code as used
        await repo.mark_authorization_code_used(request.code)

        # Get user information  
        user_id_raw = code_record.get('user_id')
        # Handle both string and UUID types
        user_id = user_id_raw if isinstance(user_id_raw, UUID) else UUID(user_id_raw)
        user_data = await repo.get_user_by_id(user_id)
        if not user_data:
            logger.error(f"User not found for authorization code: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User not found"
            )

        # Get user roles
        roles = await get_user_roles(str(user_id))

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": str(user_id),
                "email": user_data['email'],
                "is_admin": user_data.get('is_admin', False),
                "roles": roles,
                "client_id": request.client_id  # Include client_id in token for auditing
            },
            expires_delta=access_token_expires
        )

        logger.info(f"Access token issued for user {user_data['email']}, client {request.client_id}")
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user_id=str(user_id),
            email=user_data['email'],
            first_name=user_data.get('first_name'),
            middle_name=user_data.get('middle_name'),
            last_name=user_data.get('last_name'),
            is_admin=user_data.get('is_admin', False),
            roles=roles
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in token_exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Admin endpoints for OAuth client management

@oauth_router.post("/clients", response_model=OAuthClientInDB, summary="Create OAuth client (Admin only)")
async def create_oauth_client(
    client_data: OAuthClientCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new OAuth client for external applications."""
    try:
        # Check admin permissions
        admin_roles = ['admin', 'super_user', 'firm_admin', 'group_admin']
        has_admin_role = any(role in current_user.roles for role in admin_roles)
        
        if not current_user.is_admin and not has_admin_role:
            logger.warning(f"Non-admin user {current_user.email} tried to create OAuth client")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        repo = get_repository()
        
        # Check if client_id already exists
        existing_client = await repo.get_oauth_client_by_id(client_data.client_id)
        if existing_client:
            logger.warning(f"OAuth client with ID {client_data.client_id} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client ID already exists"
            )

        # Create client
        client_record = await repo.create_oauth_client({
            'client_id': client_data.client_id,
            'client_name': client_data.client_name,
            'redirect_uris': client_data.redirect_uris,
            'is_active': True
        })

        if not client_record:
            logger.error(f"Failed to create OAuth client {client_data.client_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create OAuth client"
            )

        logger.info(f"OAuth client {client_data.client_id} created by {current_user.email}")
        return OAuthClientInDB(**client_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_oauth_client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@oauth_router.get("/clients", response_model=list[OAuthClientInDB], summary="List OAuth clients (Admin only)")
async def list_oauth_clients(current_user: TokenData = Depends(get_current_user)):
    """List all OAuth clients."""
    try:
        # Check admin permissions
        admin_roles = ['admin', 'super_user', 'firm_admin', 'group_admin']
        has_admin_role = any(role in current_user.roles for role in admin_roles)
        
        if not current_user.is_admin and not has_admin_role:
            logger.warning(f"Non-admin user {current_user.email} tried to list OAuth clients")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        repo = get_repository()
        clients = await repo.list_oauth_clients()
        
        return [OAuthClientInDB(**client) for client in clients]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_oauth_clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )