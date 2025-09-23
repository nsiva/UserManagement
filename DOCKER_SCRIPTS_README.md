# Docker Build and Run Scripts

This directory contains comprehensive scripts for building, packaging, and running the User Management System Docker images.

## 📦 Scripts Overview

### `build-docker-images.sh`
Builds Docker images for both API and WebUI applications and exports them as tar files for easy distribution.

### `run-docker-images.sh`
Loads Docker images from tar files and manages container lifecycle (run, stop, logs, etc.).

## 🚀 Quick Start

### 1. Build Both Applications
```bash
# Build both API and WebUI with default settings
./build-docker-images.sh

# Build with custom tag and API URL
./build-docker-images.sh -t v1.0.0 -a https://api.myapp.com

# Build only API with verbose output
./build-docker-images.sh --api-only --verbose
```

### 2. Run the Applications
```bash
# Load images and run both containers
./run-docker-images.sh load
./run-docker-images.sh run

# Check status
./run-docker-images.sh status

# View logs
./run-docker-images.sh logs --follow
```

### 3. Stop and Clean Up
```bash
# Stop containers
./run-docker-images.sh stop

# Clean up everything
./run-docker-images.sh clean
```

## 📋 Build Script Features

### Command Line Options
- `--tag TAG` - Set custom image tag
- `--api-url URL` - Set API URL for WebUI build
- `--output DIR` - Custom output directory for tar files
- `--api-only` / `--webui-only` - Build specific application
- `--no-export` - Don't create tar files
- `--clean` - Clean existing images before building
- `--verbose` - Show detailed build output

### Examples
```bash
# Development build
./build-docker-images.sh -t dev --verbose

# Production build with custom API URL
./build-docker-images.sh -t prod -a https://api.production.com

# Quick API-only build for testing
./build-docker-images.sh --api-only -t test --no-export
```

## 🏃 Run Script Features

### Available Commands
- `load` - Load Docker images from tar files
- `run` - Start containers in background
- `stop` - Stop running containers
- `status` - Show container status
- `logs` - Display container logs
- `clean` - Remove containers and images

### Command Line Options
- `--tag TAG` - Specify image tag to use
- `--dir DIR` - Directory containing tar files
- `--api-port PORT` - Custom API port mapping
- `--webui-port PORT` - Custom WebUI port mapping
- `--api-only` / `--webui-only` - Work with specific container
- `--follow` - Follow log output (for logs command)

### Examples
```bash
# Load and run with custom ports
./run-docker-images.sh load -t v1.0.0
./run-docker-images.sh run --api-port 8080 --webui-port 3000

# Monitor API logs
./run-docker-images.sh logs --api-only --follow

# Work with specific version
./run-docker-images.sh run -t v1.0.0
```

## 🌐 Default Ports and URLs

| Service | Container Port | Host Port | URL |
|---------|---------------|-----------|-----|
| API | 8001 | 8001 | http://localhost:8001 |
| WebUI | 80 | 4201 | http://localhost:4201 |

## 📁 Output Structure

```
docker-images/
├── user-management-api_latest.tar     # API Docker image
└── user-management-webui_latest.tar   # WebUI Docker image
```

## 🔧 Container Names

- **API Container**: `user-management-api-container`
- **WebUI Container**: `user-management-webui-container`

## 📊 Build Process

### API Application
1. Multi-stage Docker build using Python 3.11
2. UV package manager for dependency management
3. Virtual environment setup and activation
4. Application code copying with .dockerignore filtering
5. Non-root user configuration for security

### WebUI Application
1. Node.js build stage with Angular CLI
2. Production build with configurable API URL
3. Nginx serving stage with security headers
4. Health check endpoint configuration
5. Static asset caching optimization

## 🛡️ Security Features

### API Container
- Non-root user execution
- Minimal base image (Python slim)
- Environment variable security
- Health check monitoring

### WebUI Container
- Security headers (XSS, CSRF protection)
- Content Security Policy
- Cache control for static assets
- Nginx security configuration

## 🐛 Troubleshooting

### Build Issues
```bash
# Check Docker is running
docker info

# Verbose build output
./build-docker-images.sh --verbose

# Clean build
./build-docker-images.sh --clean --verbose
```

### Runtime Issues
```bash
# Check container status
./run-docker-images.sh status

# View container logs
./run-docker-images.sh logs --follow

# Test container health
docker exec user-management-api-container curl http://localhost:8001/
docker exec user-management-webui-container curl http://localhost/health
```

### Port Conflicts
```bash
# Use custom ports
./run-docker-images.sh run --api-port 8080 --webui-port 3000

# Check what's using ports
lsof -i :8001
lsof -i :4201
```

## 📚 Additional Resources

- **API Documentation**: See `Api/CLAUDE.md` for backend setup
- **WebUI Documentation**: See `WebUI/CLAUDE.md` for frontend setup
- **Docker Best Practices**: Both Dockerfiles follow multi-stage builds and security best practices

## 🤝 Contributing

When adding new dependencies or changing the application structure:

1. **API Changes**: Update `Api/.dockerignore` if needed
2. **WebUI Changes**: Update WebUI build configuration
3. **Test Builds**: Always test with `--verbose` flag
4. **Update Scripts**: Modify scripts if new requirements arise

## 📝 Notes

- Docker images are optimized for production use
- Tar files enable easy distribution without Docker registries  
- Scripts include comprehensive error handling and logging
- Both applications support health checks for monitoring
- Environment variables can be customized for different deployments