# Backend

This directory contains all backend code for the Research Assistant application.

## Structure

```
backend/
├── api_server.py          # FastAPI server entry point
├── src/                   # Source code
│   ├── workflows/        # CrewAI flow orchestration
│   ├── tools/            # Agent tools (RAG, Memory, Web, ArXiv)
│   ├── rag/              # RAG pipeline (embeddings, retriever)
│   ├── memory/           # Zep memory layer
│   ├── generation/       # Response generation
│   ├── document_processing/  # Document parsing
│   └── config/           # Configuration loader
├── config/               # YAML configuration files
│   ├── agents/          # Agent definitions
│   └── tasks/           # Task definitions
├── pyproject.toml       # Python dependencies
├── uv.lock              # Dependency lock file
└── .env.example         # Environment variables template
```

## Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   # Or with Python 3.13 specifically:
   py -3.13 -m venv .venv
   ```

3. **Activate virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # MacOS/Linux
   source .venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   uv sync
   # or
   pip install -e .
   ```

5. **Configure environment:**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env with your API keys
   ```

6. **Start the server:**
   ```bash
   python api_server.py
   ```

The server will run on `http://localhost:8003` (or the port specified in `API_PORT` environment variable).

## Environment Variables

Create a `.env` file in the `backend/` directory with:

```env
# API Keys
TENSORLAKE_API_KEY=your_key
VOYAGE_API_KEY=your_key
OPENAI_API_KEY=your_key
# OR
OPENROUTER_API_KEY=your_key
ZEP_API_KEY=your_key
FIRECRAWL_API_KEY=your_key

# Configuration
API_PORT=8003
FRONTEND_PORT=3003
QDRANT_DB_PATH=./qdrant_db
```

**Note:** `QDRANT_DB_PATH` defaults to `./qdrant_db` (relative to backend folder, where qdrant_db is now located).

## Running from Backend Directory

When running from the `backend/` directory, all paths are relative to this folder:
- Database: `./qdrant_db` (in backend folder)
- Data files: `./data/` (in backend folder)
- Outputs: `./outputs/` (in backend folder)
- Config files: `config/` (in backend folder)
- Source code: `src/` (in backend folder)

## API Endpoints

- `GET /health` - Health check
- `POST /api/initialize` - Initialize the research assistant
- `GET /api/status` - Get assistant status
- `POST /api/upload-document` - Upload and process a PDF
- `POST /api/query` - Process a research query
- `GET /docs` - Swagger UI documentation

