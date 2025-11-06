# External Application Integration Guide for UserManagement System

This guide provides step-by-step instructions for integrating external applications with the UserManagement system using OAuth 2.0 with PKCE (Proof Key for Code Exchange) and theme support.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Step-by-Step Integration](#step-by-step-integration)
5. [Frontend Implementation](#frontend-implementation)
6. [Backend Implementation](#backend-implementation)
7. [Theme Integration](#theme-integration)
8. [Security Considerations](#security-considerations)
9. [Testing and Debugging](#testing-and-debugging)
10. [Common Issues](#common-issues)

## Overview

The UserManagement system provides centralized authentication for multiple external applications. External apps redirect users to UserManagement for login, then receive authenticated sessions back through OAuth 2.0 flow.

### Key Features
- **OAuth 2.0 with PKCE**: Secure authorization flow
- **Theme Support**: Custom styling for login pages
- **Session Management**: Centralized user sessions
- **MFA Support**: Multi-factor authentication
- **Role-based Access**: User permissions and roles

## Prerequisites

### UserManagement System Requirements
- UserManagement API running (default: `http://localhost:8001`)
- UserManagement WebUI running (default: `http://localhost:4201`)
- Database with OAuth client configuration

### External Application Requirements
- Web application (any framework)
- Backend API capability
- Frontend with redirect handling
- HTTPS support (production)

## Architecture Overview

```
External App (4202) ←→ External API (8002) ←→ UserManagement API (8001)
                                              ↑
                      UserManagement WebUI (4201)
```

### Flow Summary
1. **User initiates login** → External App Frontend
2. **Theme selection** → Stored in localStorage
3. **Login request** → External App Backend
4. **OAuth URL construction** → With theme parameter
5. **Redirect to UserManagement** → Themed login page
6. **User authentication** → UserManagement system
7. **OAuth callback** → External App Backend
8. **Token exchange** → Access token retrieval
9. **Session creation** → Local user session
10. **Dashboard access** → Authenticated user

## Step-by-Step Integration

### Step 1: Register OAuth Client

Register your external application in the UserManagement database:

```sql
INSERT INTO aaa_clients (client_id, name, redirect_uris, is_active) VALUES (
    'your_external_app',
    'Your External App Name',
    '["http://localhost:8002/oauth/callback"]',
    true
);
```

### Step 2: Configure Environment Variables

```bash
# External App Configuration
USER_MGMT_WEB_BASE="http://localhost:4201"
USER_MGMT_API_BASE="http://localhost:8001"
EXTERNAL_APP_BASE="http://localhost:4202"
OAUTH_CLIENT_ID="your_external_app"
OAUTH_REDIRECT_URI="http://localhost:8002/oauth/callback"
```

### Step 3: Set Up CORS

Configure CORS in your external app backend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4202",  # External App Frontend
        "http://localhost:4201",  # UserManagement Frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Frontend Implementation

### Theme Selector Component

Create a theme selector that stores the selected theme URL:

```typescript
// theme-selector.component.ts
export class ThemeSelectorComponent {
  selectedThemeUrl = '';
  
  themeOptions = [
    { name: 'Orange', url: 'http://localhost:4202/assets/PRODUCTION_ORANGE_THEME.css' },
    { name: 'Green', url: 'http://localhost:4202/assets/PRODUCTION_GREEN_THEME.css' },
    { name: 'Blue', url: 'http://localhost:4202/assets/PRODUCTION_BLUE_THEME.css' },
    { name: 'Dark', url: 'http://localhost:4202/assets/PRODUCTION_DARK_THEME.css' },
    { name: 'Purple', url: 'http://localhost:4202/assets/PRODUCTION_PURPLE_THEME.css' }
  ];

  onThemeUrlChange(): void {
    if (this.selectedThemeUrl) {
      this.themeService.setSelectedThemeUrl(this.selectedThemeUrl);
    }
  }
}
```

```html
<!-- Theme selector template -->
<select [(ngModel)]="selectedThemeUrl" (change)="onThemeUrlChange()">
  <option value="">Select Theme</option>
  <option *ngFor="let theme of themeOptions" [value]="theme.url">
    {{ theme.name }}
  </option>
</select>
```

### Theme Service

```typescript
// theme.service.ts
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private selectedThemeUrlSubject = new BehaviorSubject<string>('');
  
  get selectedThemeUrl$(): Observable<string> {
    return this.selectedThemeUrlSubject.asObservable();
  }
  
  get selectedThemeUrl(): string {
    return this.selectedThemeUrlSubject.value;
  }
  
  setSelectedThemeUrl(url: string): void {
    this.selectedThemeUrlSubject.next(url);
    localStorage.setItem('selected-theme-url', url);
  }
  
  private getStoredThemeUrl(): string {
    return localStorage.getItem('selected-theme-url') || '';
  }
}
```

### Authentication Service

```typescript
// auth.service.ts
@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = environment.apiUrl;
  
  initiateLogin(returnUrl?: string, styleUrl?: string): Observable<LoginResponse> {
    const body: any = {};
    if (returnUrl) body.return_url = returnUrl;
    if (styleUrl) body.style_url = styleUrl;
    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, body);
  }
  
  login(): void {
    const returnUrl = `${window.location.origin}/dashboard`;
    const selectedThemeUrl = this.themeService.selectedThemeUrl;
    
    this.initiateLogin(returnUrl, selectedThemeUrl).subscribe({
      next: (response) => {
        if (response.success && response.login_url) {
          window.location.href = response.login_url;
        }
      },
      error: (error) => {
        console.error('Login failed:', error);
      }
    });
  }
}
```

## Backend Implementation

### Required Dependencies

```python
# requirements.txt
fastapi
uvicorn
pydantic
requests
python-multipart
```

### Data Models

```python
# models.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class LoginRequest(BaseModel):
    return_url: Optional[str] = None
    style_url: Optional[str] = None

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

class PKCESession(BaseModel):
    state: str
    code_verifier: str
    code_challenge: str
    redirect_uri: str
    created_at: datetime
```

### PKCE Helper Functions

```python
# pkce_utils.py
import hashlib
import base64
import secrets

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
```

### Login Endpoint

```python
# main.py
@app.post("/auth/login")
async def initiate_login(request: LoginRequest):
    """
    Initiate OAuth PKCE login flow with UserManagement system
    """
    try:
        # 1. Generate PKCE parameters
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state()
        
        # 2. Store PKCE session for later validation
        redirect_uri = request.return_url or f"{EXTERNAL_APP_BASE}/dashboard"
        pkce_session = PKCESession(
            state=state,
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            redirect_uri=redirect_uri,
            created_at=datetime.now()
        )
        pkce_sessions[state] = pkce_session
        
        # 3. Build OAuth authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': OAUTH_CLIENT_ID,
            'redirect_uri': OAUTH_REDIRECT_URI,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': state
        }
        
        oauth_url = f"{USER_MGMT_API_BASE}/oauth/authorize?{urllib.parse.urlencode(auth_params)}"
        
        # 4. Build final login URL with theme parameter
        login_params = {}
        
        # Add styleUrl as first parameter if provided
        if request.style_url:
            login_params['styleUrl'] = request.style_url
            
        login_params['return_url'] = oauth_url
        
        # 5. Construct final login URL for UserManagement frontend
        auth_url = f"{USER_MGMT_WEB_BASE}/login?{urllib.parse.urlencode(login_params)}"
        
        return {
            "success": True,
            "login_url": auth_url,
            "message": "Redirect to UserManagement for OAuth authentication",
            "state": state
        }
        
    except Exception as e:
        logger.error(f"Error initiating OAuth login: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### OAuth Callback Endpoint

```python
@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str, error: Optional[str] = None):
    """
    Handle OAuth callback from UserManagement system
    """
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        # 1. Validate state parameter
        if state not in pkce_sessions:
            logger.error(f"Invalid state parameter: {state}")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        pkce_session = pkce_sessions[state]
        
        # 2. Exchange authorization code for access token
        token_request = {
            'grant_type': 'authorization_code',
            'client_id': OAUTH_CLIENT_ID,
            'code': code,
            'redirect_uri': OAUTH_REDIRECT_URI,
            'code_verifier': pkce_session.code_verifier
        }
        
        token_response = requests.post(f"{USER_MGMT_API_BASE}/oauth/token", json=token_request)
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.status_code}")
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # 3. Get user profile using access token
        profile_headers = {'Authorization': f'Bearer {access_token}'}
        profile_response = requests.get(f"{USER_MGMT_API_BASE}/profiles/me", headers=profile_headers)
        
        if profile_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user profile")
        
        # 4. Create user session
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
        
        # 5. Clean up PKCE session
        del pkce_sessions[state]
        
        # 6. Redirect to original destination
        redirect_url = f"{pkce_session.redirect_uri}?session_id={session_id}&auth_success=true"
        
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
```

### Session Validation

```python
@app.get("/auth/status")
async def get_auth_status(request: Request, session_id: Optional[str] = None):
    """
    Check authentication status of current session
    """
    try:
        # Get session ID from query parameter or headers
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        if session_id and session_id in user_sessions:
            session = user_sessions[session_id]
            return {
                "authenticated": True,
                "user": {
                    "id": session.user_id,
                    "email": session.email,
                    "first_name": session.first_name,
                    "middle_name": session.middle_name,
                    "last_name": session.last_name,
                    "roles": session.roles,
                    "is_admin": session.is_admin,
                    "authenticated_at": session.authenticated_at.isoformat()
                }
            }
        
        return {"authenticated": False}
        
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Theme Integration

### Theme URL Structure

Theme URLs should follow this pattern:
```
http://your-external-app-domain/assets/PRODUCTION_{THEME_NAME}_THEME.css
```

Example theme URLs:
```
http://localhost:4202/assets/PRODUCTION_ORANGE_THEME.css
http://localhost:4202/assets/PRODUCTION_GREEN_THEME.css
http://localhost:4202/assets/PRODUCTION_BLUE_THEME.css
http://localhost:4202/assets/PRODUCTION_DARK_THEME.css
http://localhost:4202/assets/PRODUCTION_PURPLE_THEME.css
```

### Theme CSS Files

Create theme CSS files in your external app's assets directory:

```css
/* PRODUCTION_ORANGE_THEME.css */
:root {
  --primary-color: #ff6b35;
  --secondary-color: #f7931e;
  --background-color: #fff5f0;
  --text-color: #2c1810;
}

/* Apply your theme styles here */
```

### Final Login URL Format

When a user selects a theme and initiates login, the final URL will be:

```
http://localhost:4201/login?styleUrl=http://localhost:4202/assets/PRODUCTION_PURPLE_THEME.css&return_url=http%3A//localhost%3A8001/oauth/authorize%3Fresponse_type%3Dcode%26client_id%3Dyour_external_app%26redirect_uri%3Dhttp%253A//localhost%253A8002/oauth/callback%26code_challenge%3D...%26code_challenge_method%3DS256%26state%3D...
```

## Security Considerations

### 1. PKCE Implementation
- Always use PKCE for OAuth flows
- Generate cryptographically secure random values
- Validate state parameters to prevent CSRF

### 2. HTTPS in Production
```python
# Use HTTPS in production
OAUTH_REDIRECT_URI = "https://your-app.com/oauth/callback"
USER_MGMT_API_BASE = "https://usermgmt.com"
```

### 3. Session Security
- Implement session expiration
- Use secure session storage
- Clear sessions on logout

### 4. CORS Configuration
- Restrict origins to known domains
- Don't use wildcard (*) in production

### 5. Error Handling
- Don't expose sensitive information in error messages
- Log security events for monitoring

## Testing and Debugging

### 1. Test OAuth Flow
```bash
# Test login initiation
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"return_url": "http://localhost:4202/dashboard", "style_url": "http://localhost:4202/assets/PRODUCTION_PURPLE_THEME.css"}'
```

### 2. Verify URL Construction
Check that the login URL contains:
- `styleUrl` parameter (first)
- Properly encoded `return_url`
- Valid OAuth parameters

### 3. Debug Session Storage
```python
# Add logging to track sessions
logger.info(f"Active sessions: {len(user_sessions)}")
logger.info(f"PKCE sessions: {len(pkce_sessions)}")
```

### 4. Monitor Network Traffic
Use browser dev tools to monitor:
- Redirect chains
- OAuth parameter passing
- Session cookie handling

## Common Issues

### 1. Theme URL Not Appearing
**Problem**: StyleUrl parameter missing from login URL
**Solution**: 
- Verify frontend is sending `style_url` in POST body
- Check backend `LoginRequest` model includes `style_url` field
- Ensure URL encoding is proper

### 2. OAuth Callback Fails
**Problem**: "Invalid state parameter" error
**Solution**:
- Check PKCE session storage
- Verify state parameter generation and validation
- Ensure session cleanup doesn't happen too early

### 3. Session Not Created
**Problem**: User authentication succeeds but no session created
**Solution**:
- Verify token exchange endpoint
- Check user profile retrieval
- Validate session storage logic

### 4. CORS Errors
**Problem**: Cross-origin requests blocked
**Solution**:
- Add all required origins to CORS middleware
- Include credentials in CORS config
- Check preflight request handling

### 5. Theme Not Applied
**Problem**: Theme CSS not loading in UserManagement
**Solution**:
- Verify theme CSS files are accessible
- Check URL encoding in styleUrl parameter
- Ensure UserManagement can access external CSS

## Deployment Checklist

### Development Environment
- [ ] OAuth client registered in database
- [ ] CORS configured for localhost
- [ ] Theme CSS files accessible
- [ ] Logging enabled for debugging

### Production Environment
- [ ] HTTPS enabled for all endpoints
- [ ] CORS restricted to production domains
- [ ] OAuth client configured with production URLs
- [ ] Session storage implemented (Redis/Database)
- [ ] Error monitoring configured
- [ ] Security headers implemented
- [ ] Rate limiting configured

## Example Application Structure

```
external-app/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── theme-selector/
│   │   │   │   └── header/
│   │   │   ├── services/
│   │   │   │   ├── auth.service.ts
│   │   │   │   └── theme.service.ts
│   │   │   └── guards/
│   │   │       └── auth.guard.ts
│   │   └── assets/
│   │       ├── PRODUCTION_ORANGE_THEME.css
│   │       ├── PRODUCTION_GREEN_THEME.css
│   │       ├── PRODUCTION_BLUE_THEME.css
│   │       ├── PRODUCTION_DARK_THEME.css
│   │       └── PRODUCTION_PURPLE_THEME.css
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── pkce_utils.py
│   └── requirements.txt
└── README.md
```

This guide provides a complete implementation reference for integrating external applications with the UserManagement system, including theme support and secure OAuth 2.0 authentication.