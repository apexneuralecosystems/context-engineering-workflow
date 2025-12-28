import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from crewai import Crew, Task
from crewai.flow.flow import Flow, listen, start

from src.rag import RAGPipeline
from src.memory import ZepMemoryLayer
from .agents import Agents
from .tasks import Tasks

class ResearchAssistantState(BaseModel):
    query: str = ""
    user_id: str = "default_user"
    thread_id: str = "default_thread"


class ContextEvaluationResult(BaseModel):
    """Pydantic schema for context evaluation agent output validation"""
    relevant_sources: List[str] = Field(
        ..., 
        description="List of source names that are relevant to the query (e.g., 'RAG', 'Memory', 'Web', 'ArXiv')"
    )
    filtered_context: Dict[str, Any] = Field(
        ..., 
        description="Dictionary containing only relevant information from each source, keyed by source name"
    )
    relevance_scores: Dict[str, float] = Field(
        ..., 
        description="Confidence scores (0-1) for each source's relevance to the query"
    )
    reasoning: str = Field(
        ..., 
        description="Brief explanation of filtering decisions and why certain sources were included/excluded"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "relevant_sources": ["RAG", "Web"],
                "filtered_context": {
                    "RAG": {
                        "status": "OK",
                        "answer": "Relevant document context...",
                        "citations": [{"label": "Paper Title", "locator": "chunk_1"}]
                    },
                    "Web": {
                        "status": "OK", 
                        "answer": "Recent web information...",
                        "citations": [{"label": "Article Title", "locator": "https://example.com"}]
                    }
                },
                "relevance_scores": {
                    "RAG": 0.95,
                    "Memory": 0.3,
                    "Web": 0.85,
                    "ArXiv": 0.1
                },
                "reasoning": "RAG and Web sources contain highly relevant information for the query. Memory has some context but low relevance. ArXiv results don't match the specific query focus."
            }
        }


class ResearchAssistantFlow(Flow[ResearchAssistantState]):
    def __init__(
        self,
        tensorlake_api_key: Optional[str] = None,
        voyage_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        firecrawl_api_key: Optional[str] = None,
        qdrant_db_path: Optional[str] = None,
    ):
        super().__init__()
        
        self.rag_pipeline = RAGPipeline(
            tensorlake_api_key=tensorlake_api_key,
            voyage_api_key=voyage_api_key,
            openrouter_api_key=openrouter_api_key,
            qdrant_db_path=qdrant_db_path
        )
        
        self.memory_layer = ZepMemoryLayer(
            user_id=self.state.user_id,
            thread_id=self.state.thread_id,
            zep_api_key=zep_api_key
        )
        
        # Initialize tasks and agents
        self.tasks = Tasks()
        self.agents = Agents()
        
        # Create agents
        self.rag_agent = self.agents.create_rag_agent(self.rag_pipeline)
        self.memory_agent = self.agents.create_memory_agent(self.memory_layer)
        self.web_search_agent = self.agents.create_web_search_agent(firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY"))
        self.tool_calling_agent = self.agents.create_arxiv_agent()
        self.evaluator_agent = self.agents.create_evaluator_agent()
        self.synthesizer_agent = self.agents.create_synthesizer_agent()
    
    @start()
    def process_query(self) -> Dict[str, Any]:
        query = self.state.query
        
        # Save user query to memory
        summarized_query = self._summarize_for_memory(query, max_length=1500)
        self.memory_layer.save_user_message(summarized_query)
        
        return {
            "query": query,
            "status": "processing",
            "user_id": self.state.user_id,
            "session_id": self.state.thread_id,
        }
    
    @listen(process_query)
    def gather_context_from_all_sources(self, flow_state: Dict[str, Any]) -> Dict[str, Any]:
        query = flow_state["query"]
        
        # Create tasks for each agent
        rag_task = self.tasks.create_rag_search_task(query, self.rag_agent)
        
        memory_task = self.tasks.create_memory_retrieval_task(query, self.memory_agent)
        web_search_task = self.tasks.create_web_search_task(query, self.web_search_agent)
        tool_calling_task = self.tasks.create_arxiv_search_task(query, self.tool_calling_agent)
        
        context_crew = Crew(
            agents=[self.rag_agent, self.memory_agent, self.web_search_agent, self.tool_calling_agent],
            tasks=[rag_task, memory_task, web_search_task, tool_calling_task],
            verbose=True
        )
        
        # Execute crew
        results = context_crew.kickoff()
        
        # Debug: Log raw agent outputs before parsing
        print(f"\n{'='*80}")
        print("DEBUG: Raw Agent Outputs (Before Parsing)")
        print(f"{'='*80}")
        for idx, task_output in enumerate(results.tasks_output):
            source_names = ["rag_result", "memory_result", "web_result", "tool_result"]
            print(f"\n{source_names[idx]} raw output (first 500 chars):")
            print(f"{task_output.raw[:500]}...")
            print(f"Full raw output length: {len(task_output.raw)} chars")
        print(f"{'='*80}\n")
        
        # Parse results from each agent
        context_sources = {
            "rag_result": self._parse_agent_result(results.tasks_output[0].raw),
            "memory_result": self._parse_agent_result(results.tasks_output[1].raw),
            "web_result": self._parse_agent_result(results.tasks_output[2].raw),
            "tool_result": self._parse_agent_result(results.tasks_output[3].raw)
        }
        
        # Debug: Log parsed context sources with full data
        print(f"\n{'='*80}")
        print("DEBUG: Parsed Context Sources (Full Data)")
        print(f"{'='*80}")
        for source_key, source_data in context_sources.items():
            if isinstance(source_data, dict):
                print(f"\n{source_key}:")
                print(f"  status: {source_data.get('status')}")
                print(f"  confidence: {source_data.get('confidence')}")
                print(f"  source_used: {source_data.get('source_used')}")
                print(f"  has_context: {'context' in source_data}")
                print(f"  has_search_results: {'search_results' in source_data}")
                print(f"  context type: {type(source_data.get('context'))}")
                print(f"  search_results type: {type(source_data.get('search_results'))}")
                if 'context' in source_data:
                    context_val = source_data.get('context')
                    if isinstance(context_val, str):
                        print(f"  context length: {len(context_val)} chars")
                        print(f"  context preview: {context_val[:200]}...")
                        # Check if context is empty
                        if not context_val or context_val.strip() == "":
                            print(f"  WARNING: context is empty or whitespace only!")
                    else:
                        print(f"  context: {context_val}")
                if 'search_results' in source_data:
                    search_results = source_data.get('search_results')
                    if isinstance(search_results, list):
                        print(f"  search_results count: {len(search_results)}")
                        if search_results:
                            print(f"  first result keys: {list(search_results[0].keys()) if isinstance(search_results[0], dict) else 'not a dict'}")
                print(f"  all keys: {list(source_data.keys())}")
                # For Memory specifically, ensure context is preserved
                if source_key == "memory_result" and source_data.get("status") == "OK":
                    if "context" not in source_data or not source_data.get("context"):
                        print(f"  ERROR: Memory has OK status but no context field!")
            else:
                print(f"{source_key}: {type(source_data)}")
        print(f"{'='*80}\n")
        
        return {
            **flow_state,
            "context_sources": context_sources,
            "raw_results": [task.raw for task in results.tasks_output]
        }
    
    @listen(gather_context_from_all_sources)
    def evaluate_context_relevance(self, flow_state: Dict[str, Any]) -> Dict[str, Any]:
        query = flow_state["query"]
        context_sources = flow_state["context_sources"]
        
        evaluation_task = self.tasks.create_context_evaluation_task(
            query, context_sources, self.evaluator_agent, ContextEvaluationResult
        )
        
        evaluation_crew = Crew(
            agents=[self.evaluator_agent],
            tasks=[evaluation_task],
            verbose=True
        )
        
        # Execute crew
        evaluation_result = evaluation_crew.kickoff()
        evaluation_output = evaluation_result.tasks_output[0].pydantic
        
        if isinstance(evaluation_output, ContextEvaluationResult):
            filtered_context = evaluation_output.filtered_context
            evaluation_data = evaluation_output.model_dump()
        else:
            print("Pydantic output not available, falling back to raw parsing")
            filtered_context = self._parse_agent_result(evaluation_result.tasks_output[0].raw)
            evaluation_data = {"raw_fallback": evaluation_result.tasks_output[0].raw}
        
        return {
            **flow_state,
            "filtered_context": filtered_context,
            "evaluation_result": evaluation_data,
            "evaluation_raw": evaluation_result.tasks_output[0].raw
        }
    
    @listen(evaluate_context_relevance)
    def synthesize_final_response(self, flow_state: Dict[str, Any]) -> Dict[str, Any]:
        query = flow_state["query"]
        filtered_context = flow_state["filtered_context"]
        evaluation_result = flow_state.get("evaluation_result", {})
        context_sources = flow_state.get("context_sources", {})
        
        synthesis_task = self.tasks.create_synthesis_task(
            query, filtered_context, self.synthesizer_agent
        )
        
        synthesis_crew = Crew(
            agents=[self.synthesizer_agent],
            tasks=[synthesis_task],
            verbose=True
        )
        
        # Execute crew
        synthesis_result = synthesis_crew.kickoff()
        final_response = synthesis_result.tasks_output[0].raw
        
        # Save summarized assistant response to memory
        summarized_response = self._summarize_for_memory(final_response)
        self.memory_layer.save_assistant_message(summarized_response)
        
        # Debug: Log evaluation result structure
        print(f"\n{'='*80}")
        print("DEBUG: Evaluation Result Structure")
        print(f"{'='*80}")
        print(f"evaluation_result type: {type(evaluation_result)}")
        if isinstance(evaluation_result, dict):
            print(f"evaluation_result keys: {list(evaluation_result.keys())}")
        print(f"context_sources keys: {list(context_sources.keys()) if isinstance(context_sources, dict) else 'Not a dict'}")
        
        # Determine status, source_used, and confidence from evaluation and context sources
        # Handle both dict and Pydantic model formats
        if isinstance(evaluation_result, dict):
            relevant_sources = evaluation_result.get("relevant_sources", [])
            relevance_scores = evaluation_result.get("relevance_scores", {})
        else:
            # If it's a Pydantic model or other format
            relevant_sources = getattr(evaluation_result, "relevant_sources", []) if hasattr(evaluation_result, "relevant_sources") else []
            relevance_scores = getattr(evaluation_result, "relevance_scores", {}) if hasattr(evaluation_result, "relevance_scores") else {}
        
        print(f"relevant_sources: {relevant_sources}")
        print(f"relevance_scores: {relevance_scores}")
        print(f"{'='*80}\n")
        
        # Collect all sources with OK status and their confidences (regardless of evaluation)
        available_sources = []
        source_confidences = {}
        
        for source_name, source_key in [("RAG", "rag_result"), ("Memory", "memory_result"), 
                                       ("Web", "web_result"), ("ArXiv", "tool_result")]:
            source_data = context_sources.get(source_key, {})
            if isinstance(source_data, dict):
                source_status = source_data.get("status", "")
                source_conf = source_data.get("confidence", 0.0)
                
                # Include sources with OK status, even if not in relevant_sources
                if source_status == "OK":
                    available_sources.append(source_name)
                    source_confidences[source_name] = source_conf
                    print(f"Found available source: {source_name} with confidence {source_conf}")
        
        # Determine primary source used
        # Priority: 1) relevant_sources with relevance_scores, 2) available_sources with confidences
        if relevant_sources and relevance_scores:
            # Use the source with highest relevance score from evaluation
            source_used = max(relevant_sources, key=lambda s: relevance_scores.get(s, source_confidences.get(s, 0.0)))
            print(f"Using source from relevant_sources: {source_used}")
        elif available_sources:
            # Fallback: use the source with highest confidence from source data
            source_used = max(available_sources, key=lambda s: source_confidences.get(s, 0.0))
            print(f"Using source from available_sources: {source_used}")
        else:
            source_used = "NONE"
            print("No available sources found, using NONE")
        
        # Calculate overall confidence
        # Priority: 1) relevance_score for source_used, 2) confidence from source data, 3) max of all
        if source_used != "NONE":
            if source_used in relevance_scores:
                confidence = relevance_scores[source_used]
                print(f"Using relevance_score for {source_used}: {confidence}")
            elif source_used in source_confidences:
                confidence = source_confidences[source_used]
                print(f"Using source confidence for {source_used}: {confidence}")
            elif relevance_scores:
                confidence = max(relevance_scores.values())
                print(f"Using max relevance_score: {confidence}")
            elif source_confidences:
                confidence = max(source_confidences.values())
                print(f"Using max source confidence: {confidence}")
            else:
                confidence = 0.0
                print("No confidence scores available, defaulting to 0.0")
        else:
            confidence = 0.0
            print("Source is NONE, confidence is 0.0")
        
        # Determine status based on confidence and available context
        if confidence > 0.5 and final_response:
            status = "OK"
        elif confidence > 0.0:
            status = "OK"  # Even low confidence is OK if we have some context
        else:
            status = "INSUFFICIENT_CONTEXT"
        
        # Extract citations from context sources
        citations = []
        for source_data in context_sources.values():
            if isinstance(source_data, dict):
                source_citations = source_data.get("citations", [])
                if source_citations:
                    citations.extend(source_citations)
        
        return {
            **flow_state,
            "final_response": final_response,
            "synthesis_raw": final_response,
            "status": status,
            "source_used": source_used,
            "answer": final_response,
            "confidence": confidence,
            "citations": citations,
            "missing": [] if status == "OK" else ["Additional context needed to fully answer the query"],
            "context_sources": context_sources,  # Ensure context sources are included
            "evaluation_result": evaluation_result,  # Include evaluation result for frontend display
            "flow_status": "completed"
        }
    
    def _parse_agent_result(self, raw_result: str) -> Dict[str, Any]:
        try:
            # Try to parse as JSON first
            parsed = json.loads(raw_result)
            
            # Ensure status is set - if it's missing, try to infer from content
            if "status" not in parsed:
                if "error" in parsed or "Error" in str(parsed):
                    parsed["status"] = "ERROR"
                elif not parsed.get("answer") and not parsed.get("citations"):
                    parsed["status"] = "INSUFFICIENT_CONTEXT"
                else:
                    parsed["status"] = "OK"
            
            # Preserve all original fields (context, search_results, etc.)
            # This ensures Memory and Web data is not lost
            return parsed
        except json.JSONDecodeError:
            # If it's not JSON, check if it looks like an error
            raw_lower = raw_result.lower()
            if "error" in raw_lower or "failed" in raw_lower:
                return {
                    "status": "ERROR",
                    "source_used": "UNKNOWN",
                    "answer": raw_result,
                    "error": raw_result,
                    "citations": [],
                    "confidence": 0.0
                }
            else:
                return {
                    "status": "OK",
                    "source_used": "UNKNOWN",
                    "answer": raw_result,
                    "citations": [],
                    "confidence": 0.5
                }
    
    def _summarize_for_memory(self, response: str, max_length: int = 2000) -> str:
        if len(response) <= max_length:
            return response
        
        truncated = response[:max_length]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > max_length * 0.7: 
            return truncated[:last_sentence_end + 1] + " [Response truncated for memory storage]"
        else:
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:
                return truncated[:last_space] + "... [Response truncated for memory storage]"
            else:
                return truncated + "... [Response truncated for memory storage]"
    
    def process_documents(self, document_paths: List[str]) -> Dict[str, Any]:
        return self.rag_pipeline.process_documents(document_paths)


def create_research_assistant_flow(**kwargs) -> ResearchAssistantFlow:
    return ResearchAssistantFlow(**kwargs)
