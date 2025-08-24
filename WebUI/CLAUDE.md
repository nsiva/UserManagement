# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is an Angular 20 user management application with TypeScript and Tailwind CSS. The main application code is in `/user-management-app/` subdirectory.

### Key Architecture Components

- **Authentication Flow**: Custom JWT-based authentication with multi-factor authentication (MFA) support
- **Role-Based Access Control**: Admin and user roles with route guards
- **Backend Integration**: Python FastAPI backend running on localhost:8001
- **Component Structure**: Non-standalone Angular components with traditional module-based architecture

### Authentication System

The app uses a custom authentication flow instead of third-party providers:
- Login component handles initial authentication
- MFA component for two-factor authentication verification
- AuthService manages JWT tokens and user sessions in localStorage
- AuthGuard protects routes based on authentication status and user roles
- API endpoints defined in `src/app/api-paths.ts`

### Component Architecture

- `LoginComponent`: Handles initial login and MFA verification in a single component
- `AdminDashboardComponent`: Admin-only interface protected by role-based guard
- `ProfileComponent`: User profile management
- `MfaComponent`: Standalone MFA verification component
- `MfaSetupModalComponent`: Modal for MFA setup with QR code display

## Development Commands

The project uses Angular CLI with custom port configuration.

### Essential Commands
```bash
# Navigate to application directory first
cd user-management-app

# Development server (runs on port 4201)
npm run start
# or
ng serve --port 4201

# Build for production
npm run build
# or 
ng build

# Run unit tests
npm run test
# or
ng test

# Build and watch for changes
npm run watch
# or
ng build --watch --configuration development
```

### Code Generation
```bash
# Generate new component (non-standalone)
ng generate component component-name

# Generate service
ng generate service services/service-name

# Generate guard
ng generate guard guards/guard-name
```

## Configuration Details

### Environment Configuration
- API base URL configured in `src/environments/environment.ts` (currently localhost:8001)
- Angular serves on port 4201 (configured in package.json)

### TypeScript Configuration
- Strict mode enabled with comprehensive type checking
- Angular compiler options configured for strict templates and injection parameters
- Project uses traditional module-based architecture (not standalone components)

### Styling
- Tailwind CSS configured for utility-first styling
- SCSS support for component-specific styles
- Prettier configured with Angular HTML parser

## Backend Integration

The application expects a Python FastAPI backend with the following endpoints:
- `POST /auth/login` - User authentication
- `POST /auth/mfa/verify` - MFA verification
- `GET /profiles/me` - User profile data

Authentication uses JWT tokens stored in localStorage with role-based access control.

## Testing

- Karma and Jasmine configured for unit testing
- Angular testing utilities with Chrome launcher
- Coverage reporting enabled