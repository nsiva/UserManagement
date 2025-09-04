# Docker Build and Deployment Guide

This guide covers building and running Docker images for both the API backend and WebUI frontend with configurable parameters.

## API Service (FastAPI Backend)

### Build Arguments

The API Dockerfile currently doesn't expose build arguments, but you can pass environment variables at runtime.

#### Basic Build
```bash
# Build from project root
docker build -f Api/Dockerfile -t user-management-api ./Api/

# Build from Api directory
cd Api
docker build -t user-management-api .
```

#### Runtime Environment Variables
```bash
# Required environment variables
docker run -d \
  -p 8001:8001 \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_SERVICE_KEY=your-service-key \
  -e JWT_SECRET_KEY=your-secret-key-32-chars-minimum \
  -e PORT=8001 \
  --name user-management-api \
  user-management-api
```

#### Environment File Approach
```bash
# Create .env file with your settings
echo "SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
JWT_SECRET_KEY=your-secret-key-32-chars-minimum
PORT=8001" > .env

# Run with environment file
docker run -d \
  -p 8001:8001 \
  --env-file .env \
  --name user-management-api \
  user-management-api
```

### API Service Features
- **Port**: 8001 (configurable via PORT environment variable)
- **Health Check**: Built-in health check at `http://localhost:8001/`
- **Security**: Runs as non-root user
- **Documentation**: Available at `http://localhost:8001/docs`

---

## WebUI Service (Angular Frontend)

### Build Arguments

The WebUI Dockerfile supports configurable API URL through build arguments.

#### Available Build Arguments
- `API_URL`: Backend API URL (default: `http://localhost:8001`)

#### Build Examples

**Default Build (API on localhost:8001):**
```bash
# Build from project root
docker build -f WebUI/user-management-app/Dockerfile -t user-management-ui ./WebUI/user-management-app/

# Build from WebUI directory  
cd WebUI/user-management-app
docker build -t user-management-ui .
```

**Custom API URL:**
```bash
# Different port
docker build --build-arg API_URL=http://localhost:8081 -t user-management-ui .

# Remote API server
docker build --build-arg API_URL=https://api.example.com -t user-management-ui .

# Docker network (for use with docker-compose)
docker build --build-arg API_URL=http://backend:8001 -t user-management-ui .

# Production API
docker build --build-arg API_URL=https://api.production.com -t user-management-ui:prod .
```

#### Running WebUI Container
```bash
# Run with default port mapping
docker run -d -p 4201:80 --name user-management-ui user-management-ui

# Custom port mapping
docker run -d -p 8080:80 --name user-management-ui user-management-ui
```

### WebUI Service Features
- **Port**: 80 (nginx), map to any host port
- **Health Check**: Available at `/health` endpoint
- **Angular Routing**: SPA routing fully supported
- **Security Headers**: XSS protection, CSP, frame options
- **Static Caching**: Optimized caching for assets

---

## Multi-Environment Builds

### Development Environment
```bash
# API for development
docker build -t user-management-api:dev ./Api/

# WebUI for development (connects to local API)
docker build --build-arg API_URL=http://localhost:8001 -t user-management-ui:dev ./WebUI/user-management-app/
```

### Staging Environment
```bash
# API for staging
docker build -t user-management-api:staging ./Api/

# WebUI for staging (connects to staging API)
docker build --build-arg API_URL=https://api-staging.example.com -t user-management-ui:staging ./WebUI/user-management-app/
```

### Production Environment
```bash
# API for production
docker build -t user-management-api:prod ./Api/

# WebUI for production (connects to production API)
docker build --build-arg API_URL=https://api.example.com -t user-management-ui:prod ./WebUI/user-management-app/
```

---

## Docker Compose Configurations

### Development Setup
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build:
      context: ./Api
    ports:
      - "8001:8001"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    networks:
      - app-network

  frontend:
    build:
      context: ./WebUI/user-management-app
      args:
        API_URL: http://backend:8001
    ports:
      - "4201:80"
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### Production Setup with Nginx Proxy
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./Api
    expose:
      - "8001"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    networks:
      - app-network

  frontend:
    build:
      context: ./WebUI/user-management-app
      args:
        API_URL: http://nginx/api
    expose:
      - "80"
    depends_on:
      - backend
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## Build Commands Reference

### API Service Commands
```bash
# Basic build
docker build -t user-management-api ./Api/

# Build with tag
docker build -t user-management-api:v1.0.0 ./Api/

# Build from project root
docker build -f Api/Dockerfile -t user-management-api ./Api/

# Run with environment variables
docker run -d \
  -p 8001:8001 \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_SERVICE_KEY=your-key \
  -e JWT_SECRET_KEY=your-secret \
  --name api \
  user-management-api
```

### WebUI Service Commands
```bash
# Basic build (default API URL: localhost:8001)
docker build -t user-management-ui ./WebUI/user-management-app/

# Build with custom API URL
docker build --build-arg API_URL=http://localhost:8081 -t user-management-ui ./WebUI/user-management-app/

# Build with remote API
docker build --build-arg API_URL=https://api.example.com -t user-management-ui ./WebUI/user-management-app/

# Build from project root
docker build -f WebUI/user-management-app/Dockerfile --build-arg API_URL=http://api:8001 -t user-management-ui ./WebUI/user-management-app/

# Run the WebUI container
docker run -d -p 4201:80 --name ui user-management-ui
```

---

## Verification Commands

### Check Build Arguments
```bash
# Verify API URL in WebUI image
docker run --rm user-management-ui cat /usr/share/nginx/html/assets/env.js

# Check API container environment
docker run --rm user-management-api env | grep -E "(SUPABASE|JWT|PORT)"
```

### Health Checks
```bash
# API health check
curl -f http://localhost:8001/ || echo "API not responding"

# WebUI health check
curl -f http://localhost:4201/health || echo "WebUI not responding"

# Container logs
docker logs user-management-api
docker logs user-management-ui
```

---

## Complete Deployment Example

### 1. Build Images
```bash
# Build API
docker build -t user-management-api:latest ./Api/

# Build WebUI with production API URL
docker build --build-arg API_URL=https://api.production.com -t user-management-ui:latest ./WebUI/user-management-app/
```

### 2. Run Services
```bash
# Start API with production environment
docker run -d \
  -p 8001:8001 \
  -e SUPABASE_URL=https://prod.supabase.co \
  -e SUPABASE_SERVICE_KEY=prod-service-key \
  -e JWT_SECRET_KEY=production-secret-key \
  --name production-api \
  user-management-api:latest

# Start WebUI (configured to connect to production API)
docker run -d \
  -p 80:80 \
  --name production-ui \
  user-management-ui:latest
```

### 3. Verify Deployment
```bash
# Check both services are running
docker ps

# Test API
curl -f http://localhost:8001/

# Test WebUI
curl -f http://localhost/health
```

---

## Troubleshooting

### Common Issues

**WebUI can't connect to API:**
- Check API URL in build args: `docker run --rm image cat /usr/share/nginx/html/assets/env.js`
- Verify API is accessible from WebUI container
- Check network configuration in docker-compose

**API database connection issues:**
- Verify Supabase environment variables are set
- Check service key permissions
- Ensure database tables exist with `aaa_` prefix

**Port conflicts:**
- Change host port mapping: `-p 8080:80` instead of `-p 4201:80`
- Check what's using the port: `lsof -i :4201`

**Permission denied in containers:**
- API runs as non-root user `appuser`
- WebUI runs as root (nginx requirement)
- Check file permissions if mounting volumes

### Debug Commands
```bash
# Run containers interactively for debugging
docker run -it --entrypoint /bin/sh user-management-api
docker run -it --entrypoint /bin/sh user-management-ui

# Check container filesystem
docker run --rm user-management-ui ls -la /usr/share/nginx/html/
docker run --rm user-management-api ls -la /app/

# Monitor container logs in real-time
docker logs -f user-management-api
docker logs -f user-management-ui
```

---

## Security Considerations

### API Security
- Runs as non-root user `appuser`
- Health checks monitor application status
- Environment variables for sensitive data
- JWT tokens with configurable expiration

### WebUI Security
- Security headers configured in nginx
- Content Security Policy (CSP) enabled
- XSS and clickjacking protection
- Static asset caching with proper headers

### Network Security
- Use Docker networks to isolate services
- Don't expose database directly
- Use HTTPS in production
- Configure proper CORS settings

### Secrets Management
- Never include secrets in Dockerfiles
- Use environment variables or Docker secrets
- Rotate JWT secret keys regularly
- Use strong Supabase service keys