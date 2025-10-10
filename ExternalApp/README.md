# ExternalApp

Test application to demonstrate User Management redirect_uri functionality.

This application mirrors the UserManagement architecture with:
- **Api/**: FastAPI backend 
- **WebUI/**: Angular frontend

## Purpose

This app demonstrates how external applications can integrate with the User Management system by:
1. Redirecting users to UserManagement for authentication
2. Receiving users back after successful login (including MFA)
3. Providing a protected dashboard that requires authentication

## Architecture

- **Backend**: FastAPI running on port 8002
- **Frontend**: Angular running on port 4202  
- **Authentication**: Delegates to UserManagement system at localhost:4201

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

## Usage

1. Visit http://localhost:4202
2. Click "Login" - you'll be redirected to UserManagement
3. Complete authentication (including MFA if enabled)
4. You'll be redirected back to ExternalApp dashboard