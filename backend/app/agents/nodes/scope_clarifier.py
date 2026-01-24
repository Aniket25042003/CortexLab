"""
Scope Clarifier Agent Node

Analyzes user query to establish research domain boundaries and search strategy.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings
from app.agents.state import DiscoveryState

settings = get_settings()


SCOPE_CLARIFIER_PROMPT = """You are a research scope clarifier agent. Your job is to analyze a researcher's query and establish clear boundaries for the research exploration.

Given the user's research interest:
"{user_query}"

Analyze and provide:
1. Domain Boundaries: Break down the research area into hierarchical levels (field → subfield → specific topic)
2. Search Queries: Generate 5-10 effective search queries for academic databases
3. Constraints: Identify any constraints mentioned (target venues, datasets, compute limitations, timeframe)

Respond in the following JSON format:
{{
    "domain_boundaries": {{
        "field": "e.g., Computer Vision",
        "subfield": "e.g., Image Classification", 
        "specific_topic": "e.g., Fine-grained Recognition under Distribution Shift",
        "related_areas": ["list of related topics to also search"]
    }},
    "search_queries": [
        "query 1",
        "query 2"
    ],
    "constraints": {{
        "target_venues": ["optional list of target conferences/journals"],
        "datasets": ["any specific datasets mentioned"],
        "compute_level": "low/medium/high or null",
        "recency": "focus on papers from last N years or null"
    }}
}}
"""


async def scope_clarifier_node(state: DiscoveryState) -> DiscoveryState:
    """
    Process user query to establish research scope.
    
    Input: user_query
    Output: domain_boundaries, search_queries, constraints
    """
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"[SCOPE_CLARIFIER] Processing query: {state['user_query']}")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-lite-latest",
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )
    
    prompt = ChatPromptTemplate.from_template(SCOPE_CLARIFIER_PROMPT)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"user_query": state["user_query"]})
        
        # Parse JSON from response
        content = response.content
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content.strip())
        
        return {
            **state,
            "domain_boundaries": result.get("domain_boundaries"),
            "search_queries": result.get("search_queries", []),
            "constraints": result.get("constraints"),
            "current_step": "scope_clarified",
            "messages": state.get("messages", []) + [{
                "type": "agent_note",
                "agent": "scope_clarifier",
                "content": f"Identified research scope: {result.get('domain_boundaries', {}).get('specific_topic', 'Unknown')}"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Scope clarification failed: {str(e)}",
            "current_step": "error",
        }
