# Frontend 502 Bad Gateway - Diagnosis & Fix

## Current Configuration ✅

Your setup is correct:
- **Port Mapping:** 3003:80 (host:container)
- **Nginx:** Listening on port 80 inside container
- **Next.js:** Running on port 3000 inside container
- **Both processes:** Starting successfully according to logs

## Issues Found & Fixed

### 1. ✅ Fixed: Duplicate Connection Headers
- **Problem:** Connection header was set twice in root location block
- **Fix:** Moved `map` directive to http level, using conditional Connection header

### 2. ✅ Fixed: Missing Error Handling
- **Problem:** No retry logic for failed upstream connections
- **Fix:** Added `proxy_next_upstream` directives for better error handling

### 3. ✅ Fixed: Missing Buffer Settings
- **Problem:** Default buffers might be too small
- **Fix:** Added explicit buffer configuration

## Testing After Rebuild

After rebuilding, test these:

```bash
# 1. Check container is running
docker ps | grep frontend

# 2. Check both processes are running
docker exec context-engineering-frontend supervisorctl status

# 3. Test nginx directly
docker exec context-engineering-frontend wget -qO- http://localhost/health

# 4. Test Next.js directly
docker exec context-engineering-frontend wget -qO- http://127.0.0.1:3000/ 2>&1 | head -5

# 5. Test from host
curl http://localhost:3003/health
curl http://localhost:3003/

# 6. Check nginx error logs
docker exec context-engineering-frontend cat /var/log/nginx/error.log
```

## Common 502 Causes in Production

### 1. External Nginx/Proxy Misconfiguration

If you have an external nginx on your production server, ensure it proxies correctly:

```nginx
upstream frontend {
    server localhost:3003;  # Must match your FRONTEND_PORT
    keepalive 64;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 2. Firewall Blocking Port 3003

```bash
# Check if port is open
sudo netstat -tulpn | grep 3003
# or
sudo ss -tulpn | grep 3003

# Open port if needed
sudo ufw allow 3003/tcp
```

### 3. Next.js Not Fully Ready

Even though logs show "Ready", Next.js might need a moment. The wait script helps, but you can increase the delay:

```bash
# In Dockerfile, increase wait time in wait-for-nextjs.sh
# Currently waits up to 20 seconds (10 attempts × 2 seconds)
```

## Rebuild Instructions

```bash
cd frontend

# Stop and remove existing container
docker stop context-engineering-frontend
docker rm context-engineering-frontend

# Rebuild with fixes
docker-compose up -d --build

# Or manually:
docker build --no-cache --build-arg NEXT_PUBLIC_API_URL=http://localhost:8003 -t context-engineering-frontend .
docker run -d --name context-engineering-frontend -p 3003:80 context-engineering-frontend
```

## Verify Fix

After rebuilding:

1. **Check logs:**
   ```bash
   docker logs context-engineering-frontend --tail 50
   ```

2. **Test endpoints:**
   ```bash
   curl http://localhost:3003/health
   curl http://localhost:3003/
   ```

3. **Check nginx error logs:**
   ```bash
   docker exec context-engineering-frontend tail -20 /var/log/nginx/error.log
   ```

## If Still Getting 502

1. **Check nginx can reach Next.js:**
   ```bash
   docker exec context-engineering-frontend wget -qO- http://127.0.0.1:3000/ 2>&1
   ```

2. **Check nginx configuration:**
   ```bash
   docker exec context-engineering-frontend nginx -t
   ```

3. **Check for port conflicts:**
   ```bash
   docker exec context-engineering-frontend netstat -tulpn | grep -E "80|3000"
   ```

4. **Review full logs:**
   ```bash
   docker logs context-engineering-frontend
   ```
