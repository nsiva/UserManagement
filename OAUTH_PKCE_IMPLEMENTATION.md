# OAuth 2.0 PKCE Implementation Guide

This document describes the complete OAuth 2.0 with PKCE (Proof Key for Code Exchange) implementation for the User Management system.

## Overview

The implementation allows external applications to securely obtain access tokens for authenticated users without requiring client secrets, using the OAuth 2.0 Authorization Code flow with PKCE extension.

## Architecture

### Backend Components

1. **OAuth Router** (`/Api/routers/oauth.py`)
   - `/oauth/authorize` - Authorization endpoint
   - `/oauth/token` - Token exchange endpoint
   - `/oauth/clients` - Client management (admin only)

2. **Database Support**
   - **Tables**: Extended `aaa_clients` (unified table), `aaa_authorization_codes`
   - **Repository Pattern**: Both Supabase and PostgreSQL repositories implemented
   - **Migration**: Single migration to extend existing `aaa_clients` table

3. **Models** (`/Api/models.py`)
   - `OAuthClientCreate/Update/InDB` - Client management
   - `AuthorizationRequest` - Authorization parameters
   - `TokenExchangeRequest` - Token exchange parameters
   - `OAuthTokenResponse` - Token response

### Frontend Components

1. **Login Flow Enhancement** (`/WebUI/user-management-app/src/app/components/login/`)
   - Handles `return_url` parameter for OAuth redirects
   - Preserves OAuth context through MFA and setup flows

2. **OAuth Callback** (`/WebUI/user-management-app/src/app/components/oauth-callback/`)
   - Handles OAuth callback responses
   - Displays success/error messages

3. **MFA Integration**
   - Updated to preserve OAuth context during MFA verification
   - Redirects back to OAuth flow after successful verification

## PKCE Flow

### Step 1: External App Initiates Flow

```javascript
// External app generates PKCE parameters
const codeVerifier = generateCodeVerifier(); // 43-128 characters
const codeChallenge = await generateCodeChallenge(codeVerifier); // SHA256 hash

// Redirect user to authorization endpoint
const authUrl = `http://localhost:8001/oauth/authorize?` + 
  `response_type=code&` +
  `client_id=your_client_id&` +
  `redirect_uri=http://localhost:3000/callback&` +
  `code_challenge=${codeChallenge}&` +
  `code_challenge_method=S256&` +
  `state=${state}`;

window.location.href = authUrl;
```

### Step 2: User Authentication

The authorization endpoint checks if the user is authenticated:

- **Not authenticated**: Redirects to login with `return_url` parameter
- **Authenticated**: Proceeds to authorization code generation

#### With MFA

If MFA is required:
1. User enters credentials
2. System detects MFA requirement (HTTP 402)
3. Frontend stores OAuth context and redirects to MFA page
4. After MFA verification, redirects back to OAuth authorization
5. Authorization code is generated and returned

### Step 3: Authorization Code Generation

```python
# Backend generates authorization code
auth_code = generate_authorization_code()
expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

# Store code with PKCE challenge
code_data = {
    'code': auth_code,
    'client_id': client_id,
    'user_id': str(current_user.user_id),
    'redirect_uri': redirect_uri,
    'code_challenge': code_challenge,
    'code_challenge_method': 'S256',
    'expires_at': expires_at
}

# Redirect to callback URL
callback_url = f"{redirect_uri}?code={auth_code}&state={state}"
```

### Step 4: Token Exchange

External app exchanges authorization code for access token:

```javascript
// External app backend exchanges code for token
const tokenResponse = await fetch('http://localhost:8001/oauth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    grant_type: 'authorization_code',
    client_id: 'your_client_id',
    code: authorizationCode,
    redirect_uri: 'http://localhost:3000/callback',
    code_verifier: codeVerifier
  })
});

const tokens = await tokenResponse.json();
// tokens.access_token can now be used to access user data
```

### Step 5: API Access

```javascript
// Use access token to access user profile
const userProfile = await fetch('http://localhost:8001/profiles/me', {
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`
  }
});
```

## Security Features

### PKCE Security
- **Code Verifier**: Cryptographically random string (43-128 chars)
- **Code Challenge**: SHA256 hash of code verifier
- **Challenge Method**: Only S256 supported (not plain text)

### Additional Security
- **State Parameter**: CSRF protection
- **Authorization Code Expiry**: 10 minutes
- **Client Validation**: Redirect URI whitelist
- **User Context**: Access token includes user roles and permissions

## Database Schema

### Extended Clients Table (Unified)
```sql
-- Extended existing aaa_clients table to support both client types
ALTER TABLE aaa_clients 
ADD COLUMN IF NOT EXISTS redirect_uris TEXT[], -- Array of allowed redirect URIs for OAuth
ADD COLUMN IF NOT EXISTS client_type VARCHAR(20) DEFAULT 'client_credentials' 
    CHECK (client_type IN ('client_credentials', 'oauth_pkce')),
ADD COLUMN IF NOT EXISTS description TEXT;

-- Make client_secret optional (not needed for PKCE clients)
ALTER TABLE aaa_clients ALTER COLUMN client_secret DROP NOT NULL;
```

**Client Types:**
- `client_credentials` - For server-to-server authentication (requires `client_secret`)
- `oauth_pkce` - For OAuth PKCE flow (no `client_secret`, requires `redirect_uris`)

### Authorization Codes Table
```sql
CREATE TABLE aaa_authorization_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    client_id TEXT NOT NULL REFERENCES aaa_clients(client_id),
    user_id UUID NOT NULL REFERENCES aaa_profiles(id),
    redirect_uri TEXT NOT NULL,
    code_challenge TEXT NOT NULL,
    code_challenge_method TEXT NOT NULL DEFAULT 'S256',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Configuration

### Backend Setup

1. **Run Database Migration**
   
   **For both Supabase and PostgreSQL:**
   ```bash
   cd Api
   # Extend existing aaa_clients table for OAuth PKCE support
   psql -h your-host -U your-username -d your-database -f migrations/extend_aaa_clients_for_oauth.sql
   ```

2. **Register OAuth Client**
   ```bash
   # Via API (admin required)
   curl -X POST "http://localhost:8001/oauth/clients" \
     -H "Authorization: Bearer admin_token" \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "your_app_id",
       "name": "Your Application",
       "redirect_uris": ["http://localhost:3000/callback"],
       "scopes": ["read:profile", "read:roles"],
       "description": "My external application"
     }'
   ```
   
   **Or directly in database:**
   ```sql
   INSERT INTO aaa_clients (client_id, name, client_type, redirect_uris, scopes, description) 
   VALUES (
     'your_app_id',
     'Your Application', 
     'oauth_pkce',
     ARRAY['http://localhost:3000/callback'],
     ARRAY['read:profile', 'read:roles'],
     'My external application'
   );
   ```

3. **Update CORS Settings** (if needed)
   ```python
   # In main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:4201", "http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Frontend Setup

No additional configuration needed. The login flow automatically handles OAuth parameters.

## Testing

### Automated Testing
```bash
cd Api
python scripts/test_pkce_flow.py
```

### Manual Testing

1. **Create Test Client**
   ```bash
   # Insert test client directly in database
   INSERT INTO aaa_clients (client_id, name, client_type, redirect_uris, scopes) 
   VALUES ('test_app', 'Test Application', 'oauth_pkce', ARRAY['http://localhost:3000/callback'], ARRAY['read:profile']);
   ```

2. **Test Authorization URL**
   ```
   http://localhost:8001/oauth/authorize?response_type=code&client_id=test_app&redirect_uri=http://localhost:3000/callback&code_challenge=CHALLENGE&code_challenge_method=S256&state=STATE
   ```

3. **Test Token Exchange**
   ```bash
   curl -X POST "http://localhost:8001/oauth/token" \
     -H "Content-Type: application/json" \
     -d '{
       "grant_type": "authorization_code",
       "client_id": "test_app",
       "code": "AUTH_CODE",
       "redirect_uri": "http://localhost:3000/callback",
       "code_verifier": "CODE_VERIFIER"
     }'
   ```

## Error Handling

### Common Errors

- **400 Bad Request**: Invalid parameters, client_id, or redirect_uri
- **401 Unauthorized**: Invalid or expired authorization code
- **403 Forbidden**: Client not active or unauthorized
- **404 Not Found**: Client not found

### Frontend Error Handling

The OAuth callback component displays appropriate error messages and redirects users back to login on failures.

## Production Considerations

### Security
- Use HTTPS for all OAuth endpoints
- Implement rate limiting on OAuth endpoints
- Monitor for suspicious authorization patterns
- Regularly clean up expired authorization codes

### Performance
- Add database indexes for OAuth queries
- Implement caching for client validation
- Set up monitoring for OAuth endpoint performance

### Monitoring
- Log all OAuth authorization attempts
- Track token issuance metrics
- Monitor authorization code usage patterns
- Alert on security anomalies

## Integration Examples

### React Application
```javascript
// PKCE helper functions
function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64URLEncode(array);
}

async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64URLEncode(new Uint8Array(digest));
}

// OAuth integration
class UserManagementOAuth {
  constructor(clientId, redirectUri) {
    this.clientId = clientId;
    this.redirectUri = redirectUri;
  }

  async login() {
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    const state = generateRandomString();

    // Store verifier for later use
    sessionStorage.setItem('code_verifier', codeVerifier);
    sessionStorage.setItem('oauth_state', state);

    const authUrl = new URL('http://localhost:8001/oauth/authorize');
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('client_id', this.clientId);
    authUrl.searchParams.set('redirect_uri', this.redirectUri);
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('state', state);

    window.location.href = authUrl.toString();
  }

  async handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      throw new Error(`OAuth error: ${error}`);
    }

    const storedState = sessionStorage.getItem('oauth_state');
    if (state !== storedState) {
      throw new Error('State mismatch');
    }

    const codeVerifier = sessionStorage.getItem('code_verifier');
    const tokens = await this.exchangeCodeForToken(code, codeVerifier);
    
    // Clean up
    sessionStorage.removeItem('code_verifier');
    sessionStorage.removeItem('oauth_state');

    return tokens;
  }

  async exchangeCodeForToken(code, codeVerifier) {
    const response = await fetch('http://localhost:8001/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grant_type: 'authorization_code',
        client_id: this.clientId,
        code: code,
        redirect_uri: this.redirectUri,
        code_verifier: codeVerifier
      })
    });

    if (!response.ok) {
      throw new Error('Token exchange failed');
    }

    return response.json();
  }
}
```

This implementation provides a secure, standards-compliant OAuth 2.0 with PKCE flow that integrates seamlessly with the existing User Management system's authentication and MFA capabilities.