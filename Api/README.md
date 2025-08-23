# User Management API

A secure, modern FastAPI-based user management system with JWT authentication, role-based access control, and Multi-Factor Authentication (MFA).

## 🚀 Features

- **🔐 Secure Authentication**: JWT tokens with bcrypt password hashing
- **🛡️ Multi-Factor Authentication**: TOTP-based MFA with QR code generation
- **👥 Role-Based Access Control**: Flexible user roles and permissions
- **⚡ Modern Stack**: FastAPI, UV package manager, Python 3.11
- **🗄️ Database**: Supabase PostgreSQL with direct table access
- **📱 API-First**: Complete REST API with automatic OpenAPI documentation
- **🔒 Security-First**: No external auth dependencies, full control over authentication

## 📋 Prerequisites

- Python 3.9+ (3.11 recommended)
- UV package manager (automatic installation via scripts)
- Supabase account and project
- Authenticator app (Google Authenticator, Microsoft Authenticator, Authy, etc.)

## 🛠️ Quick Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd UserManagement/Api

# One-click setup (installs UV and dependencies)
./scripts/install.sh

# Activate environment
source .venv/bin/activate
```

### 2. Configure Environment Variables

Create a `.env` file with:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_service_role_key
JWT_SECRET_KEY=your_strong_jwt_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=8001
```

### 3. Create Database Tables

Run this SQL in your Supabase SQL Editor:

```sql
-- User profiles table
CREATE TABLE aaa_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    mfa_secret TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Roles table
CREATE TABLE aaa_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User-Role junction table
CREATE TABLE aaa_user_roles (
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES aaa_roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- API clients table
CREATE TABLE aaa_clients (
    client_id TEXT PRIMARY KEY,
    client_secret TEXT NOT NULL,
    name TEXT,
    scopes TEXT[],
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable RLS for direct access
ALTER TABLE aaa_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_user_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE aaa_clients DISABLE ROW LEVEL SECURITY;

-- Create performance indexes
CREATE INDEX idx_aaa_profiles_email ON aaa_profiles(email);
CREATE INDEX idx_aaa_user_roles_user_id ON aaa_user_roles(user_id);
CREATE INDEX idx_aaa_user_roles_role_id ON aaa_user_roles(role_id);

-- Insert default roles
INSERT INTO aaa_roles (name) VALUES 
    ('viewer'),
    ('editor'),
    ('manager'),
    ('admin');
```

### 4. Create Admin User

```bash
# Generate admin user SQL
python3 generate_admin_sql.py
```

Copy the generated SQL and run it in Supabase SQL Editor.

### 5. Start the Server

```bash
# Start development server
./scripts/start.sh

# Server runs on http://localhost:8001
# API docs available at http://localhost:8001/docs
```

## 🔐 Multi-Factor Authentication (MFA) Setup

### For Admin Users

#### Step 1: Login and Get Token

```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "password": "SecureAdmin123!"}'
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "admin@yourdomain.com",
  "is_admin": true,
  "roles": ["admin"]
}
```

#### Step 2: Setup MFA

```bash
curl -X POST "http://localhost:8001/auth/mfa/setup?email=admin@yourdomain.com" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "qr_code_base64": "iVBORw0KGgo...",
  "secret": "35Y6OXFTT77RKOZW...",
  "provisioning_uri": "otpauth://totp/YourAppName:admin@yourdomain.com?secret=..."
}
```

#### Step 3: Configure Authenticator App

**Option A: QR Code Method**
1. Save QR code to file:
   ```bash
   echo "iVBORw0KGgo..." | base64 -d > mfa-qr.png
   ```
2. Open the PNG file and scan with your authenticator app

**Option B: Manual Entry**
1. Open Google Authenticator, Microsoft Authenticator, or Authy
2. Select "Enter a setup key" or "Manual entry"
3. Enter:
   - **Account name**: admin@yourdomain.com
   - **Secret key**: 35Y6OXFTT77RKOZW... (from API response)
   - **Type**: Time-based

#### Step 4: Test MFA Login

**First attempt (will require MFA):**
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "password": "SecureAdmin123!"}'
```

**Response (HTTP 402):**
```json
{
  "detail": "MFA required. Please provide MFA code."
}
```

**Complete login with MFA:**
```bash
curl -X POST "http://localhost:8001/auth/mfa/verify" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "mfa_code": "123456"}'
```

Replace `123456` with the 6-digit code from your authenticator app.

### For Regular Users

MFA can be set up for any user by an admin:

```bash
curl -X POST "http://localhost:8001/auth/mfa/setup?email=user@example.com" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 📱 Using Authenticator Apps

### Recommended Apps

1. **Google Authenticator**
   - iOS: [App Store](https://apps.apple.com/app/google-authenticator/id388497605)
   - Android: [Play Store](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)

2. **Microsoft Authenticator**
   - iOS: [App Store](https://apps.apple.com/app/microsoft-authenticator/id983156458)
   - Android: [Play Store](https://play.google.com/store/apps/details?id=com.azure.authenticator)

3. **Authy**
   - iOS: [App Store](https://apps.apple.com/app/authy/id494168017)
   - Android: [Play Store](https://play.google.com/store/apps/details?id=com.authy.authy)

### Setup Process

1. **Install** your preferred authenticator app
2. **Add Account** by either:
   - Scanning the QR code from MFA setup
   - Manually entering the secret key
3. **Verify** the setup by logging in with MFA

## 🔧 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login (email/password) |
| POST | `/auth/mfa/verify` | MFA verification with TOTP code |
| POST | `/auth/mfa/setup` | Setup MFA for a user (admin only) |
| POST | `/auth/token` | Client credentials authentication |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/users` | Create new user |
| GET | `/admin/users` | List all users |
| PUT | `/admin/users/{user_id}` | Update user |
| DELETE | `/admin/users/{user_id}` | Delete user |
| POST | `/admin/roles` | Create role |
| GET | `/admin/roles` | List roles |
| PUT | `/admin/roles/{role_id}` | Update role |
| DELETE | `/admin/roles/{role_id}` | Delete role |
| POST | `/admin/users/{user_id}/roles` | Assign roles to user |

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profiles/me` | Get current user profile |

## 🛠️ Development

### Project Structure

```
UserManagement/Api/
├── main.py                 # FastAPI application entry point
├── database.py            # Supabase client configuration
├── models.py              # Pydantic models for requests/responses
├── routers/
│   ├── auth.py           # Authentication endpoints
│   ├── admin.py          # Admin management endpoints
│   └── profiles.py       # User profile endpoints
├── scripts/
│   ├── install.sh        # Environment setup script
│   └── start.sh          # Server start script
├── sqls/
│   ├── create_admin.py   # Admin user creation script
│   └── Tables.sql        # Database schema
├── pyproject.toml        # UV project configuration
├── .env                  # Environment variables
├── CLAUDE.md            # Development documentation
└── README.md            # This file
```

### Development Commands

```bash
# Install dependencies
uv pip install -r requirements.txt

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Run with UV environment
source .venv/bin/activate
./scripts/start.sh
```

### Testing

```bash
# Test admin login
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "password": "SecureAdmin123!"}'

# Test API documentation
open http://localhost:8001/docs
```

## 🔒 Security Features

- **Password Hashing**: Bcrypt with configurable rounds
- **JWT Tokens**: Secure token-based authentication
- **MFA Support**: TOTP-based multi-factor authentication
- **Role-Based Access**: Granular permission system
- **API Rate Limiting**: Built-in protection against abuse
- **CORS Configuration**: Configurable cross-origin requests
- **Input Validation**: Pydantic model validation
- **SQL Injection Protection**: Parameterized queries

## 🚨 Troubleshooting

### Common Issues

**1. MFA Setup Not Working**
```bash
# Check if user exists and has admin privileges
curl -X GET "http://localhost:8001/admin/users" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**2. QR Code Not Scanning**
- Ensure the base64 string is complete
- Try manual entry with the secret key
- Check authenticator app supports TOTP

**3. MFA Code Invalid**
- Verify time sync on your device
- TOTP codes expire every 30 seconds
- Try the next code if current one fails

**4. Database Connection Issues**
```bash
# Verify environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
```

**5. Server Won't Start**
```bash
# Check port availability
lsof -i :8001

# Kill existing process
lsof -ti:8001 | xargs kill -9
```

### Environment Variables

Ensure all required environment variables are set:

```bash
# Check current environment
env | grep SUPABASE
env | grep JWT
```

### Database Issues

1. **RLS Policies**: Ensure Row Level Security is disabled for aaa_* tables
2. **Service Key**: Use service role key, not anon key
3. **Table Names**: All tables use `aaa_` prefix

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Supabase Documentation](https://supabase.com/docs)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)
- [JWT.io](https://jwt.io/) - JWT token debugger

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**⚠️ Security Notice**: Always use strong passwords, enable MFA for admin accounts, and keep your environment variables secure. Never commit secrets to version control.