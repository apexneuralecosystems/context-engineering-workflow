# Backend Docker Deployment

This guide explains how to deploy the backend service using Docker.

## Prerequisites

- Docker Engine 20.10+
- Environment variables configured (see below)

## Quick Start

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your API keys:
   ```env
   OPENROUTER_API_KEY=your_key
   TENSORLAKE_API_KEY=your_key
   VOYAGE_API_KEY=your_key
   ZEP_API_KEY=your_key
   FIRECRAWL_API_KEY=your_key
   API_PORT=8003
   FRONTEND_PORT=3003
   ```

3. **Build and run:**
   ```bash
   docker build -t context-engineering-backend .
   docker run -d \
     --name backend \
     -p 8003:8003 \
     --env-file .env \
     -v $(pwd)/qdrant_db:/app/qdrant_db \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/outputs:/app/outputs \
     context-engineering-backend
   ```

4. **View logs:**
   ```bash
   docker logs -f backend
   ```

5. **Stop container:**
   ```bash
   docker stop backend
   docker rm backend
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

- `OPENROUTER_API_KEY` - OpenRouter API key for LLM access
- `TENSORLAKE_API_KEY` - TensorLake API key for document processing
- `VOYAGE_API_KEY` - Voyage AI API key for embeddings
- `ZEP_API_KEY` - Zep API key for memory
- `FIRECRAWL_API_KEY` - Firecrawl API key for web scraping
- `API_PORT` - Backend server port (default: 8003)
- `FRONTEND_PORT` - Frontend port for CORS (default: 3003)

### Optional Variables

- `QDRANT_DB_PATH` - Path to Qdrant database (default: ./qdrant_db)
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins
- `DEBUG` - Enable debug mode (true/false)
- `OPENROUTER_REFERER` - OpenRouter referer URL
- `OPENROUTER_APP_NAME` - Application name for OpenRouter

## Volumes

The following directories are persisted as volumes:

- `./qdrant_db` - Vector database storage
- `./data` - Uploaded documents
- `./outputs` - Processing outputs

## Health Check

The container includes a health check endpoint at `/health`. Check container health:

```bash
docker ps  # Check STATUS column
curl http://localhost:8003/health
```

## Port Configuration

Ports are fully configurable via environment variables:

- `API_PORT` - Controls both host and container port (default: 8003)
- `FRONTEND_PORT` - Used for CORS configuration (default: 3003)

The docker-compose automatically uses these environment variables for port mapping:
```yaml
ports:
  - "${API_PORT:-8003}:${API_PORT:-8003}"
```

**For detailed deployment instructions with configurable ports, see [DEPLOY.md](./DEPLOY.md)**

## Troubleshooting

- **Port conflicts**: Change `API_PORT` in `.env` or set as environment variable
- **Database errors**: Ensure `qdrant_db` volume has correct permissions
- **API key errors**: Verify all API keys are set correctly in `.env`
- **View logs**: `docker logs backend`
- **Restart container**: `docker restart backend`
