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
        """Configure LLM for CrewAI agents using OpenRouter if available, otherwise OpenAI"""
        # Check for OpenRouter first
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if openrouter_key:
            # Configure for OpenRouter - set environment variables that litellm will use
            # CrewAI uses litellm internally, which can use OPENAI_API_KEY with base_url
            os.environ["OPENAI_API_KEY"] = openrouter_key
            os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
            # Return model string in OpenRouter format
            return "openai/gpt-4o-mini"  # OpenRouter model format
        elif openai_key:
            # Use OpenAI directly
            return "gpt-4o-mini"
        else:
            # Fallback
            return "gpt-4o-mini"
    
    def create_rag_agent(self, rag_pipeline: RAGPipeline) -> Agent:
        config = self.config_loader.get_agent_config("rag_agent")
        rag_tool = RAGTool(rag_pipeline=rag_pipeline)
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[rag_tool],
            llm=self.llm,
            verbose=config.get("verbose", True)
        )
    
    def create_memory_agent(self, memory_layer: ZepMemoryLayer) -> Agent:
        config = self.config_loader.get_agent_config("memory_agent")
        memory_tool = MemoryTool(memory_layer=memory_layer)
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[memory_tool],
            llm=self.llm,
            verbose=config.get("verbose", True)
        )
    
    def create_web_search_agent(self, firecrawl_api_key: str) -> Agent:
        config = self.config_loader.get_agent_config("web_search_agent")
        web_search_tool = FirecrawlSearchTool(api_key=firecrawl_api_key)
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[web_search_tool],
            llm=self.llm,
            verbose=config.get("verbose", True)
        )
    
    def create_arxiv_agent(self) -> Agent:
        config = self.config_loader.get_agent_config("arxiv_agent")
        arxiv_tool = ArxivTool()
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[arxiv_tool],
            llm=self.llm,
            verbose=config.get("verbose", True)
        )
    
    def create_evaluator_agent(self) -> Agent:
        config = self.config_loader.get_agent_config("evaluator_agent")
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self.llm,
            verbose=config.get("verbose", True)
        )
    
    def create_synthesizer_agent(self) -> Agent:
        config = self.config_loader.get_agent_config("synthesizer_agent")
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self.llm,
            verbose=config.get("verbose", True)
        )