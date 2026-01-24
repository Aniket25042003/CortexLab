"""
Literature Scout Agent Node

Searches Google Scholar for relevant papers via SerpAPI.
"""

from app.agents.state import DiscoveryState
from app.agents.tools.google_scholar import search_google_scholar


async def literature_scout_node(state: DiscoveryState) -> DiscoveryState:
    """
    Search for relevant papers using the search queries.
    
    Input: search_queries from scope clarifier
    Output: papers list with metadata
    """
    search_queries = state.get("search_queries", [])
    
    import logging
    logger = logging.getLogger(__name__)
    
    if not search_queries:
        logger.warning("[LITERATURE_SCOUT] No search queries provided")
        return {
            **state,
            "error": "No search queries available",
            "current_step": "error",
        }
    
    logger.info(f"[LITERATURE_SCOUT] Searching for {len(search_queries)} queries: {search_queries[:3]}...")
    
    all_papers = []
    seen_ids = set()
    
    try:
        # Search with each query
        for query in search_queries[:5]:  # Limit to first 5 queries
            papers = await search_google_scholar(query, limit=20)
            
            for paper in papers:
                if paper["id"] not in seen_ids:
                    seen_ids.add(paper["id"])
                    all_papers.append(paper)
        
        # Sort by citation count (descending)
        all_papers.sort(key=lambda x: x.get("citation_count", 0) or 0, reverse=True)
        
        # Limit total papers
        all_papers = all_papers[:50]
        
        return {
            **state,
            "papers": all_papers,
            "current_step": "papers_retrieved",
            "messages": state.get("messages", []) + [{
                "type": "agent_note",
                "agent": "literature_scout",
                "content": f"Found {len(all_papers)} relevant papers"
            }]
        }
    except Exception as e:
        return {
            **state,
            "error": f"Literature search failed: {str(e)}",
            "current_step": "error",
        }
