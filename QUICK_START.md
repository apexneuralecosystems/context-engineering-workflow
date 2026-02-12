# Quick Start Guide - Running Backend and Frontend

This guide shows you how to run both the backend and frontend services.

## Option 1: Local Development (Recommended for Development)

### Prerequisites
- Python 3.10-3.13 installed
- Node.js 18+ installed
- API keys for required services

### Step 1: Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
# Windows: py -3.13 -m venv .venv
# Mac/Linux: python3.13 -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# OR with uv:
uv sync

# Create .env file (copy from .env.example if it exists)
# Add your API keys to .env file:
# OPENROUTER_API_KEY=your_key
# TENSORLAKE_API_KEY=your_key
# VOYAGE_API_KEY=your_key
# ZEP_API_KEY=your_key
# FIRECRAWL_API_KEY=your_key
# API_PORT=8003
# FRONTEND_PORT=3003
```

### Step 2: Start Backend Server

```bash
# Make sure you're in backend directory with venv activated
cd backend
python api_server.py
```

✅ Backend will run on: **http://localhost:8003**

You should see:
```
Starting API server on port 8003
```

### Step 3: Setup Frontend (New Terminal)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env.local file
# Add this line:
# NEXT_PUBLIC_API_URL=http://localhost:8003
```

### Step 4: Start Frontend Server

```bash
# Make sure you're in frontend directory
cd frontend
npm run dev
```

✅ Frontend will run on: **http://localhost:3003**

### Step 5: Access the Application

1. Open your browser and go to: **http://localhost:3003**
2. Click "Initialize Assistant"
3. Upload a PDF document
4. Start asking questions!

---

## Option 2: Docker (Recommended for Production)

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+ (optional)

### Running Backend with Docker

```bash
cd backend

# Create .env file with your API keys
# Then build and run:
docker build -t context-engineering-backend .
docker run -d \
  --name backend \
  -p 8003:8003 \
  --env-file .env \
  -v $(pwd)/qdrant_db:/app/qdrant_db \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  context-engineering-backend

# Or use docker-compose:
docker-compose up -d --build
```

### Running Frontend with Docker

```bash
cd frontend

# Build with API URL
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8003 \
  -t context-engineering-frontend .

# Run container
docker run -d \
  --name frontend \
  -p 3003:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8003 \
  context-engineering-frontend

# Or use docker-compose:
docker-compose up -d --build
```

### View Logs

```bash
# Backend logs
docker logs -f backend

# Frontend logs
docker logs -f frontend
```

---

## Option 3: Docker Compose (Both Services Together)

If you want to run both services together with Docker Compose, you'll need to create a compose file at the root level or use the individual compose files in each directory.

### Using Individual Compose Files

**Terminal 1 - Backend:**
```bash
cd backend
docker-compose up
```

**Terminal 2 - Frontend:**
```bash
cd frontend
docker-compose up
```

---

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Change API_PORT in backend/.env file
API_PORT=8004
```

**Missing API keys:**
- Make sure all required API keys are in `backend/.env`
- Check that `.env` file is in the `backend/` directory

**Python version issues:**
- Use Python 3.10, 3.11, 3.12, or 3.13 (NOT 3.14)
- Verify: `python --version`

### Frontend Issues

**Cannot connect to backend:**
- Verify backend is running: `curl http://localhost:8003/health`
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local` matches backend URL
- Ensure backend CORS is configured correctly

**Port conflicts:**
- Change port in `frontend/.env.local`: `PORT=3004`
- Or use: `npm run dev -- -p 3004`

### General

**Check if services are running:**
```bash
# Backend health check
curl http://localhost:8003/health

# Frontend (should return HTML)
curl http://localhost:3003
```

**View running processes:**
```bash
# Python processes
ps aux | grep python
# or on Windows:
tasklist | findstr python

# Node processes
ps aux | grep node
# or on Windows:
tasklist | findstr node
```

---

## Environment Variables Summary

### Backend (.env in backend/ directory)
```env
OPENROUTER_API_KEY=your_key
TENSORLAKE_API_KEY=your_key
VOYAGE_API_KEY=your_key
ZEP_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
API_PORT=8003
FRONTEND_PORT=3003
```

### Frontend (.env.local in frontend/ directory)
```env
NEXT_PUBLIC_API_URL=http://localhost:8003
PORT=3003
```

---

## Next Steps

1. ✅ Backend running on http://localhost:8003
2. ✅ Frontend running on http://localhost:3003
3. 🌐 Open http://localhost:3003 in browser
4. 🚀 Start using the Research Assistant!

For more detailed information, see:
- `backend/README.md` - Backend documentation
- `frontend/README.md` - Frontend documentation
- `backend/DOCKER.md` - Backend Docker guide
- `frontend/DOCKER.md` - Frontend Docker guide
