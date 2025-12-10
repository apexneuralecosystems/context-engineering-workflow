import os
import threading
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Reuse a single embedded client per storage path to avoid lock conflicts
# Use thread-safe dictionary for Streamlit's multi-threaded environment
_CLIENT_CACHE: Dict[str, QdrantClient] = {}
_CACHE_LOCK = threading.Lock()


class QdrantVectorDB:
    """Qdrant vector database implementation using embedded mode for local storage"""
    def __init__(
        self, 
        db_path: Optional[str] = None,
        collection_name: str = "research_assistant"
    ):
        # Use embedded mode with local storage
        # If db_path is provided, use it; otherwise use default path
        if db_path:
            self.db_path = os.path.abspath(db_path)  # Use absolute path for consistency
        else:
            # Default to a local directory
            default_path = os.getenv("QDRANT_DB_PATH", "./qdrant_db")
            self.db_path = os.path.abspath(default_path)
        
        # Normalize path for cache key (handle both relative and absolute paths)
        cache_key = os.path.normpath(self.db_path)
        
        # Thread-safe client reuse
        with _CACHE_LOCK:
            if cache_key in _CLIENT_CACHE:
                # Reuse existing client
                self.client = _CLIENT_CACHE[cache_key]
                print(f"Reusing existing Qdrant client for: {self.db_path}")
            else:
                # Try to create new client, handle lock errors gracefully
                try:
                    self.client = QdrantClient(path=self.db_path)
                    _CLIENT_CACHE[cache_key] = self.client
                    print(f"Created new Qdrant client for: {self.db_path}")
                except RuntimeError as e:
                    error_str = str(e).lower()
                    if "already accessed" in error_str or "lock" in error_str:
                        # Database is locked - this happens when Streamlit reloads
                        # Try to use any existing client from cache
                        print(f"⚠️  Warning: Database locked ({self.db_path}), checking for existing client...")
                        
                        # Check if any client exists in cache (even for different paths)
                        if _CLIENT_CACHE:
                            # Use the first available client - it should work for the same database
                            cached_path, cached_client = next(iter(_CLIENT_CACHE.items()))
                            self.client = cached_client
                            _CLIENT_CACHE[cache_key] = self.client  # Add to cache with current key
                            print(f"Reusing existing client from cache (original path: {cached_path})")
                        else:
                            # No cached client - provide helpful error message
                            raise RuntimeError(
                                f"Qdrant database is locked. This usually happens when:\n"
                                f"1. Streamlit app is reloading\n"
                                f"2. Another instance is using the database\n\n"
                                f"Solution: Restart the Streamlit app completely (stop and start again).\n"
                                f"Database path: {self.db_path}\n"
                                f"Original error: {str(e)}"
                            ) from e
                    else:
                        raise
        
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self, dim: int = 1024):
        # Only create collection if it does not exist (avoid dropping data)
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            if self.collection_name in collection_names:
                return
        except Exception as e:
            # Collection might not exist yet, which is fine
            print(f"Note: Collection check - {e}")

        # Create collection with vector configuration
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dim,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {self.collection_name} with dimension {dim}")
        except Exception as e:
            # Collection might already exist (race condition), check and continue
            try:
                collection_info = self.client.get_collection(self.collection_name)
                print(f"Collection {self.collection_name} already exists with {collection_info.points_count} points")
            except Exception:
                raise Exception(f"Failed to create or verify collection: {e}")

    def insert(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]] = None):
        assert len(chunks) == len(embeddings), "Mismatch between chunks and embeddings"
        
        if metadata:
            assert len(chunks) == len(metadata), "Mismatch between chunks and metadata"

        # Get current collection count to generate unique IDs
        try:
            collection_info = self.client.get_collection(self.collection_name)
            start_id = collection_info.points_count
        except Exception:
            start_id = 0

        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            payload = {
                "text": chunk,
            }
            
            if metadata and i < len(metadata):
                meta = metadata[i]
                payload["page_number"] = meta.get("page_number", 0)
                payload["chunk_index"] = meta.get("chunk_index", i)
                payload["source_file"] = meta.get("source_file", "unknown")
            else:
                payload["page_number"] = 0
                payload["chunk_index"] = i
                payload["source_file"] = "unknown"
            
            # Use start_id + i to generate unique IDs
            points.append(
                PointStruct(
                    id=start_id + i,
                    vector=emb,
                    payload=payload
                )
            )

        # Upsert points (insert or update)
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def get_collection_count(self) -> int:
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count
        except Exception as e:
            error_str = str(e).lower()
            # Provide more specific error messages
            if "not found" in error_str or "does not exist" in error_str:
                print(f"Collection '{self.collection_name}' does not exist yet. Upload a document to create it.")
            elif "lock" in error_str or "already accessed" in error_str:
                print(f"Database is locked: {e}")
            else:
                print(f"Error getting collection count: {e}")
            return 0
    
    def diagnose(self) -> Dict[str, Any]:
        """Diagnostic function to check database state"""
        diagnostics = {
            "db_path": self.db_path,
            "collection_name": self.collection_name,
            "client_initialized": self.client is not None,
            "collection_exists": False,
            "collection_count": 0,
            "error": None
        }
        
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            diagnostics["collection_exists"] = self.collection_name in collection_names
            
            if diagnostics["collection_exists"]:
                collection_info = self.client.get_collection(self.collection_name)
                diagnostics["collection_count"] = collection_info.points_count
        except Exception as e:
            diagnostics["error"] = str(e)
        
        return diagnostics

    def search(
        self,
        query_embedding: List[float],
        limit: int = 3,
        metric: str = "COSINE"
    ) -> List[Dict[str, Any]]:
        # Qdrant uses the distance metric set during collection creation
        # The metric parameter is kept for API compatibility but not used
        
        try:
            # Validate query embedding
            if not query_embedding:
                raise ValueError("Query embedding is empty")
            if not isinstance(query_embedding, list):
                raise ValueError(f"Query embedding must be a list, got {type(query_embedding)}")
            if len(query_embedding) == 0:
                raise ValueError("Query embedding has zero length")
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )

            hits = []
            for hit in results:
                payload = hit.payload
                hits.append({
                    "text": payload.get("text", ""),
                    "score": hit.score,
                    "page_number": payload.get("page_number", 0),
                    "chunk_index": payload.get("chunk_index", 0),
                    "source_file": payload.get("source_file", "unknown")
                })

            return hits
        except Exception as e:
            error_msg = f"Qdrant search failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(f"  Collection: {self.collection_name}")
            print(f"  Query embedding length: {len(query_embedding) if query_embedding else 0}")
            raise Exception(error_msg) from e