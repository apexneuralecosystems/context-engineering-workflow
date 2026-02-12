# Port Configuration for Deployment

This document explains how ports are configured from environment variables when deploying to a server.

## Overview

Both backend and frontend services use environment variables to configure ports dynamically. This allows you to:
- Deploy to different servers with different port requirements
- Avoid port conflicts
- Configure ports from your deployment environment
- Use the same Docker images across different environments

## Backend Port Configuration

### Environment Variables

- `API_PORT` - Backend API server port (default: 8003)
  - Controls both the container's internal port and the host port mapping
  - Used in: Dockerfile EXPOSE, CMD, health checks, and docker-compose port mapping

### Configuration

**Docker Compose:**
```yaml
ports:
  - "${API_PORT:-8003}:${API_PORT:-8003}"
```

**Dockerfile:**
- EXPOSE uses: `${API_PORT:-8003}`
- CMD uses: `--port ${API_PORT}`
- Health check uses: `http://localhost:${API_PORT:-8003}/health`

### Example Deployment

```bash
# Set port from server environment
export API_PORT=8080

# Deploy - port will be automatically used
cd backend
docker-compose up -d --build

# Backend will be accessible on port 8080
curl http://localhost:8080/health
```

## Frontend Port Configuration

### Environment Variables

- `FRONTEND_PORT` - Host port for frontend access (default: 3003)
  - Controls the host port mapping
  - Nginx always runs on port 80 inside the container

- `NEXT_PUBLIC_API_URL` - Backend API URL (must include backend port)
  - Should be set at build time
  - Example: `http://localhost:8003` or `https://api.yourdomain.com`

- `API_PORT` - Backend port (optional, used for reference)

### Configuration

**Docker Compose:**
```yaml
ports:
  - "${FRONTEND_PORT:-3003}:80"
```

**Dockerfile:**
- EXPOSE: `80` (nginx internal port, fixed)
- Host port comes from `FRONTEND_PORT` environment variable

### Example Deployment

```bash
# Set ports from server environment
export FRONTEND_PORT=3000
export API_PORT=8080
export NEXT_PUBLIC_API_URL=http://localhost:8080

# Build with API URL
cd frontend
docker build --build-arg NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} -t frontend .

# Deploy
docker-compose up -d

# Frontend will be accessible on port 3000
curl http://localhost:3000/health
```

## Complete Deployment Example

### Step 1: Set Environment Variables on Server

```bash
# In your server's deployment script or .env file
export API_PORT=8003
export FRONTEND_PORT=3003
export NEXT_PUBLIC_API_URL=http://localhost:8003

# API Keys
export OPENROUTER_API_KEY=your_key
export TENSORLAKE_API_KEY=your_key
export VOYAGE_API_KEY=your_key
export ZEP_API_KEY=your_key
export FIRECRAWL_API_KEY=your_key
```

### Step 2: Deploy Backend

```bash
cd backend

# Create .env file (or use environment variables)
cat > .env << EOF
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
TENSORLAKE_API_KEY=${TENSORLAKE_API_KEY}
VOYAGE_API_KEY=${VOYAGE_API_KEY}
ZEP_API_KEY=${ZEP_API_KEY}
FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
API_PORT=${API_PORT}
FRONTEND_PORT=${FRONTEND_PORT}
EOF

# Deploy
docker-compose up -d --build
```

### Step 3: Deploy Frontend

```bash
cd frontend

# Create .env file
cat > .env << EOF
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
FRONTEND_PORT=${FRONTEND_PORT}
API_PORT=${API_PORT}
EOF

# Deploy
docker-compose up -d --build
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Backend
        env:
          API_PORT: ${{ secrets.API_PORT }}
          FRONTEND_PORT: ${{ secrets.FRONTEND_PORT }}
        run: |
          cd backend
          docker-compose up -d --build
      
      - name: Deploy Frontend
        env:
          FRONTEND_PORT: ${{ secrets.FRONTEND_PORT }}
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
        run: |
          cd frontend
          docker build --build-arg NEXT_PUBLIC_API_URL=${{ secrets.NEXT_PUBLIC_API_URL }} -t frontend .
          docker-compose up -d
```

### GitLab CI Example

```yaml
deploy:
  script:
    - export API_PORT=$API_PORT
    - export FRONTEND_PORT=$FRONTEND_PORT
    - export NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
    - cd backend && docker-compose up -d --build
    - cd ../frontend && docker-compose up -d --build
```

## Production Server Setup

### Using Systemd Environment Files

Create `/etc/systemd/system/context-engineering.env`:

```env
API_PORT=8003
FRONTEND_PORT=3003
NEXT_PUBLIC_API_URL=http://localhost:8003
```

Load in your deployment script:

```bash
set -a
source /etc/systemd/system/context-engineering.env
set +a

cd backend && docker-compose up -d
cd ../frontend && docker-compose up -d
```

### Using Docker Secrets (Production)

For production, use Docker secrets instead of environment variables:

```yaml
services:
  backend:
    secrets:
      - api_port
    environment:
      API_PORT_FILE: /run/secrets/api_port
```

## Verification

After deployment, verify ports are correctly configured:

```bash
# Check backend port
echo "Backend should be on port: $API_PORT"
curl http://localhost:${API_PORT}/health

# Check frontend port
echo "Frontend should be on port: $FRONTEND_PORT"
curl http://localhost:${FRONTEND_PORT}/health

# Check docker port mappings
docker port backend
docker port frontend
```

## Troubleshooting

### Port Not Accessible

1. **Check environment variable is set:**
   ```bash
   echo $API_PORT
   echo $FRONTEND_PORT
   ```

2. **Check docker-compose is using the variable:**
   ```bash
   docker-compose config | grep ports
   ```

3. **Check container is running:**
   ```bash
   docker ps
   ```

4. **Check port mapping:**
   ```bash
   docker port backend
   docker port frontend
   ```

### Port Conflicts

If a port is already in use:

```bash
# Find what's using the port
lsof -i :${API_PORT}
netstat -tulpn | grep ${API_PORT}

# Change the port
export API_PORT=9000
docker-compose down
docker-compose up -d
```

## Summary

- ✅ Backend port: Controlled by `API_PORT` environment variable
- ✅ Frontend port: Controlled by `FRONTEND_PORT` environment variable  
- ✅ Ports are read from environment at deployment time
- ✅ Same Docker images work across different environments
- ✅ No hardcoded ports in Dockerfiles
- ✅ Easy to configure for different servers

For more details, see:
- [Backend Deployment Guide](./backend/DEPLOY.md)
- [Frontend Deployment Guide](./frontend/DEPLOY.md)
