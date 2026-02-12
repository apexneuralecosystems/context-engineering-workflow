# Troubleshooting 502 Bad Gateway Error

## Common Causes

A 502 Bad Gateway error means Nginx (or your reverse proxy) cannot connect to the backend API server. Here are the most common causes and solutions:

## 1. Check if Backend Container is Running

```bash
# Check container status
docker ps -a | grep backend

# Check if container is running
docker ps | grep context-engineering-backend

# If not running, check why it stopped
docker logs context-engineering-backend
```

**Solution:** If the container is stopped or crashed, restart it:
```bash
docker start context-engineering-backend
# or
docker-compose up -d
```

## 2. Check Backend Logs for Errors

```bash
# View recent logs
docker logs context-engineering-backend --tail 100

# Follow logs in real-time
docker logs -f context-engineering-backend
```

**Common errors to look for:**

### Missing Environment Variables

The backend requires these environment variables:
- `OPENROUTER_API_KEY` - **REQUIRED** (backend will crash if missing)
- `API_PORT` - **REQUIRED** (backend will crash if missing)
- `FRONTEND_PORT` - **REQUIRED** (backend will crash if missing)
- `TENSORLAKE_API_KEY` - Required for document processing
- `VOYAGE_API_KEY` - Required for embeddings
- `ZEP_API_KEY` - Required for memory
- `FIRECRAWL_API_KEY` - Required for web search

**Error messages:**
```
ValueError: OPENROUTER_API_KEY is required...
ValueError: API_PORT environment variable is required...
ValueError: FRONTEND_PORT environment variable is required...
```

**Solution:** Ensure all required environment variables are set in your `.env` file or deployment configuration.

## 3. Verify Port Configuration

The backend must be accessible on the port that Nginx is trying to connect to.

```bash
# Check what port the container is listening on
docker port context-engineering-backend

# Test if backend is responding
curl http://localhost:${API_PORT}/health

# Or from inside the container
docker exec context-engineering-backend curl http://localhost:${API_PORT}/health
```

**Common issues:**
- Port mismatch between Nginx config and backend
- Backend listening on wrong port
- Firewall blocking the port

**Solution:** 
1. Check your Nginx configuration - ensure `proxy_pass` points to the correct backend URL
2. Verify `API_PORT` environment variable matches what Nginx expects
3. Ensure the port is exposed in Docker: `-p ${API_PORT}:${API_PORT}`

## 4. Check Nginx Configuration

If you're using Nginx as a reverse proxy, verify the configuration:

```nginx
# Example Nginx config
upstream backend {
    server localhost:8003;  # Must match API_PORT
}

server {
    listen 80;
    server_name contextstack-api.apexneural.cloud;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Common issues:**
- `proxy_pass` URL doesn't match backend port
- Backend container not accessible from Nginx (network issue)
- Nginx can't resolve `localhost` (use container name in Docker networks)

**Solution:**
- If using Docker Compose, use service name: `proxy_pass http://backend:8003;`
- If using separate containers, ensure they're on the same network
- Verify Nginx can reach the backend: `curl http://backend:8003/health` from Nginx container

## 5. Check Container Health

```bash
# Check container health status
docker inspect context-engineering-backend | grep -A 10 Health

# Check if health check is passing
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Solution:** If health check is failing, check the logs to see why the `/health` endpoint isn't responding.

## 6. Verify Environment Variables in Container

```bash
# Check if environment variables are set in container
docker exec context-engineering-backend env | grep -E "API_PORT|FRONTEND_PORT|OPENROUTER"

# Verify API_PORT is set correctly
docker exec context-engineering-backend sh -c 'echo $API_PORT'
```

**Solution:** If variables are missing, ensure they're passed to the container:
- In `docker-compose.yml`: Check `environment:` section
- In `docker run`: Use `-e` flags or `--env-file .env`

## 7. Test Backend Directly

```bash
# Test health endpoint
curl http://localhost:${API_PORT}/health

# Test docs endpoint
curl http://localhost:${API_PORT}/docs

# Test from inside container
docker exec context-engineering-backend curl http://localhost:${API_PORT}/health
```

**Solution:** If backend responds directly but Nginx gets 502, it's an Nginx configuration issue.

## 8. Check Network Connectivity

```bash
# If using Docker Compose, check network
docker network ls
docker network inspect <network_name>

# Test connectivity from Nginx to backend
docker exec <nginx_container> ping backend
docker exec <nginx_container> curl http://backend:8003/health
```

## Quick Fix Checklist

1. ✅ **Container is running:** `docker ps | grep backend`
2. ✅ **No errors in logs:** `docker logs backend --tail 50`
3. ✅ **Health endpoint works:** `curl http://localhost:${API_PORT}/health`
4. ✅ **Environment variables set:** Check `.env` file or deployment config
5. ✅ **Port matches Nginx config:** Verify `API_PORT` matches Nginx `proxy_pass`
6. ✅ **Network connectivity:** Ensure Nginx can reach backend

## Production Deployment Checklist

When deploying to production (like `contextstack-api.apexneural.cloud`):

1. **Set all required environment variables:**
   ```bash
   export OPENROUTER_API_KEY=your_key
   export API_PORT=8003
   export FRONTEND_PORT=3003
   export TENSORLAKE_API_KEY=your_key
   export VOYAGE_API_KEY=your_key
   export ZEP_API_KEY=your_key
   export FIRECRAWL_API_KEY=your_key
   ```

2. **Build and run with environment:**
   ```bash
   docker build -t context-engineering-backend .
   docker run -d \
     --name context-engineering-backend \
     -p 8003:8003 \
     -e OPENROUTER_API_KEY=${OPENROUTER_API_KEY} \
     -e API_PORT=8003 \
     -e FRONTEND_PORT=3003 \
     -e TENSORLAKE_API_KEY=${TENSORLAKE_API_KEY} \
     -e VOYAGE_API_KEY=${VOYAGE_API_KEY} \
     -e ZEP_API_KEY=${ZEP_API_KEY} \
     -e FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY} \
     context-engineering-backend
   ```

3. **Verify backend is accessible:**
   ```bash
   curl http://localhost:8003/health
   curl http://localhost:8003/docs
   ```

4. **Configure Nginx to proxy to backend:**
   ```nginx
   location / {
       proxy_pass http://localhost:8003;
       # ... other proxy settings
   }
   ```

## Still Having Issues?

1. **Check full logs:** `docker logs context-engineering-backend`
2. **Verify Docker version:** `docker --version`
3. **Check system resources:** `docker stats`
4. **Review deployment platform logs** (if using cloud platform)
