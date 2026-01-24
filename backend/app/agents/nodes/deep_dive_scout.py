"""
Deep Dive Scout Agent Node

Performs targeted search for a specific research direction,
gathering baselines, datasets, metrics, and failure cases.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings
from app.agents.state import DeepDiveState
from app.agents.tools.google_scholar import search_google_scholar
import json

settings = get_settings()


DEEP_DIVE_ANALYSIS_PROMPT = """You are a research deep dive analyst. Given a specific research direction, analyze the gathered papers to extract detailed information for experiment planning.

Research Direction:
Title: {direction_title}
Description: {direction_description}
Novelty Angle: {novelty_angle}

Papers found for this direction:
{papers_text}

Analyze these papers and extract:

1. **Baseline Methods**: What are the established baseline methods that any new work must compare against?
2. **Standard Datasets**: What datasets are commonly used for evaluation in this area?
3. **Evaluation Metrics**: What metrics are standard for measuring performance?
4. **Known Failure Cases**: What scenarios or edge cases do current methods struggle with?
5. **Implementation Details**: Common architectures, hyperparameters, training procedures mentioned.

Respond in JSON format:
{{
    "baseline_methods": [
        {{
            "name": "method name",
            "description": "brief description",
            "performance_summary": "typical performance metrics",
            "paper_reference": "paper title that describes it"
        }}
    ],
    "datasets": [
        {{
            "name": "dataset name",
            "description": "what it contains",
            "size": "approximate size",
            "url": "if mentioned",
            "common_splits": "train/val/test splits if standard"
        }}
    ],
    "metrics": [
        {{
            "name": "metric name",
            "description": "what it measures",
            "formula": "if applicable",
            "typical_range": "expected values"
        }}
    ],
    "failure_cases": [
        {{
            "scenario": "description of failure case",
            "why_it_fails": "reason current methods struggle",
            "potential_solution_hints": "any mentioned approaches"
        }}
    ],
    "implementation_notes": {{
        "common_architectures": ["list of architectures"],
        "typical_hyperparameters": {{}},
        "training_tips": ["any tips mentioned"],
        "compute_requirements": "typical GPU/time requirements"
    }}
}}
"""


SEARCH_QUERIES_PROMPT = """Generate 5 specific search queries to find papers about baselines, datasets, and methods for this research direction:

Direction: {direction_title}
Description: {direction_description}

Focus on finding:
1. Survey papers that cover baselines
2. Benchmark papers with dataset comparisons
3. Recent state-of-the-art methods
4. Analysis papers discussing limitations

Return as a JSON array of search query strings:
["query 1", "query 2", "query 3", "query 4", "query 5"]
"""


async def deep_dive_scout_node(state: DeepDiveState) -> DeepDiveState:
    """
    Scout for detailed information about a chosen research direction.
    
    Input: direction (dict with title, description, novelty_angle)
    Output: baseline_methods, datasets, metrics, failure_cases
    """
    direction = state.get("direction", {})
    
    if not direction:
        return {
            **state,
            "error": "No direction provided for deep dive",
            "current_step": "error",
        }
    
    direction_title = direction.get("title", "Unknown direction")
    direction_description = direction.get("description", "")
    novelty_angle = direction.get("novelty_angle", "")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )
    
    try:
        # Step 1: Generate targeted search queries
        query_prompt = ChatPromptTemplate.from_template(SEARCH_QUERIES_PROMPT)
        query_chain = query_prompt | llm
        
        query_response = await query_chain.ainvoke({
            "direction_title": direction_title,
            "direction_description": direction_description,
        })
        
        # Parse search queries
        query_content = query_response.content
        if "```json" in query_content:
            query_content = query_content.split("```json")[1].split("```")[0]
        elif "```" in query_content:
            query_content = query_content.split("```")[1].split("```")[0]
        
        search_queries = json.loads(query_content.strip())
        
        # Step 2: Search for papers with each query
        all_papers = []
        seen_ids = set()
        
        for query in search_queries[:5]:
            papers = await search_google_scholar(query, limit=15)
            for paper in papers:
                if paper["id"] not in seen_ids:
                    seen_ids.add(paper["id"])
                    all_papers.append(paper)
        
        # Sort by citation count and limit
        all_papers.sort(key=lambda x: x.get("citation_count", 0) or 0, reverse=True)
        all_papers = all_papers[:30]
        
        # Step 3: Analyze papers for deep dive information
        papers_text = "\n\n".join([
            f"Title: {p.get('title', 'Unknown')}\n"
            f"Year: {p.get('year', 'Unknown')}\n"
            f"Citations: {p.get('citation_count', 0)}\n"
            f"Abstract: {p.get('abstract', 'No abstract')[:600]}..."
            for p in all_papers[:25]
        ])
        
        analysis_prompt = ChatPromptTemplate.from_template(DEEP_DIVE_ANALYSIS_PROMPT)
        analysis_chain = analysis_prompt | llm
        
        analysis_response = await analysis_chain.ainvoke({
            "direction_title": direction_title,
            "direction_description": direction_description,
            "novelty_angle": novelty_angle,
            "papers_text": papers_text,
        })
        
        # Parse analysis result
        content = analysis_response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content.strip())
        
        return {
            **state,
            "baseline_methods": result.get("baseline_methods", []),
            "datasets": result.get("datasets", []),
            "metrics": result.get("metrics", []),
            "failure_cases": result.get("failure_cases", []),
            "implementation_notes": result.get("implementation_notes", {}),
            "deep_dive_papers": all_papers,
            "current_step": "deep_dive_complete",
            "messages": state.get("messages", []) + [
                {
                    "type": "agent_note",
                    "agent": "deep_dive_scout",
                    "content": f"Found {len(result.get('baseline_methods', []))} baselines, "
                              f"{len(result.get('datasets', []))} datasets, "
                              f"{len(result.get('metrics', []))} metrics"
                }
            ]
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Deep dive scouting failed: {str(e)}",
            "current_step": "error",
        }
