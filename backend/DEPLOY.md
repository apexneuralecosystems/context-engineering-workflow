# Backend Deployment Guide

This guide explains how to deploy the backend service with configurable ports from environment variables.

## Environment Variables for Ports

The backend uses the following environment variables for port configuration:

- `API_PORT` - Port for the backend API server (default: 8003)
- `FRONTEND_PORT` - Port for the frontend (used for CORS configuration, default: 3003)

## Deployment Methods

### Method 1: Docker Compose (Recommended)

1. **Create `.env` file** in the backend directory:
   ```env
   # API Keys
   OPENROUTER_API_KEY=your_key
   TENSORLAKE_API_KEY=your_key
   VOYAGE_API_KEY=your_key
   ZEP_API_KEY=your_key
   FIRECRAWL_API_KEY=your_key
   
   # Port Configuration (set from server environment)
   API_PORT=8003
   FRONTEND_PORT=3003
   
   # Optional
   CORS_ORIGINS=https://yourdomain.com
   DEBUG=false
   ```

2. **Deploy:**
   ```bash
   docker-compose up -d --build
   ```

3. **Ports are automatically configured** from the `.env` file.

### Method 2: Docker Run

```bash
# Set ports via environment variables
export API_PORT=8003
export FRONTEND_PORT=3003

# Build and run
docker build -t context-engineering-backend .
docker run -d \
  --name backend \
  -p ${API_PORT}:${API_PORT} \
  -e API_PORT=${API_PORT} \
  -e FRONTEND_PORT=${FRONTEND_PORT} \
  --env-file .env \
  -v $(pwd)/qdrant_db:/app/qdrant_db \
  context-engineering-backend
```

### Method 3: Server Environment Variables

On your deployment server, set environment variables:

```bash
# In your server's .bashrc, .profile, or deployment script
export API_PORT=8003
export FRONTEND_PORT=3003
```

Then use docker-compose or docker run, and they will be automatically picked up.

## Port Configuration Examples

### Example 1: Custom Ports
```bash
# Set custom ports
export API_PORT=9000
export FRONTEND_PORT=4000

# Deploy
docker-compose up -d
# Backend will run on port 9000
```

### Example 2: Production Server
```bash
# Production server with specific ports
export API_PORT=8080
export FRONTEND_PORT=3000

# Deploy with docker-compose
docker-compose up -d --build
```

### Example 3: Multiple Instances
```bash
# Instance 1
API_PORT=8001 FRONTEND_PORT=3001 docker-compose up -d

# Instance 2
API_PORT=8002 FRONTEND_PORT=3002 docker-compose up -d
```

## Verification

After deployment, verify the port configuration:

```bash
# Check if container is running
docker ps

# Check logs
docker logs backend

# Test health endpoint
curl http://localhost:${API_PORT}/health
```

## Important Notes

1. **Port Mapping**: The docker-compose uses `${API_PORT:-8003}:${API_PORT:-8003}` which maps the host port to the same container port. Both are controlled by the `API_PORT` environment variable.

2. **CORS Configuration**: The `FRONTEND_PORT` is used for CORS configuration. Make sure it matches your frontend's port.

3. **Health Checks**: Health checks automatically use the `API_PORT` environment variable.

4. **Firewall**: Ensure your server's firewall allows traffic on the configured `API_PORT`.

## Troubleshooting

**Port already in use:**
```bash
# Check what's using the port
lsof -i :${API_PORT}
# or
netstat -tulpn | grep ${API_PORT}

# Change API_PORT in .env and redeploy
```

**Port not accessible:**
- Verify environment variable is set: `echo $API_PORT`
- Check docker-compose logs: `docker-compose logs backend`
- Verify port mapping: `docker port backend`
