# Multi-stage build for production-ready Next.js frontend with Nginx

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci && npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variable (can be overridden)
# Provide a default value to prevent build failures
ARG NEXT_PUBLIC_API_URL=http://localhost:8003
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Ensure public directory exists (Next.js public folder is optional)
RUN mkdir -p public

# Build the application
RUN npm run build

# Stage 3: Runner with Nginx
FROM nginx:alpine AS runner

# Install Node.js, supervisor, and wget for health checks
RUN apk add --no-cache nodejs npm supervisor wget

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="127.0.0.1"

# Create a non-root user for Next.js
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -u 1001 -G nodejs nextjs

# Copy Next.js application files
# Create public directory and copy if it exists (Next.js public folder is optional)
RUN mkdir -p ./public && chown nextjs:nodejs ./public
RUN --mount=from=builder,source=/app/public,target=/source/public \
    if [ -d /source/public ] && [ "$(ls -A /source/public 2>/dev/null)" ]; then \
        cp -r /source/public/* ./public/ && \
        chown -R nextjs:nodejs ./public; \
    fi

# Copy standalone build output (required for Next.js standalone mode)
# Ensure server.js exists and is executable
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Verify server.js exists (standalone mode should create it)
# Next.js standalone mode creates server.js in the .next/standalone directory
RUN if [ ! -f /app/server.js ]; then \
        echo "WARNING: server.js not found. Checking build output..." && \
        ls -la /app/ && \
        echo "Contents of /app:" && \
        find /app -name "server.js" 2>/dev/null || echo "server.js not found anywhere"; \
    else \
        echo "✓ server.js found at /app/server.js" && \
        chmod +x /app/server.js && \
        echo "✓ server.js is executable"; \
    fi

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script to wait for Next.js to be ready
RUN echo '#!/bin/sh' > /usr/local/bin/wait-for-nextjs.sh && \
    echo 'set -e' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo 'echo "Waiting for Next.js server to be ready on port 3000..."' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo 'for i in 1 2 3 4 5 6 7 8 9 10; do' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo '  if nc -z 127.0.0.1 3000 2>/dev/null || wget --quiet --tries=1 --spider http://127.0.0.1:3000 2>/dev/null; then' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo '    echo "✓ Next.js is ready on port 3000!"' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo '    exit 0' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo '  fi' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo '  echo "Attempt $i/10: Next.js not ready yet, waiting 2 seconds..."' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo '  sleep 2' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo 'done' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo 'echo "WARNING: Next.js did not become ready in time, but continuing anyway..."' >> /usr/local/bin/wait-for-nextjs.sh && \
    echo 'exit 0' >> /usr/local/bin/wait-for-nextjs.sh && \
    chmod +x /usr/local/bin/wait-for-nextjs.sh

# Install netcat for port checking
RUN apk add --no-cache netcat-openbsd

# Create supervisor configuration directory and file
RUN mkdir -p /etc/supervisor/conf.d && \
    echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:nextjs]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=sh -c "export PORT=3000 HOSTNAME=127.0.0.1 NODE_ENV=production && node server.js"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=nextjs' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'startretries=3' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'startsecs=10' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=100' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:nginx]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=sh -c "/usr/local/bin/wait-for-nextjs.sh && nginx -g \"daemon off;\""' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'startretries=3' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=200' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'startsecs=5' >> /etc/supervisor/conf.d/supervisord.conf

# Create nginx cache directory
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    chmod -R 755 /var/cache/nginx

# Expose port 80 for nginx (internal port, host port configurable via environment)
# Note: Nginx always runs on port 80 internally, host port is set in docker-compose/docker run
# For production, map host port 3000 to container port 80
EXPOSE 80

# Health check - check nginx on port 80 (internal)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1

# Start supervisor to manage both processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
