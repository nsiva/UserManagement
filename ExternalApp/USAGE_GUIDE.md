# ExternalApp - Usage Guide

## 🎯 Overview

ExternalApp demonstrates how external applications can integrate with the User Management system using the `redirect_uri` parameter for seamless authentication including MFA support.

## 🏗️ Architecture

```
ExternalApp (Port 4202)     UserManagement (Port 4201)
     ↓                              ↑
     ↓                              ↑
ExternalApp API (Port 8002)   UserManagement API (Port 8001)
```

## 🚀 Quick Start

### Prerequisites
- UserManagement system must be running (ports 4201 and 8001)
- Node.js and npm installed
- Python 3.8+ installed

### Start Everything
```bash
# Make the startup script executable
chmod +x start-all.sh

# Start both backend and frontend
./start-all.sh
```

### Manual Start (Development)

#### Backend Only
```bash
cd Api
chmod +x start.sh
./start.sh
```

#### Frontend Only
```bash
cd WebUI
chmod +x start.sh
./start.sh
```

## 🔧 Configuration

### Backend Configuration (Api/.env)
```env
API_PORT=8002
USER_MGMT_WEB_BASE=http://localhost:4201
USER_MGMT_API_BASE=http://localhost:8001
EXTERNAL_APP_BASE=http://localhost:4202
```

### Frontend Configuration (WebUI/external-app/src/environments/environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8002',
  userManagementUrl: 'http://localhost:4201',
  appName: 'ExternalApp'
};
```

## 🎮 How to Test

### 1. Start All Systems
```bash
# In UserManagement directory
cd Api && ./scripts/start.sh &
cd WebUI/user-management-app && npm start &

# In ExternalApp directory  
./start-all.sh
```

### 2. Test Authentication Flow
1. **Visit ExternalApp**: http://localhost:4202
2. **Click "Login via User Management"**
3. **You'll be redirected to**: http://localhost:4201/login?redirect_uri=http://localhost:4202/dashboard
4. **Enter credentials** in UserManagement login
5. **Complete MFA** if enabled for the user
6. **You'll be redirected back to**: http://localhost:4202/dashboard
7. **Verify** you're logged in and see dashboard data

### 3. Test Different Scenarios

#### Scenario A: User without MFA
- Login flow: UserManagement Login → Back to ExternalApp Dashboard
- Expected: Direct redirect after password

#### Scenario B: User with MFA  
- Login flow: UserManagement Login → MFA Page → Back to ExternalApp Dashboard
- Expected: MFA verification step, then redirect

#### Scenario C: Logout and Re-login
- Logout from ExternalApp → Try to access dashboard → Redirected to login
- Expected: Forced fresh authentication

## 🛠️ Technical Flow

### 1. Login Initiation
```typescript
// ExternalApp frontend calls its backend
POST /auth/login
{
  "return_url": "http://localhost:4202/dashboard"
}

// Backend responds with UserManagement URL
{
  "success": true,
  "login_url": "http://localhost:4201/login?redirect_uri=http://localhost:4202/dashboard"
}
```

### 2. User Authentication
- User redirected to UserManagement
- Completes login + MFA (if required)
- UserManagement redirects back: `http://localhost:4202/dashboard`

### 3. Session Establishment
- ExternalApp frontend detects return from authentication
- Establishes local session
- Displays protected dashboard content

## 📊 API Endpoints

### ExternalApp Backend (Port 8002)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/auth/login` | Initiate login redirect |
| GET | `/auth/status` | Check authentication status |
| POST | `/auth/callback` | Handle auth callback (future) |
| GET | `/dashboard/data` | Protected dashboard data |
| POST | `/auth/logout` | Logout user |

### Example API Usage
```bash
# Check if user is authenticated
curl -X GET "http://localhost:8002/auth/status" \
  -H "X-Session-ID: session_123"

# Initiate login
curl -X POST "http://localhost:8002/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"return_url": "http://localhost:4202/dashboard"}'

# Get dashboard data (authenticated)
curl -X GET "http://localhost:8002/dashboard/data" \
  -H "X-Session-ID: session_123"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Failed to initiate login"
- **Cause**: ExternalApp backend not running
- **Solution**: Start the backend with `cd Api && ./start.sh`

#### 2. "Authentication Error" in UserManagement
- **Cause**: Invalid redirect_uri or UserManagement not running
- **Solution**: Verify UserManagement is running on port 4201

#### 3. "Redirect loop"
- **Cause**: Browser caching or session issues
- **Solution**: Clear browser cache and localStorage

#### 4. "CORS errors"
- **Cause**: Ports mismatch or CORS configuration
- **Solution**: Verify all services are running on expected ports

### Debug Tips
1. **Check browser console** for authentication flow logs
2. **Verify ports**: 4201 (UserManagement), 4202 (ExternalApp), 8001 (UserMgmt API), 8002 (ExternalApp API)
3. **Check network tab** to see redirect URLs
4. **Verify localStorage** for session data

## 🔒 Security Notes

⚠️ **This is a demonstration application**. In production:

1. **Validate redirect URIs** on the server side
2. **Use proper token validation** instead of simple session IDs
3. **Implement CSRF protection**
4. **Use HTTPS** for all communications
5. **Implement proper session management** (Redis, database)
6. **Add request signing/validation** for callbacks

## 📝 Customization

### Adding New Pages
1. Create component in `WebUI/external-app/src/app/components/`
2. Add route in `app.routes.ts`
3. Add navigation in header component

### Adding Authentication to Pages
```typescript
// In component
ngOnInit(): void {
  this.authStatus$.subscribe(status => {
    if (!status.authenticated) {
      this.login(); // Redirect to UserManagement
    }
  });
}
```

### Custom Return URLs
```typescript
// Specify custom return URL
this.authService.initiateLogin('http://localhost:4202/custom-page');
```

This demonstrates the complete integration pattern for external applications with the User Management system!