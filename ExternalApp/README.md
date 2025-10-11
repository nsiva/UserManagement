# ExternalApp - OAuth 2.0 PKCE Integration

Test application demonstrating secure OAuth 2.0 with PKCE integration with the User Management system.

This application mirrors the UserManagement architecture with:
- **Api/**: FastAPI backend with OAuth PKCE client implementation
- **WebUI/**: Angular frontend with OAuth flow handling

## Purpose

This app demonstrates how external applications can securely integrate with the User Management system using OAuth 2.0 PKCE by:
1. Initiating OAuth PKCE flow with code challenge
2. Redirecting users to UserManagement for authentication  
3. Receiving authorization code and exchanging for access token
4. Using access token to access user profile and roles
5. Providing a protected dashboard with full user context

## Architecture

- **Backend**: FastAPI running on port 8002
- **Frontend**: Angular running on port 4202  
- **Authentication**: OAuth 2.0 PKCE flow with UserManagement at localhost:8001
- **OAuth Client**: Registered as `test_external_app` in User Management database

## Quick Start

⚠️ **Important**: If you get npm/Angular errors, see [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed setup instructions.

### Easy Setup (Recommended)
```bash
# Install frontend dependencies (one-time)
cd WebUI
./setup.sh

# Start both backend and frontend
cd ..
./start-all.sh
```

### Manual Setup

#### Backend
```bash
cd Api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

#### Frontend  
```bash
cd WebUI/external-app
npm install  # Required first time
npm start    # Runs on port 4202
```

## OAuth Setup

Before using ExternalApp, ensure the OAuth client is registered:

### Option 1: Run Database Migration
```bash
cd /Users/siva/projects/UserManagement/Api
psql -h your-host -U your-username -d your-database -f migrations/extend_aaa_clients_for_oauth.sql
```

### Option 2: Manual Database Insert
```sql
INSERT INTO aaa_clients (client_id, name, client_type, redirect_uris, scopes, description) 
VALUES (
    'test_external_app',
    'ExternalApp Test Client', 
    'oauth_pkce',
    ARRAY['http://localhost:4202/oauth/callback'],
    ARRAY['read:profile', 'read:roles'],
    'OAuth PKCE client for ExternalApp testing'
);
```

### Option 3: Test OAuth Setup
```bash
python test_oauth_setup.py
```

## Usage

1. **Start User Management System** (if not already running):
   ```bash
   cd /Users/siva/projects/UserManagement/Api
   ./scripts/start.sh  # Starts on port 8001
   ```

2. **Start ExternalApp**:
   ```bash
   cd /Users/siva/projects/UserManagement/ExternalApp
   ./start-all.sh  # Starts API on 8002, WebUI on 4202
   ```

3. **Test OAuth Flow**:
   - Visit http://localhost:4202
   - Click "Login via User Management" 
   - Complete OAuth authentication (including MFA if enabled)
   - You'll be redirected back to ExternalApp dashboard with full user context

## OAuth Flow Details

### 1. Login Initiation
- ExternalApp generates PKCE code verifier and challenge
- Redirects to User Management OAuth authorization endpoint
- Includes client_id, redirect_uri, code_challenge, and state

### 2. User Authentication  
- User authenticates with User Management (including MFA)
- User Management validates client and redirect URI
- Generates authorization code tied to PKCE challenge

### 3. Callback Processing
- User Management redirects to ExternalApp OAuth callback
- ExternalApp receives authorization code and state
- ExternalApp exchanges code for access token using PKCE code verifier

### 4. Access Token Usage
- ExternalApp uses access token to fetch user profile
- Creates local session with full user context
- Redirects user to protected dashboard

## Security Features

- **PKCE**: Code challenge prevents authorization code interception
- **State Parameter**: CSRF protection during OAuth flow  
- **Redirect URI Validation**: Prevents unauthorized redirects
- **Access Token**: JWT token with user roles and permissions
- **Secure Sessions**: Server-side session management