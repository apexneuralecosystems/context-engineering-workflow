# Confidence Scores in Research Assistant

## Overview

Confidence scores (0.0 to 1.0) indicate how confident the system is that the retrieved information is **relevant and sufficient** to answer the user's query. A score of 0.98 means 98% confidence.

## How Confidence is Calculated

### 1. **Memory Tool** (`src/tools/memory_tool.py`)
- **Fixed Score: 0.98** when memory is found
- **Score: 0.0** when no memory is found or on error
- **Rationale**: Conversation history is considered highly reliable since it's from previous interactions with the same user

```python
"confidence": 0.98  # Fixed high confidence for memory
```

### 2. **RAG Tool** (`src/tools/rag_tool.py`)
- **Dynamic Score**: Uses the **maximum similarity score** from vector search results
- **Calculation**: `max([r.get("score", 0.0) for r in context_results])`
- **Range**: 0.0 to 1.0 (cosine similarity from Qdrant vector search)
- **Rationale**: The highest similarity score indicates how well the retrieved document chunks match the query

```python
# Line 149 in rag_tool.py
"confidence": max([r.get("score", 0.0) for r in context_results])
```

The similarity score comes from Qdrant's vector search (`hit.score` in `retriever.py` line 215), which uses **cosine similarity**:
- **1.0** = Perfect match (vectors are identical, angle = 0°)
- **0.9-0.99** = Very high similarity (angle < 25°)
- **0.7-0.89** = Good similarity (angle 25-45°)
- **0.5-0.69** = Moderate similarity (angle 45-60°)
- **< 0.5** = Lower similarity (angle > 60°)

**Note**: Qdrant returns cosine similarity scores directly, where:
- Higher score = More similar vectors = Better match
- The score represents the cosine of the angle between query and document vectors

### 3. **Web Search Tool** (`src/tools/web_search_tool.py`)
- **Fixed Score: 0.97** when search results are found
- **Score: 0.0** when no results or on error
- **Rationale**: Web search results are considered reliable but slightly less than memory (due to potential staleness or relevance issues)

```python
"confidence": 0.97  # Fixed high confidence for web search
```

### 4. **ArXiv Tool** (`src/tools/arxiv_tool.py`)
- **Fixed Score: 0.92** when papers are found
- **Score: 0.0** when no papers or on error
- **Rationale**: Academic papers are reliable but may not always directly answer the query

```python
"confidence": 0.92  # Fixed confidence for ArXiv papers
```

### 5. **Structured Response Generator** (`src/generation/generation.py`)
- **LLM-Generated Score**: The LLM (GPT-4o-mini) generates a confidence score based on:
  - How well the context answers the query
  - Completeness of the information
  - Quality of citations
- **Range**: 0.0 to 1.0 (as specified in the response schema)
- **Rationale**: The LLM evaluates the overall quality and sufficiency of the answer

```python
# Schema definition (line 44 in generation.py)
"confidence": {"type": "number", "minimum": 0, "maximum": 1}
```

## Confidence Score Interpretation

| Score Range | Meaning | Example |
|------------|---------|---------|
| **0.95 - 1.0** | Very High Confidence | Perfect match, complete answer |
| **0.85 - 0.94** | High Confidence | Strong match, mostly complete |
| **0.70 - 0.84** | Moderate Confidence | Good match, some gaps |
| **0.50 - 0.69** | Low Confidence | Partial match, significant gaps |
| **0.0 - 0.49** | Very Low Confidence | Poor match or error |

## Where Confidence is Used

1. **Source Evaluation** (`src/workflows/flow.py`):
   - The evaluator agent uses confidence scores to determine which sources are relevant
   - Sources with higher confidence are more likely to be included in the final answer

2. **UI Display** (`app.py`):
   - Confidence scores are displayed next to each source
   - Helps users understand the reliability of each information source

3. **Response Filtering**:
   - Sources with very low confidence (< 0.5) may be excluded from the final synthesis
   - Only high-confidence sources are used to generate the final answer

## Example: Confidence 0.98

When you see **"Confidence: 0.98"**, it typically means:

1. **Memory Source**: The system found relevant conversation history (fixed 0.98)
2. **RAG Source**: The vector search returned a document chunk with 0.98 similarity score
3. **LLM Evaluation**: The LLM determined the answer is 98% complete and accurate

## Factors Affecting Confidence

### For RAG (Dynamic):
- **Query-document similarity**: How well the query matches the document content
- **Embedding quality**: Quality of the Voyage AI embeddings
- **Vector search accuracy**: How well Qdrant finds relevant chunks

### For All Sources:
- **Data quality**: Accuracy and completeness of source data
- **Relevance**: How directly the source answers the query
- **Completeness**: Whether the source provides a complete answer

## Improving Confidence Scores

1. **Better Documents**: Upload more relevant, high-quality documents
2. **Better Queries**: Ask more specific, well-formed questions
3. **Better Embeddings**: Use high-quality embedding models (Voyage AI)
4. **More Context**: Provide more context in queries for better matching

