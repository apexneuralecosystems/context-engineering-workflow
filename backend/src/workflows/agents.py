import os
from crewai import Agent
from typing import Optional
from langchain_openai import ChatOpenAI

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
        
        # Configure environment variables for litellm (CrewAI uses litellm internally)
        os.environ["OPENAI_API_KEY"] = openrouter_key
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
        os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
        
        # Create explicit LangChain LLM with OpenRouter configuration
        # This ensures the base_url is explicitly set and not relying on environment variables
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",  # OpenRouter model format
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://github.com/your-repo"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "Research Assistant")
            },
            temperature=0.2
        )
        
        # Log for debugging
        print(f"\n{'='*80}")
        print("CrewAI/LiteLLM OpenRouter Configuration:")
        print(f"  OPENROUTER_API_KEY: SET")
        print(f"  OPENAI_API_KEY: SET (OpenRouter key)")
        print(f"  OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
        print(f"  LITELLM_API_BASE: {os.environ.get('LITELLM_API_BASE')}")
        print(f"  Using explicit ChatOpenAI with base_url: https://openrouter.ai/api/v1")
        print(f"  Model: openai/gpt-4o-mini")
        print(f"{'='*80}\n")
        
        return llm
    
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