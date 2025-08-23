# MFA Troubleshooting Guide

## 🚨 Common MFA Issues and Solutions

### 1. MFA Setup Issues

#### Problem: "MFA setup failed" or empty response
**Symptoms:**
- Setup endpoint returns empty response
- No QR code or secret generated

**Solutions:**
```bash
# Check if user has admin privileges
curl -X GET "http://localhost:8001/admin/users" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify JWT token is valid
curl -X GET "http://localhost:8001/profiles/me" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check server logs for errors
tail -f server.log
```

#### Problem: QR Code won't scan
**Symptoms:**
- Authenticator app won't recognize QR code
- Scanner says "Invalid QR code"

**Solutions:**
```bash
# Save QR code to file and verify
echo "BASE64_STRING" | base64 -d > qr-test.png
file qr-test.png  # Should show "PNG image data"

# Try manual entry instead:
# Use the secret key directly in your authenticator app
```

### 2. MFA Login Issues

#### Problem: "Invalid MFA code" error
**Symptoms:**
- Correct-looking 6-digit code rejected
- Error: "Invalid MFA code"

**Solutions:**
1. **Check time synchronization:**
   ```bash
   # On macOS
   sudo sntp -sS time.apple.com
   
   # On Linux
   sudo ntpdate pool.ntp.org
   ```

2. **Try adjacent time windows:**
   - TOTP codes change every 30 seconds
   - Try the current code and the next one

3. **Verify secret in database:**
   ```sql
   SELECT email, mfa_secret FROM aaa_profiles 
   WHERE email = 'your_email@domain.com';
   ```

#### Problem: MFA required but user doesn't have MFA
**Symptoms:**
- Login returns "MFA required"
- But user never set up MFA

**Solutions:**
```sql
-- Check MFA status
SELECT email, mfa_secret IS NOT NULL as has_mfa 
FROM aaa_profiles 
WHERE email = 'user@domain.com';

-- Disable MFA if needed
UPDATE aaa_profiles 
SET mfa_secret = NULL 
WHERE email = 'user@domain.com';
```

### 3. Authentication Flow Issues

#### Problem: 402 status but can't verify MFA
**Symptoms:**
- Login returns HTTP 402
- MFA verification endpoint fails

**Debug steps:**
```bash
# 1. Verify MFA endpoint is available
curl -X POST "http://localhost:8001/docs" # Check API docs

# 2. Test with exact user email
curl -X POST "http://localhost:8001/auth/mfa/verify" \
  -H "Content-Type: application/json" \
  -d '{"email": "exact_email@domain.com", "mfa_code": "123456"}' \
  -v  # Verbose output for debugging

# 3. Check database for user
```

### 4. Database Issues

#### Problem: User not found errors
```sql
-- Verify user exists
SELECT id, email, is_admin, mfa_secret IS NOT NULL as has_mfa 
FROM aaa_profiles 
WHERE email = 'user@domain.com';

-- Check user roles
SELECT p.email, r.name as role
FROM aaa_profiles p
LEFT JOIN aaa_user_roles ur ON p.id = ur.user_id
LEFT JOIN aaa_roles r ON ur.role_id = r.id
WHERE p.email = 'user@domain.com';
```

#### Problem: Permission denied errors
```sql
-- Verify RLS is disabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename LIKE 'aaa_%';

-- Should show rowsecurity = false for all aaa_ tables
```

### 5. Server Configuration Issues

#### Problem: Environment variables not loading
```bash
# Check .env file exists and is readable
ls -la .env
cat .env | head -5  # Don't show secrets

# Verify variables are loaded
export PATH="/Users/siva/.local/bin:$PATH"
source .venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SUPABASE_URL:', 'SET' if os.getenv('SUPABASE_URL') else 'NOT SET')
print('JWT_SECRET_KEY:', 'SET' if os.getenv('JWT_SECRET_KEY') else 'NOT SET')
"
```

### 6. Authenticator App Issues

#### Google Authenticator
- **Time sync**: Settings → Time correction for codes → Sync now
- **Manual entry**: Choose "Enter a setup key"
- **Account name**: Use email address
- **Key type**: Time-based

#### Microsoft Authenticator
- **Add account**: Other (Google, Facebook, etc.)
- **Enter manually**: Use secret key
- **Account name**: Your email
- **Type**: Time-based

#### Authy
- **Add account**: Scan QR code or enter manually
- **Digits**: 6
- **Period**: 30 seconds
- **Algorithm**: SHA1

### 7. Testing MFA Setup

#### Quick Test Script
```bash
#!/bin/bash
# Save as test_mfa_simple.sh

EMAIL="your_admin@domain.com"
PASSWORD="your_password"

# Login
TOKEN=$(curl -s -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:20}..."

# Setup MFA
curl -X POST "http://localhost:8001/auth/mfa/setup?email=$EMAIL" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -m json.tool
```

### 8. Debugging Server Responses

#### Enable Detailed Logging
```python
# Add to main.py for debugging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# In routers/auth.py, add more debug info
logger.debug(f"MFA verification attempt for {request.email}")
logger.debug(f"Provided code: {request.mfa_code}")
logger.debug(f"Expected time window: {totp.now()}")
```

#### Check API Response Format
```bash
# Pretty print JSON responses
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test"}' | \
  python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print('Invalid JSON response')
"
```

### 9. Reset MFA for User

#### Complete MFA Reset Process
```sql
-- 1. Remove MFA secret
UPDATE aaa_profiles 
SET mfa_secret = NULL 
WHERE email = 'user@domain.com';

-- 2. Verify removal
SELECT email, mfa_secret IS NULL as mfa_disabled 
FROM aaa_profiles 
WHERE email = 'user@domain.com';
```

```bash
# 3. Test login (should work without MFA)
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@domain.com", "password": "password"}'

# 4. Setup MFA again
curl -X POST "http://localhost:8001/auth/mfa/setup?email=user@domain.com" \
  -H "Authorization: Bearer NEW_TOKEN"
```

### 10. Production Checklist

#### Before Deploying MFA
- [ ] Test MFA setup with at least 3 different authenticator apps
- [ ] Verify time synchronization on server
- [ ] Test MFA with multiple admin users
- [ ] Document recovery process for lost devices
- [ ] Set up monitoring for failed MFA attempts
- [ ] Create admin override process for emergencies

#### Security Considerations
- [ ] MFA secrets are never logged
- [ ] Failed attempts are rate-limited
- [ ] Backup admin account exists
- [ ] Recovery codes implemented (optional)
- [ ] MFA is enforced for all admin accounts

### 11. Emergency Recovery

#### Lost Authenticator Device
```sql
-- Temporarily disable MFA for emergency access
UPDATE aaa_profiles 
SET mfa_secret = NULL 
WHERE email = 'admin@domain.com' 
AND is_admin = true;

-- Log the emergency access
INSERT INTO audit_log (action, user_email, timestamp, reason)
VALUES ('MFA_DISABLED', 'admin@domain.com', NOW(), 'Lost authenticator device');
```

#### Backup Access Methods
1. **Backup Admin Account**: Always have a second admin account
2. **Database Access**: Direct database modification as last resort
3. **Recovery Codes**: Implement one-time backup codes (future enhancement)

## 📞 Getting Help

If you're still experiencing issues:

1. **Check server logs** for detailed error messages
2. **Verify database** connection and table structure
3. **Test with curl** commands for exact API behavior
4. **Review environment** variables and configuration
5. **Create minimal test case** to isolate the problem

## 🔧 Useful Commands

```bash
# Server status
curl -s http://localhost:8001/ || echo "Server down"

# Check database connection
python3 -c "
from database import supabase
print('DB Connection:', supabase.table('aaa_profiles').select('count').execute())
"

# Test JWT generation
python3 -c "
from routers.auth import create_access_token
from datetime import timedelta
token = create_access_token({'test': 'data'}, timedelta(minutes=5))
print('JWT Test:', token[:20] + '...')
"

# Validate environment
env | grep -E "(SUPABASE|JWT)" | sort
```