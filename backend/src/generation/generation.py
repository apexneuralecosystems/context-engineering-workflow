import os
import json
import uuid
from typing import Dict, Any, List, Optional
from openai import OpenAI
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a research assistant that MUST ground answers in provided context.
Policy:
1) Use only the supplied CONTEXT and/or explicit SOURCE items.
2) If context is INSUFFICIENT to answer the QUESTION, return status=INSUFFICIENT_CONTEXT with what is missing.
3) If sufficient, answer concisely with citations (doc/page or URL) and a confidence score (0–1).
4) Never rely on parametric knowledge if it is not in the context.
5) Output MUST match the response schema exactly.
"""

RAG_TEMPLATE = (
    "CONTEXT:\n{context}\n"
    "---------------------\n"
    "QUESTION:\n{query}\n\n"
    "Task: Determine if the CONTEXT is sufficient to answer the QUESTION.\n"
    "- If sufficient: produce a grounded answer with citations and confidence.\n"
    "- If NOT sufficient: do NOT answer; return status=INSUFFICIENT_CONTEXT and list missing info.\n"
    "Fill the structured fields only.\n"
)

# Structured Output schema 
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["OK", "INSUFFICIENT_CONTEXT"]},
        "source_used": {"type": "string", "enum": ["MEMORY", "RAG", "WEB", "TOOL", "NONE"]},
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "locator": {"type": "string"}
                },
                "required": ["label", "locator"],
                "additionalProperties": False
            }
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "missing": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["status", "source_used", "answer", "citations", "confidence", "missing"],
    "additionalProperties": False
}


class StructuredResponseGen:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        system_prompt: str = SYSTEM_PROMPT,
        rag_template: str = RAG_TEMPLATE,
        temperature: float = 0.2,
        use_openrouter: bool = False,
    ):
        # Check for OpenRouter API key first, then fall back to OpenAI
        if use_openrouter or os.getenv("OPENROUTER_API_KEY"):
            api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1"
            # OpenRouter model names can be prefixed with provider (e.g., "openai/gpt-4o-mini")
            # or used directly if OpenRouter supports it
            if not model.startswith(("openai/", "anthropic/", "google/", "meta/", "mistralai/")):
                # Default to OpenAI provider if no prefix
                model = f"openai/{model}"
            # OpenRouter recommends HTTP-Referer header (optional but recommended)
            default_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://github.com/your-repo"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "Research Assistant")
            }
            provider_name = "OpenRouter"
        else:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            base_url = None  # Use default OpenAI base URL
            default_headers = None
            provider_name = "OpenAI"
        
        # Validate that API key is provided
        if not api_key:
            error_msg = f"❌ {provider_name} API key is required but not found.\n\n"
            error_msg += "Please set one of the following environment variables:\n"
            if provider_name == "OpenRouter":
                error_msg += "  - OPENROUTER_API_KEY (recommended - supports multiple LLM providers)\n"
                error_msg += "  - OPENAI_API_KEY (fallback)\n"
            else:
                error_msg += "  - OPENAI_API_KEY\n"
                error_msg += "  - OPENROUTER_API_KEY (alternative - supports multiple LLM providers)\n"
            error_msg += "\nAdd it to your .env file or set it as an environment variable.\n"
            error_msg += f"Get your API key from: https://{'openrouter.ai' if provider_name == 'OpenRouter' else 'platform.openai.com'}"
            raise ValueError(error_msg)
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers
        )
        self.model = model
        self.system_prompt = system_prompt
        self.rag_template = rag_template
        self.temperature = temperature
        self.is_openrouter = provider_name == "OpenRouter"

    def generate(
        self,
        *,
        query: str,
        context_blocks: List[str],
        source_used: str = "RAG",
        schema: Dict[str, Any] = RESPONSE_SCHEMA,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = datetime.now()
        logger.info("="*80)
        logger.info("Starting structured response generation")
        logger.info(f"Timestamp: {start_time}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Temperature: {self.temperature}")
        logger.info(f"Source: {source_used}")
        logger.info(f"Context blocks: {len(context_blocks)}")
        
        context = "\n\n".join(context_blocks).strip()
        user_prompt = self.rag_template.format(context=context, query=query)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"Input prompt length: {len(user_prompt)} characters")

        try:
            # Prepare request kwargs
            request_kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "messages": messages,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "research_briefing",
                        "schema": schema,
                        "strict": True  # hard schema adherence
                    }
                },
            }
            
            # Enable OpenRouter cost tracking
            if self.is_openrouter:
                # OpenRouter requires extra_body to include cost data in response
                request_kwargs["extra_body"] = {"usage": {"include": True}}
                logger.info("OpenRouter cost tracking enabled")
            
            logger.info("Sending request to LLM for structured response generation...")
            response = self.client.chat.completions.create(**request_kwargs)
            logger.info("Received response from LLM")

            try:
                output_text = response.choices[0].message.content
            except Exception as e:
                raise RuntimeError(f"Unexpected responses payload shape: {e}")

            try:
                data = json.loads(output_text)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Model did not return valid JSON: {e}\nRaw: {output_text[:400]}")

            # Extract cost and usage from response
            # Note: extract_cost_from_response and extract_usage_from_response are designed for LangChain responses
            # For OpenAI SDK responses, we use our custom extraction method
            usage_details = None
            cost = None
            metadata = {
                "finish_reason": response.choices[0].finish_reason,
                "status": data.get("status"),
                "confidence": data.get("confidence"),
            }
            
            if hasattr(response, 'usage') and response.usage:
                usage_details = {
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                    "unit": "TOKENS"
                }
                
                # Extract cost from OpenRouter response
                if self.is_openrouter:
                    cost = self._extract_cost_from_openrouter_response(response)
                    if cost is not None and cost > 0:
                        metadata["cost"] = cost
                        metadata["total_cost"] = cost
                        metadata["cost_unit"] = "USD"
                        usage_details["total_cost"] = cost
                        usage_details["cost_unit"] = "USD"
                        logger.info(f"LLM call cost: ${cost:.6f}")
                    else:
                        logger.warning("No cost found in OpenRouter response. Ensure extra_body={'usage': {'include': True}} is set.")
                        # Debug: log response structure for troubleshooting
                        if logger.isEnabledFor(logging.DEBUG):
                            try:
                                response_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                                logger.debug(f"Response attributes: {response_attrs}")
                                if hasattr(response, 'usage'):
                                    logger.debug(f"Usage object: {response.usage}")
                                    if hasattr(response.usage, '__dict__'):
                                        logger.debug(f"Usage dict: {response.usage.__dict__}")
                            except Exception as e:
                                logger.debug(f"Failed to log response structure: {e}")
                
                if usage_details:
                    logger.info(f"Token usage: {usage_details.get('input', 0)} input, {usage_details.get('output', 0)} output, {usage_details.get('total', 0)} total")
            
            # Ensure cost is properly included in usage_details
            if usage_details:
                if cost is not None and cost > 0:
                    usage_details["total_cost"] = cost
                    usage_details["cost_unit"] = "USD"
                    # Also add input/output costs if available
                    if hasattr(response, 'usage') and response.usage:
                        # Try to extract detailed costs from OpenRouter response
                        cost_details = self._extract_cost_details_from_openrouter_response(response)
                        if cost_details:
                            if cost_details.get('input_cost'):
                                usage_details["input_cost"] = cost_details['input_cost']
                            if cost_details.get('output_cost'):
                                usage_details["output_cost"] = cost_details['output_cost']

            data["source_used"] = source_used
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Structured response generation completed successfully")
            logger.info(f"Total execution time: {execution_time:.2f} seconds")
            logger.info(f"Response status: {data.get('status')}")
            logger.info(f"Confidence: {data.get('confidence')}")
            logger.info("="*80)
            
            return data
        except Exception as e:
            error_msg = str(e)
            logger.error("="*80)
            logger.error(f"Error during structured response generation: {error_msg}")
            logger.error("Exception details:", exc_info=True)
            logger.error("="*80)
            
            raise
    
    def _extract_cost_from_openrouter_response(self, response) -> Optional[float]:
        """
        Extract cost from OpenRouter response (OpenAI SDK format).
        
        OpenRouter returns cost in various places:
        1. response.usage (if available as custom fields)
        2. response._response.headers (X-OpenRouter-* headers)
        3. response._response.json() (in the raw response body)
        
        Args:
            response: OpenAI SDK ChatCompletion response object
            
        Returns:
            Cost as float, or None if not available
        """
        try:
            # Method 1: Check if cost is in usage object (OpenRouter may add it)
            if hasattr(response, 'usage') and response.usage:
                # Check for cost in usage object attributes
                if hasattr(response.usage, 'cost'):
                    return float(response.usage.cost)
                # Check if usage is a dict-like object
                if hasattr(response.usage, '__dict__'):
                    usage_dict = response.usage.__dict__
                    if 'cost' in usage_dict:
                        return float(usage_dict['cost'])
            
            # Method 2: Check response headers (OpenRouter may include cost in headers)
            if hasattr(response, '_response') and hasattr(response._response, 'headers'):
                headers = response._response.headers
                # OpenRouter may include cost in custom headers
                cost_header = headers.get('X-OpenRouter-Cost') or headers.get('x-openrouter-cost')
                if cost_header:
                    try:
                        return float(cost_header)
                    except (ValueError, TypeError):
                        pass
            
            # Method 3: Check raw response body (OpenRouter includes cost in response)
            # Try multiple ways to access the raw response
            raw_response_data = None
            
            # Try _response.json() (httpx response)
            if hasattr(response, '_response') and hasattr(response._response, 'json'):
                try:
                    raw_response_data = response._response.json()
                except Exception:
                    pass
            
            # Try accessing via model_dump or similar
            if raw_response_data is None and hasattr(response, 'model_dump'):
                try:
                    raw_response_data = response.model_dump()
                except Exception:
                    pass
            
            # Try accessing via dict conversion
            if raw_response_data is None:
                try:
                    raw_response_data = dict(response) if hasattr(response, '__iter__') else None
                except Exception:
                    pass
            
            # Extract cost from raw response data
            if raw_response_data and isinstance(raw_response_data, dict):
                # Check top level
                if 'cost' in raw_response_data:
                    return float(raw_response_data['cost'])
                # Check in usage
                if 'usage' in raw_response_data and isinstance(raw_response_data['usage'], dict):
                    usage_data = raw_response_data['usage']
                    if 'cost' in usage_data:
                        return float(usage_data['cost'])
                    # Check cost_details (OpenRouter format)
                    if 'cost_details' in usage_data:
                        cost_details = usage_data['cost_details']
                        if isinstance(cost_details, dict):
                            # Try upstream_inference_cost first (total cost)
                            upstream_cost = cost_details.get('upstream_inference_cost')
                            if upstream_cost is not None:
                                return float(upstream_cost)
                            # Fallback: calculate from prompt and completion costs
                            prompt_cost = cost_details.get('upstream_inference_prompt_cost', 0)
                            completion_cost = cost_details.get('upstream_inference_completions_cost', 0)
                            if prompt_cost or completion_cost:
                                total = (float(prompt_cost) if prompt_cost else 0) + (float(completion_cost) if completion_cost else 0)
                                if total > 0:
                                    return total
            
            # Method 4: Check if response has a _raw_response attribute
            if hasattr(response, '_raw_response'):
                raw_response = response._raw_response
                if isinstance(raw_response, dict):
                    if 'cost' in raw_response:
                        return float(raw_response['cost'])
                    if 'usage' in raw_response and isinstance(raw_response['usage'], dict):
                        if 'cost' in raw_response['usage']:
                            return float(raw_response['usage']['cost'])
            
            return None
        except Exception as e:
            logger.debug(f"Failed to extract cost from OpenRouter response: {e}")
            return None
    
    def _extract_cost_details_from_openrouter_response(self, response) -> Optional[Dict[str, float]]:
        """
        Extract detailed cost breakdown from OpenRouter response.
        
        Returns:
            Dictionary with 'input_cost', 'output_cost', 'total_cost' if available
        """
        try:
            cost_details = {}
            
            # Try to get cost details from raw response
            raw_response_data = None
            
            # Try _response.json() (httpx response)
            if hasattr(response, '_response') and hasattr(response._response, 'json'):
                try:
                    raw_response_data = response._response.json()
                except Exception:
                    pass
            
            # Try accessing via model_dump or similar
            if raw_response_data is None and hasattr(response, 'model_dump'):
                try:
                    raw_response_data = response.model_dump()
                except Exception:
                    pass
            
            # Extract cost details from raw response data
            if raw_response_data and isinstance(raw_response_data, dict):
                if 'usage' in raw_response_data and isinstance(raw_response_data['usage'], dict):
                    usage_data = raw_response_data['usage']
                    if 'cost_details' in usage_data:
                        cost_details_raw = usage_data['cost_details']
                        if isinstance(cost_details_raw, dict):
                            # Extract individual costs
                            prompt_cost = cost_details_raw.get('upstream_inference_prompt_cost')
                            completion_cost = cost_details_raw.get('upstream_inference_completions_cost')
                            total_cost = cost_details_raw.get('upstream_inference_cost')
                            
                            if prompt_cost is not None:
                                cost_details['input_cost'] = float(prompt_cost)
                            if completion_cost is not None:
                                cost_details['output_cost'] = float(completion_cost)
                            if total_cost is not None:
                                cost_details['total_cost'] = float(total_cost)
                            
                            if cost_details:
                                return cost_details
            
            return None
        except Exception as e:
            logger.debug(f"Failed to extract cost details from OpenRouter response: {e}")
            return None