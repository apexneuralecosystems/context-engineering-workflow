import os
import voyageai
from typing import List, Optional, Literal
from dotenv import load_dotenv

load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")


class ContextualizedEmbeddings:
    def __init__(self, api_key: Optional[str] = None, model: str = "voyage-context-3"):
        self.api_key = api_key or VOYAGE_API_KEY
        self.client = voyageai.Client(api_key=self.api_key)
        self.model = model

    def embed_document_chunks(
        self,
        docs_chunks: List[List[str]],
        *,
        output_dimension = 1024,
        output_dtype = "float",
    ) -> List[List[List[float]]]:

        resp = self.client.contextualized_embed(
            inputs=docs_chunks,
            model=self.model,
            input_type="document",               
            output_dimension=output_dimension,   
            output_dtype=output_dtype,          
        )
        return [r.embeddings for r in resp.results]

    def embed_query(
        self,
        query,
        *,
        output_dimension = None,
        output_dtype: Literal["float", "int8", "uint8", "binary", "ubinary"] = "float",
    ) -> List[float]:
        try:
            if not self.api_key:
                raise ValueError("VOYAGE_API_KEY is not set. Cannot generate embeddings.")
            
            resp = self.client.contextualized_embed(
                inputs=[[query]],
                model=self.model,
                input_type="query",
                output_dimension=output_dimension,
                output_dtype=output_dtype,
            )
            if not resp or not resp.results or not resp.results[0].embeddings:
                raise ValueError("Empty response from Voyage API. Check API key and connectivity.")
            return resp.results[0].embeddings[0]
        except Exception as e:
            error_msg = f"Failed to generate query embedding: {str(e)}"
            if not self.api_key:
                error_msg += " VOYAGE_API_KEY is not set."
            print(f"Embedding Error: {error_msg}")
            raise Exception(error_msg) from e