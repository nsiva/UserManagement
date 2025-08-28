# Forgot Password API Setup Guide

## Overview
The forgot password functionality has been implemented with three new API endpoints that provide secure password recovery for users who cannot log in.

## New API Endpoints

### 1. POST /auth/forgot-password
- **Purpose**: Initiate password reset process
- **Input**: `{"email": "user@example.com"}`
- **Response**: Always returns success message (prevents email enumeration)
- **Security**: Rate limiting recommended, logs all attempts

### 2. GET /auth/verify-reset-token/{token}
- **Purpose**: Verify if reset token is valid
- **Input**: Token as URL parameter
- **Response**: `{"valid": true/false, "email": "masked_email"}`
- **Use Case**: Frontend validation before showing password reset form

### 3. POST /auth/set-new-password
- **Purpose**: Complete password reset with new password
- **Input**: `{"token": "reset_token", "new_password": "new_password"}`
- **Response**: Success confirmation
- **Security**: Single-use tokens, automatic invalidation

## Database Setup

1. **Run SQL Migration**:
   ```bash
   # Execute the contents of Api/sqls/password_reset_tokens.sql in your Supabase SQL Editor
   ```

2. **Table Created**: `aaa_password_reset_tokens`
   - Stores reset tokens with 30-minute expiration
   - Links to user profiles via foreign key
   - Tracks token usage to prevent reuse

## Environment Variables

Add these to your `.env` file:

```env
# Email Configuration (Required for forgot password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Token Expiration (Optional - defaults to 30 minutes)
RESET_TOKEN_EXPIRE_MINUTES=30
```

### Gmail Setup (Recommended)
1. Enable 2FA on your Gmail account
2. Generate an App Password: Google Account → Security → App passwords
3. Use the app password (not your regular password) in `SMTP_PASSWORD`

## Security Features

- **Cryptographically secure tokens** using Python's `secrets` module
- **Email enumeration protection** - always returns success
- **Token expiration** - 30-minute default lifetime
- **Single-use tokens** - automatically invalidated after use
- **Email masking** - logs show masked emails (e.g., u***r@example.com)
- **Comprehensive logging** - all attempts logged for security monitoring

## Testing the Implementation

### 1. Test Forgot Password Request
```bash
curl -X POST "http://localhost:8001/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### 2. Check Email for Reset Link
- Look for email with reset link
- Extract token from the URL

### 3. Verify Token
```bash
curl "http://localhost:8001/auth/verify-reset-token/YOUR_TOKEN_HERE"
```

### 4. Set New Password
```bash
curl -X POST "http://localhost:8001/auth/set-new-password" \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_HERE", "new_password": "new_secure_password"}'
```

## Frontend Integration

The reset link in emails points to: `http://localhost:4201/reset-password?token={token}`

Your Angular frontend should:
1. Extract token from URL parameters
2. Call verify-reset-token to validate
3. Show password reset form if valid
4. Call set-new-password when form is submitted

## Rate Limiting (Recommended)

Consider implementing rate limiting on the `/auth/forgot-password` endpoint to prevent abuse:
- 5 requests per IP per hour
- 3 requests per email per hour

## Monitoring

Monitor these log messages for security:
- Failed email sending attempts
- Invalid token usage attempts  
- High volume of reset requests from single IP

## Troubleshooting

### Email Not Sending
1. Check SMTP environment variables
2. Verify Gmail app password (not regular password)
3. Check firewall/network restrictions on SMTP port 587
4. Review application logs for detailed error messages

### Token Issues
1. Ensure database table was created successfully
2. Check token expiration settings
3. Verify tokens are being marked as used after successful reset

## Security Notes

- Store SMTP credentials securely (use environment variables)
- Consider using dedicated email service (SendGrid, AWS SES) for production
- Implement monitoring for unusual password reset patterns
- Regularly clean up expired tokens from database