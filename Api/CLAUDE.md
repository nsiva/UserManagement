# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Setup with UV (Recommended)
```bash
# Install UV and set up environment (first time only)
./scripts/install.sh

# Activate environment
source .venv/bin/activate

# Start the server
./scripts/start.sh
```

### Manual UV Setup
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/Users/siva/.local/bin:$PATH"

# Create virtual environment
uv venv --python 3.11

# Install dependencies
uv pip install fastapi uvicorn 'passlib[bcrypt]' 'python-jose[cryptography]' supabase pyotp 'qrcode[pil]' python-dotenv httpx pydantic-settings 'pydantic[email]'

# Activate environment
source .venv/bin/activate

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Testing and Quality Commands
```bash
# Run tests (if test framework exists)
uv run pytest tests/ -v

# Code formatting and linting (configured in pyproject.toml)
uv run black .
uv run isort .
uv run flake8 .
uv run mypy .

# Run MFA testing script
./scripts/test_mfa.sh

# Check server health
curl -s http://localhost:8001/ || echo "Server not running"
```

The application runs on port 8001 by default (configurable via PORT environment variable).

### Environment Setup
- Copy `.env.example` to `.env` if it exists, or create `.env` with required variables:
  - `SUPABASE_URL`: Your Supabase project URL (for data storage only)
  - `SUPABASE_SERVICE_KEY`: Supabase service role key (for direct database access)
  - `JWT_SECRET_KEY`: Secret key for JWT token signing
  - `ALGORITHM`: JWT algorithm (e.g., "HS256")
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
  - `PORT`: Server port (default: 8001)

## Architecture Overview

### Core Structure
This is a FastAPI-based User Management API with the following key components:

**Main Application (`main.py`)**
- FastAPI application setup with CORS middleware
- Router inclusion and basic error handling
- Runs on uvicorn server

**Database Layer (`database.py`)**
- Supabase client initialization for data storage only
- Uses service key for direct database access (no auth features)

**Data Models (`models.py`)**
- Pydantic models for request/response validation
- Auth models: `LoginRequest`, `MFARequest`, `TokenResponse`, `TokenData`
- User management: `UserCreate`, `UserUpdate`, `UserWithRoles`, `UserInDB` (includes password_hash)
- Role management: `RoleCreate`, `RoleInDB`
- Client credentials: `ClientTokenRequest`, `ClientTokenResponse`
- Profile models: `ProfileResponse`

### Router Organization

**Authentication Router (`routers/auth.py`)**
- Pure Python JWT token-based authentication with bcrypt password hashing
- MFA support using TOTP (Time-based One-Time Password)
- Client credentials flow for API access
- Password verification and hashing handled entirely in Python
- Dependencies: `get_current_user`, `get_current_admin_user`, `get_current_client`
- Endpoints: `/auth/login`, `/auth/mfa/verify`, `/auth/mfa/setup`, `/auth/token`

**Admin Router (`routers/admin.py`)**
- Complete user lifecycle management (CRUD operations)
- Role management and user-role assignments
- Dual authentication support (admin users OR API clients with proper scopes)
- Pure Python user creation with password hashing (no Supabase Auth dependency)
- Endpoints: `/admin/users/*`, `/admin/roles/*`

**Profiles Router (`routers/profiles.py`)**
- User profile information retrieval
- Self-service profile access
- Endpoint: `/profiles/me`

### Database Schema (Supabase)
The application expects the following tables in Supabase:
- `aaa_profiles` - User profile data with hashed passwords (id, email, password_hash, is_admin, mfa_secret, created_at, updated_at)
- `aaa_roles` - Role definitions (id, name, created_at)
- `aaa_user_roles` - Many-to-many relationship between users and roles (user_id, role_id, assigned_at)
- `aaa_clients` - API client credentials for client_credentials flow (client_id, client_secret, name, scopes, is_active, created_at, updated_at)

### Key Features
1. **Pure Python Authentication**: Complete control over authentication logic without external auth services
2. **Bcrypt Password Hashing**: Secure password storage with industry-standard hashing
3. **Multi-Factor Authentication**: TOTP-based MFA with QR code generation
4. **Role-Based Access Control**: Flexible role assignment system
5. **Dual Authentication**: Supports both user sessions and API client authentication
6. **Admin Operations**: Complete user management through admin endpoints
7. **JWT Security**: Secure token-based authentication with configurable expiration

### Authentication Flow
1. **User Registration**: Admin creates user → password hashed with bcrypt → stored in aaa_profiles table
2. **User Login**: Email/password verification → JWT token (with MFA if enabled)
3. **Client Credentials**: client_id/client_secret → client JWT token with scopes
4. **Protected Routes**: Bearer token validation via dependencies
5. **Admin Operations**: Require admin user OR client with `manage:users` scope

### Error Handling Patterns
- Comprehensive logging throughout the application
- HTTPException raising with appropriate status codes
- Exception chaining with proper cleanup (e.g., deleting user_roles before user deletion)
- Sensitive information protection in error responses
- Password validation errors return generic "Incorrect email or password" messages

### Important Notes
- **Supabase Usage**: Only used for data storage, not authentication
- **Password Security**: All passwords are hashed with bcrypt before storage
- **Database Direct Access**: Uses service role key for direct database operations
- **No External Auth Dependencies**: Complete authentication control within the Python application
- **Table Prefix**: All tables use `aaa_` prefix to avoid conflicts with existing tables
- **RLS Disabled**: All application tables have Row Level Security disabled for direct access
- **UV Environment**: Modern Python package management with faster dependency resolution
- **Python 3.11**: Recommended Python version for optimal performance

### Development Tools
- **UV**: Fast Python package installer and resolver (configured in pyproject.toml)
- **FastAPI**: Modern async web framework with automatic OpenAPI docs at `/docs`
- **Uvicorn**: ASGI server with auto-reload for development
- **Bcrypt**: Industry-standard password hashing
- **Supabase**: PostgreSQL database as a service

### Code Quality Tools (Pre-configured)
- **Black**: Code formatter (88 char line length)
- **isort**: Import sorting (black-compatible profile)
- **Flake8**: Style guide enforcement
- **MyPy**: Static type checking
- **Pytest**: Testing framework with async support

## Multi-Factor Authentication (MFA) Setup

### Overview
The application supports TOTP-based MFA using authenticator apps like Google Authenticator, Microsoft Authenticator, or Authy.

### Setting Up MFA for Admin Users

#### Step 1: Login as Admin
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your_admin@email.com", "password": "your_password"}'
```

Save the returned `access_token` for the next step.

#### Step 2: Setup MFA
```bash
curl -X POST "http://localhost:8001/auth/mfa/setup?email=your_admin@email.com" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

This returns:
- `qr_code_base64`: QR code image in base64 format
- `secret`: TOTP secret key
- `provisioning_uri`: URI for manual entry

#### Step 3: Configure Authenticator App
1. **Option A: Scan QR Code**
   - Decode the base64 QR code and scan with your authenticator app
   - Or save the base64 to a file and open: `echo "BASE64_STRING" | base64 -d > qr.png`

2. **Option B: Manual Entry**
   - Open your authenticator app
   - Choose "Enter a setup key" or "Manual entry"
   - Enter the secret key and account name

#### Step 4: Test MFA Login
```bash
# This will now require MFA
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your_admin@email.com", "password": "your_password"}'

# You'll get a 402 error with "MFA required" message
# Then use the MFA verification endpoint:
curl -X POST "http://localhost:8001/auth/mfa/verify" \
  -H "Content-Type: application/json" \
  -d '{"email": "your_admin@email.com", "mfa_code": "123456"}'
```

### MFA Workflow
1. **First Login**: User logs in with email/password
2. **MFA Check**: System checks if user has MFA enabled
3. **MFA Required**: If enabled, login returns 402 status with "MFA required"
4. **MFA Verification**: User provides 6-digit TOTP code
5. **Access Granted**: System validates TOTP and returns JWT token

### MFA Management
- **Enable MFA**: Use `/auth/mfa/setup` endpoint (admin only)
- **Disable MFA**: Update user's `mfa_secret` to `NULL` in database
- **Reset MFA**: Generate new secret using setup endpoint again
- **Test MFA**: Use `./scripts/test_mfa.sh` for automated testing

### Security Notes
- MFA secrets are stored encrypted in the database
- TOTP codes are time-based (30-second windows)
- Failed MFA attempts should be logged and monitored
- Admin users should always have MFA enabled in production

## Development Workflows

### Adding New Endpoints
1. **Define Models**: Add Pydantic models in `models.py`
2. **Create Router Function**: Add endpoint function to appropriate router
3. **Add Dependencies**: Use `get_current_user` or `get_current_admin_user` for protection
4. **Update Router**: Include new router in `main.py` if creating new router file
5. **Test**: Use FastAPI docs at `http://localhost:8001/docs` for testing

### Database Changes
1. **Update Schema**: Modify `sqls/Tables.sql` with new tables/columns
2. **Run SQL**: Execute changes in Supabase SQL Editor
3. **Update Models**: Add corresponding Pydantic models in `models.py`
4. **Test Queries**: Verify database operations work correctly

### Troubleshooting Common Issues
- **MFA Issues**: See `TROUBLESHOOTING.md` for comprehensive MFA debugging
- **Environment Issues**: Verify `.env` file and use `env | grep -E "(SUPABASE|JWT)"` to check
- **Database Issues**: Ensure RLS is disabled on `aaa_*` tables and service key is used
- **Port Issues**: Check if port 8001 is available: `lsof -ti:8001 | xargs kill -9`

### Key File Locations
- `main.py` - FastAPI application entry point
- `database.py` - Supabase client configuration  
- `models.py` - All Pydantic models for request/response validation
- `routers/auth.py` - Authentication endpoints (login, MFA)
- `routers/admin.py` - Admin user management endpoints
- `routers/profiles.py` - User profile endpoints
- `scripts/` - Utility scripts (install, start, test MFA)
- `sqls/Tables.sql` - Database schema definition
- `TROUBLESHOOTING.md` - Comprehensive MFA troubleshooting guide