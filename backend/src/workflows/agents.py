import os
from crewai import Agent
from typing import Optional

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
    """Class for creating agents from configuration files"""
    def __init__(self, config_loader: Optional[ConfigLoader] = None, llm: Optional[str] = None):
        self.config_loader = config_loader or ConfigLoader()
        self.llm = llm or self._create_default_llm()
    
    def _create_default_llm(self):
        """Configure LLM for CrewAI agents using OpenRouter (required)"""
        # This project uses OpenRouter exclusively
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        if not openrouter_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required. Please set it in your .env file.\n"
                "Get your API key from: https://openrouter.ai/"
            )
        
        # Configure for OpenRouter - set environment variables that litellm will use
        # CrewAI uses litellm internally, which can use OPENAI_API_KEY with base_url
        # IMPORTANT: Set these BEFORE any CrewAI agents are created
        os.environ["OPENAI_API_KEY"] = openrouter_key
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
        
        # Also set litellm-specific variables
        os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
        
        # Log for debugging
        if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
            print(f"\n{'='*80}")
            print("CrewAI/LiteLLM OpenRouter Configuration:")
            print(f"  OPENROUTER_API_KEY: SET")
            print(f"  OPENAI_API_KEY: SET (OpenRouter key)")
            print(f"  OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
            print(f"  LITELLM_API_BASE: {os.environ.get('LITELLM_API_BASE')}")
            print(f"{'='*80}\n")
        
        # Return model string in OpenRouter format
        model = "openai/gpt-4o-mini"  # OpenRouter model format
        
        return model
    
    def create_rag_agent(self, rag_pipeline: RAGPipeline) -> Agent:
        config = self.config_loader.get_agent_config("rag_agent")
        rag_tool = RAGTool(rag_pipeline=rag_pipeline)
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [rag_tool],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_memory_agent(self, memory_layer: ZepMemoryLayer) -> Agent:
        config = self.config_loader.get_agent_config("memory_agent")
        memory_tool = MemoryTool(memory_layer=memory_layer)
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [memory_tool],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_web_search_agent(self, firecrawl_api_key: str) -> Agent:
        config = self.config_loader.get_agent_config("web_search_agent")
        web_search_tool = FirecrawlSearchTool(api_key=firecrawl_api_key)
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [web_search_tool],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_arxiv_agent(self) -> Agent:
        config = self.config_loader.get_agent_config("arxiv_agent")
        arxiv_tool = ArxivTool()
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [arxiv_tool],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_evaluator_agent(self) -> Agent:
        config = self.config_loader.get_agent_config("evaluator_agent")
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)
    
    def create_synthesizer_agent(self) -> Agent:
        config = self.config_loader.get_agent_config("synthesizer_agent")
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        return Agent(**agent_kwargs)