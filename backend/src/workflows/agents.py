import os
from typing import Optional

# CRITICAL: Configure environment variables for CrewAI BEFORE importing
# CrewAI uses litellm internally, which reads environment variables at import time
# This is the ONLY way to configure CrewAI - no manual LLM creation needed
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    # Set environment variables - CrewAI/litellm will read these automatically
    os.environ["OPENAI_API_KEY"] = openrouter_key
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
    
    # Optional: Configure litellm module-level as backup
    try:
        import litellm
        if hasattr(litellm, 'api_base'):
            litellm.api_base = "https://openrouter.ai/api/v1"
        if hasattr(litellm, 'api_key'):
            litellm.api_key = openrouter_key
        if hasattr(litellm, 'set_verbose'):
            litellm.set_verbose(False)
    except (ImportError, AttributeError):
        # litellm might not be directly importable or configured differently
        # Environment variables should be enough
        pass

from crewai import Agent

from src.config import ConfigLoader
from src.tools import (
    RAGTool, 
    MemoryTool, 
    ArxivTool, 
    FirecrawlSearchTool
)
from src.rag import RAGPipeline
from src.memory import ZepMemoryLayer


class Agents:
    """
    Class for creating CrewAI agents.
    
    Uses CrewAI's native LLM configuration via environment variables.
    No manual LLM creation needed - CrewAI handles it internally.
    """
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        self.config_loader = config_loader or ConfigLoader()
        
        # Verify OpenRouter configuration is set
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required. Please set it in your .env file.\n"
                "Get your API key from: https://openrouter.ai/"
            )
        
        # Ensure environment variables are set (CrewAI reads these)
        os.environ["OPENAI_API_KEY"] = openrouter_key
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
        os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
        
        # Log configuration
        print(f"\n{'='*80}")
        print("CrewAI Native LLM Configuration (CrewAI Only Mode):")
        print(f"{'='*80}")
        print(f"  [OK] OPENROUTER_API_KEY: SET ({len(openrouter_key)} chars)")
        print(f"  [OK] OPENAI_API_KEY: SET (OpenRouter key)")
        print(f"  [OK] OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
        print(f"  [OK] LITELLM_API_BASE: {os.environ.get('LITELLM_API_BASE')}")
        print(f"  [INFO] Using CrewAI's native LLM (no manual LLM creation)")
        print(f"  [INFO] CrewAI will use environment variables automatically")
        print(f"{'='*80}\n")
        
        import sys
        sys.stdout.flush()
    
    def create_rag_agent(self, rag_pipeline: RAGPipeline) -> Agent:
        """Create RAG agent using CrewAI's native LLM configuration"""
        config = self.config_loader.get_agent_config("rag_agent")
        rag_tool = RAGTool(rag_pipeline=rag_pipeline)
        
        # CrewAI will use its default LLM from environment variables
        # No need to pass llm parameter - CrewAI handles it
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [rag_tool],
            # No llm parameter - CrewAI uses environment variables
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_memory_agent(self, memory_layer: ZepMemoryLayer) -> Agent:
        """Create memory agent using CrewAI's native LLM configuration"""
        config = self.config_loader.get_agent_config("memory_agent")
        memory_tool = MemoryTool(memory_layer=memory_layer)
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [memory_tool],
            # No llm parameter - CrewAI uses environment variables
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_web_search_agent(self, firecrawl_api_key: str) -> Agent:
        """Create web search agent using CrewAI's native LLM configuration"""
        config = self.config_loader.get_agent_config("web_search_agent")
        web_search_tool = FirecrawlSearchTool(api_key=firecrawl_api_key)
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [web_search_tool],
            # No llm parameter - CrewAI uses environment variables
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_arxiv_agent(self) -> Agent:
        """Create ArXiv agent using CrewAI's native LLM configuration"""
        config = self.config_loader.get_agent_config("arxiv_agent")
        arxiv_tool = ArxivTool()
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [arxiv_tool],
            # No llm parameter - CrewAI uses environment variables
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_evaluator_agent(self) -> Agent:
        """Create evaluator agent using CrewAI's native LLM configuration"""
        config = self.config_loader.get_agent_config("evaluator_agent")
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            # No llm parameter - CrewAI uses environment variables
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_synthesizer_agent(self) -> Agent:
        """Create synthesizer agent using CrewAI's native LLM configuration"""
        config = self.config_loader.get_agent_config("synthesizer_agent")
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            # No llm parameter - CrewAI uses environment variables
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)