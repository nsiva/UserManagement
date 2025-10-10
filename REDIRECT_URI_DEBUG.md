# 🐛 redirect_uri Issue Debugging Guide

## 🔍 Problem Description
User gets redirected to UserManagement login with correct URL:
```
http://localhost:4201/login?redirect_uri=http:%2F%2Flocalhost:4202%2Fdashboard
```

But after MFA completion, user goes to `/admin` instead of back to ExternalApp.

## 🎯 Debug Steps

I've added comprehensive debugging to help identify the issue. Follow these steps:

### Step 1: Restart UserManagement
```bash
cd /Users/siva/projects/UserManagement/WebUI/user-management-app
# Stop current server (Ctrl+C)
npm start
```

### Step 2: Test the Flow with Console Open

1. **Open Browser Developer Tools** (F12)
2. **Clear Console** and **Clear Application Storage**:
   - Go to Application tab → Storage → Clear site data
3. **Start the test flow**:
   - Visit: http://localhost:4202
   - Click "Login via User Management"

### Step 3: Check Console Logs

Look for these debug messages in the console:

#### In Login Component:
```
=== LOGIN COMPONENT DEBUG ===
Raw query params: {redirect_uri: "http://localhost:4202/dashboard"}
redirect_uri from params: http://localhost:4202/dashboard
Decoded redirect_uri: http://localhost:4202/dashboard
Current URL: http://localhost:4201/login?redirect_uri=http%3A%2F%2Flocalhost%3A4202%2Fdashboard
==============================
```

#### During MFA Storage:
```
=== MFA REDIRECT STORAGE DEBUG ===
Storing redirect_uri for MFA: http://localhost:4202/dashboard
Stored in sessionStorage as login_redirect_uri: http://localhost:4202/dashboard
==================================
```

#### In MFA Component:
```
=== MFA COMPONENT DEBUG ===
Retrieved email: user@example.com
Retrieved name: User Name
Retrieved userId: user123
Retrieved redirect URI: http://localhost:4202/dashboard
All sessionStorage keys: ["mfa_user_email", "mfa_user_name", "mfa_user_id", "login_redirect_uri"]
SessionStorage login_redirect_uri: http://localhost:4202/dashboard
==========================
```

#### After MFA Success:
```
=== MFA SUCCESS REDIRECT DEBUG ===
Current redirectUri value: http://localhost:4202/dashboard
SessionStorage login_redirect_uri: http://localhost:4202/dashboard
MFA verification successful - redirecting to external URI: http://localhost:4202/dashboard
About to redirect to: http://localhost:4202/dashboard
=================================
```

### Step 4: Identify the Issue

Based on what you see in the console:

#### ✅ Expected Behavior:
- Login component shows the correct redirect_uri
- Redirect URI gets stored in sessionStorage
- MFA component retrieves the redirect URI
- After MFA success, redirects to ExternalApp

#### ❌ Issue Scenarios:

**Scenario A: URL Decoding Issue**
```
redirect_uri from params: undefined
```
**Fix**: The URL encoding is wrong

**Scenario B: Storage Issue**
```
Storing redirect_uri for MFA: null
```
**Fix**: redirect_uri is not being captured correctly

**Scenario C: Retrieval Issue**
```
Retrieved redirect URI: null
```
**Fix**: sessionStorage is being cleared somewhere

**Scenario D: No Debug Logs**
**Fix**: UserManagement app needs to be restarted with new code

## 🔧 Quick Fixes

### Fix 1: Manual URL Test
Try accessing the login URL directly with proper encoding:
```
http://localhost:4201/login?redirect_uri=http://localhost:4202/dashboard
```
(Note: No %2F encoding - let Angular handle it)

### Fix 2: Check UserManagement App Restart
Make sure UserManagement app is running the updated code:
```bash
cd /Users/siva/projects/UserManagement/WebUI/user-management-app
# Ctrl+C to stop
npm start
```

### Fix 3: Clear Browser Cache
- Clear all browser data
- Use incognito/private mode
- Try different browser

### Fix 4: Alternative URL Generation
In ExternalApp, try generating the URL without encoding:
```typescript
// In ExternalApp auth.service.ts
const loginUrl = `http://localhost:4201/login?redirect_uri=${returnUrl}`;
// Instead of encoding the returnUrl
```

## 📋 Report Back

Please run the test and let me know:

1. **What debug logs you see** (copy the console output)
2. **Which scenario matches** your situation
3. **At what step it fails**

This will help me provide the exact fix needed!

## 🚨 Emergency Fix

If debugging doesn't work, here's a simple manual test:

1. **Manually access**:
   ```
   http://localhost:4201/login?redirect_uri=http://localhost:4202/dashboard
   ```

2. **Complete login + MFA**

3. **Check if you get redirected back to ExternalApp**

If this works, the issue is in ExternalApp's URL generation.
If this doesn't work, the issue is in UserManagement's redirect handling.