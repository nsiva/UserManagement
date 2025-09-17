# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a full-stack User Management system with two main components:

- **Api/**: FastAPI backend with JWT authentication and MFA support
- **WebUI/**: Angular 20 frontend with TypeScript and Tailwind CSS

Each component has its own CLAUDE.md with detailed setup instructions.

## Development Commands

### Backend (Api/)
```bash
cd Api

# Quick start (installs UV and dependencies)
./scripts/install.sh
source .venv/bin/activate
./scripts/start.sh  # Runs on port 8001

# Quality tools (configured in pyproject.toml)
uv run black .
uv run isort .
uv run flake8 .
uv run mypy .
uv run pytest tests/ -v

# MFA testing
./scripts/test_mfa.sh

# Database management tools
./scripts/db-tools.sh help                        # Show database tools help
./scripts/db-tools.sh setup                       # Generate database setup SQL (public schema)
./scripts/db-tools.sh setup --schema user_mgmt    # Generate with custom schema
./scripts/db-tools.sh quick-setup                 # Quick setup with instructions
./scripts/db-tools.sh inspect                     # Inspect existing database
./scripts/db-tools.sh export json                 # Export data as JSON
```

### Frontend (WebUI/user-management-app/)
```bash
cd WebUI/user-management-app

# Development server
npm run start  # Runs on port 4201

# Build and test
npm run build
npm run test
ng generate component component-name  # Non-standalone components
```

## Core Architecture

### Authentication Flow
This system implements custom JWT authentication (not using Supabase Auth):

1. **Backend**: Python handles all auth logic with bcrypt password hashing
2. **Database**: Supabase PostgreSQL for data storage only (aaa_* tables)
3. **MFA**: TOTP-based with QR code generation for authenticator apps
4. **Frontend**: JWT tokens stored in localStorage, AuthGuard for route protection

### Key Integration Points
- Backend API runs on port 8001, frontend on port 4201
- CORS configured for localhost:4201 in FastAPI main.py:29
- API endpoints defined in WebUI/user-management-app/src/app/api-paths.ts
- AuthService manages JWT tokens and user sessions

### Database Schema
All tables use `aaa_` prefix with Row Level Security disabled:
- `aaa_profiles`: Users with bcrypt password hashes and MFA secrets
- `aaa_roles`: Role definitions (viewer, editor, manager, admin)  
- `aaa_user_roles`: User-role relationships
- `aaa_clients`: API client credentials for client_credentials flow

### Component Structure
**Backend routers**:
- `auth.py`: Login, MFA verification, client credentials
- `admin.py`: User CRUD operations (admin or API client access)
- `profiles.py`: User profile endpoints

**Frontend components** (traditional modules, not standalone):
- LoginComponent handles both login and MFA verification
- AdminDashboardComponent protected by role-based AuthGuard
- MfaSetupModalComponent displays QR codes for MFA setup

## Environment Setup

**Backend (.env)**:
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` for database access
- `JWT_SECRET_KEY` for token signing
- `PORT` (defaults to 8001)

**Frontend**: API URL configured in src/environments/environment.ts

## Multi-Factor Authentication

MFA uses TOTP with 30-second windows. Setup flow:
1. Admin calls `/auth/mfa/setup?email=user@example.com`
2. Returns QR code (base64) and secret for authenticator app
3. Subsequent logins require 6-digit TOTP code via `/auth/mfa/verify`
4. Test with `./scripts/test_mfa.sh` in Api directory