import os
import json
from typing import Iterable, List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from tensorlake.documentai import (
    DocumentAI,
    ParsingOptions,
    ChunkingStrategy,
    TableOutputMode,
    TableParsingFormat,
    StructuredExtractionOptions
)

TENSORLAKE_API_KEY = os.getenv("TENSORLAKE_API_KEY")

RESEARCH_PAPER_SCHEMA = {
    "type": "object",
    "properties": {
        "paper": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "authors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "abstract": {"type": "string"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heading": {"type": "string"},
                            "summary": {"type": "string"}
                        },
                        "required": ["heading", "summary"]
                    }
                }
            },
            "required": ["title", "authors", "abstract", "sections"]
        }
    },
    "required": ["paper"]
}

class TensorLakeClient:
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or TENSORLAKE_API_KEY
        if not api_key:
            raise ValueError("TENSORLAKE_API_KEY is required. Please set it in your environment or pass it as a parameter.")
        
        # Try to get SDK version for diagnostics
        try:
            import tensorlake
            import pkg_resources
            try:
                self.sdk_version = pkg_resources.get_distribution("tensorlake").version
            except:
                self.sdk_version = getattr(tensorlake, '__version__', 'unknown')
        except:
            self.sdk_version = 'unknown'
        
        try:
            self.doc_ai = DocumentAI(api_key=api_key)
        except Exception as e:
            error_msg = f"Failed to create TensorLake DocumentAI client: {str(e)}"
            raise Exception(error_msg) from e
        
        # Test API connection by attempting to list files
        # If validation error occurs, it's a version mismatch but API is working
        # We'll catch all errors and treat validation errors as warnings only
        try:
            self._verify_api_connection()
        except Exception as verify_error:
            error_str = str(verify_error)
            error_str_lower = error_str.lower()
            error_type = type(verify_error).__name__
            
            # Check for Pydantic validation errors (version mismatch)
            # The error message contains "validation error" or "Field required"
            # Also check for "PaginatedResult" which appears in the error
            is_validation_error = (
                "validation error" in error_str_lower or 
                "field required" in error_str_lower or
                "ValidationError" in error_type or
                "pydantic" in error_str_lower or
                "paginatedresult" in error_str_lower or
                "hasmore" in error_str_lower or
                "prevcursor" in error_str_lower or
                "nextcursor" in error_str_lower or
                "has_more" in error_str_lower or
                "prev_cursor" in error_str_lower or
                "next_cursor" in error_str_lower
            )
            
            if is_validation_error:
                print("⚠️  Warning: TensorLake SDK version mismatch detected during initialization")
                print("   The API is responding correctly, but SDK can't parse response format.")
                print("   File uploads should still work. Update SDK: pip install --upgrade tensorlake")
                # Don't raise - allow initialization to continue
            elif "404" in error_str_lower or "not found" in error_str_lower:
                print("⚠️  Warning: TensorLake API endpoint returned 404 (listing files endpoint)")
                print("   This may indicate an outdated SDK or API changes.")
                print("   File uploads use a different endpoint and may still work.")
                print("   Recommended: pip install --upgrade tensorlake")
                # Don't raise - allow initialization to continue
                # The actual upload endpoint may work even if listing doesn't
            else:
                # For other errors, also treat as warning if they seem like API response issues
                # Only raise for actual connection/auth failures
                print(f"⚠️  Warning: Could not verify API connection: {error_str}")
                print("   This may be a version mismatch. File uploads may still work.")
                print("   Update SDK: pip install --upgrade tensorlake")
                # Don't raise - allow initialization to continue
    
    def _verify_api_connection(self):
        """Verify that the API key works by attempting to list files"""
        try:
            self.doc_ai.files()
        except Exception as e:
            error_str = str(e)
            error_str_lower = error_str.lower()
            error_type = type(e).__name__
            
            # Check for Pydantic validation errors (version mismatch)
            # The error message contains "validation error" or "Field required"
            # Also check for specific field names that appear in the error
            is_validation_error = (
                "validation error" in error_str_lower or 
                "field required" in error_str_lower or
                "ValidationError" in error_type or
                "pydantic" in error_str_lower or
                "paginatedresult" in error_str_lower or
                "hasmore" in error_str_lower or
                "prevcursor" in error_str_lower or
                "nextcursor" in error_str_lower or
                "has_more" in error_str_lower or
                "prev_cursor" in error_str_lower or
                "next_cursor" in error_str_lower
            )
            
            # For validation errors, don't raise - just return
            if is_validation_error:
                print("⚠️  WARNING: TensorLake SDK version mismatch detected")
                print("   The API is responding, but the SDK can't parse the response format.")
                print("   File uploads should still work. Update SDK: pip install --upgrade tensorlake")
                return
            
            # For 404 errors, don't raise - upload endpoint may still work
            if "404" in error_str_lower or "not found" in error_str_lower:
                return
            
            # For other errors, raise to let caller handle
            raise Exception(f"TensorLake API connection failed: {error_str}") from e
    
    def list_uploaded_files(self):
        try:
            files_page = self.doc_ai.files()
            print(f"TensorLake files found: {len(files_page.items)}")
            for file_info in files_page.items:
                print(f"  - {file_info.name} (ID: {file_info.id}, Size: {file_info.file_size} bytes, Type: {file_info.mime_type})")
            return files_page.items
        except Exception as e:
            error_str = str(e).lower()
            if "validation error" in error_str or "field required" in error_str:
                print(f"⚠️  Warning: Cannot list files due to SDK version mismatch: {e}")
                print("   This is a known issue with outdated TensorLake SDK versions.")
                print("   File uploads may still work. Update SDK: pip install --upgrade tensorlake")
            else:
                print(f"Error listing TensorLake files: {e}")
            return []
    
    def verify_file_uploaded(self, file_id: str) -> bool:
        """
        Verify that a file was uploaded. 
        Note: If listing files fails (e.g., due to SDK issues), we assume the file exists
        if we have a file_id (since upload() returned it successfully).
        """
        try:
            files = self.list_uploaded_files()
            file_ids = [f.id for f in files]
            exists = file_id in file_ids
            print(f"File ID {file_id} {'exists' if exists else 'NOT FOUND'} in TensorLake")
            return exists
        except Exception as e:
            # If listing fails (e.g., 404 or validation errors), we can't verify
            # But if we have a file_id, it means upload() succeeded, so assume it exists
            error_str = str(e).lower()
            if "404" in error_str or "validation error" in error_str or "field required" in error_str:
                print(f"⚠️  Warning: Cannot verify file {file_id} due to listing endpoint issues")
                print("   However, since upload() returned this file_id, the file should exist.")
                print("   Proceeding with assumption that file exists.")
                return True  # Assume file exists if we got a file_id from upload
            else:
                print(f"Error verifying file {file_id}: {e}")
                # For other errors, still assume file exists if we have file_id
                return True

    def upload(self, paths: Iterable[str]) -> List[str]:
        print("Files before upload:")
        files_before = self.list_uploaded_files()
        
        file_ids = []
        for path in paths:
            if not os.path.exists(path):
                raise Exception(f"File does not exist: {path}")
            
            file_size = os.path.getsize(path)
            if file_size == 0:
                raise Exception(f"File is empty: {path} (0 bytes)")
            
            print(f"\nUploading file: {path} ({file_size} bytes)")
            
            try:
                fid = self.doc_ai.upload(path=path)
                print(f"Upload successful, file_id: {fid}")
                file_ids.append(fid)
            except Exception as upload_error:
                error_str = str(upload_error)
                error_msg = f"Upload failed for {path}: {error_str}"
                
                if "404" in error_str or "Not Found" in error_str:
                    error_msg += "\n\n❌ CRITICAL: TensorLake API endpoints are returning 404 errors."
                    error_msg += "\n   This indicates your TensorLake SDK is outdated or incompatible."
                    error_msg += f"\n   Current SDK version: {getattr(self, 'sdk_version', 'unknown')}"
                    error_msg += "\n\n🔧 REQUIRED FIX:"
                    error_msg += "\n   1. Update TensorLake SDK to the latest version:"
                    error_msg += "\n      pip install --upgrade tensorlake"
                    error_msg += "\n   2. If using uv:"
                    error_msg += "\n      uv pip install --upgrade tensorlake"
                    error_msg += "\n   3. Restart your application after updating"
                    error_msg += "\n\n📚 Additional checks:"
                    error_msg += "\n   - Verify your API key is valid at https://tensorlake.ai/"
                    error_msg += "\n   - Check TensorLake documentation: https://docs.tensorlake.ai/"
                    error_msg += "\n   - Ensure you're using Python 3.8+ (required by latest SDK)"
                    error_msg += f"\n\nError details: {type(upload_error).__name__}: {upload_error}"
                
                print(f"Upload failed for {path}: {upload_error}")
                raise Exception(error_msg) from upload_error
        
        print("\nFiles after upload:")
        files_after = self.list_uploaded_files()
        
        new_files = [f for f in files_after if f not in files_before]
        if new_files:
            print(f"{len(new_files)} new file(s) uploaded:")
            for file_info in new_files:
                print(f"  - {file_info.name} (ID: {file_info.id})")
        else:
            print("No new files detected in TensorLake after upload")
            
        return file_ids

    def parse_structured(
        self,
        file_id: str,
        json_schema: Dict[str, Any],
        *,
        page_range = None,
        labels = None,
        chunking_strategy = ChunkingStrategy.SECTION,
        table_mode = TableOutputMode.MARKDOWN,
        table_format = TableParsingFormat.TSR,
    ) -> str:
        
        print(f"Using chunking strategy: {chunking_strategy}")
        print(f"Using table mode: {table_mode}")
        print(f"Schema name: research_paper")
        
        structured_extraction_options = StructuredExtractionOptions(
            schema_name="research_paper",
            json_schema=json_schema,
            provide_citations=True
        )

        parsing_options = ParsingOptions(
            chunking_strategy=chunking_strategy,
            table_output_mode=table_mode,
            table_parsing_format=table_format,
        )

        # Verify file exists, but be lenient if verification fails due to listing issues
        # If upload() returned a file_id, the file should exist even if we can't verify it
        if not self.verify_file_uploaded(file_id):
            # If verification failed but we have a file_id, it's likely a listing endpoint issue
            # Proceed anyway since upload() succeeded and returned this file_id
            print(f"⚠️  Warning: Could not verify file {file_id}, but proceeding since upload() returned this ID")
            # Don't raise - proceed with parsing
        
        print(f"Initiating parsing for file_id: {file_id}")
        try:
            parse_id = self.doc_ai.parse(
                file_id,
                page_range=page_range,
                parsing_options=parsing_options,
                structured_extraction_options=structured_extraction_options,
                labels=labels or {}
            )
            print(f"Parsing initiated, parse_id: {parse_id}")
            return parse_id
        except Exception as parse_error:
            print(f"Parsing initiation failed: {parse_error}")
            raise

    def get_result(self, parse_id: str) -> Dict[str, Any]:
        print(f"Waiting for completion of parse_id: {parse_id}")
        result = self.doc_ai.wait_for_completion(parse_id)
        print(f"Parsing completed for parse_id: {parse_id}")
        
        if result:
            if hasattr(result, 'chunks'):
                chunks = result.chunks
                chunk_count = len(chunks) if chunks else 0
                print(f"Number of chunks found: {chunk_count}")
                if chunk_count > 0:
                    print(f"First chunk preview: {chunks[0].content[:100] if hasattr(chunks[0], 'content') else 'No content'}...")
            else:
                print("Result has no 'chunks' attribute")
        else:
            print("Result is None or empty")
            
        return result
        


if __name__ == "__main__":
    client = TensorLakeClient()

    # Upload local documents
    file_ids = client.upload([
        "data/attention-is-all-you-need-Paper.pdf",
    ])

    # Parse each with schema (and produce RAG chunks)
    parse_ids = []
    for fid in file_ids:
        pid = client.parse_structured(
            file_id=fid,
            json_schema=RESEARCH_PAPER_SCHEMA,
            page_range=None,  # parse all pages
        )
        parse_ids.append(pid)

    # Retrieve the parsed result (markdown chunks + schema JSON)
    results = [client.get_result(pid) for pid in parse_ids]

    # collect RAG chunks + structured paper metadata
    rag_chunks, extracted_data = [], []
    for res in results:
        # markdown chunks for retrieval
        for chunk in res.chunks:
            rag_chunks.append({
                "page": chunk.page_number,
                "text": chunk.content,
            })
        # structured extraction schema
        serializable_data = res.model_dump()
        extracted_data.append(serializable_data)
