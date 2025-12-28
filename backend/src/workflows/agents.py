import os
from typing import Optional
from langchain_openai import ChatOpenAI

# CRITICAL: Configure litellm BEFORE importing CrewAI
# CrewAI uses litellm internally, and it reads configuration at import time
# Set environment variables first - this is the PRIMARY method
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    # Force set environment variables - these are what litellm reads
    os.environ["OPENAI_API_KEY"] = openrouter_key
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
    
    # Also try to configure litellm module-level if available
    # This is a backup - environment variables are primary
    try:
        import litellm
        # Set litellm configuration directly
        if hasattr(litellm, 'api_base'):
            litellm.api_base = "https://openrouter.ai/api/v1"
        if hasattr(litellm, 'api_key'):
            litellm.api_key = openrouter_key
        # Some versions use different attribute names
        if hasattr(litellm, 'set_verbose'):
            litellm.set_verbose(False)
    except (ImportError, AttributeError, Exception) as e:
        # litellm might not be directly importable or configured differently
        # Environment variables should be enough - this is just a backup
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
        
        # CRITICAL: Re-verify environment variables are set
        # CrewAI uses litellm internally, which reads from environment
        os.environ["OPENAI_API_KEY"] = openrouter_key
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
        os.environ["LITELLM_API_BASE"] = "https://openrouter.ai/api/v1"
        
        # Try to configure litellm directly if available
        try:
            import litellm
            litellm.api_base = "https://openrouter.ai/api/v1"
            litellm.api_key = openrouter_key
        except (ImportError, AttributeError):
            pass
        
        # Create explicit LangChain LLM with OpenRouter configuration
        # IMPORTANT: langchain-openai uses 'base_url' parameter (not openai_api_base)
        # This ensures the base_url is explicitly set and not relying on environment variables
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",  # OpenRouter model format
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",  # CRITICAL: This must be set
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://github.com/your-repo"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "Research Assistant")
            },
            temperature=0.2
        )
        
        # CRITICAL: Verify the LLM client is configured correctly
        # Access the underlying client and verify base_url
        if hasattr(llm, 'client') and hasattr(llm.client, 'base_url'):
            actual_base_url = str(llm.client.base_url)
            if actual_base_url != "https://openrouter.ai/api/v1":
                print(f"WARNING: LLM client base_url is {actual_base_url}, not OpenRouter!")
                # Force set it
                llm.client.base_url = "https://openrouter.ai/api/v1"
                print(f"  Fixed: Set base_url to https://openrouter.ai/api/v1")
        
        # CRITICAL: Verify and fix the LLM client's base_url
        # Access the underlying OpenAI client and ensure base_url is correct
        try:
            if hasattr(llm, 'client'):
                client = llm.client
                if hasattr(client, 'base_url'):
                    actual_base = str(client.base_url).rstrip('/')
                    expected_base = "https://openrouter.ai/api/v1"
                    if actual_base != expected_base:
                        print(f"WARNING: LLM client base_url is '{actual_base}', forcing to '{expected_base}'")
                        client.base_url = expected_base
                        print(f"  Fixed: base_url set to {expected_base}")
        except Exception as e:
            print(f"  Warning: Could not verify/fix LLM client base_url: {e}")
        
        # CRITICAL: Comprehensive logging to verify configuration
        print(f"\n{'='*80}")
        print("🔧 CrewAI/LiteLLM OpenRouter Configuration (DEBUG):")
        print(f"{'='*80}")
        print(f"  ✅ OPENROUTER_API_KEY: SET ({len(openrouter_key)} chars)")
        print(f"  ✅ OPENAI_API_KEY: SET (OpenRouter key, {len(os.environ.get('OPENAI_API_KEY', ''))} chars)")
        print(f"  ✅ OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
        print(f"  ✅ LITELLM_API_BASE: {os.environ.get('LITELLM_API_BASE')}")
        
        # Check litellm configuration
        try:
            import litellm
            litellm_base = getattr(litellm, 'api_base', None)
            litellm_key = getattr(litellm, 'api_key', None)
            print(f"  📦 litellm.api_base: {litellm_base}")
            print(f"  📦 litellm.api_key: {'SET' if litellm_key else 'NOT SET'} ({len(str(litellm_key)) if litellm_key else 0} chars)")
        except Exception as e:
            print(f"  ⚠️  litellm check failed: {e}")
        
        # Check ChatOpenAI client configuration
        try:
            if hasattr(llm, 'client'):
                client = llm.client
                if hasattr(client, 'base_url'):
                    client_base = str(client.base_url)
                    print(f"  🤖 ChatOpenAI.client.base_url: {client_base}")
                    if "openrouter" not in client_base.lower():
                        print(f"  ❌ ERROR: Client base_url does NOT contain 'openrouter'!")
                    else:
                        print(f"  ✅ Client base_url correctly points to OpenRouter")
                
                # Check if client has _client attribute (OpenAI SDK client)
                if hasattr(client, '_client') and hasattr(client._client, 'base_url'):
                    sdk_base = str(client._client.base_url)
                    print(f"  🔍 OpenAI SDK base_url: {sdk_base}")
            
            model_name = getattr(llm, 'model_name', getattr(llm, 'model', 'N/A'))
            print(f"  📝 ChatOpenAI model: {model_name}")
        except Exception as e:
            print(f"  ⚠️  ChatOpenAI check failed: {e}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
        
        print(f"  🎯 Expected base_url: https://openrouter.ai/api/v1")
        print(f"{'='*80}\n")
        
        # Force flush to ensure logs appear immediately
        import sys
        sys.stdout.flush()
        
        return llm
    
    def create_rag_agent(self, rag_pipeline: RAGPipeline) -> Agent:
        config = self.config_loader.get_agent_config("rag_agent")
        rag_tool = RAGTool(rag_pipeline=rag_pipeline)
        
        # Log LLM configuration when creating agent
        print(f"\n🔧 Creating RAG Agent with LLM:")
        try:
            if hasattr(self.llm, 'client') and hasattr(self.llm.client, 'base_url'):
                print(f"  📍 LLM base_url: {self.llm.client.base_url}")
        except:
            pass
        
        agent_kwargs = {
            "role": config["role"],
            "goal": config["goal"],
            "backstory": config["backstory"],
            "tools": [rag_tool],
            "llm": self.llm,
            "verbose": config.get("verbose", True)
        }
        agent = Agent(**agent_kwargs)
        
        # Verify agent has correct LLM
        if hasattr(agent, 'llm'):
            try:
                if hasattr(agent.llm, 'client') and hasattr(agent.llm.client, 'base_url'):
                    agent_base = str(agent.llm.client.base_url)
                    print(f"  ✅ Agent LLM base_url: {agent_base}")
                    if "openrouter" not in agent_base.lower():
                        print(f"  ❌ WARNING: Agent LLM base_url does NOT contain 'openrouter'!")
            except:
                pass
        
        import sys
        sys.stdout.flush()
        return agent
    
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