# Port 3003 Production Fix Summary

## Problem
The context-engineering-workflow frontend was not working on port 3003 in production, while notebook-lm-clone frontend works correctly on port 3019.

## Root Cause Analysis

### Key Differences Between Projects

**NotebookLM Clone (Working):**
- Uses `output: 'export'` (static export)
- Nginx serves static files directly on port 3019
- Simple architecture: nginx → static files

**Context Engineering (Not Working):**
- Uses `output: 'standalone'` (Next.js server mode)
- Nginx acts as reverse proxy to Next.js server
- Complex architecture: nginx (port 80) → Next.js (port 3000)

## Issues Fixed

### 1. **Nginx Configuration**
- ✅ Added IPv6 support: `listen [::]:80`
- ✅ Improved upstream configuration with fail handling
- ✅ Added comments clarifying port mapping

### 2. **Dockerfile Improvements**
- ✅ Added startup script to wait for Next.js to be ready before starting nginx
- ✅ Improved supervisor configuration with explicit environment variables
- ✅ Added server.js verification and error handling
- ✅ Added netcat for port checking
- ✅ Improved process startup order and retry logic

### 3. **Port Configuration**
- ✅ Next.js runs on port 3000 internally (127.0.0.1:3000)
- ✅ Nginx listens on port 80 internally
- ✅ Docker-compose maps host port 3003 → container port 80
- ✅ Health check verifies nginx on port 80

## Architecture Flow

```
Host Port 3003
    ↓
Container Port 80 (nginx)
    ↓
127.0.0.1:3000 (Next.js server)
```

## Changes Made

### Dockerfile
1. Added wait script that checks if Next.js is ready on port 3000
2. Improved supervisor config with explicit PORT=3000 environment variable
3. Added server.js verification during build
4. Added netcat for port checking
5. Improved startup order: Next.js starts first, nginx waits for it

### nginx.conf
1. Added IPv6 support (`listen [::]:80`)
2. Improved upstream configuration with `max_fails` and `fail_timeout`
3. Added clarifying comments

## Testing

### Build and Run
```bash
cd ai-engineering/advanced/context-engineering-workflow/frontend

# Build the image
docker build -t context-engineering-frontend .

# Run with port 3003
docker run -p 3003:80 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8003 \
  context-engineering-frontend

# Or use docker-compose
FRONTEND_PORT=3003 docker-compose up
```

### Verify
1. Check if container is running: `docker ps`
2. Check logs: `docker logs <container-id>`
3. Test health endpoint: `curl http://localhost:3003/health`
4. Test main page: `curl http://localhost:3003`

### Expected Logs
```
Waiting for Next.js server to be ready on port 3000...
Attempt 1/10: Next.js not ready yet, waiting 2 seconds...
✓ Next.js is ready on port 3000!
[nginx starts]
```

## Troubleshooting

### If Next.js doesn't start:
1. Check if `server.js` exists: `docker exec <container> ls -la /app/server.js`
2. Check Next.js logs: `docker logs <container> | grep nextjs`
3. Verify PORT environment: `docker exec <container> env | grep PORT`

### If nginx can't connect to Next.js:
1. Check if Next.js is listening: `docker exec <container> nc -z 127.0.0.1 3000`
2. Check nginx error logs: `docker exec <container> cat /var/log/nginx/error.log`
3. Verify upstream configuration in nginx.conf

### If port 3003 is not accessible:
1. Verify port mapping: `docker ps | grep 3003`
2. Check firewall/security groups
3. Verify container is running: `docker ps`

## Comparison with NotebookLM Clone

| Aspect | NotebookLM Clone | Context Engineering |
|--------|------------------|---------------------|
| Next.js Mode | Static Export | Standalone Server |
| Nginx Role | Static File Server | Reverse Proxy |
| Internal Ports | Nginx: 3019 | Nginx: 80, Next.js: 3000 |
| Complexity | Simple | Complex (2 processes) |
| Startup | Direct | Requires coordination |

## Key Takeaway

The main difference is that **standalone mode requires both Next.js server and nginx to run**, while **static export only needs nginx**. The fix ensures proper startup coordination between these two processes.
