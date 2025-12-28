"""
FastAPI backend server for the Research Assistant frontend
"""

import os
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, Optional, Generic, TypeVar
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

# IMPORTANT: Configure OpenRouter for CrewAI/litellm BEFORE importing workflows
# CrewAI uses litellm internally, which reads environment variables at import time
# This project uses OpenRouter exclusively - no OpenAI fallback

openrouter_key = os.getenv("OPENROUTER_API_KEY")

if not openrouter_key:
    raise ValueError(
        "OPENROUTER_API_KEY is required. Please set it in your .env file.\n"
        "Get your API key from: https://openrouter.ai/\n"
        "OpenRouter supports multiple LLM providers (OpenAI, Anthropic, Google, Meta, etc.)"
    )

# Configure OpenRouter - set environment variables that litellm/CrewAI will use
os.environ["OPENAI_API_KEY"] = openrouter_key  # Use OpenRouter key as OpenAI key for litellm
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"  # CRITICAL: Set base URL
os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"

# Set OpenRouter-specific headers
os.environ["OPENROUTER_REFERER"] = os.getenv("OPENROUTER_REFERER", "https://github.com/your-repo")
os.environ["OPENROUTER_APP_NAME"] = os.getenv("OPENROUTER_APP_NAME", "Research Assistant")

# Log configuration - CRITICAL for debugging production issues
print(f"\n{'='*80}")
print("🚀 OpenRouter Configuration (Pre-import) - PRODUCTION DEBUG:")
print(f"{'='*80}")
print(f"  ✅ OPENROUTER_API_KEY: SET ({len(openrouter_key)} chars)")
print(f"  ✅ OPENAI_API_KEY: {openrouter_key[:20]}... (OpenRouter key, {len(openrouter_key)} chars)")
print(f"  ✅ OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
print(f"  ✅ LITELLM_API_BASE: {os.environ.get('LITELLM_API_BASE')}")
print(f"  📍 Current working directory: {os.getcwd()}")
print(f"  📍 Python path: {os.sys.path[:3]}...")
print(f"{'='*80}\n")
import sys
sys.stdout.flush()  # Force flush to ensure logs appear immediately

from src.workflows import ResearchAssistantFlow

# Generic response model
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    status_code: int = Field(..., description="HTTP status code")
    status: bool = Field(..., description="Success status (true/false)")
    message: str = Field(..., description="Response message")
    path: str = Field(..., description="API endpoint path")
    data: Optional[T] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": 200,
                "status": True,
                "message": "Operation successful",
                "path": "/api/endpoint",
                "data": {}
            }
        }

# Request models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Research query")
    user_id: Optional[str] = Field(None, description="User ID")
    thread_id: Optional[str] = Field(None, description="Thread/Session ID")

class InitializeRequest(BaseModel):
    """Optional request body for initialization"""
    pass

app = FastAPI(
    title="Research Assistant API",
    description="API for the AI Research Assistant with RAG capabilities",
    version="1.0.0"
)

# CORS middleware - get frontend port from environment
FRONTEND_PORT = os.getenv("FRONTEND_PORT")
if not FRONTEND_PORT:
    raise ValueError("FRONTEND_PORT environment variable is required. Please set it in .env file.")

FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"
FRONTEND_URL_127 = f"http://127.0.0.1:{FRONTEND_PORT}"

# Get additional allowed origins from environment (comma-separated)
# Supports formats like:
# CORS_ORIGINS=https://example.com,https://www.example.com
# CORS_ORIGINS=https://example.com, http://localhost:3000
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "")
ADDITIONAL_ORIGINS = []

if CORS_ORIGINS_ENV:
    # Split by comma and clean up each origin
    ADDITIONAL_ORIGINS = [
        origin.strip() 
        for origin in CORS_ORIGINS_ENV.split(",") 
        if origin.strip()
    ]
    # Remove trailing slashes for consistency
    ADDITIONAL_ORIGINS = [origin.rstrip('/') for origin in ADDITIONAL_ORIGINS]

# Build complete list of allowed origins
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    FRONTEND_URL_127,
    *ADDITIONAL_ORIGINS,
]

# Log CORS configuration for debugging (only in development)
if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
    print(f"\n{'='*80}")
    print("CORS Configuration:")
    print(f"  FRONTEND_PORT: {FRONTEND_PORT}")
    print(f"  Localhost URLs: {FRONTEND_URL}, {FRONTEND_URL_127}")
    if ADDITIONAL_ORIGINS:
        print(f"  Additional Origins: {', '.join(ADDITIONAL_ORIGINS)}")
    else:
        print("  Additional Origins: None (set CORS_ORIGINS in .env for production)")
    print(f"  Total Allowed Origins: {len(ALLOWED_ORIGINS)}")
    print(f"{'='*80}\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global assistant instance
_assistant: Optional[ResearchAssistantFlow] = None
_document_processed: bool = False
_current_document: Optional[str] = None
_qdrant_initialized: bool = False


def get_assistant() -> ResearchAssistantFlow:
    """Get or create the research assistant instance"""
    global _assistant, _qdrant_initialized
    
    if _assistant is None or not _qdrant_initialized:
        try:
            # Verify OpenRouter configuration is still set before creating assistant
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_key:
                raise ValueError("OPENROUTER_API_KEY is required but not found in environment")
            
            # Re-verify and enforce OpenRouter settings
            if os.environ.get("OPENAI_API_BASE") != "https://openrouter.ai/api/v1":
                print(f"WARNING: OPENAI_API_BASE was changed! Re-setting to OpenRouter URL")
                os.environ["OPENAI_API_KEY"] = openrouter_key
                os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
                os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
                print(f"  Fixed: OPENAI_API_BASE = {os.environ.get('OPENAI_API_BASE')}")
            
            _assistant = ResearchAssistantFlow(
                tensorlake_api_key=os.getenv("TENSORLAKE_API_KEY"),
                voyage_api_key=os.getenv("VOYAGE_API_KEY"),
                openrouter_api_key=openrouter_key,
                zep_api_key=os.getenv("ZEP_API_KEY"),
                firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
                qdrant_db_path=os.getenv("QDRANT_DB_PATH", os.path.join(os.path.dirname(__file__), "qdrant_db"))
            )
            _qdrant_initialized = True
            
            # Log final configuration after assistant creation
            print(f"\n{'='*80}")
            print("✅ Assistant Created - Final OpenRouter Configuration (PRODUCTION DEBUG):")
            print(f"{'='*80}")
            openai_key = os.getenv('OPENAI_API_KEY', 'NOT SET')
            openai_base = os.environ.get('OPENAI_API_BASE', 'NOT SET')
            litellm_base = os.environ.get('LITELLM_API_BASE', 'NOT SET')
            
            print(f"  🔑 OPENAI_API_KEY: {openai_key[:20] if openai_key != 'NOT SET' else 'NOT SET'}... ({len(openai_key) if openai_key != 'NOT SET' else 0} chars)")
            print(f"  🌐 OPENAI_API_BASE: {openai_base}")
            print(f"  🌐 LITELLM_API_BASE: {litellm_base}")
            
            # Verify configuration is correct
            if openai_base != "https://openrouter.ai/api/v1":
                print(f"  ❌ ERROR: OPENAI_API_BASE is NOT set to OpenRouter URL!")
            else:
                print(f"  ✅ OPENAI_API_BASE correctly set to OpenRouter")
            
            if litellm_base != "https://openrouter.ai/api/v1":
                print(f"  ❌ ERROR: LITELLM_API_BASE is NOT set to OpenRouter URL!")
            else:
                print(f"  ✅ LITELLM_API_BASE correctly set to OpenRouter")
            
            print(f"{'='*80}\n")
            import sys
            sys.stdout.flush()  # Force flush
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize Research Assistant: {str(e)}"
            )
    
    return _assistant


def create_response(
    status_code: int,
    message: str,
    path: str,
    data: Any = None,
    status_bool: Optional[bool] = None
) -> APIResponse:
    """Helper function to create standardized API response"""
    if status_bool is None:
        status_bool = 200 <= status_code < 300
    
    return APIResponse(
        status_code=status_code,
        status=status_bool,
        message=message,
        path=path,
        data=data
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for standardized error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_response(
            status_code=exc.status_code,
            message=exc.detail,
            path=str(request.url.path),
            status_bool=False
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Internal server error: {str(exc)}",
            path=str(request.url.path),
            status_bool=False
        ).model_dump()
    )


@app.get("/health", response_model=APIResponse[Dict[str, str]], tags=["Health"])
async def health_check(request: Request):
    """Health check endpoint"""
    return create_response(
        status_code=status.HTTP_200_OK,
        message="Service is healthy",
        path=str(request.url.path),
        data={"status": "healthy", "service": "Research Assistant API"}
    )


@app.post(
    "/api/initialize",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    tags=["Assistant"]
)
async def initialize_assistant(request: Request):
    """Initialize the research assistant"""
    try:
        assistant = get_assistant()
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Assistant initialized successfully",
            path=str(request.url.path),
            data={
                "initialized": True,
                "document_processed": _document_processed,
                "current_document": _current_document
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize assistant: {str(e)}"
        )


@app.get(
    "/api/status",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    tags=["Assistant"]
)
async def get_status(request: Request):
    """Get the current status of the assistant"""
    return create_response(
        status_code=status.HTTP_200_OK,
        message="Status retrieved successfully",
        path=str(request.url.path),
        data={
            "initialized": _assistant is not None and _qdrant_initialized,
            "document_processed": _document_processed,
            "current_document": _current_document
        }
    )


@app.post(
    "/api/upload-document",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    tags=["Documents"]
)
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    global _document_processed, _current_document
    
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_file_path = tmp_file.name
        
        # Process document
        assistant = get_assistant()
        results = assistant.process_documents([tmp_file_path])
        
        # Clean up temp file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        _document_processed = True
        _current_document = file.filename
        
        return create_response(
            status_code=status.HTTP_200_OK,
            message=f"Document '{file.filename}' processed successfully",
            path=str(request.url.path),
            data={
                "success": True,
                "document_name": file.filename,
                "message": f"Document '{file.filename}' processed successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up temp file on error
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        error_msg = str(e)
        if "TensorLake" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document parsing failed: {error_msg}"
            )
        elif "Embedding" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Embedding generation failed: {error_msg}"
            )
        elif "API" in error_msg or "key" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"API authentication failed: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {error_msg}"
            )


@app.post(
    "/api/query",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    tags=["Query"]
)
async def query(request: Request, query_request: QueryRequest):
    """Process a research query"""
    global _document_processed
    
    if not _document_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload and process a document first"
        )
    
    try:
        assistant = get_assistant()
        
        # Log the query for debugging
        print(f"\n{'='*80}")
        print(f"Processing query: {query_request.query}")
        print(f"User ID: {query_request.user_id or 'web_user'}")
        print(f"Thread ID: {query_request.thread_id or f'web_session_{os.getpid()}'}")
        print(f"{'='*80}\n")
        
        # Run kickoff in a thread executor to avoid asyncio.run() conflict
        # CrewAI's kickoff() is synchronous and uses asyncio.run() internally,
        # which cannot be called from within an already running event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,  # Use default ThreadPoolExecutor
            lambda: assistant.kickoff(inputs={
                "query": query_request.query,
                "user_id": query_request.user_id or "web_user",
                "thread_id": query_request.thread_id or f"web_session_{os.getpid()}"
            })
        )
        
        # Log RAG result status for debugging
        if "context_sources" in result and "rag_result" in result["context_sources"]:
            rag_result = result["context_sources"]["rag_result"]
            if isinstance(rag_result, dict):
                rag_status = rag_result.get("status", "UNKNOWN")
                print(f"\nRAG Status: {rag_status}")
                if rag_status == "ERROR":
                    print(f"RAG Error: {rag_result.get('error', 'Unknown error')}")
                    print(f"RAG Error Type: {rag_result.get('error_type', 'Unknown')}")
                    print(f"RAG Answer: {rag_result.get('answer', 'No answer')}")
                print(f"{'='*80}\n")
        
        # Extract source_used and confidence from result, with fallback to context sources
        source_used = result.get("source_used", "NONE")
        confidence = result.get("confidence", 0.0)
        
        # Fallback: If source_used is NONE or confidence is 0.0, try to extract from context sources
        if source_used == "NONE" or confidence == 0.0:
            context_sources = result.get("context_sources", {})
            
            # Find the first source with OK status and confidence > 0
            for source_key, source_name in [("rag_result", "RAG"), ("memory_result", "Memory"), 
                                           ("web_result", "Web"), ("tool_result", "ArXiv")]:
                source_data = context_sources.get(source_key, {})
                if isinstance(source_data, dict):
                    if source_data.get("status") == "OK":
                        source_conf = source_data.get("confidence", 0.0)
                        if source_conf > 0:
                            if source_used == "NONE":
                                source_used = source_name
                            if confidence == 0.0:
                                confidence = source_conf
                            break
        
        # Format response to match frontend expectations
        response_data: Dict[str, Any] = {
            "status": result.get("status", "OK"),
            "source_used": source_used,
            "answer": result.get("answer", ""),
            "citations": result.get("citations", []),
            "confidence": confidence,
            "missing": result.get("missing", []),
        }
        
        # Add final_response if available
        if "final_response" in result:
            response_data["final_response"] = result["final_response"]
        
        # Add context sources if available
        if "context_sources" in result:
            response_data["context_sources"] = result["context_sources"]
        
        # Add evaluation result if available
        if "evaluation_result" in result:
            response_data["evaluation_result"] = result["evaluation_result"]
        
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Query processed successfully",
            path=str(request.url.path),
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


if __name__ == "__main__":
    # Get API port from environment variable (required)
    # Set API_PORT in .env file (e.g., API_PORT=8003)
    api_port = os.getenv("API_PORT")
    if not api_port:
        raise ValueError("API_PORT environment variable is required. Please set it in .env file.")
    port = int(api_port)
    
    print(f"Starting API server on port {port} (from API_PORT environment variable)")
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
