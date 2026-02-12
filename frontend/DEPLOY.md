# Frontend Deployment Guide

This guide explains how to deploy the frontend service with configurable ports from environment variables.

## Environment Variables for Ports

The frontend uses the following environment variables for port configuration:

- `FRONTEND_PORT` - Host port for the frontend (default: 3003)
- `NEXT_PUBLIC_API_URL` - Backend API URL (should include backend port)
- `API_PORT` - Backend API port (used to construct API URL if NEXT_PUBLIC_API_URL not set)

**Note:** Nginx always runs on port 80 internally. The `FRONTEND_PORT` environment variable controls the host port mapping.

## Deployment Methods

### Method 1: Docker Compose (Recommended)

1. **Create `.env` file** in the frontend directory (or use root `.env`):
   ```env
   # Backend API URL (use API_PORT from environment)
   NEXT_PUBLIC_API_URL=http://localhost:8003
   # Or use environment variable:
   # NEXT_PUBLIC_API_URL=http://localhost:${API_PORT}
   
   # Frontend Port (host port mapping)
   FRONTEND_PORT=3003
   
   # Backend Port (for reference, used in API URL construction)
   API_PORT=8003
   ```

2. **Deploy:**
   ```bash
   docker-compose up -d --build
   ```

3. **Ports are automatically configured** from the `.env` file.

### Method 2: Docker Run

```bash
# Set ports via environment variables
export FRONTEND_PORT=3003
export API_PORT=8003
export NEXT_PUBLIC_API_URL=http://localhost:${API_PORT}

# Build with API URL
docker build \
  --build-arg NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
  -t context-engineering-frontend .

# Run container
docker run -d \
  --name frontend \
  -p ${FRONTEND_PORT}:80 \
  -e NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
  context-engineering-frontend
```

### Method 3: Server Environment Variables

On your deployment server, set environment variables:

```bash
# In your server's .bashrc, .profile, or deployment script
export FRONTEND_PORT=3003
export API_PORT=8003
export NEXT_PUBLIC_API_URL=http://localhost:${API_PORT}
```

Then use docker-compose or docker run, and they will be automatically picked up.

## Port Configuration Examples

### Example 1: Custom Ports
```bash
# Set custom ports
export FRONTEND_PORT=4000
export API_PORT=9000
export NEXT_PUBLIC_API_URL=http://localhost:9000

# Deploy
docker-compose up -d
# Frontend will be accessible on port 4000
```

### Example 2: Production Server with Domain
```bash
# Production configuration
export FRONTEND_PORT=80
export API_PORT=8080
export NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Deploy
docker-compose up -d --build
```

### Example 3: Behind Reverse Proxy
```bash
# Frontend behind nginx reverse proxy
export FRONTEND_PORT=3000
export API_PORT=8000
export NEXT_PUBLIC_API_URL=http://backend:8000

# Deploy
docker-compose up -d
```

## Important Notes

1. **Port Mapping**: The docker-compose uses `${FRONTEND_PORT:-3003}:80` which maps the host port (from env var) to container port 80 (nginx).

2. **Nginx Internal Port**: Nginx always runs on port 80 inside the container. Only the host port is configurable.

3. **API URL**: The `NEXT_PUBLIC_API_URL` must be set at build time for Next.js. If you need to change it, rebuild the image.

4. **Build vs Runtime**: 
   - `NEXT_PUBLIC_API_URL` must be set at build time (via `--build-arg`)
   - `FRONTEND_PORT` is used at runtime for port mapping

## Dynamic API URL (Advanced)

If you need to change the API URL without rebuilding, you can use a runtime script. However, this requires additional setup and is not recommended for production.

## Verification

After deployment, verify the port configuration:

```bash
# Check if container is running
docker ps

# Check logs
docker logs frontend

# Test frontend
curl http://localhost:${FRONTEND_PORT}/health

# Test in browser
open http://localhost:${FRONTEND_PORT}
```

## Troubleshooting

**Port already in use:**
```bash
# Check what's using the port
lsof -i :${FRONTEND_PORT}
# or
netstat -tulpn | grep ${FRONTEND_PORT}

# Change FRONTEND_PORT in .env and redeploy
```

**API connection errors:**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check if backend is accessible: `curl ${NEXT_PUBLIC_API_URL}/health`
- Rebuild image if API URL changed: `docker-compose build --no-cache`

**Port not accessible:**
- Verify environment variable: `echo $FRONTEND_PORT`
- Check docker-compose logs: `docker-compose logs frontend`
- Verify port mapping: `docker port frontend`

## Production Deployment Checklist

- [ ] Set `FRONTEND_PORT` from server environment
- [ ] Set `API_PORT` from server environment  
- [ ] Configure `NEXT_PUBLIC_API_URL` with production backend URL
- [ ] Rebuild image with correct API URL
- [ ] Configure firewall rules for `FRONTEND_PORT`
- [ ] Set up SSL/TLS (via reverse proxy or nginx config)
- [ ] Configure domain name and DNS
- [ ] Test health endpoint
- [ ] Verify API connectivity
