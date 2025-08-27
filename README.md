# User Management System

A full-stack user management application with JWT authentication, multi-factor authentication (MFA), and role-based access control.

## Architecture

- **Backend**: FastAPI with Python 3.11, JWT authentication, TOTP-based MFA
- **Frontend**: Angular 20 with TypeScript and Tailwind CSS
- **Database**: Supabase PostgreSQL (data storage only)
- **Deployment**: Docker with multi-service orchestration

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- Supabase account (for database)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd UserManagement

# Copy environment template
cp .env.example .env

# Edit .env with your actual values
nano .env
```

Required environment variables:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
JWT_SECRET_KEY=your-very-secure-secret-key-here-at-least-32-characters
```

### 2. Database Setup

Create the following tables in your Supabase database using the SQL Editor:

```sql
-- Run the SQL from Api/sqls/Tables.sql
-- This creates aaa_profiles, aaa_roles, aaa_user_roles, aaa_clients tables
```

### 3. Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Applications

- **Frontend**: http://localhost:4201
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

### 5. Create Admin User

```bash
# Execute into the backend container
docker exec -it user-management-api bash

# Run the admin creation script
python sqls/create_admin.py
```

## Docker Services

### Backend Service (FastAPI)
- **Image**: Built from `Api/Dockerfile`
- **Port**: 8001
- **Health Check**: `http://localhost:8001/`
- **Features**: JWT auth, MFA, role-based access

### Frontend Service (Angular)
- **Image**: Built from `WebUI/user-management-app/Dockerfile`
- **Port**: 4201 (mapped to container port 80)
- **Health Check**: `http://localhost/health`
- **Features**: Angular 20, Tailwind CSS, responsive UI

### Additional Services
- **Redis**: Caching and session management (port 6379)
- **Nginx**: Reverse proxy (production profile only)

## Docker Commands

### Development
```bash
# Start all services
docker-compose up

# Rebuild specific service
docker-compose up --build backend
docker-compose up --build frontend

# View logs
docker-compose logs backend
docker-compose logs frontend

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production
```bash
# Run with Nginx reverse proxy
docker-compose --profile production up -d --build

# This exposes:
# - Frontend: http://localhost (port 80)
# - Backend API: http://localhost/api
```

### Individual Service Management
```bash
# Build and run backend only
docker build -t user-management-api ./Api
docker run -p 8001:8001 --env-file ./Api/.env user-management-api

# Build and run frontend only
docker build -t user-management-web ./WebUI/user-management-app
docker run -p 4201:80 user-management-web
```

## Development Setup (Non-Docker)

### Backend Development
```bash
cd Api

# Install UV and dependencies
./scripts/install.sh

# Activate environment
source .venv/bin/activate

# Start development server
./scripts/start.sh
```

### Frontend Development
```bash
cd WebUI/user-management-app

# Install dependencies
npm install

# Start development server
npm run start
```

## Authentication Flow

1. **Login**: Email/password authentication
2. **MFA Setup**: Admin generates QR code for users
3. **MFA Verification**: TOTP codes from authenticator apps
4. **JWT Tokens**: Secure API access with role-based permissions

### Default Admin Setup
```bash
# Using Docker
docker exec -it user-management-api python sqls/create_admin.py

# Local development
cd Api && python sqls/create_admin.py
```

## API Endpoints

- `POST /auth/login` - User authentication
- `POST /auth/mfa/verify` - MFA verification
- `POST /auth/mfa/setup` - MFA setup (admin only)
- `GET /profiles/me` - User profile
- `GET /admin/users` - List users (admin only)
- `POST /admin/users` - Create user (admin only)

Full API documentation: http://localhost:8001/docs

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using ports
lsof -ti:8001 # Backend port
lsof -ti:4201 # Frontend port

# Kill processes if needed
lsof -ti:8001 | xargs kill -9
lsof -ti:4201 | xargs kill -9
```

**Docker build issues:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Environment issues:**
```bash
# Verify environment variables
docker-compose config

# Check service logs
docker-compose logs backend
```

### Database Connection Issues
1. Verify Supabase URL and service key in `.env`
2. Check if tables exist in Supabase
3. Ensure Row Level Security is disabled on `aaa_*` tables

### MFA Issues
- See `Api/TROUBLESHOOTING.md` for detailed MFA debugging
- Test MFA setup: `docker exec -it user-management-api bash -c "./scripts/test_mfa.sh"`

## Security Notes

- All passwords are hashed with bcrypt
- JWT tokens expire after 30 minutes (configurable)
- MFA uses TOTP with 30-second windows
- Docker containers run as non-root users
- CORS configured for localhost development

## Contributing

1. Make changes to respective service directories
2. Test locally with Docker Compose
3. Ensure all health checks pass
4. Update documentation as needed

For detailed development instructions, see:
- `Api/CLAUDE.md` - Backend development guide
- `WebUI/CLAUDE.md` - Frontend development guide