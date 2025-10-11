# External App Integration Guide

This guide provides step-by-step instructions for integrating external applications with the User Management authentication system using OAuth 2.0 PKCE (Proof Key for Code Exchange) flow.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Database Configuration](#database-configuration)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [OAuth Flow Documentation](#oauth-flow-documentation)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Overview

The User Management system provides secure authentication for external applications using OAuth 2.0 PKCE flow. This integration supports:

- ✅ **Secure Authentication**: OAuth 2.0 with PKCE for enhanced security
- ✅ **Multi-Factor Authentication**: Automatic MFA support if enabled for users
- ✅ **Role-Based Access**: User roles and permissions included in tokens
- ✅ **Session Management**: Proper logout handling across systems
- ✅ **Seamless Redirects**: Users are redirected back to the external app after authentication

## Prerequisites

### System Requirements
- **User Management API**: Running on `http://localhost:8001`
- **User Management Frontend**: Running on `http://localhost:4201`
- **External App Backend**: Your application's backend API
- **External App Frontend**: Your application's frontend

### Authentication Flow URLs
- **OAuth Authorization**: `http://localhost:8001/oauth/authorize`
- **Token Exchange**: `http://localhost:8001/oauth/token`
- **User Profile**: `http://localhost:8001/profiles/me`
- **Logout**: `http://localhost:8001/auth/logout`

## Database Configuration

### Step 1: Register Your OAuth Client

Insert your external application's OAuth client configuration into the `aaa_clients` table:

```sql
-- Insert OAuth client configuration for your external app
INSERT INTO aaa.aaa_clients (
    client_id,
    client_name, 
    redirect_uris,
    is_active,
    created_at,
    updated_at
) VALUES (
    'your_external_app_id',           -- Unique identifier for your app
    'Your External App Name',         -- Human-readable name
    ARRAY[
        'http://localhost:8002/oauth/callback',     -- Your backend OAuth callback
        'https://yourdomain.com/oauth/callback'     -- Production callback URL
    ],
    true,                             -- Enable the client
    NOW(),
    NOW()
);
```

### Step 2: Verify Client Registration

```sql
-- Verify your client was created successfully
SELECT 
    client_id,
    client_name,
    redirect_uris,
    is_active,
    created_at
FROM aaa.aaa_clients 
WHERE client_id = 'your_external_app_id';
```

### Example Client Configurations

```sql
-- Example: Test External App (Development)
INSERT INTO aaa.aaa_clients (
    client_id, client_name, redirect_uris, is_active, created_at, updated_at
) VALUES (
    'test_external_app',
    'Test External App',
    ARRAY['http://localhost:8002/oauth/callback'],
    true, NOW(), NOW()
);

-- Example: Production Web App
INSERT INTO aaa.aaa_clients (
    client_id, client_name, redirect_uris, is_active, created_at, updated_at
) VALUES (
    'prod_webapp_client',
    'Production Web Application',
    ARRAY[
        'https://myapp.example.com/oauth/callback',
        'https://staging.myapp.example.com/oauth/callback'
    ],
    true, NOW(), NOW()
);

-- Example: Mobile App Backend
INSERT INTO aaa.aaa_clients (
    client_id, client_name, redirect_uris, is_active, created_at, updated_at
) VALUES (
    'mobile_app_backend',
    'Mobile App Backend Service',
    ARRAY['https://api.mobileapp.com/auth/callback'],
    true, NOW(), NOW()
);
```

## Backend Implementation

### Step 1: Install Required Dependencies

**Python (FastAPI)**:
```bash
pip install fastapi uvicorn requests pydantic
```

**Node.js (Express)**:
```bash
npm install express axios cors
```

### Step 2: Configuration Constants

```python
# Python configuration
USER_MGMT_API_BASE = "http://localhost:8001"
OAUTH_CLIENT_ID = "your_external_app_id"  # Must match database entry
OAUTH_REDIRECT_URI = "http://localhost:8002/oauth/callback"  # Must match database
OAUTH_AUTHORIZE_URL = f"{USER_MGMT_API_BASE}/oauth/authorize"
OAUTH_TOKEN_URL = f"{USER_MGMT_API_BASE}/oauth/token"
USER_PROFILE_URL = f"{USER_MGMT_API_BASE}/profiles/me"
```

### Step 3: PKCE Helper Functions

```python
import hashlib
import base64
import secrets
from urllib.parse import urlencode

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

### Step 4: Initiate Login Endpoint

```python
@app.post("/auth/login")
async def initiate_login(return_url: Optional[str] = None):
    """Initiate OAuth PKCE login flow with User Management system"""
    try:
        # Generate PKCE parameters
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state()
        
        # Store PKCE session (use Redis/database in production)
        redirect_uri = return_url or "http://localhost:4202/dashboard"
        pkce_sessions[state] = {
            'code_verifier': code_verifier,
            'redirect_uri': redirect_uri,
            'created_at': datetime.now()
        }
        
        # Build OAuth authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': OAUTH_CLIENT_ID,
            'redirect_uri': OAUTH_REDIRECT_URI,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': state
        }
        
        auth_url = f"{OAUTH_AUTHORIZE_URL}?{urlencode(auth_params)}"
        
        return {
            "success": True,
            "login_url": auth_url,
            "message": "Redirect to User Management for OAuth authentication"
        }
    except Exception as e:
        logger.error(f"Error initiating OAuth login: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 5: OAuth Callback Handler

```python
@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str, error: Optional[str] = None):
    """Handle OAuth callback from User Management system"""
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        # Validate state parameter
        if state not in pkce_sessions:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        pkce_session = pkce_sessions[state]
        
        # Exchange authorization code for access token
        token_request = {
            'grant_type': 'authorization_code',
            'client_id': OAUTH_CLIENT_ID,
            'code': code,
            'redirect_uri': OAUTH_REDIRECT_URI,
            'code_verifier': pkce_session['code_verifier']
        }
        
        token_response = requests.post(OAUTH_TOKEN_URL, json=token_request)
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Create user session
        session_id = f"session_{datetime.now().timestamp()}"
        user_sessions[session_id] = {
            'user_id': token_data.get('user_id'),
            'email': token_data.get('email'),
            'roles': token_data.get('roles', []),
            'access_token': access_token,
            'authenticated_at': datetime.now()
        }
        
        # Clean up PKCE session
        del pkce_sessions[state]
        
        # Redirect to original destination
        redirect_url = f"{pkce_session['redirect_uri']}?session_id={session_id}&auth_success=true"
        
        return JSONResponse(
            status_code=302,
            headers={"Location": redirect_url},
            content={"message": "Redirecting to application"}
        )
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 6: Logout Handler

```python
@app.post("/auth/logout")
async def logout(session_id: str):
    """Handle logout - clear local session and call User Management logout"""
    try:
        # Get user session
        if session_id in user_sessions:
            user_session = user_sessions[session_id]
            access_token = user_session.get('access_token')
            
            # Call User Management logout API
            if access_token:
                headers = {'Authorization': f'Bearer {access_token}'}
                requests.post(f"{USER_MGMT_API_BASE}/auth/logout", headers=headers)
            
            # Clear local session
            del user_sessions[session_id]
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Frontend Implementation

### Step 1: Authentication Service

```typescript
// auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

export interface AuthStatus {
  authenticated: boolean;
  user?: any;
  login_url?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8002'; // Your backend URL
  private authStatusSubject = new BehaviorSubject<AuthStatus>({ authenticated: false });

  constructor(private http: HttpClient) {
    this.checkAuthStatus();
  }

  initiateLogin(returnUrl?: string): Observable<any> {
    const body = returnUrl ? { return_url: returnUrl } : {};
    return this.http.post(`${this.apiUrl}/auth/login`, body);
  }

  getAuthStatus(): Observable<AuthStatus> {
    return this.authStatusSubject.asObservable();
  }

  private checkAuthStatus(): void {
    const sessionId = this.getSessionId();
    if (sessionId) {
      this.http.get<AuthStatus>(`${this.apiUrl}/auth/status?session_id=${sessionId}`)
        .subscribe(status => this.authStatusSubject.next(status));
    }
  }

  handleOAuthReturn(urlParams: URLSearchParams): void {
    const sessionId = urlParams.get('session_id');
    const authSuccess = urlParams.get('auth_success');
    
    if (sessionId && authSuccess) {
      localStorage.setItem('session_id', sessionId);
      this.checkAuthStatus();
    }
  }

  logout(): Observable<any> {
    const sessionId = this.getSessionId();
    return this.http.post(`${this.apiUrl}/auth/logout`, { session_id: sessionId });
  }

  private getSessionId(): string | null {
    return localStorage.getItem('session_id');
  }

  clearSession(): void {
    localStorage.removeItem('session_id');
    this.authStatusSubject.next({ authenticated: false });
  }
}
```

### Step 2: Home Component (Login Page)

```typescript
// home.component.ts
import { Component } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-home',
  template: `
    <div class="container">
      <h1>Welcome to External App</h1>
      <p>Please log in to access the application.</p>
      
      <button (click)="login()" class="btn btn-primary">
        🔐 Login via User Management
      </button>
    </div>
  `
})
export class HomeComponent {
  constructor(private authService: AuthService) {}

  login(): void {
    const returnUrl = `${window.location.origin}/dashboard`;
    
    this.authService.initiateLogin(returnUrl).subscribe({
      next: (response) => {
        if (response.success && response.login_url) {
          window.location.href = response.login_url;
        }
      },
      error: (error) => {
        console.error('Error initiating login:', error);
        alert('Failed to initiate login. Please try again.');
      }
    });
  }
}
```

### Step 3: Dashboard Component (OAuth Return Page)

```typescript
// dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, AuthStatus } from '../services/auth.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  template: `
    <div class="container">
      <ng-container *ngIf="authStatus$ | async as status">
        <div *ngIf="status.authenticated">
          <h1>Dashboard</h1>
          
          <!-- Navigation Links -->
          <div class="nav-links">
            <button (click)="showProfile()" class="btn btn-primary">
              👤 Profile
            </button>
            <button (click)="logout()" class="btn btn-danger">
              🚪 Logout
            </button>
          </div>
          
          <!-- Profile Details -->
          <div *ngIf="showProfileDetails && status.user" class="profile-card">
            <h2>User Profile</h2>
            <p><strong>Email:</strong> {{ status.user.email }}</p>
            <p><strong>Roles:</strong> {{ status.user.roles.join(', ') }}</p>
            <p><strong>Admin:</strong> {{ status.user.is_admin ? 'Yes' : 'No' }}</p>
          </div>
          
          <!-- Your app content here -->
          <div class="app-content">
            <h3>Application Features</h3>
            <p>Your external application content goes here...</p>
          </div>
        </div>
        
        <div *ngIf="!status.authenticated">
          <p>Please log in to access this page.</p>
          <a routerLink="/home" class="btn btn-primary">Go to Login</a>
        </div>
      </ng-container>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  authStatus$: Observable<AuthStatus>;
  showProfileDetails = false;

  constructor(
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router
  ) {
    this.authStatus$ = this.authService.getAuthStatus();
  }

  ngOnInit(): void {
    // Handle OAuth return
    this.route.queryParams.subscribe(params => {
      const sessionId = params['session_id'];
      const authSuccess = params['auth_success'];
      
      if (sessionId && authSuccess) {
        console.log('OAuth authentication successful');
        const urlParams = new URLSearchParams(window.location.search);
        this.authService.handleOAuthReturn(urlParams);
        
        // Clean up URL
        this.router.navigate(['/dashboard'], { replaceUrl: true });
      }
    });
  }

  showProfile(): void {
    this.showProfileDetails = !this.showProfileDetails;
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.authService.clearSession();
        this.router.navigate(['/home']);
      },
      error: (error) => {
        console.error('Error during logout:', error);
        this.authService.clearSession();
        this.router.navigate(['/home']);
      }
    });
  }
}
```

### Step 4: Routing Configuration

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { HomeComponent } from './components/home.component';
import { DashboardComponent } from './components/dashboard.component';

export const routes: Routes = [
  { path: '', redirectTo: '/home', pathMatch: 'full' },
  { path: 'home', component: HomeComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: '**', redirectTo: '/home' }
];
```

## OAuth Flow Documentation

### Complete Authentication Flow

| Step | Component | Action | Database Tables | API Endpoints |
|------|-----------|--------|----------------|---------------|
| 1 | **External App Frontend** | User clicks "Login" button | - | `POST /auth/login` |
| 2 | **External App Backend** | Generate PKCE params, create OAuth URL | - | - |
| 3 | **External App Frontend** | Redirect to User Management OAuth URL | - | - |
| 4 | **User Management Frontend** | Display login form | - | `GET /login?return_url=...` |
| 5 | **User Management Backend** | Validate credentials | `aaa_profiles` | `POST /auth/login` |
| 6 | **User Management Frontend** | Show MFA form (if enabled) | - | `GET /mfa` |
| 7 | **User Management Backend** | Verify MFA code | `aaa_profiles` | `POST /auth/mfa/verify` |
| 8 | **User Management Frontend** | Redirect to OAuth authorize with token | - | - |
| 9 | **User Management Backend** | Validate token, generate auth code | `aaa_authorization_codes`, `aaa_clients` | `GET /oauth/authorize` |
| 10 | **User Management Backend** | Redirect to external app callback | `aaa_authorization_codes` | - |
| 11 | **External App Backend** | Exchange code for access token | `aaa_authorization_codes`, `aaa_clients`, `aaa_profiles` | `POST /oauth/token` |
| 12 | **External App Backend** | Create user session, redirect to app | - | - |
| 13 | **External App Frontend** | Display dashboard with user info | - | `GET /dashboard` |

### Database Tables Involved

#### 1. `aaa_clients` - OAuth Client Registration
```sql
-- Stores OAuth client configurations
CREATE TABLE aaa.aaa_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(255) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    redirect_uris TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. `aaa_authorization_codes` - Temporary Authorization Codes
```sql
-- Stores temporary authorization codes for PKCE flow
CREATE TABLE aaa.aaa_authorization_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255) REFERENCES aaa.aaa_clients(client_id),
    user_id UUID REFERENCES aaa.aaa_profiles(id),
    redirect_uri TEXT NOT NULL,
    code_challenge VARCHAR(255) NOT NULL,
    code_challenge_method VARCHAR(10) DEFAULT 'S256',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. `aaa_profiles` - User Accounts
```sql
-- Stores user account information
-- (existing table with email, password_hash, mfa_secret, etc.)
```

### API Endpoints Reference

#### User Management API Endpoints

| Method | Endpoint | Purpose | Required Parameters |
|--------|----------|---------|-------------------|
| `GET` | `/oauth/authorize` | Start OAuth authorization | `response_type`, `client_id`, `redirect_uri`, `code_challenge`, `state` |
| `POST` | `/oauth/token` | Exchange code for token | `grant_type`, `client_id`, `code`, `redirect_uri`, `code_verifier` |
| `POST` | `/auth/login` | User authentication | `email`, `password` |
| `POST` | `/auth/mfa/verify` | MFA verification | `email`, `mfa_code` |
| `GET` | `/profiles/me` | Get user profile | `Authorization: Bearer <token>` |
| `POST` | `/auth/logout` | User logout | `Authorization: Bearer <token>` |

#### External App API Endpoints

| Method | Endpoint | Purpose | Parameters |
|--------|----------|---------|-----------|
| `POST` | `/auth/login` | Initiate OAuth flow | `return_url` (optional) |
| `GET` | `/oauth/callback` | Handle OAuth callback | `code`, `state`, `error` |
| `GET` | `/auth/status` | Check auth status | `session_id` |
| `POST` | `/auth/logout` | Logout user | `session_id` |

### Security Considerations

#### PKCE Implementation
- **Code Verifier**: Random 43-128 character string
- **Code Challenge**: SHA256 hash of code verifier, base64url encoded
- **State Parameter**: Random string for CSRF protection
- **Authorization Code**: Single-use, expires in 10 minutes

#### Token Security
- **JWT Tokens**: Signed with secret key, include user claims
- **Token Expiration**: Configurable (default: 60 minutes)
- **Secure Storage**: Tokens stored securely in sessions/localStorage
- **Logout Handling**: Tokens invalidated on both systems

## Testing

### 1. Test OAuth Client Registration

```sql
-- Verify client exists
SELECT * FROM aaa.aaa_clients WHERE client_id = 'your_external_app_id';
```

### 2. Test Complete Flow

1. **Start External App**: Access `http://localhost:4202/home`
2. **Click Login**: Should redirect to User Management
3. **Enter Credentials**: Login with valid user account
4. **Complete MFA**: Enter MFA code (if enabled)
5. **Return to App**: Should redirect back to dashboard
6. **Check Profile**: Profile button should show user details
7. **Test Logout**: Logout should clear sessions on both systems

### 3. Debug Common Issues

```bash
# Check User Management API logs
tail -f /path/to/usermanagement/logs/app.log

# Check External App logs  
tail -f /path/to/externalapp/logs/app.log

# Verify database state
SELECT * FROM aaa.aaa_authorization_codes WHERE used = false;
```

## Troubleshooting

### Common Issues

#### 1. "Invalid client_id" Error
**Cause**: OAuth client not registered or inactive
**Solution**: 
```sql
-- Check client registration
SELECT * FROM aaa.aaa_clients WHERE client_id = 'your_client_id';

-- Activate client if needed
UPDATE aaa.aaa_clients SET is_active = true WHERE client_id = 'your_client_id';
```

#### 2. "Invalid redirect_uri" Error
**Cause**: Redirect URI doesn't match registered URIs
**Solution**:
```sql
-- Update redirect URIs
UPDATE aaa.aaa_clients 
SET redirect_uris = ARRAY['http://localhost:8002/oauth/callback', 'https://yourdomain.com/oauth/callback']
WHERE client_id = 'your_client_id';
```

#### 3. "Authorization code expired" Error
**Cause**: Authorization code used after 10-minute expiry
**Solution**: 
- Retry the login flow
- Check system clocks are synchronized

#### 4. MFA Redirect Loop
**Cause**: MFA component not including JWT token in redirect
**Solution**: Ensure MFA verification includes access token in OAuth redirect URL

#### 5. CORS Errors
**Cause**: Cross-origin requests blocked
**Solution**: Configure CORS in your backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4202", "http://localhost:4201"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Debug Commands

```bash
# Check running services
lsof -i :8001  # User Management API
lsof -i :4201  # User Management Frontend  
lsof -i :8002  # External App API
lsof -i :4202  # External App Frontend

# Test OAuth endpoints
curl -X POST "http://localhost:8002/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"return_url": "http://localhost:4202/dashboard"}'

# Test token exchange
curl -X POST "http://localhost:8001/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "authorization_code",
    "client_id": "your_client_id", 
    "code": "auth_code_here",
    "redirect_uri": "http://localhost:8002/oauth/callback",
    "code_verifier": "code_verifier_here"
  }'
```

### Production Deployment Notes

1. **Environment Variables**: Store sensitive configuration in environment variables
2. **HTTPS Required**: Use HTTPS for all production URLs
3. **Session Storage**: Use Redis or database for session/PKCE storage in production
4. **Error Handling**: Implement comprehensive error handling and logging
5. **Rate Limiting**: Add rate limiting to prevent abuse
6. **Monitoring**: Monitor OAuth flows and authentication metrics

## Support

For additional support:
- Review User Management API documentation at `/docs`
- Check application logs for detailed error messages
- Verify database table schemas and data integrity
- Test with curl commands to isolate frontend vs backend issues

---

**⚠️ Security Note**: This integration uses OAuth 2.0 PKCE which is designed for public clients. Always use HTTPS in production and follow OAuth 2.0 security best practices.