### Development Environment
```bash
# API for development
docker build -t user-management-api:dev ./Api/

# WebUI for development (connects to local API)
docker build --build-arg API_URL=http://localhost:8001 -t user-management-web:dev ./WebUI/user-management-app/


 docker run -p 8001:8001 --name user-management-api-dev --env-file  ./Api/.env_local_aaa_test user-management-api:dev

 docker run -p 4201:80 --name user-management-web-dev  user-management-web:dev
