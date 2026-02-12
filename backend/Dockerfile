# Multi-stage build for production-ready backend
FROM python:3.13-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY api_server.py ./
COPY src/ ./src/
COPY config/ ./config/

# Create directories for data persistence
RUN mkdir -p /app/data /app/outputs /app/qdrant_db

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_PORT=8003 \
    FRONTEND_PORT=3003

# Expose port (default, can be overridden via environment variable)
# Note: Actual port is controlled by API_PORT environment variable
EXPOSE ${API_PORT:-8003}

# Health check (uses API_PORT environment variable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c "curl -f http://localhost:${API_PORT:-8003}/health || exit 1"

# Run the application
# Note: Using sh -c to properly expand environment variable
CMD sh -c "python -m uvicorn api_server:app --host 0.0.0.0 --port ${API_PORT} --workers 1"
