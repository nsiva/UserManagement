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

# Pydantic models
class UserSession(BaseModel):
    user_id: str
    email: str
    roles: list[str]
    authenticated_at: datetime
    
class LoginRequest(BaseModel):
    return_url: Optional[str] = None

class AuthStatus(BaseModel):
    authenticated: bool
    user: Optional[Dict[str, Any]] = None
    login_url: Optional[str] = None

# In-memory session store (in production, use Redis or database)
user_sessions: Dict[str, UserSession] = {}

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
    Initiate login by redirecting to User Management system
    """
    try:
        # Build the return URL for where UserManagement should redirect back to
        return_url = request.return_url or f"{EXTERNAL_APP_BASE}/dashboard"
        
        # Create the UserManagement login URL with redirect_uri parameter
        # Let the browser handle URL encoding naturally
        login_url = f"{USER_MGMT_WEB_BASE}/login?redirect_uri={return_url}"
        
        logger.info(f"Return URL: {return_url}")
        logger.info(f"Initiating login redirect to: {login_url}")
        
        return {
            "success": True,
            "login_url": login_url,
            "message": "Redirect to User Management for authentication"
        }
        
    except Exception as e:
        logger.error(f"Error initiating login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/status")
async def get_auth_status(request: Request):
    """
    Check authentication status of current session
    """
    try:
        # In a real application, you would check session cookies or tokens
        # For this demo, we'll use a simple session store
        
        # Get session ID from headers or cookies (simplified)
        session_id = request.headers.get("X-Session-ID")
        
        if session_id and session_id in user_sessions:
            session = user_sessions[session_id]
            return AuthStatus(
                authenticated=True,
                user={
                    "id": session.user_id,
                    "email": session.email,
                    "roles": session.roles,
                    "authenticated_at": session.authenticated_at.isoformat()
                }
            )
        
        # Not authenticated - provide login URL
        login_url = f"{USER_MGMT_WEB_BASE}/login?redirect_uri={EXTERNAL_APP_BASE}/dashboard"
        
        return AuthStatus(
            authenticated=False,
            login_url=login_url
        )
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/callback")
async def auth_callback(request: Request):
    """
    Handle callback from User Management after successful authentication
    This would typically receive tokens or user info
    """
    try:
        # In a real implementation, you would:
        # 1. Validate the callback (check tokens, signatures, etc.)
        # 2. Extract user information
        # 3. Create a local session
        
        # For this demo, we'll simulate receiving user info
        body = await request.json()
        
        # Create a session (simplified)
        session_id = f"session_{datetime.now().timestamp()}"
        user_session = UserSession(
            user_id=body.get("user_id", "demo_user"),
            email=body.get("email", "user@example.com"),
            roles=body.get("roles", ["user"]),
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
        logger.error(f"Error in auth callback: {e}")
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