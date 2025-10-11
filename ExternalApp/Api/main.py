from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import requests
from datetime import datetime
import logging
import urllib.parse
import hashlib
import base64
import secrets
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ExternalApp API",
    description="Test application demonstrating User Management integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4202",  # ExternalApp frontend
        "http://localhost:4201",  # UserManagement frontend
        "http://127.0.0.1:4202",
        "http://127.0.0.1:4201",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
USER_MGMT_WEB_BASE = "http://localhost:4201"
USER_MGMT_API_BASE = "http://localhost:8001"
EXTERNAL_APP_BASE = "http://localhost:4202"

# OAuth PKCE Configuration
OAUTH_CLIENT_ID = "test_external_app"
OAUTH_REDIRECT_URI = "http://localhost:8002/oauth/callback"
OAUTH_AUTHORIZE_URL = f"{USER_MGMT_API_BASE}/oauth/authorize"
OAUTH_TOKEN_URL = f"{USER_MGMT_API_BASE}/oauth/token"
USER_PROFILE_URL = f"{USER_MGMT_API_BASE}/profiles/me"

# Pydantic models
class UserSession(BaseModel):
    user_id: str
    email: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: list[str]
    is_admin: bool = False
    access_token: str
    authenticated_at: datetime
    
class LoginRequest(BaseModel):
    return_url: Optional[str] = None

class AuthStatus(BaseModel):
    authenticated: bool
    user: Optional[Dict[str, Any]] = None
    login_url: Optional[str] = None

class PKCESession(BaseModel):
    state: str
    code_verifier: str
    code_challenge: str
    redirect_uri: str
    created_at: datetime

# In-memory stores (in production, use Redis or database)
user_sessions: Dict[str, UserSession] = {}
pkce_sessions: Dict[str, PKCESession] = {}  # state -> PKCESession

# PKCE Helper Functions
def generate_code_verifier() -> str:
    """Generate PKCE code verifier (43-128 characters)."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge (SHA256 hash of verifier)."""
    digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

def generate_state() -> str:
    """Generate random state parameter for CSRF protection."""
    return secrets.token_urlsafe(16)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ExternalApp API is running",
        "version": "1.0.0",
        "user_management_integration": True
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/auth/login")
async def initiate_login(request: LoginRequest):
    """
    Initiate OAuth PKCE login flow with User Management system
    """
    try:
        # Generate PKCE parameters
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state()
        
        # Store PKCE session
        redirect_uri = request.return_url or f"{EXTERNAL_APP_BASE}/dashboard"
        pkce_session = PKCESession(
            state=state,
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            redirect_uri=redirect_uri,
            created_at=datetime.now()
        )
        pkce_sessions[state] = pkce_session
        
        # Build OAuth authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': OAUTH_CLIENT_ID,
            'redirect_uri': OAUTH_REDIRECT_URI,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': state
        }
        
        auth_url = f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(auth_params)}"
        
        logger.info(f"PKCE session created with state: {state}")
        logger.info(f"Redirect URI after auth: {redirect_uri}")
        logger.info(f"OAuth authorization URL: {auth_url}")
        
        return {
            "success": True,
            "login_url": auth_url,
            "message": "Redirect to User Management for OAuth authentication",
            "state": state  # Frontend can use this to track the flow
        }
        
    except Exception as e:
        logger.error(f"Error initiating OAuth login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/status")
async def get_auth_status(request: Request, session_id: Optional[str] = None):
    """
    Check authentication status of current session
    """
    try:
        # Get session ID from query parameter, headers, or cookies
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        if session_id and session_id in user_sessions:
            session = user_sessions[session_id]
            full_name_parts = [session.first_name, session.middle_name, session.last_name]
            full_name = " ".join(part for part in full_name_parts if part)
            
            return AuthStatus(
                authenticated=True,
                user={
                    "id": session.user_id,
                    "email": session.email,
                    "first_name": session.first_name,
                    "middle_name": session.middle_name,
                    "last_name": session.last_name,
                    "full_name": full_name,
                    "roles": session.roles,
                    "is_admin": session.is_admin,
                    "authenticated_at": session.authenticated_at.isoformat()
                }
            )
        
        # Not authenticated - provide OAuth login URL
        return AuthStatus(
            authenticated=False,
            login_url=None  # Frontend will call /auth/login to get proper OAuth URL
        )
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str, error: Optional[str] = None):
    """
    Handle OAuth callback from User Management system
    """
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        # Validate state parameter
        if state not in pkce_sessions:
            logger.error(f"Invalid state parameter: {state}")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        pkce_session = pkce_sessions[state]
        
        # Exchange authorization code for access token
        token_request = {
            'grant_type': 'authorization_code',
            'client_id': OAUTH_CLIENT_ID,
            'code': code,
            'redirect_uri': OAUTH_REDIRECT_URI,
            'code_verifier': pkce_session.code_verifier
        }
        
        logger.info(f"Exchanging authorization code for access token")
        token_response = requests.post(OAUTH_TOKEN_URL, json=token_request)
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            logger.error("No access token received")
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user profile using access token
        profile_headers = {'Authorization': f'Bearer {access_token}'}
        profile_response = requests.get(USER_PROFILE_URL, headers=profile_headers)
        
        if profile_response.status_code != 200:
            logger.error(f"Failed to get user profile: {profile_response.status_code}")
            raise HTTPException(status_code=400, detail="Failed to get user profile")
        
        profile_data = profile_response.json()
        
        # Create user session
        session_id = f"session_{datetime.now().timestamp()}"
        user_session = UserSession(
            user_id=token_data.get('user_id'),
            email=token_data.get('email'),
            first_name=token_data.get('first_name'),
            middle_name=token_data.get('middle_name'),
            last_name=token_data.get('last_name'),
            roles=token_data.get('roles', []),
            is_admin=token_data.get('is_admin', False),
            access_token=access_token,
            authenticated_at=datetime.now()
        )
        
        user_sessions[session_id] = user_session
        
        # Clean up PKCE session
        del pkce_sessions[state]
        
        # Redirect to original destination
        redirect_url = f"{pkce_session.redirect_uri}?session_id={session_id}&auth_success=true"
        
        logger.info(f"OAuth callback successful for user: {user_session.email}")
        logger.info(f"Redirecting to: {redirect_url}")
        
        return JSONResponse(
            status_code=302,
            headers={"Location": redirect_url},
            content={"message": "Redirecting to application"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/callback")
async def auth_callback_legacy(request: Request):
    """
    Legacy callback endpoint for backward compatibility
    """
    try:
        body = await request.json()
        
        # Create a session (simplified)
        session_id = f"session_{datetime.now().timestamp()}"
        user_session = UserSession(
            user_id=body.get("user_id", "demo_user"),
            email=body.get("email", "user@example.com"),
            first_name=body.get("first_name"),
            middle_name=body.get("middle_name"),
            last_name=body.get("last_name"),
            roles=body.get("roles", ["user"]),
            is_admin=body.get("is_admin", False),
            access_token=body.get("access_token", "legacy_token"),
            authenticated_at=datetime.now()
        )
        
        user_sessions[session_id] = user_session
        
        return {
            "success": True,
            "session_id": session_id,
            "user": {
                "id": user_session.user_id,
                "email": user_session.email,
                "roles": user_session.roles
            },
            "message": "Authentication successful"
        }
        
    except Exception as e:
        logger.error(f"Error in legacy auth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/data")
async def get_dashboard_data():
    """
    Protected endpoint that returns dashboard data
    In a real app, this would check authentication
    """
    try:
        return {
            "dashboard": {
                "title": "ExternalApp Dashboard",
                "message": "Welcome to the external application!",
                "features": [
                    "User Management Integration",
                    "Secure Authentication",
                    "MFA Support",
                    "Seamless Redirect Flow"
                ],
                "stats": {
                    "total_users": 42,
                    "active_sessions": len(user_sessions),
                    "last_login": datetime.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/logout")
async def logout(request: Request):
    """
    Handle logout - clear local session
    """
    try:
        session_id = request.headers.get("X-Session-ID")
        
        if session_id and session_id in user_sessions:
            del user_sessions[session_id]
            logger.info(f"Session {session_id} logged out")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)