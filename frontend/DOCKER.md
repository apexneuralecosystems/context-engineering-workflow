# Frontend Docker Deployment

This guide explains how to deploy the frontend service using Docker with Nginx as a reverse proxy.

## Prerequisites

- Docker Engine 20.10+
- Backend API URL

## Architecture

The frontend Docker container uses:
- **Nginx** as a reverse proxy (port 80)
- **Next.js** application running internally (port 3000)
- **Supervisor** to manage both processes

Benefits:
- ✅ Better performance with Nginx caching
- ✅ Gzip compression
- ✅ Security headers
- ✅ Rate limiting
- ✅ Static file optimization

## Quick Start

1. **Build the image:**
   ```bash
   docker build \
     --build-arg NEXT_PUBLIC_API_URL=http://localhost:8003 \
     -t context-engineering-frontend .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name frontend \
     -p 3003:80 \
     -e NEXT_PUBLIC_API_URL=http://localhost:8003 \
     context-engineering-frontend
   ```

   **Note:** The container now exposes port 80 (nginx), not 3000. Map to your desired host port.

3. **Access the application:**
   Open http://localhost:3003 in your browser

4. **View logs:**
   ```bash
   docker logs -f frontend
   ```

5. **Stop container:**
   ```bash
   docker stop frontend
   docker rm frontend
   ```

## Using Docker Compose

A `docker-compose.yml` file is included for easier management:

```bash
docker-compose up -d --build
docker-compose logs -f
docker-compose down
```

## Environment Variables

### Required Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL
  - For Docker Compose with backend service: `http://backend:8003`
  - For standalone: `http://localhost:8003` or your backend URL
  - For production: Your production backend URL

### Build Arguments

- `NEXT_PUBLIC_API_URL` - Must be set at build time for Next.js static optimization

## Building for Different Environments

### Development
```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8003 \
  -t context-engineering-frontend:dev .
```

### Production
```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  -t context-engineering-frontend:prod .
```

## Health Check

The container includes a health check endpoint at `/health`. Check container health:

```bash
docker ps  # Check STATUS column
curl http://localhost:3003/health
```

## Nginx Configuration

The nginx configuration (`nginx.conf`) includes:

- **Reverse proxy** to Next.js on port 3000
- **Gzip compression** for better performance
- **Security headers** (X-Frame-Options, X-Content-Type-Options, etc.)
- **Rate limiting** for API routes (10 requests/second)
- **Static file caching** (1 year for `/_next/static`, 30 days for `/public`)
- **WebSocket support** for real-time features
- **File upload support** (50MB max body size)

To customize nginx settings, edit `nginx.conf` and rebuild the image.

## Troubleshooting

- **API connection errors**: 
  - Verify `NEXT_PUBLIC_API_URL` matches your backend URL
  - Check backend is running and accessible
  - For Docker Compose, use service name: `http://backend:8003`

- **Build failures**: 
  - Ensure Node.js version matches (20.x)
  - Clear build cache: `docker build --no-cache ...`

- **CORS errors**: 
  - Verify backend `CORS_ORIGINS` includes frontend URL
  - Check backend is configured to allow frontend origin

- **View logs**: `docker logs frontend`
- **Restart container**: `docker restart frontend`

## Port Configuration

Ports are fully configurable via environment variables:

- `FRONTEND_PORT` - Host port for frontend access (default: 3003)
- `NEXT_PUBLIC_API_URL` - Backend API URL (should include backend port)
- `API_PORT` - Backend port (used if NEXT_PUBLIC_API_URL not fully specified)

The docker-compose automatically uses these environment variables:
```yaml
ports:
  - "${FRONTEND_PORT:-3003}:80"
```

**Note:** Nginx always runs on port 80 inside the container. Only the host port is configurable.

**For detailed deployment instructions with configurable ports, see [DEPLOY.md](./DEPLOY.md)**

## Next.js Standalone Mode

This Dockerfile uses Next.js standalone output mode for optimal Docker images:
- Smaller image size
- Faster startup times
- Production-optimized builds

## Nginx Features

The nginx reverse proxy provides:

1. **Performance Optimization**
   - Gzip compression for text-based files
   - Static file caching with long expiration times
   - Connection keepalive for upstream

2. **Security**
   - Security headers (XSS protection, frame options, etc.)
   - Rate limiting on API routes
   - Request size limits

3. **Reliability**
   - Health check endpoint
   - Proper error handling
   - WebSocket support

## Customizing Nginx

To modify nginx configuration:

1. Edit `nginx.conf` in the frontend directory
2. Rebuild the Docker image
3. Restart the container

Common customizations:
- SSL/TLS configuration (for HTTPS)
- Additional security headers
- Custom caching rules
- Load balancing (if scaling)
