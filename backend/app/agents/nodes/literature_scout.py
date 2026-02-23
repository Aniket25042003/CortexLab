"""
Literature Scout Agent Node

Searches Google Scholar for relevant papers via SerpAPI.
Falls back to the raw user_query if no search queries were produced by scope_clarifier.
"""

from app.agents.state import DiscoveryState
from app.agents.tools.google_scholar import search_google_scholar

import logging
logger = logging.getLogger(__name__)


async def literature_scout_node(state: DiscoveryState) -> DiscoveryState:
    """
    Search for relevant papers using the search queries.

    Input:  search_queries (from scope clarifier), or user_query as fallback
    Output: papers list with metadata
    """
    search_queries: list = state.get("search_queries") or []
    user_query: str = state.get("user_query", "")

    # ── Fallback: generate basic queries from user_query directly ─────────────
    if not search_queries and user_query:
        logger.warning(
            "[LITERATURE_SCOUT] No search queries from scope_clarifier — "
            "generating fallback queries from user_query."
        )
        # Simple keyword-based fallback queries
        base = user_query.strip()
        search_queries = [
            base,
            f"{base} survey",
            f"{base} review",
            f"{base} state of the art",
            f"{base} recent advances",
        ]

    if not search_queries:
        logger.error("[LITERATURE_SCOUT] No search queries available and no user_query to fall back to.")
        return {
            **state,
            "error": "No search queries available — scope clarification likely failed.",
            "current_step": "error",
        }

    logger.info(f"[LITERATURE_SCOUT] Searching with {len(search_queries)} queries: {search_queries[:3]}...")

    all_papers = []
    seen_ids: set = set()

    try:
        for query in search_queries[:5]:          # limit to first 5 queries  
            papers = await search_google_scholar(query, limit=20)
            for paper in papers:
                pid = paper.get("id") or paper.get("title", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_papers.append(paper)

        # Sort by citation count descending, limit total
        all_papers.sort(key=lambda x: x.get("citation_count") or 0, reverse=True)
        all_papers = all_papers[:50]

        logger.info(f"[LITERATURE_SCOUT] Retrieved {len(all_papers)} unique papers.")

        # If SerpAPI is not configured we get 0 papers — that's fine;
        # downstream nodes will do their best with empty lists.
        return {
            **state,
            "papers": all_papers,
            "current_step": "papers_retrieved",
            "messages": state.get("messages", []) + [{
                "type": "agent_note",
                "agent": "literature_scout",
                "content": f"Found {len(all_papers)} relevant papers",
            }],
        }

    except Exception as e:
        logger.error(f"[LITERATURE_SCOUT] Search failed: {e}")
        return {
            **state,
            "error": f"Literature search failed: {e}",
            "current_step": "error",
        }
